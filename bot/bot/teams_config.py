# bot/bot/teams_config.py
from pydantic import BaseModel, Field, field_validator


class TeamsConfig(BaseModel):
    """Configuration for Microsoft Teams bot."""

    app_id: str = Field(..., description="Microsoft Teams App ID")
    app_password: str = Field(..., description="Microsoft Teams App Password")
    port: int = Field(default=3978, description="Port for Teams bot server")

    @field_validator('app_id')
    @classmethod
    def validate_app_id(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError('App ID cannot be empty')
        return v

    @field_validator('app_password')
    @classmethod
    def validate_app_password(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError('App password cannot be empty')
        return v
