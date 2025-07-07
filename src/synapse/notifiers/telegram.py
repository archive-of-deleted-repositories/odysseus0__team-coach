"""Simple Telegram bot notification module."""

import httpx

from synapse.config import get_settings


def send_telegram_notification(
    message: str,
    bot_token: str | None = None,
    chat_id: str | None = None,
    thread_id: str | None = None,
) -> None:
    """Send notification via Telegram bot. Simple as possible."""
    settings = get_settings()
    token = bot_token or settings.telegram_notifier.bot_token
    chat = chat_id or settings.telegram_notifier.target.id
    thread = thread_id or settings.telegram_notifier.target.topic_id
    
    if not token or not chat:
        raise ValueError("Missing bot token or chat ID")
    
    params = {'chat_id': chat, 'text': message, 'parse_mode': 'Markdown'}
    if thread:
        params['message_thread_id'] = str(thread)
    
    response = httpx.post(
        f'https://api.telegram.org/bot{token}/sendMessage',
        json=params,
    )
    
    if not response.is_success:
        # Extract actual error from Telegram API
        try:
            error = response.json().get('description', 'Unknown error')
        except:
            error = f"HTTP {response.status_code}"
        raise RuntimeError(f"Telegram API error: {error}")