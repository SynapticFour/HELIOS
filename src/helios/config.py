"""Typed HELIOS configuration loaded from TOML and environment variables."""

from pathlib import Path
from typing import Any, Literal

from pydantic import BaseModel, Field
from pydantic_settings import (
    BaseSettings,
    PydanticBaseSettingsSource,
    SettingsConfigDict,
    TomlConfigSettingsSource,
)


class ChecksConfig(BaseModel):
    """Configuration for compliance checks."""

    enabled: list[str] = Field(
        default_factory=lambda: [
            "reference_genome",
            "container_pinning",
            "mane_transcripts",
            "vus_rate",
            "crypt4gh_output",
        ]
    )
    reference_genome_required: str = "GRCh38"
    mane_pass_threshold: float = 0.90
    mane_warn_threshold: float = 0.50
    container_digest_required: bool = True
    vus_warn_threshold: float = 0.40
    vus_fail_threshold: float = 0.70


class ExportConfig(BaseModel):
    """Configuration for report export behavior."""

    default_format: Literal["json", "pdf", "rocrate"] = "json"
    output_dir: Path = Path("./helios-reports")
    include_rocrate: bool = False
    ai_act_fragment: bool = False


class DashboardConfig(BaseModel):
    """Configuration for dashboard API server."""

    host: str = "127.0.0.1"
    port: int = 8765
    allowed_origins: list[str] = Field(default_factory=lambda: ["http://localhost:8765"])
    # Nested TOML/env: HELIOS_DASHBOARD__API_KEY (prefer top-level HELIOS_DASHBOARD_API_KEY).
    api_key: str | None = None
    # Deletion is off by default; audit rows are append-only unless explicitly enabled.
    allow_delete: bool = False
    max_import_bytes: int = 10 * 1024 * 1024


class HeliosTomlSource(TomlConfigSettingsSource):
    """TOML source that unwraps a top-level [helios] table."""

    def __call__(self) -> dict[str, Any]:
        data = super().__call__()
        nested = data.get("helios")
        if isinstance(nested, dict):
            return nested
        return data


class HeliosSettings(BaseSettings):
    """Top-level HELIOS configuration."""

    model_config = SettingsConfigDict(
        toml_file="helios.toml",
        env_prefix="HELIOS_",
        env_nested_delimiter="__",
        extra="ignore",
    )

    signing_key: Path = Path("~/.helios/keys/helios.key")
    trusted_keys_dir: Path = Path("~/.helios/keys")
    audit_db: Path = Path("~/.helios/helios.db")
    cache_dir: Path = Path("~/.helios/cache")
    log_level: str = "INFO"
    command_timeout_seconds: int = 86_400
    checks: ChecksConfig = Field(default_factory=ChecksConfig)
    export: ExportConfig = Field(default_factory=ExportConfig)
    dashboard: DashboardConfig = Field(default_factory=DashboardConfig)
    # Preferred env: HELIOS_DASHBOARD_API_KEY (maps via env_prefix + field name).
    dashboard_api_key: str | None = None

    def model_post_init(self, __context: object) -> None:
        """Expand home references for configured path settings."""
        object.__setattr__(self, "signing_key", self.signing_key.expanduser())
        object.__setattr__(self, "trusted_keys_dir", self.trusted_keys_dir.expanduser())
        object.__setattr__(self, "audit_db", self.audit_db.expanduser())
        object.__setattr__(self, "cache_dir", self.cache_dir.expanduser())
        export_value = self.export.model_copy(
            update={"output_dir": self.export.output_dir.expanduser()}
        )
        object.__setattr__(self, "export", export_value)
        # Prefer HELIOS_DASHBOARD_API_KEY; fall back to nested dashboard.api_key.
        resolved_key = self.dashboard_api_key or self.dashboard.api_key
        if resolved_key != self.dashboard_api_key:
            object.__setattr__(self, "dashboard_api_key", resolved_key)
        if resolved_key != self.dashboard.api_key:
            object.__setattr__(
                self,
                "dashboard",
                self.dashboard.model_copy(update={"api_key": resolved_key}),
            )

    def require_dashboard_api_key(self) -> str:
        """Return the configured dashboard API key or raise if missing."""
        key = self.dashboard_api_key or self.dashboard.api_key
        if not key:
            raise ValueError(
                "HELIOS_DASHBOARD_API_KEY is required to run the dashboard. "
                "Generate a secret and export it before `helios serve` or `make up`."
            )
        return key

    def redacted_dump(self) -> dict[str, Any]:
        """JSON-ready settings with secrets replaced."""
        payload = self.model_dump(mode="json")
        _redact_secret(payload, "dashboard_api_key")
        dashboard = payload.get("dashboard")
        if isinstance(dashboard, dict):
            _redact_secret(dashboard, "api_key")
        return payload

    @classmethod
    def settings_customise_sources(
        cls,
        settings_cls: type[BaseSettings],
        init_settings: PydanticBaseSettingsSource,
        env_settings: PydanticBaseSettingsSource,
        dotenv_settings: PydanticBaseSettingsSource,
        file_secret_settings: PydanticBaseSettingsSource,
    ) -> tuple[PydanticBaseSettingsSource, ...]:
        """Enable TOML file loading while preserving env/init precedence."""
        return (
            init_settings,
            env_settings,
            dotenv_settings,
            HeliosTomlSource(settings_cls),
            file_secret_settings,
        )


def _redact_secret(mapping: dict[str, Any], key: str) -> None:
    value = mapping.get(key)
    if isinstance(value, str) and value:
        mapping[key] = "***"


def load_config(path: str | None = None) -> HeliosSettings:
    """Load HELIOS settings from an optional TOML file path and environment."""
    if path is None:
        return HeliosSettings()
    config_path = Path(path)
    if not config_path.exists():
        raise FileNotFoundError(f"Configuration file not found: {config_path}")
    from tomllib import loads

    raw = loads(config_path.read_text(encoding="utf-8"))
    data = raw.get("helios", raw)
    return HeliosSettings(**data)
