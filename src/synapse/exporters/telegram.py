"""Telegram API exporter using telethon."""

import json
from datetime import datetime
from pathlib import Path
from typing import Any

from telethon import TelegramClient
from telethon.sessions import StringSession
from telethon.tl.types import Channel, Message, MessageReactions, ReactionEmoji, User

from synapse.config import get_settings


async def authenticate_client() -> TelegramClient:
    """Create and authenticate a Telegram client using session string.
    
    Returns:
        Authenticated TelegramClient instance
        
    Raises:
        ValueError: If required credentials are missing
    """
    settings = get_settings()
    
    if not settings.telegram.api_id or not settings.telegram.api_hash:
        raise ValueError('SYNAPSE_TELEGRAM__API_ID and SYNAPSE_TELEGRAM__API_HASH must be set')
    
    if not settings.telegram.session_string:
        raise ValueError('SYNAPSE_TELEGRAM__SESSION_STRING must be set. Generate one using the setup script.')
    
    client = TelegramClient(
        StringSession(settings.telegram.session_string),
        settings.telegram.api_id,
        settings.telegram.api_hash
    )
    
    await client.start()
    return client


async def list_available_channels(client: TelegramClient) -> list[tuple[int, str]]:
    """List all available channels/groups for the authenticated user.
    
    Args:
        client: Authenticated TelegramClient
        
    Returns:
        List of (channel_id, channel_name) tuples
    """
    channels = []
    async for dialog in client.iter_dialogs():
        if isinstance(dialog.entity, Channel):
            channels.append((dialog.entity.id, dialog.entity.title))
    return channels


def format_text_entities(message: Message) -> str | list[dict[str, Any]]:
    """Format message text with entities.
    
    Args:
        message: Telegram message object
        
    Returns:
        Either plain text string or list of text entities
    """
    if not message.entities:
        return message.message or ''
    
    # For now, return plain text. Can be enhanced to handle formatting.
    return message.message or ''


def format_reactions(reactions: MessageReactions | None) -> list[dict[str, Any]]:
    """Format message reactions to match expected JSON structure.
    
    Args:
        reactions: Telegram reactions object
        
    Returns:
        List of formatted reaction dictionaries
    """
    if not reactions or not reactions.results:
        return []
    
    formatted_reactions = []
    for reaction in reactions.results:
        if isinstance(reaction.reaction, ReactionEmoji):
            formatted_reactions.append({
                'type': 'emoji',
                'count': reaction.count,
                'emoji': reaction.reaction.emoticon,
                'recent': []  # Would need additional API calls to get reactor details
            })
    
    return formatted_reactions


def format_message(message: Message, users: dict[int, User]) -> dict[str, Any]:
    """Format a Telegram message to match the expected JSON structure.
    
    Args:
        message: Telegram message object
        users: Dict mapping user IDs to User objects
        
    Returns:
        Formatted message dictionary
    """
    # Get sender info
    sender_id = message.sender_id
    sender = users.get(sender_id)
    
    if sender:
        from_name = sender.first_name or ''
        if sender.last_name:
            from_name += f' {sender.last_name}'
        from_id = f'user{sender_id}'
    else:
        from_name = 'Unknown User'
        from_id = f'user{sender_id}'
    
    # Base message structure
    formatted = {
        'id': message.id,
        'type': 'message',
        'date': message.date.strftime('%Y-%m-%dT%H:%M:%S'),
        'date_unixtime': str(int(message.date.timestamp())),
        'from': from_name,
        'from_id': from_id,
        'text': format_text_entities(message),
        'text_entities': []  # Simplified for MVP
    }
    
    # Add optional fields
    if message.reply_to and message.reply_to.reply_to_msg_id:
        formatted['reply_to_message_id'] = message.reply_to.reply_to_msg_id
    
    if message.photo:
        formatted['photo'] = f'photo_{message.id}.jpg'
    
    if message.document:
        # Look for filename in attributes
        file_name = f'document_{message.id}'
        if message.document.attributes:
            for attr in message.document.attributes:
                if hasattr(attr, 'file_name'):
                    file_name = attr.file_name
                    break
        formatted['file'] = file_name
    
    if message.sticker:
        # Try to get emoji from sticker attributes
        for attr in message.sticker.attributes:
            if hasattr(attr, 'alt'):
                formatted['sticker_emoji'] = attr.alt
                break
    
    if message.poll:
        formatted['poll'] = {'question': message.poll.poll.question}
    
    # Add reactions if present
    reactions = format_reactions(message.reactions)
    if reactions:
        formatted['reactions'] = reactions
    
    return formatted


