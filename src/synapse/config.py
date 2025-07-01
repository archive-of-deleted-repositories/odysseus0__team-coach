"""Configuration for Synapse Pipeline using Pydantic settings."""

from pathlib import Path

from pydantic import BaseModel, Field
from pydantic_settings import (
    BaseSettings,
    PydanticBaseSettingsSource,
    SettingsConfigDict,
    TomlConfigSettingsSource,
)


class TelegramConfig(BaseModel):
    """Configuration for Telegram data processing."""
    
    export_dir: str = Field(default='./data/telegram', description='Directory containing Telegram JSON exports')
    topic_mapping_file: str = Field(default='./data/telegram_topic_mapping.csv', description='CSV file mapping topic IDs to names')
    output_dir: str = Field(default='./output/telegram', description='Directory for transformed Telegram data')
    
    # Telegram API credentials
    api_id: int | None = Field(default=None, description='Telegram API ID')
    api_hash: str | None = Field(default=None, description='Telegram API hash')
    session_string: str | None = Field(default=None, description='Telegram session string for authentication')
    channel_ids: list[str] = Field(default_factory=list, description='List of channel IDs to export')


class ScheduleConfig(BaseModel):
    """Configuration for scheduled exports."""
    
    enabled: bool = Field(default=False, description='Enable scheduled exports')
    cron_expression: str = Field(default='0 0 * * 1', description='Cron expression for scheduling (default: weekly on Monday)')


class GDriveConfig(BaseModel):
    """Configuration for Google Drive integration."""
    
    service_account_path: str | None = Field(default=None, description='Path to Google service account JSON file')
    team_data_folder_id: str | None = Field(default=None, description='Google Drive folder ID for team data inputs')
    team_digests_folder_id: str | None = Field(default=None, description='Google Drive folder ID for team digest outputs')
    rclone_config_path: Path | None = Field(default=None, description='Optional path to rclone config file')


class TelegramTarget(BaseModel):
    """Target location for Telegram notifications."""
    
    id: str | None = Field(default=None, description='Telegram channel/group/supergroup ID')
    topic_id: int | None = Field(default=None, description='Topic ID within a supergroup (optional)')


class TelegramNotifierConfig(BaseModel):
    """Configuration for Telegram notifications."""
    
    bot_token: str | None = Field(default=None, description='Telegram bot token')
    target: TelegramTarget = Field(default_factory=TelegramTarget, description='Notification target')


class Settings(BaseSettings):
    """Main configuration for Synapse Pipeline."""
    
    model_config = SettingsConfigDict(
        env_prefix='SYNAPSE_',
        env_nested_delimiter='__',
        env_file='.env',
        env_file_encoding='utf-8',
        case_sensitive=False,
    )
    
    telegram: TelegramConfig = Field(default_factory=TelegramConfig)
    schedule: ScheduleConfig = Field(default_factory=ScheduleConfig)
    gdrive: GDriveConfig = Field(default_factory=GDriveConfig)
    telegram_notifier: TelegramNotifierConfig = Field(default_factory=TelegramNotifierConfig)
    
    @classmethod
    def settings_customise_sources(
        cls,
        settings_cls: type[BaseSettings],
        init_settings: PydanticBaseSettingsSource,
        env_settings: PydanticBaseSettingsSource,
        dotenv_settings: PydanticBaseSettingsSource,
        file_secret_settings: PydanticBaseSettingsSource,
    ) -> tuple[PydanticBaseSettingsSource, ...]:
        """
        Customize settings sources to include TOML file.
        
        Priority order (first has highest priority):
        1. Init settings (when creating instance) - highest priority
        2. Environment variables
        3. .env file  
        4. TOML file (config.toml) - lowest priority
        """
        return (
            init_settings,
            env_settings,
            dotenv_settings,
            TomlConfigSettingsSource(settings_cls, toml_file='config.toml'),
        )


def get_settings() -> Settings:
    """Get the current settings instance."""
    return Settings()