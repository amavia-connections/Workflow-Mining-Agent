"""
Configuration management for Workflow Mining Agent.
AI Builder Cup 2026.

Supports both GCP Cloud Mode (Vertex AI, BigQuery) and Local Demo Mode (deterministic local execution).
"""

import os
from typing import Optional
from pydantic import BaseModel, Field


class Settings(BaseModel):
    # Application Mode: 'DEMO' or 'CLOUD'
    APP_MODE: str = Field(
        default_factory=lambda: os.environ.get("APP_MODE", "DEMO"),
        description="'DEMO' for local standalone mode, 'CLOUD' for GCP"
    )
    
    # Google Cloud Configuration
    GOOGLE_CLOUD_PROJECT: Optional[str] = Field(
        default_factory=lambda: os.environ.get("GOOGLE_CLOUD_PROJECT", None),
        description="GCP Project ID"
    )
    GOOGLE_CLOUD_LOCATION: str = Field(
        default_factory=lambda: os.environ.get("GOOGLE_CLOUD_LOCATION", "us-central1"),
        description="GCP Region (e.g. us-central1)"
    )
    BIGQUERY_DATASET: str = Field(
        default_factory=lambda: os.environ.get("BIGQUERY_DATASET", "workflow_mining"),
        description="BigQuery Dataset Name"
    )
    GOOGLE_GENAI_USE_VERTEXAI: bool = Field(
        default_factory=lambda: os.environ.get("GOOGLE_GENAI_USE_VERTEXAI", "true").lower() in ("true", "1"),
        description="Use Vertex AI endpoint for Gemini"
    )
    
    # Gemini Model configuration
    GEMINI_MODEL: str = Field(
        default_factory=lambda: os.environ.get("GEMINI_MODEL", "gemini-1.5-flash"),
        description="Gemini model name"
    )
    EMBEDDING_MODEL: str = Field(
        default_factory=lambda: os.environ.get("EMBEDDING_MODEL", "text-embedding-004"),
        description="Vertex AI embedding model"
    )
    
    # Analytical Financial Defaults
    DEFAULT_HOURLY_LABOR_RATE: float = Field(
        default_factory=lambda: float(os.environ.get("DEFAULT_HOURLY_LABOR_RATE", "65.0")),
        description="Default labor rate in USD/hour"
    )
    DEFAULT_AUTOMATABLE_PERCENTAGE: float = Field(
        default_factory=lambda: float(os.environ.get("DEFAULT_AUTOMATABLE_PERCENTAGE", "0.75")),
        description="Default automatable percentage (75%)"
    )
    
    # Server configuration
    HOST: str = Field(
        default_factory=lambda: os.environ.get("HOST", "0.0.0.0"),
        description="Bind host"
    )
    PORT: int = Field(
        default_factory=lambda: int(os.environ.get("PORT", "8000")),
        description="Bind port"
    )
    
    # Storage paths
    DATA_DIR: str = Field(
        default_factory=lambda: os.environ.get("DATA_DIR", "data"),
        description="Data directory path"
    )
    DATABASE_URL: str = Field(
        default_factory=lambda: os.environ.get("DATABASE_URL", "sqlite:///./data/workflow_mining.db"),
        description="Local SQLite DB URL"
    )


settings = Settings()


def is_cloud_mode_ready() -> bool:
    """
    Checks whether real Google Cloud credentials and project ID are configured.
    Never pretends cloud is active unless verified.
    """
    if settings.APP_MODE.upper() != "CLOUD":
        return False
    if not settings.GOOGLE_CLOUD_PROJECT:
        return False
    # Check if ADC or GOOGLE_APPLICATION_CREDENTIALS exists
    creds_path = os.environ.get("GOOGLE_APPLICATION_CREDENTIALS")
    if creds_path and os.path.exists(creds_path):
        return True
    # Or check if gcloud ADC credentials file exists in standard location
    default_adc_path = os.path.expanduser("~/.config/gcloud/application_default_credentials.json")
    windows_adc_path = os.path.expandvars("%APPDATA%/gcloud/application_default_credentials.json")
    if os.path.exists(default_adc_path) or os.path.exists(windows_adc_path):
        return True
    return False