async def export_channel_messages(
    client: TelegramClient,
    channel_id: int,
    start_date: datetime,
    end_date: datetime
) -> dict[str, Any]:
    """Export messages from a single channel.
    
    Args:
        client: Authenticated TelegramClient
        channel_id: ID of the channel to export
        start_date: Start date for export
        end_date: End date for export
        
    Returns:
        Dictionary with channel data in expected format
    """
    try:
        channel = await client.get_entity(channel_id)
    except Exception as e:
        print(f'Warning: Could not access channel {channel_id}: {e}')
        return {}
    
    if not isinstance(channel, Channel):
        print(f'Warning: Entity {channel_id} is not a channel')
        return {}
    
    messages = []
    users = {}
    
    # Fetch messages in date range
    async for message in client.iter_messages(
        channel,
        limit=1000  # Increase limit for production use
    ):
        if hasattr(message, 'date') and message.date:
            msg_date = message.date.replace(tzinfo=None) if message.date.tzinfo else message.date
            # Check if message is within date range
            if msg_date < start_date or msg_date > end_date:
                continue  # Skip messages outside date range
        
        # Skip service messages
        if not isinstance(message, Message) or message.action:
            continue
        
        # Collect user info
        if message.sender_id and message.sender_id not in users:
            try:
                sender = await client.get_entity(message.sender_id)
                if isinstance(sender, User):
                    users[message.sender_id] = sender
            except Exception:
                pass
        
        
        messages.append(message)
    
    # Format messages
    formatted_messages = [format_message(msg, users) for msg in messages]
    
    return {
        'name': channel.title,
        'type': 'private_supergroup' if channel.megagroup else 'channel',
        'id': channel.id,
        'messages': formatted_messages
    }


async def export_telegram_channels(
    start_date: datetime,
    end_date: datetime,
    output_dir: Path
) -> list[Path]:
    """Export telegram data to JSON files matching existing format.
    
    Channels to export are read from SYNAPSE_TELEGRAM__CHANNEL_IDS env var.
    
    Args:
        start_date: Start date for export
        end_date: End date for export  
        output_dir: Directory to save JSON files
        
    Returns:
        List of paths to created JSON files
    """
    settings = get_settings()
    
    # Get channel IDs from config
    channel_ids = settings.telegram.channel_ids
    if not channel_ids:
        raise ValueError('No channel IDs configured. Set channel_ids in config.toml or SYNAPSE_TELEGRAM__CHANNEL_IDS')
    
    # Convert string IDs to integers
    channel_ids = [int(cid) for cid in channel_ids]
    
    # Create output directory
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Connect to Telegram
    client = await authenticate_client()
    
    try:
        output_files = []
        
        for channel_id in channel_ids:
            print(f'Exporting channel {channel_id}...')
            
            # Export messages
            channel_data = await export_channel_messages(
                client,
                channel_id,
                start_date,
                end_date
            )
            
            if not channel_data:
                continue
            
            # Generate filename
            date_str = start_date.strftime('%Y-%m-%d')
            safe_name = channel_data['name'].replace(' ', '_').replace('/', '_')
            filename = f'telegram_export_{safe_name}_week_{date_str}.json'
            output_path = output_dir / filename
            
            # Save to JSON
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(channel_data, f, ensure_ascii=False, indent=1)
            
            output_files.append(output_path)
            print(f'✓ Exported {len(channel_data.get("messages", []))} messages to {output_path}')
        
        return output_files
        
    finally:
        await client.disconnect()


if __name__ == '__main__':
    # Example: Generate session string (run this once locally)
    
    async def generate_session_string():
        """One-time setup to generate session string."""
        api_id = int(input('Enter your API ID: '))
        api_hash = input('Enter your API Hash: ')
        
        async with TelegramClient(StringSession(), api_id, api_hash) as client:
            await client.start()
            print('Session string:', client.session.save())
            print('Save this as SYNAPSE_TELEGRAM__SESSION_STRING')
    
    # Uncomment to generate session string
    # asyncio.run(generate_session_string())