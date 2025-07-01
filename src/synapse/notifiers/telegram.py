"""Simple Telegram bot notification module."""

import httpx

from synapse.config import get_settings


def send_telegram_notification(
    message: str,
    bot_token: str | None = None,
    chat_id: str | None = None,
    thread_id: str | None = None,
) -> bool:
    """Send notification via Telegram bot. Simple as possible."""
    settings = get_settings()
    token = bot_token or settings.telegram_notifier.bot_token
    chat = chat_id or settings.telegram_notifier.target.id
    thread = thread_id or settings.telegram_notifier.target.topic_id
    
    if not token or not chat:
        return False
    
    params = {'chat_id': chat, 'text': message, 'parse_mode': 'Markdown'}
    if thread:
        params['message_thread_id'] = thread
    
    response = httpx.post(
        f'https://api.telegram.org/bot{token}/sendMessage',
        json=params,
    )
    return response.is_success