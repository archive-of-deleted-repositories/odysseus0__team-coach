"""
Integration tests for Telegram exporter with real Telegram API.

These tests require valid Telegram credentials and will make actual API calls.
Run with: pytest -m integration tests/test_telegram_exporter_integration.py
"""

import asyncio
import json
import os
from datetime import datetime, timedelta
from pathlib import Path

import pytest

from synapse.config import Settings

from synapse.exporters.telegram import authenticate_client, export_telegram_channels, list_available_channels


@pytest.mark.integration
class TestTelegramExporterIntegration:
    """Integration tests that use real Telegram API."""
    
    @pytest.fixture
    def settings(self):
        """Create settings from environment variables."""
        # Check if we have all required credentials
        api_id = os.getenv('SYNAPSE_TELEGRAM__API_ID')
        api_hash = os.getenv('SYNAPSE_TELEGRAM__API_HASH')
        session_string = os.getenv('SYNAPSE_TELEGRAM__SESSION_STRING')
        
        if not all([api_id, api_hash, session_string]):
            pytest.fail('Telegram credentials not configured. Set SYNAPSE_TELEGRAM__* environment variables.')
        
        return Settings()
    
    @pytest.fixture
    async def client(self, settings):
        """Create authenticated Telegram client."""
        # authenticate_client uses get_settings() internally
        return await authenticate_client()
    
    @pytest.mark.asyncio
    async def test_list_channels_real(self, client):
        """Test listing real channels from authenticated account."""
        channels = await list_available_channels(client)
        
        # Should return a list of channels
        assert isinstance(channels, list)
        
        # If account has channels, verify structure
        if channels:
            channel = channels[0]
            assert 'id' in channel
            assert 'title' in channel
            assert isinstance(channel['id'], int)
            assert isinstance(channel['title'], str)
        
        print(f'Found {len(channels)} channels')
        for ch in channels[:5]:  # Print first 5
            print(f"  - {ch['title']} (ID: {ch['id']})")
    
    @pytest.mark.asyncio
    async def test_export_recent_messages(self, settings, tmp_path):
        """Test exporting recent messages from configured channels."""
        # Use a short time range for testing
        end_date = datetime.now()
        start_date = end_date - timedelta(hours=1)
        
        # Get channel IDs from settings
        channel_ids = settings.telegram.channel_ids
        if not channel_ids:
            pytest.fail('No channel IDs configured for export. Set SYNAPSE_TELEGRAM__CHANNEL_IDS.')
        
        # Set export directory
        settings.telegram.export_dir = str(tmp_path)
        
        # Export messages
        export_files = await export_telegram_channels(
            channel_ids=channel_ids[:1],  # Just test first channel
            start_date=start_date,
            end_date=end_date
        )
        
        # Should create at least one file
        assert len(export_files) > 0
        
        # Verify file contents
        export_file = export_files[0]
        assert export_file.exists()
        
        with open(export_file) as f:
            data = json.load(f)
        
        # Verify structure
        assert 'name' in data
        assert 'type' in data
        assert 'id' in data
        assert 'messages' in data
        assert isinstance(data['messages'], list)
        
        print(f"Exported {len(data['messages'])} messages from {data['name']}")
    
    @pytest.mark.asyncio
    async def test_export_with_reactions(self, settings, tmp_path):
        """Test that reactions are properly exported if present."""
        # This test is more of a verification that reactions work
        # when they exist in the channel
        
        # Use a longer time range to find messages with reactions
        end_date = datetime.now()
        start_date = end_date - timedelta(days=7)
        
        channel_ids = settings.telegram.channel_ids
        if not channel_ids:
            pytest.fail('No channel IDs configured. Set SYNAPSE_TELEGRAM__CHANNEL_IDS.')
        
        # Set export directory
        settings.telegram.export_dir = str(tmp_path)
        
        export_files = await export_telegram_channels(
            channel_ids=channel_ids[:1],
            start_date=start_date,
            end_date=end_date
        )
        
        assert export_files, 'No messages exported - check if channel has messages in date range'
        
        # Check if any messages have reactions
        with open(export_files[0]) as f:
            data = json.load(f)
        
        messages_with_reactions = [
            msg for msg in data['messages']
            if msg.get('reactions')
        ]
        
        if messages_with_reactions:
            print(f'Found {len(messages_with_reactions)} messages with reactions')
            # Verify reaction structure
            reaction = messages_with_reactions[0]['reactions'][0]
            assert 'emoji' in reaction
            assert 'count' in reaction
        else:
            print('No messages with reactions found in test period')
    
    @pytest.mark.asyncio
    async def test_connection_error_handling(self, settings, tmp_path, monkeypatch):
        """Test handling of invalid credentials."""
        # Monkey patch the settings to have bad credentials
        monkeypatch.setenv('SYNAPSE_TELEGRAM__API_HASH', 'invalid_hash')
        
        # Should raise an appropriate error
        with pytest.raises(Exception) as exc_info:
            # This will use the bad credentials from env
            client = await authenticate_client()
            await list_available_channels(client)
        
        # The exact error depends on telethon's implementation
        assert exc_info.value is not None


# Helper script to test credentials
if __name__ == '__main__':
    """Quick script to test if credentials work."""
    import sys
    
    async def test_credentials():
        try:
            client = await authenticate_client()
            channels = await list_available_channels(client)
            print(f'✅ Credentials valid! Found {len(channels)} channels')
            return True
        except Exception as e:
            print(f'❌ Credential test failed: {e}')
            return False
    
    if asyncio.run(test_credentials()):
        sys.exit(0)
    else:
        sys.exit(1)