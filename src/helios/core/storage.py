"""SQLite persistence for audit records (mutable store; integrity is the trust-store signature)."""

from __future__ import annotations

import contextlib
from datetime import datetime
from pathlib import Path
from typing import Any, cast
from uuid import UUID, uuid4

from sqlalchemy import desc, event, text
from sqlmodel import Field, Session, SQLModel, create_engine, select

from helios.core.audit_record import AuditRecord


class AuditRecordRow(SQLModel, table=True):
    """Database row storing serialized audit record JSON."""

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    run_id: UUID = Field(index=True, unique=True)
    start_time: datetime = Field(index=True)
    pipeline_name: str = Field(index=True)
    record_json: str


def _sqlite_connect_args(db_url: str) -> dict[str, Any]:
    if db_url.startswith("sqlite"):
        return {"check_same_thread": False}
    return {}


_RUN_ID_UNIQUE_INDEX = "ix_auditrecordrow_run_id"


def _enable_sqlite_wal(engine: Any) -> None:
    @event.listens_for(engine, "connect")
    def _set_sqlite_pragma(dbapi_connection: Any, _connection_record: Any) -> None:
        cursor = dbapi_connection.cursor()
        try:
            cursor.execute("PRAGMA journal_mode=WAL")
        finally:
            cursor.close()


def _run_id_has_unique_index(connection: Any) -> bool:
    listed = connection.execute(text("PRAGMA index_list('auditrecordrow')")).fetchall()
    for row in listed:
        name = str(row[1])
        is_unique = bool(row[2])
        if not is_unique:
            continue
        if not name.replace("_", "").isalnum():
            continue
        columns = connection.execute(text(f"PRAGMA index_info('{name}')")).fetchall()
        if [str(col[2]) for col in columns] == ["run_id"]:
            return True
    return False


def _ensure_run_id_unique(engine: Any) -> None:
    """Dedupe existing rows, then add a unique index for pre-create_all databases."""
    with engine.begin() as connection:
        if _run_id_has_unique_index(connection):
            return
    with Session(engine) as session:
        rows = session.exec(select(AuditRecordRow)).all()
        keep: dict[UUID, AuditRecordRow] = {}
        extras: list[AuditRecordRow] = []
        for row in rows:
            current = keep.get(row.run_id)
            if current is None:
                keep[row.run_id] = row
                continue
            if row.start_time >= current.start_time:
                extras.append(current)
                keep[row.run_id] = row
            else:
                extras.append(row)
        for extra in extras:
            session.delete(extra)
        if extras:
            session.commit()
    with engine.begin() as connection:
        connection.execute(text(f'DROP INDEX IF EXISTS "{_RUN_ID_UNIQUE_INDEX}"'))
        connection.execute(
            text(f'CREATE UNIQUE INDEX "{_RUN_ID_UNIQUE_INDEX}" ON auditrecordrow (run_id)')
        )


class AuditStorage:
    """SQLite-backed storage for HELIOS audit records."""

    def __init__(self, database_url: str | None = None) -> None:
        db_url = database_url or f"sqlite:///{Path('~/.helios/helios.db').expanduser()}"
        db_path: Path | None = None
        if db_url.startswith("sqlite:///"):
            db_path = Path(db_url.removeprefix("sqlite:///"))
            db_path.parent.mkdir(parents=True, exist_ok=True)
            with contextlib.suppress(OSError):
                db_path.parent.chmod(0o700)
        self.engine = create_engine(db_url, connect_args=_sqlite_connect_args(db_url))
        if db_url.startswith("sqlite"):
            _enable_sqlite_wal(self.engine)
        SQLModel.metadata.create_all(self.engine)
        if db_url.startswith("sqlite"):
            _ensure_run_id_unique(self.engine)
        if db_path is not None and db_path.exists():
            with contextlib.suppress(OSError):
                db_path.chmod(0o600)

    def save_record(self, record: AuditRecord) -> None:
        """Persist an audit record. Duplicate run_id is rejected (append-only)."""
        with Session(self.engine) as session:
            existing = session.exec(
                select(AuditRecordRow).where(AuditRecordRow.run_id == record.run_id)
            ).first()
            if existing is not None:
                raise ValueError(f"Audit record {record.run_id} already exists")
            row = AuditRecordRow(
                run_id=record.run_id,
                start_time=record.start_time,
                pipeline_name=record.pipeline_name,
                record_json=record.to_json(),
            )
            session.add(row)
            session.commit()

    def get_record(self, run_id: UUID) -> AuditRecord | None:
        """Retrieve a record by run identifier."""
        with Session(self.engine) as session:
            statement = select(AuditRecordRow).where(AuditRecordRow.run_id == run_id)
            row = session.exec(statement).first()
            if row is None:
                return None
            return AuditRecord.model_validate_json(row.record_json)

    def list_records(
        self,
        limit: int = 20,
        offset: int = 0,
        pipeline_filter: str | None = None,
        start_time: datetime | None = None,
        end_time: datetime | None = None,
    ) -> list[AuditRecord]:
        """List records ordered by start time descending."""
        with Session(self.engine) as session:
            # SQLModel's field descriptor typing is broader at runtime than static type inference.
            start_col = cast(Any, AuditRecordRow.start_time)
            statement = select(AuditRecordRow).order_by(desc(start_col))
            if pipeline_filter:
                statement = statement.where(AuditRecordRow.pipeline_name == pipeline_filter)
            if start_time is not None:
                statement = statement.where(start_col >= start_time)
            if end_time is not None:
                statement = statement.where(start_col <= end_time)
            statement = statement.offset(offset).limit(limit)
            rows = session.exec(statement).all()
            return [AuditRecord.model_validate_json(row.record_json) for row in rows]

    def count_records(
        self,
        pipeline_filter: str | None = None,
        start_time: datetime | None = None,
        end_time: datetime | None = None,
    ) -> int:
        """Count records matching optional pipeline/time filters."""
        with Session(self.engine) as session:
            start_col = cast(Any, AuditRecordRow.start_time)
            statement = select(AuditRecordRow)
            if pipeline_filter:
                statement = statement.where(AuditRecordRow.pipeline_name == pipeline_filter)
            if start_time is not None:
                statement = statement.where(start_col >= start_time)
            if end_time is not None:
                statement = statement.where(start_col <= end_time)
            return len(list(session.exec(statement).all()))

    def delete_record(self, run_id: UUID) -> bool:
        """Delete an audit record by run identifier (operator maintenance)."""
        with Session(self.engine) as session:
            statement = select(AuditRecordRow).where(AuditRecordRow.run_id == run_id)
            row = session.exec(statement).first()
            if row is None:
                return False
            session.delete(row)
            session.commit()
            return True
