"""Test configuration override behavior."""

import os
from pathlib import Path
from unittest.mock import patch

import pytest

from src.synapse.config import Settings


def test_env_var_overrides_toml(tmp_path: Path, monkeypatch):
    """Test that environment variables override TOML configuration."""
    # Create a test TOML file
    toml_content = """
[telegram]
api_id = 12345
api_hash = "toml_hash"

[gdrive]
service_account_path = "toml_path.json"

[telegram_notifier]
bot_token = "toml_bot_token"
"""
    toml_path = tmp_path / "test_config.toml"
    toml_path.write_text(toml_content)
    
    # Set environment variables to override TOML
    monkeypatch.setenv("SYNAPSE_TELEGRAM__API_ID", "99999")
    monkeypatch.setenv("SYNAPSE_TELEGRAM__API_HASH", "env_hash")
    monkeypatch.setenv("SYNAPSE_TELEGRAM_NOTIFIER__BOT_TOKEN", "env_bot_token")
    
    # Also test new values not in TOML
    monkeypatch.setenv("SYNAPSE_GDRIVE__TEAM_DATA_FOLDER_ID", "env_folder_id")
    
    # Load settings with the test TOML
    with patch("src.synapse.config.TomlConfigSettingsSource") as mock_toml:
        # Make the mock return our test TOML data
        mock_toml.return_value = lambda: {
            "telegram": {"api_id": 12345, "api_hash": "toml_hash"},
            "gdrive": {"service_account_path": "toml_path.json"},
            "telegram_notifier": {"bot_token": "toml_bot_token"}
        }
        
        settings = Settings()
    
    # Verify environment variables override TOML values
    assert settings.telegram.api_id == 99999, "Env var should override TOML"
    assert settings.telegram.api_hash == "env_hash", "Env var should override TOML"
    assert settings.telegram_notifier.bot_token == "env_bot_token", "Env var should override TOML"
    
    # Verify new env values work even if not in TOML
    assert settings.gdrive.team_data_folder_id == "env_folder_id", "New env var should work"


def test_dotenv_overrides_toml(tmp_path: Path, monkeypatch):
    """Test that .env file values override TOML configuration."""
    # Create a test TOML file
    toml_content = """
[telegram]
api_id = 12345
"""
    toml_path = tmp_path / "test_config.toml"
    toml_path.write_text(toml_content)
    
    # Create a .env file
    env_content = """
SYNAPSE_TELEGRAM__API_ID=88888
SYNAPSE_TELEGRAM__API_HASH=dotenv_hash
"""
    env_path = tmp_path / ".env"
    env_path.write_text(env_content)
    
    # Change to temp directory so .env is found
    monkeypatch.chdir(tmp_path)
    
    with patch("src.synapse.config.TomlConfigSettingsSource") as mock_toml:
        mock_toml.return_value = lambda: {"telegram": {"api_id": 12345}}
        
        settings = Settings()
    
    # Verify .env overrides TOML
    assert settings.telegram.api_id == 88888, ".env should override TOML"
    assert settings.telegram.api_hash == "dotenv_hash", ".env should provide new values"


def test_source_priority_order(monkeypatch):
    """Test the complete source priority order."""
    # Set up different values in each source
    monkeypatch.setenv("SYNAPSE_TELEGRAM__API_ID", "77777")  # env var
    
    # Test 1: Init args have highest priority
    settings = Settings(telegram={"api_id": 11111})
    assert settings.telegram.api_id == 11111, "Init args should have highest priority"
    
    # Test 2: Without init args, env vars have priority
    settings = Settings()
    assert settings.telegram.api_id == 77777, "Env vars should have second priority"
    
    # Test 3: Verify TOML is loaded when no overrides
    monkeypatch.delenv("SYNAPSE_TELEGRAM__API_ID", raising=False)
    settings = Settings()
    # Should get TOML value (or None if no TOML file)
    assert settings.telegram.api_id is not None or not Path("config.toml").exists()