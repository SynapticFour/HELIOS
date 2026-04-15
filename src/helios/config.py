"""Typed HELIOS configuration loaded from TOML and environment variables."""

from pathlib import Path
from typing import Literal

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
    container_digest_required: bool = False


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


class HeliosSettings(BaseSettings):
    """Top-level HELIOS configuration."""

    model_config = SettingsConfigDict(
        toml_file="helios.toml",
        env_prefix="HELIOS_",
        env_nested_delimiter="__",
        extra="ignore",
    )

    signing_key: Path = Path("~/.helios/keys/helios.key")
    audit_db: Path = Path("~/.helios/helios.db")
    cache_dir: Path = Path("~/.helios/cache")
    log_level: str = "INFO"
    checks: ChecksConfig = Field(default_factory=ChecksConfig)
    export: ExportConfig = Field(default_factory=ExportConfig)
    dashboard: DashboardConfig = Field(default_factory=DashboardConfig)

    def model_post_init(self, __context: object) -> None:
        """Expand home references for configured path settings."""
        object.__setattr__(self, "signing_key", self.signing_key.expanduser())
        object.__setattr__(self, "audit_db", self.audit_db.expanduser())
        object.__setattr__(self, "cache_dir", self.cache_dir.expanduser())
        export_value = self.export.model_copy(
            update={"output_dir": self.export.output_dir.expanduser()}
        )
        object.__setattr__(self, "export", export_value)

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
            TomlConfigSettingsSource(settings_cls),
            file_secret_settings,
        )


def load_config(path: str | None = None) -> HeliosSettings:
    """Load HELIOS settings from an optional TOML file path and environment."""
    if path is None:
        return HeliosSettings()
    config_path = Path(path)
    if not config_path.exists():
        return HeliosSettings()
    from tomllib import loads

    raw = loads(config_path.read_text(encoding="utf-8"))
    data = raw.get("helios", raw)
    return HeliosSettings(**data)

