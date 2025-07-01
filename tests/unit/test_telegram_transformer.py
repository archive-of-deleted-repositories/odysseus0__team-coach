"""Test telegram transformer using real export data."""
import json
from pathlib import Path
import pytest

from synapse.transformers.telegram import (
    parse_telegram_export,
    load_topic_mapping,
    TelegramMessage,
)


@pytest.fixture
def test_data_dir():
    """Get the test data directory."""
    return Path(__file__).parent / "data"


@pytest.fixture
def telegram_export_data(test_data_dir):
    """Load the test Telegram export JSON."""
    with open(test_data_dir / "telegram_export_week_2025-04-28.json") as f:
        return json.load(f)


@pytest.fixture
def topic_mapping(test_data_dir):
    """Load the topic mapping CSV."""
    return load_topic_mapping(str(test_data_dir / "telegram_topic_mapping.csv"))


def test_parse_telegram_export_structure(telegram_export_data, topic_mapping):
    """Test that parse_telegram_export produces correct structure."""
    result = parse_telegram_export(telegram_export_data, topic_mapping)
    
    # Check overall structure
    assert "group_name" in result
    assert "week_of" in result
    assert "channels" in result
    assert isinstance(result["channels"], dict)
    
    # Check that we have expected channels from the topic mapping
    assert "Coordination" in result["channels"]
    assert "General" in result["channels"]


def test_parse_telegram_export_messages(telegram_export_data, topic_mapping):
    """Test that messages are properly parsed and grouped."""
    result = parse_telegram_export(telegram_export_data, topic_mapping)
    
    # Check that messages exist in channels
    for channel_name, messages in result["channels"].items():
        assert isinstance(messages, list)
        for msg in messages:
            assert isinstance(msg, TelegramMessage)
            assert msg.author  # Changed from sender to author
            assert msg.date  # Changed from timestamp to date
            assert msg.text is not None  # Can be empty string


def test_parse_telegram_message_with_reactions(telegram_export_data, topic_mapping):
    """Test that reactions are properly parsed."""
    result = parse_telegram_export(telegram_export_data, topic_mapping)
    
    # Find a message with reactions
    messages_with_reactions = []
    for channel_messages in result["channels"].values():
        for msg in channel_messages:
            if msg.reactions:
                messages_with_reactions.append(msg)
    
    assert len(messages_with_reactions) > 0
    # Check reaction format
    for msg in messages_with_reactions:
        assert isinstance(msg.reactions, list)
        for reaction in msg.reactions:
            assert hasattr(reaction, 'emoji')
            assert hasattr(reaction, 'count')
            assert reaction.count > 0


def test_markdown_output_format(telegram_export_data, topic_mapping, test_data_dir):
    """Test that the markdown output matches expected format."""
    from synapse.transformers.telegram import format_to_markdown
    
    parsed_data = parse_telegram_export(telegram_export_data, topic_mapping)
    markdown_output = format_to_markdown(parsed_data)
    
    # Check basic structure
    assert "# Telegram Export Transcript" in markdown_output
    assert "Week of" in markdown_output
    
    # Check channel headers
    assert "## Coordination" in markdown_output
    assert "## General" in markdown_output
    
    # Check message format (timestamp, sender, text)
    assert "[" in markdown_output  # Timestamp brackets
    assert "]" in markdown_output
    assert ":" in markdown_output  # Sender separator
    
    # Verify reactions appear in output
    assert "[💯]" in markdown_output or "[❤]" in markdown_output


def test_handle_service_messages(telegram_export_data, topic_mapping):
    """Test that service messages are filtered out."""
    # Add a service message to the test data
    test_data = telegram_export_data.copy()
    test_data["messages"].append({
        "id": 9999,
        "type": "service",
        "date": "2025-04-28T10:00:00",
        "text": "User joined the group"
    })
    
    result = parse_telegram_export(test_data, topic_mapping)
    
    # Service message should not appear in any channel
    all_messages = []
    for channel_messages in result["channels"].values():
        all_messages.extend(channel_messages)
    
    assert not any(msg.text == "User joined the group" for msg in all_messages)