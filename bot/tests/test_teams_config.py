# bot/tests/test_teams_config.py
import pytest
from bot.teams_config import TeamsConfig

def test_teams_config_defaults():
    """Test Teams configuration with default values."""
    config = TeamsConfig(
        app_id="test-app-id",
        app_password="test-password"
    )

    assert config.app_id == "test-app-id"
    assert config.app_password == "test-password"
    assert config.port == 3978  # Default Teams bot port

def test_teams_config_custom_port():
    """Test Teams configuration with custom port."""
    config = TeamsConfig(
        app_id="test-app-id",
        app_password="test-password",
        port=5000
    )

    assert config.port == 5000

def test_teams_config_validation():
    """Test that missing credentials raise error."""
    with pytest.raises(ValueError, match="App ID cannot be empty"):
        TeamsConfig(app_id="", app_password="test")

    with pytest.raises(ValueError, match="App password cannot be empty"):
        TeamsConfig(app_id="test", app_password="")

def test_teams_config_whitespace_rejected():
    """Test that whitespace-only values are rejected."""
    with pytest.raises(ValueError, match="App ID cannot be empty"):
        TeamsConfig(app_id="   ", app_password="test")

    with pytest.raises(ValueError, match="App password cannot be empty"):
        TeamsConfig(app_id="test", app_password="   ")

def test_teams_config_both_fields_empty():
    """Test that both empty fields raise error."""
    with pytest.raises(ValueError):
        TeamsConfig(app_id="", app_password="")

def test_teams_config_whitespace_stripped():
    """Test that leading/trailing whitespace is stripped from valid values."""
    config = TeamsConfig(
        app_id="  my-app-id  ",
        app_password="  my-password  "
    )
    assert config.app_id == "my-app-id"
    assert config.app_password == "my-password"
