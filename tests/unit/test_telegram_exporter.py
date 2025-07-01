"""Tests for the Telegram exporter."""

import json
from datetime import datetime
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from telethon.tl.types import Channel, Message, User

from synapse.exporters.telegram import (
    export_telegram_channels,
    format_message,
    format_reactions,
    format_text_entities,
    list_available_channels,
)


@pytest.fixture
def mock_user():
    """Create a mock Telegram user."""
    user = MagicMock(spec=User)
    user.id = 123456
    user.first_name = 'Test'
    user.last_name = 'User'
    return user


@pytest.fixture
def mock_channel():
    """Create a mock Telegram channel."""
    channel = MagicMock(spec=Channel)
    channel.id = 2682777986
    channel.title = 'Test Channel'
    channel.megagroup = True
    return channel


@pytest.fixture
def mock_message(mock_user):
    """Create a mock Telegram message."""
    message = MagicMock(spec=Message)
    message.id = 706
    message.date = datetime(2025, 4, 28, 8, 15, 53)
    message.sender_id = mock_user.id
    message.message = 'Test message content'
    message.entities = None
    message.reply_to = None
    message.photo = None
    message.document = None
    message.sticker = None
    message.poll = None
    message.reactions = None
    message.action = None
    return message


def test_format_text_entities():
    """Test formatting of text entities."""
    # Test simple text
    message = MagicMock()
    message.entities = None
    message.message = 'Hello world'
    assert format_text_entities(message) == 'Hello world'
    
    # Test empty message
    message.message = None
    assert format_text_entities(message) == ''


def test_format_reactions():
    """Test formatting of reactions."""
    # Test with no reactions
    assert format_reactions(None) == []
    
    # Test with emoji reaction
    from telethon.tl.types import ReactionEmoji
    
    reaction = MagicMock()
    reaction.reaction = MagicMock(spec=ReactionEmoji)
    reaction.reaction.emoticon = '👍'
    reaction.count = 3
    
    reactions = MagicMock()
    reactions.results = [reaction]
    
    formatted = format_reactions(reactions)
    assert len(formatted) == 1
    assert formatted[0]['emoji'] == '👍'
    assert formatted[0]['count'] == 3


def test_format_message(mock_message, mock_user):
    """Test message formatting."""
    users = {mock_user.id: mock_user}
    
    formatted = format_message(mock_message, users)
    
    assert formatted['id'] == 706
    assert formatted['type'] == 'message'
    assert formatted['date'] == '2025-04-28T08:15:53'
    assert formatted['from'] == 'Test User'
    assert formatted['from_id'] == 'user123456'
    assert formatted['text'] == 'Test message content'
    assert 'reply_to_message_id' not in formatted


def test_format_message_with_reply(mock_message, mock_user):
    """Test message formatting with reply."""
    mock_message.reply_to = MagicMock()
    mock_message.reply_to.reply_to_msg_id = 695
    
    users = {mock_user.id: mock_user}
    formatted = format_message(mock_message, users)
    
    assert formatted['reply_to_message_id'] == 695


def test_format_message_with_media(mock_message, mock_user):
    """Test message formatting with media."""
    # Test with photo
    mock_message.photo = MagicMock()
    users = {mock_user.id: mock_user}
    formatted = format_message(mock_message, users)
    assert 'photo' in formatted
    
    # Test with document
    mock_message.photo = None
    mock_message.document = MagicMock()
    mock_message.document.attributes = [MagicMock(file_name='test.pdf')]
    formatted = format_message(mock_message, users)
    assert formatted['file'] == 'test.pdf'


@pytest.mark.asyncio
async def test_list_available_channels():
    """Test listing available channels."""
    mock_client = MagicMock()
    
    # Create mock dialog with channel
    mock_dialog = MagicMock()
    mock_dialog.entity = MagicMock(spec=Channel)
    mock_dialog.entity.id = 123
    mock_dialog.entity.title = 'Test Channel'
    
    # Create async iterator for dialogs
    async def async_dialog_generator():
        yield mock_dialog
    
    # Make iter_dialogs return the async generator directly
    mock_client.iter_dialogs = MagicMock(return_value=async_dialog_generator())
    
    channels = await list_available_channels(mock_client)
    assert len(channels) == 1
    assert channels[0] == (123, 'Test Channel')


@pytest.mark.asyncio
async def test_export_telegram_channels(tmp_path):
    """Test exporting Telegram channels."""
    with patch('synapse.exporters.telegram.authenticate_client') as mock_auth:
        with patch('synapse.exporters.telegram.get_settings') as mock_settings:
            # Setup mocks
            mock_client = AsyncMock()
            mock_auth.return_value = mock_client
            
            mock_settings.return_value.telegram.channel_ids = '123,456'
            
            # Mock channel and messages
            mock_channel = MagicMock(spec=Channel)
            mock_channel.id = 123
            mock_channel.title = 'Test Channel'
            mock_channel.megagroup = True
            
            mock_client.get_entity.return_value = mock_channel
            
            # Mock message iteration
            mock_message = MagicMock(spec=Message)
            mock_message.id = 1
            mock_message.date = datetime(2025, 4, 28, 10, 0, 0)
            mock_message.sender_id = 789
            mock_message.message = 'Test'
            mock_message.action = None
            mock_message.entities = None
            mock_message.reply_to = None
            mock_message.photo = None
            mock_message.document = None
            mock_message.sticker = None
            mock_message.poll = None
            mock_message.reactions = None
            
            # Create async iterator for messages
            async def async_message_generator():
                yield mock_message
            
            # Make iter_messages return the async generator directly
            mock_client.iter_messages = MagicMock(return_value=async_message_generator())
            
            # Mock user
            mock_user = MagicMock(spec=User)
            mock_user.id = 789
            mock_user.first_name = 'Test'
            mock_user.last_name = None
            mock_client.get_entity.side_effect = [mock_channel, mock_user]
            
            # Run export
            start = datetime(2025, 4, 28, 0, 0, 0)
            end = datetime(2025, 4, 28, 23, 59, 59)
            
            output_files = await export_telegram_channels(start, end, tmp_path)
            
            # Verify output
            assert len(output_files) == 1
            assert output_files[0].exists()
            
            # Check JSON content
            with open(output_files[0]) as f:
                data = json.load(f)
                assert data['name'] == 'Test Channel'
                assert len(data['messages']) == 1
                assert data['messages'][0]['text'] == 'Test'