"""Integration tests for Telegram notifier - requires actual bot credentials."""

import subprocess
import sys

import pytest

from synapse.config import get_settings
from synapse.notifiers.telegram import send_telegram_notification


@pytest.mark.integration
def test_send_real_notification():
    """Test that we can actually send a message to Telegram."""
    settings = get_settings()
    bot_token = settings.telegram_notifier.bot_token
    chat_id = settings.telegram_notifier.chat_id
    
    if not bot_token or not chat_id:
        pytest.skip('Telegram credentials not configured')
    
    result = send_telegram_notification(
        message='🧪 Synapse Pipeline test message',
        bot_token=bot_token,
        chat_id=chat_id
    )
    
    assert result is True, 'Failed to send notification to Telegram'


@pytest.mark.integration
def test_cli_command():
    """Test that the CLI command works end-to-end."""
    settings = get_settings()
    bot_token = settings.telegram_notifier.bot_token
    chat_id = settings.telegram_notifier.chat_id
    
    if not bot_token or not chat_id:
        pytest.skip('Telegram credentials not configured')
    
    result = subprocess.run(
        [
            sys.executable, '-m', 'synapse.cli', 'notify',
            '🔧 Test from CLI',
            '--token', bot_token,
            '--chat', chat_id
        ],
        capture_output=True,
        text=True
    )
    
    assert result.returncode == 0, f'CLI failed: {result.stderr}'
    assert '✅ Notification sent successfully!' in result.stdout


@pytest.mark.integration  
def test_thread_support():
    """Test sending to a specific thread/topic if configured."""
    settings = get_settings()
    bot_token = settings.telegram_notifier.bot_token
    chat_id = settings.telegram_notifier.chat_id
    thread_id = settings.telegram_notifier.thread_id
    
    if not bot_token or not chat_id:
        pytest.skip('Telegram credentials not configured')
    
    if not thread_id:
        pytest.skip('Thread ID not configured - testing main chat only')
    
    result = send_telegram_notification(
        message='📌 Test to specific topic',
        bot_token=bot_token,
        chat_id=chat_id,
        thread_id=thread_id
    )
    
    assert result is True, 'Failed to send to thread'