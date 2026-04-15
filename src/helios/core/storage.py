"""SQLite persistence for immutable audit records."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Any, cast
from uuid import UUID, uuid4

from sqlmodel import Field, Session, SQLModel, create_engine, select

from helios.core.audit_record import AuditRecord


class AuditRecordRow(SQLModel, table=True):
    """Database row storing serialized audit record JSON."""

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    run_id: UUID = Field(index=True)
    start_time: datetime = Field(index=True)
    pipeline_name: str = Field(index=True)
    record_json: str


class AuditStorage:
    """SQLite-backed storage for HELIOS audit records."""

    def __init__(self, database_url: str | None = None) -> None:
        db_url = database_url or f"sqlite:///{Path('~/.helios/helios.db').expanduser()}"
        if db_url.startswith("sqlite:///"):
            db_path = Path(db_url.removeprefix("sqlite:///"))
            db_path.parent.mkdir(parents=True, exist_ok=True)
        self.engine = create_engine(db_url)
        SQLModel.metadata.create_all(self.engine)

    def save_record(self, record: AuditRecord) -> None:
        """Persist an audit record."""
        row = AuditRecordRow(
            run_id=record.run_id,
            start_time=record.start_time,
            pipeline_name=record.pipeline_name,
            record_json=record.to_json(),
        )
        with Session(self.engine) as session:
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
    ) -> list[AuditRecord]:
        """List records ordered by start time descending."""
        with Session(self.engine) as session:
            # SQLModel's field descriptor typing is broader at runtime than static type inference.
            statement = select(AuditRecordRow).order_by(cast(Any, AuditRecordRow.start_time))
            if pipeline_filter:
                statement = statement.where(AuditRecordRow.pipeline_name == pipeline_filter)
            statement = statement.offset(offset).limit(limit)
            rows = session.exec(statement).all()
            return [AuditRecord.model_validate_json(row.record_json) for row in rows]

