"""
KIE v3 Configuration Management

Centralized configuration using Pydantic for validation.
"""

import os
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, Field, field_validator


class GeocodingConfig(BaseModel):
    """Geocoding service configuration."""

    preferred_service: Literal["nominatim", "census", "google", "mapbox"] = "nominatim"
    fallback_services: list[str] = Field(default_factory=lambda: ["census"])
    rate_limit: float = 1.0  # requests per second
    timeout: int = 10  # seconds
    max_retries: int = 3
    cache_enabled: bool = True
    cache_ttl: int = 86400  # 24 hours in seconds

    # API Keys (optional, for paid services)
    google_api_key: str | None = None
    mapbox_api_key: str | None = None

    @field_validator("google_api_key", "mapbox_api_key", mode="before")
    @classmethod
    def load_from_env(cls, v: str | None, info) -> str | None:
        """Load API keys from environment if not provided."""
        if v is not None:
            return v
        field_name = info.field_name
        env_var = f"KIE_{field_name.upper()}"
        return os.getenv(env_var)


class ChartConfig(BaseModel):
    """Chart generation configuration."""

    default_width: int = 800
    default_height: int = 600
    dpi: int = 150
    interactive: bool = True
    show_gridlines: bool = False  # Must be False for KDS compliance
    data_labels: bool = True
    legend_position: Literal["top", "bottom", "left", "right"] = "bottom"


class BrandConfig(BaseModel):
    """KDS brand compliance configuration."""

    enforce_kds_colors: bool = True
    allow_custom_colors: bool = False
    enforce_typography: bool = True
    validate_on_export: bool = True
    forbidden_colors: list[str] = Field(
        default_factory=lambda: [
            "#00FF00", "#008000", "#90EE90", "#98FB98", "#00FA9A",
            "#3CB371", "#2E8B57", "#228B22", "#32CD32", "#7FFF00",
            "#7CFC00", "#ADFF2F", "#00FF7F", "#00FFFF", "#40E0D0",
            "#48D1CC", "#20B2AA"
        ]
    )


class APIConfig(BaseModel):
    """FastAPI server configuration."""

    host: str = "0.0.0.0"
    port: int = 8000
    reload: bool = True
    workers: int = 4
    cors_origins: list[str] = Field(
        default_factory=lambda: ["http://localhost:5173", "http://localhost:3000"]
    )
    api_key_required: bool = False


class KIEConfig(BaseModel):
    """Main KIE v3 configuration."""

    version: str = "3.0.0"
    kie_root: Path = Field(default_factory=lambda: Path(__file__).parent.parent)
    output_dir: Path = Field(default_factory=lambda: Path.cwd() / "outputs")
    export_dir: Path = Field(default_factory=lambda: Path.cwd() / "exports")
    data_dir: Path = Field(default_factory=lambda: Path.cwd() / "data")

    # Sub-configurations
    geocoding: GeocodingConfig = Field(default_factory=GeocodingConfig)
    charts: ChartConfig = Field(default_factory=ChartConfig)
    brand: BrandConfig = Field(default_factory=BrandConfig)
    api: APIConfig = Field(default_factory=APIConfig)

    # Logging
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR"] = "INFO"
    log_file: Path | None = None

    @field_validator("output_dir", "export_dir", "data_dir")
    @classmethod
    def ensure_dirs_exist(cls, v: Path) -> Path:
        """Ensure directories exist."""
        v.mkdir(parents=True, exist_ok=True)
        return v

    @classmethod
    def from_yaml(cls, path: Path) -> "KIEConfig":
        """Load configuration from YAML file."""
        import yaml
        with open(path) as f:
            data = yaml.safe_load(f)
        return cls(**data)

    def to_yaml(self, path: Path) -> None:
        """Save configuration to YAML file."""
        import yaml
        with open(path, "w") as f:
            yaml.dump(self.model_dump(), f, default_flow_style=False)


# Global configuration instance
_config: KIEConfig | None = None


def get_config() -> KIEConfig:
    """Get global configuration instance."""
    global _config
    if _config is None:
        _config = KIEConfig()
    return _config


def set_config(config: KIEConfig) -> None:
    """Set global configuration instance."""
    global _config
    _config = config


def load_config(path: Path) -> KIEConfig:
    """Load configuration from file and set as global."""
    config = KIEConfig.from_yaml(path)
    set_config(config)
    return config
