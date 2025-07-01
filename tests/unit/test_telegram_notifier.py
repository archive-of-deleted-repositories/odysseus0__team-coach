"""Tests for Telegram notifier module."""

import os
from unittest.mock import patch

from synapse.notifiers.telegram import send_telegram_notification


def test_missing_credentials():
    """Test that missing credentials returns False."""
    # Clear any env vars for this test
    with patch.dict(os.environ, {}, clear=True):
        # No credentials = should fail gracefully
        assert send_telegram_notification('Test') is False
        
        # Partial credentials = should also fail
        assert send_telegram_notification('Test', bot_token='token_only') is False
        assert send_telegram_notification('Test', chat_id='chat_only') is False