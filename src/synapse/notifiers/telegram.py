"""Simple Telegram bot notification module."""

import httpx

from synapse.config import get_settings

# Telegram message limits
MAX_MESSAGE_LENGTH = 4096
SAFE_MESSAGE_LENGTH = 4000  # Leave buffer for markdown overhead


def _escape_markdown_v1(text: str) -> str:
    """Escape special characters for Telegram MarkdownV1.

    MarkdownV1 requires escaping: _ * [ ] ( ) ~ ` > # + - = | { } . !
    """
    special_chars = ['_', '*', '[', ']', '(', ')', '~', '`', '>', '#', '+', '-', '=', '|', '{', '}', '.', '!']
    for char in special_chars:
        text = text.replace(char, f'\\{char}')
    return text


def _split_message(message: str, max_length: int = SAFE_MESSAGE_LENGTH) -> list[str]:
    """Split message into chunks that fit Telegram's limits.

    Tries to split on paragraph boundaries first, then line breaks, then arbitrary.
    """
    if len(message) <= max_length:
        return [message]

    chunks = []
    remaining = message

    while remaining:
        if len(remaining) <= max_length:
            chunks.append(remaining)
            break

        # Try to find a paragraph break
        split_idx = remaining.rfind('\n\n', 0, max_length)

        # If no paragraph break, try line break
        if split_idx == -1:
            split_idx = remaining.rfind('\n', 0, max_length)

        # If no line break, split arbitrarily
        if split_idx == -1:
            split_idx = max_length

        chunk = remaining[:split_idx].strip()
        if chunk:
            chunks.append(chunk)
        remaining = remaining[split_idx:].strip()

    return chunks


def send_telegram_notification(
    message: str,
    bot_token: str | None = None,
    chat_id: str | None = None,
    thread_id: str | None = None,
) -> None:
    """Send notification via Telegram bot. Handles long messages and markdown escaping."""
    settings = get_settings()
    token = bot_token or settings.telegram_notifier.bot_token
    chat = chat_id or settings.telegram_notifier.target.id
    thread = thread_id or settings.telegram_notifier.target.topic_id

    if not token or not chat:
        raise ValueError("Missing bot token or chat ID")

    # Split message if it's too long
    chunks = _split_message(message)

    for i, chunk in enumerate(chunks):
        params = {'chat_id': chat, 'text': chunk, 'parse_mode': 'Markdown'}
        if thread:
            params['message_thread_id'] = str(thread)

        response = httpx.post(
            f'https://api.telegram.org/bot{token}/sendMessage',
            json=params,
        )

        if not response.is_success:
            # If markdown parsing fails, try without markdown
            try:
                error = response.json().get('description', '')
                if "can't parse entities" in error.lower():
                    # Retry without markdown parsing
                    params_plain = params.copy()
                    params_plain.pop('parse_mode')
                    response_retry = httpx.post(
                        f'https://api.telegram.org/bot{token}/sendMessage',
                        json=params_plain,
                    )
                    if response_retry.is_success:
                        continue  # Success without markdown
                    error = response_retry.json().get('description', error)
            except:
                error = f"HTTP {response.status_code}"

            # Add context about which chunk failed
            chunk_info = f" (chunk {i+1}/{len(chunks)})" if len(chunks) > 1 else ""
            raise RuntimeError(f"Telegram API error{chunk_info}: {error}")