"""Configuration loading for HELIOS using TOML and environment overrides."""

from pathlib import Path
from typing import Literal

from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings, SettingsConfigDict


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


class ExportConfig(BaseModel):
    """Configuration for report export behavior."""

    default_format: Literal["json", "pdf", "rocrate"] = "json"
    output_dir: str = "./helios-reports"
    include_rocrate: bool = True


class HeliosConfig(BaseSettings):
    """Top-level HELIOS configuration."""

    model_config = SettingsConfigDict(
        env_prefix="HELIOS_",
        env_nested_delimiter="__",
        extra="ignore",
    )

    pipeline_executor: Literal["nextflow", "snakemake", "cwl", "unknown"] = "nextflow"
    signing_key: str = "~/.helios/keys/helios.key"
    audit_db: str = "~/.helios/helios.db"
    log_level: str = "INFO"
    checks: ChecksConfig = Field(default_factory=ChecksConfig)
    export: ExportConfig = Field(default_factory=ExportConfig)

    def expand_path(self, value: str) -> Path:
        """Expand user home for configured paths."""
        return Path(value).expanduser()


def load_config(path: str | None = None) -> HeliosConfig:
    """Load HELIOS configuration from TOML and environment variables."""
    config = HeliosConfig()
    if path is None:
        return config

    from tomllib import loads

    config_path = Path(path)
    if not config_path.exists():
        return config

    data = loads(config_path.read_text(encoding="utf-8"))
    helios_data = data.get("helios", {})
    merged = {
        "pipeline_executor": helios_data.get("pipeline_executor", config.pipeline_executor),
        "signing_key": helios_data.get("signing_key", config.signing_key),
        "audit_db": helios_data.get("audit_db", config.audit_db),
        "log_level": helios_data.get("log_level", config.log_level),
        "checks": helios_data.get("checks", {}),
        "export": helios_data.get("export", {}),
    }
    return HeliosConfig(**merged)

