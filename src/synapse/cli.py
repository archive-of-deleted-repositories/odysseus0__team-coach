"""Command-line interface for Synapse Pipeline."""

import asyncio
from datetime import datetime, timedelta
from pathlib import Path

import typer

from synapse.config import get_settings
from synapse.notifiers.telegram import send_telegram_notification
from synapse.transformers.telegram import format_to_markdown, load_topic_mapping, parse_telegram_export
from synapse.uploaders.gdrive import GoogleDriveUploader

app = typer.Typer(help='Synapse Pipeline - Transform Telegram exports to clean markdown')
doctor_app = typer.Typer(help='Developer utilities for debugging and diagnostics')
app.add_typer(doctor_app, name='doctor')


@app.command()
def transform_telegram(
    input_file: Path = typer.Argument(..., help='Path to Telegram JSON export file'),
    output_file: Path | None = typer.Option(None, '--output', '-o', help='Output markdown file path'),
    topic_mapping: Path | None = typer.Option(None, '--mapping', '-m', help='Topic mapping CSV file'),
):
    """Transform a Telegram JSON export to markdown format."""
    settings = get_settings()
    
    # Use defaults from settings if not provided
    if topic_mapping is None:
        topic_mapping = Path(settings.telegram.topic_mapping_file)
    elif not isinstance(topic_mapping, Path):
        # Handle case where topic_mapping might be a boolean or string
        topic_mapping = None
    
    if output_file is None:
        output_file = Path(settings.telegram.output_dir) / f'{input_file.stem}.md'
    
    # Ensure output directory exists
    output_file.parent.mkdir(parents=True, exist_ok=True)
    
    try:
        # Load the JSON export
        import json
        with open(input_file) as f:
            telegram_data = json.load(f)
        
        # Load topic mapping
        topic_map = load_topic_mapping(str(topic_mapping)) if topic_mapping and topic_mapping.exists() else {}
        
        # Parse the export
        parsed_data = parse_telegram_export(telegram_data, topic_map)
        
        # Convert to markdown
        markdown_content = format_to_markdown(parsed_data)
        
        # Write output
        output_file.write_text(markdown_content)
        
        typer.echo(f'✅ Transformed {input_file} → {output_file}')
        
    except Exception as e:
        typer.echo(f'❌ Error: {e}', err=True)
        raise typer.Exit(1)


@app.command()
def batch_transform(
    input_dir: Path = typer.Argument(..., help='Directory containing Telegram JSON exports'),
    output_dir: Path | None = typer.Option(None, '--output', '-o', help='Output directory for markdown files'),
):
    """Transform all Telegram JSON exports in a directory."""
    settings = get_settings()
    
    if output_dir is None:
        output_dir = Path(settings.telegram.output_dir)
    
    json_files = list(input_dir.glob('*.json'))
    if not json_files:
        typer.echo(f'No JSON files found in {input_dir}')
        raise typer.Exit(1)
    
    typer.echo(f'Found {len(json_files)} JSON files to transform')
    
    for json_file in json_files:
        output_file = output_dir / f'{json_file.stem}.md'
        try:
            transform_telegram(json_file, output_file, topic_mapping=None)
        except Exception as e:
            typer.echo(f'❌ Error processing {json_file}: {e}', err=True)
            import traceback
            traceback.print_exc()
            raise


@app.command()
def export_telegram(
    start_date: str | None = typer.Option(None, '--start', '-s', help='Start date (YYYY-MM-DD). Default: 7 days ago'),
    end_date: str | None = typer.Option(None, '--end', '-e', help='End date (YYYY-MM-DD). Default: today'),
    output_dir: Path | None = typer.Option(None, '--output', '-o', help='Output directory for JSON exports'),
):
    """Export Telegram messages using the Telegram API."""
    from synapse.exporters.telegram import export_telegram_channels
    
    settings = get_settings()
    
    # Parse dates
    if end_date is None:
        end = datetime.now().replace(hour=23, minute=59, second=59)
    else:
        end = datetime.strptime(end_date, '%Y-%m-%d').replace(hour=23, minute=59, second=59)
    
    if start_date is None:
        start = (end - timedelta(days=7)).replace(hour=0, minute=0, second=0)
    else:
        start = datetime.strptime(start_date, '%Y-%m-%d').replace(hour=0, minute=0, second=0)
    
    if output_dir is None:
        output_dir = Path(settings.telegram.export_dir)
    
    typer.echo(f'📥 Exporting Telegram messages from {start.date()} to {end.date()}')
    
    try:
        # Run the async export function
        output_files = asyncio.run(export_telegram_channels(start, end, output_dir))
        
        if output_files:
            typer.echo(f'✅ Successfully exported {len(output_files)} channel(s)')
            for file in output_files:
                typer.echo(f'   → {file}')
        else:
            typer.echo('⚠️  No messages exported. Check channel IDs and date range.')
            
    except Exception as e:
        typer.echo(f'❌ Export failed: {e}', err=True)
        raise typer.Exit(1)


@app.command()
def list_channels():
    """List available Telegram channels for the authenticated user."""
    from synapse.exporters.telegram import authenticate_client, list_available_channels
    
    async def _list():
        client = await authenticate_client()
        try:
            channels = await list_available_channels(client)
            return channels
        finally:
            await client.disconnect()  # type: ignore[misc]
    
    typer.echo('🔍 Fetching available channels...')
    
    try:
        channels = asyncio.run(_list())
        
        if channels:
            typer.echo(f'\n📋 Found {len(channels)} channel(s):')
            for channel_id, channel_name in channels:
                typer.echo(f'   {channel_id}: {channel_name}')
            typer.echo('\nAdd channel IDs to SYNAPSE_TELEGRAM__CHANNEL_IDS (comma-separated)')
        else:
            typer.echo('No channels found.')
            
    except Exception as e:
        typer.echo(f'❌ Failed to list channels: {e}', err=True)
        raise typer.Exit(1)


@app.command()
def download_gdrive(
    output_dir: Path = typer.Argument(..., help='Directory to save downloaded files'),
    since_days: int = typer.Option(7, '--since-days', '-d', help='Download files modified in the last N days'),
):
    """Download team data from Google Drive input folder."""
    try:
        # Calculate since timestamp
        since = datetime.now() - timedelta(days=since_days)
        
        # Initialize uploader
        uploader = GoogleDriveUploader()
        
        typer.echo(f'📥 Downloading files modified since {since.strftime("%Y-%m-%d")}...')
        
        # Download files
        downloaded_files = uploader.download_team_data(since, output_dir)
        
        if downloaded_files:
            typer.echo(f'✅ Downloaded {len(downloaded_files)} files:')
            for file_path in downloaded_files:
                typer.echo(f'  - {file_path.relative_to(output_dir)}')
        else:
            typer.echo('No new files found to download.')
            
    except Exception as e:
        typer.echo(f'❌ Error: {e}', err=True)
        raise typer.Exit(1)


@app.command()
def upload_digest(
    digest_file: Path = typer.Argument(..., help='Path to digest file to upload'),
    filename: str | None = typer.Option(None, '--filename', '-f', help='Custom filename for Google Drive'),
):
    """Upload team digest to Google Drive output folder."""
    try:
        # Use original filename if not specified
        if filename is None:
            filename = digest_file.name
        
        # Initialize uploader
        uploader = GoogleDriveUploader()
        
        typer.echo(f'📤 Uploading {digest_file} as {filename}...')
        
        # Upload file
        share_link = uploader.upload_team_digest(digest_file, filename)
        
        typer.echo('✅ Successfully uploaded!')
        typer.echo(f'🔗 Share link: {share_link}')
        
    except Exception as e:
        typer.echo(f'❌ Error: {e}', err=True)
        raise typer.Exit(1)


@app.command()
def notify(
    message: str = typer.Argument(..., help='Message to send'),
    bot_token: str | None = typer.Option(None, '--token', '-t', help='Telegram bot token'),
    chat_id: str | None = typer.Option(None, '--chat', '-c', help='Telegram chat ID'),
    thread_id: str | None = typer.Option(None, '--thread', help='Telegram thread ID (for forum topics)'),
):
    """Send a notification via Telegram bot."""
    settings = get_settings()
    
    # Use settings defaults if not provided
    if bot_token is None:
        bot_token = settings.telegram_notifier.bot_token
    if chat_id is None:
        chat_id = settings.telegram_notifier.target.id
    if thread_id is None:
        thread_id = settings.telegram_notifier.target.topic_id
    
    success = send_telegram_notification(message, bot_token, chat_id, thread_id)
    
    if success:
        typer.echo('✅ Notification sent successfully!')
    else:
        typer.echo('❌ Failed to send notification. Check your bot token and chat ID.', err=True)
        raise typer.Exit(1)


@doctor_app.command('user-search-topics')
def find_telegram_topics(
    search: str = typer.Option('', '--search', '-s', help='Search for messages containing this text'),
    limit: int = typer.Option(50, '--limit', '-l', help='Number of recent messages to search'),
):
    """Search Telegram groups and find topic IDs using your personal Telegram account.
    
    This uses YOUR Telegram API credentials (not bot API) to search through
    all your groups and channels for messages and topic IDs.
    
    Example:
        $ synapse-pipeline doctor user-search-topics --search "update channel"
        
        🔍 Searching for Telegram groups...
        
        📱 Flashbots_X Core (ID: -1002682777986)
           Found 2 messages matching "update channel"
           - "Let's use the update channel for..." (ID: 12345)
             🎯 Topic ID: 2457
    
    Note: Requires SYNAPSE_TELEGRAM__API_ID, API_HASH, and SESSION_STRING.
    """
    from telethon import TelegramClient
    from telethon.sessions import StringSession
    
    settings = get_settings()
    
    if not settings.telegram.api_id or not settings.telegram.api_hash:
        typer.echo('❌ Error: Telegram API credentials not configured', err=True)
        typer.echo('Please set SYNAPSE_TELEGRAM__API_ID and SYNAPSE_TELEGRAM__API_HASH', err=True)
        raise typer.Exit(1)
    
    if not settings.telegram.session_string:
        typer.echo('❌ Error: Telegram session string not configured', err=True)
        typer.echo('Please set SYNAPSE_TELEGRAM__SESSION_STRING', err=True)
        raise typer.Exit(1)
    
    async def find_topics():
        client = TelegramClient(
            StringSession(settings.telegram.session_string),
            settings.telegram.api_id,
            settings.telegram.api_hash
        )
        
        await client.start()
        typer.echo('🔍 Searching for Telegram groups...\n')
        
        found_any = False
        async for dialog in client.iter_dialogs():
            if dialog.is_group or dialog.is_channel:
                chat = dialog.entity
                typer.echo(f'📱 {dialog.name} (ID: {chat.id})')
                
                # Get recent messages
                messages = await client.get_messages(chat, limit=limit)
                
                if search:
                    # Filter messages by search term
                    matching = [m for m in messages if m.text and search.lower() in m.text.lower()]
                    if matching:
                        typer.echo(f'   Found {len(matching)} messages matching "{search}"')
                        for msg in matching[:5]:  # Show first 5 matches
                            typer.echo(f'   - "{msg.text[:50]}..." (ID: {msg.id})')
                            if msg.reply_to and hasattr(msg.reply_to, 'reply_to_msg_id'):
                                parent_id = msg.reply_to.reply_to_msg_id
                                if parent_id and parent_id <= 100:
                                    typer.echo(f'     🎯 Topic ID: {parent_id}')
                        found_any = True
                else:
                    # Just show group info
                    if hasattr(chat, 'forum') and chat.forum:
                        typer.echo('   ✅ This is a forum-style group')
                
                typer.echo('')
        
        if search and not found_any:
            typer.echo(f'No messages found containing "{search}"')
        
        await client.disconnect()
    
    asyncio.run(find_topics())


@doctor_app.command('show-config')
def check_config():
    """Display resolved configuration values showing what will actually be used.
    
    Shows the final configuration after all overrides (TOML → .env → env vars).
    
    Example:
        $ synapse-pipeline doctor show-config
        
        🔧 Current Configuration:
        
        [Telegram]
          API ID: 23568765
          API Hash: ***2c7b
          Channels: -1001234567890, -1009876543210
        
        📁 Config Sources:
          ✅ config.toml found
          ✅ .env file found
          ✅ 3 SYNAPSE_* environment variables set
    """
    settings = get_settings()
    
    typer.echo('🔧 Current Configuration:\n')
    
    # Telegram settings
    typer.echo('[Telegram]')
    typer.echo(f'  API ID: {settings.telegram.api_id or "Not set"}')
    typer.echo(f'  API Hash: {"***" + settings.telegram.api_hash[-4:] if settings.telegram.api_hash else "Not set"}')
    typer.echo(f'  Session: {"Configured" if settings.telegram.session_string else "Not set"}')
    typer.echo(f'  Channels: {", ".join(settings.telegram.channel_ids) if settings.telegram.channel_ids else "None"}')
    
    # Telegram Notifier
    typer.echo('\n[Telegram Notifier]')
    typer.echo(f'  Bot Token: {"***" + settings.telegram_notifier.bot_token[-4:] if settings.telegram_notifier.bot_token else "Not set"}')
    typer.echo(f'  Target ID: {settings.telegram_notifier.target.id or "Not set"}')
    typer.echo(f'  Topic ID: {settings.telegram_notifier.target.topic_id or "Not set"}')
    
    # Google Drive
    typer.echo('\n[Google Drive]')
    typer.echo(f'  Service Account: {settings.gdrive.service_account_path or "Not set"}')
    typer.echo(f'  Team Data Folder: {settings.gdrive.team_data_folder_id or "Not set"}')
    typer.echo(f'  Digests Folder: {settings.gdrive.team_digests_folder_id or "Not set"}')
    
    # Check which config sources are active
    typer.echo('\n📁 Config Sources:')
    if Path('config.toml').exists():
        typer.echo('  ✅ config.toml found')
    if Path('.env').exists():
        typer.echo('  ✅ .env file found')
    
    import os
    env_vars = [k for k in os.environ if k.startswith('SYNAPSE_')]
    if env_vars:
        typer.echo(f'  ✅ {len(env_vars)} SYNAPSE_* environment variables set')


@doctor_app.command('bot-list-chats')
def get_telegram_chat_id():
    """List all chats where your bot has received messages.
    
    This uses the Bot API to fetch recent updates. The bot must have
    received at least one message in the chat within the last 24 hours.
    
    Example:
        $ synapse-pipeline doctor bot-list-chats
        
        🔍 Fetching updates...
        Found 15 updates
        
        📱 Found chats:
        ──────────────────────────────────────────────────
        👥 Flashbots_X Core
           Type: supergroup
           Chat ID: -1002682777986
           
        🎯 Messages with topic IDs:
        ──────────────────────────────────────────────────
        Chat: Flashbots_X Core  
        Text: "Hello from update channel..."  
        Topic ID: 2457
    
    Steps to use:
    1. Add your bot to a group/channel
    2. Send a message in the group (mention the bot with @bot_name)
    3. Run this command within 24 hours
    """
    import httpx
    
    settings = get_settings()
    bot_token = settings.telegram_notifier.bot_token
    
    if not bot_token:
        typer.echo('❌ Error: Bot token not configured', err=True)
        typer.echo('\nPlease set in config.toml or environment:', err=True)
        typer.echo('  SYNAPSE_TELEGRAM_NOTIFIER__BOT_TOKEN=your_bot_token', err=True)
        raise typer.Exit(1)
    
    typer.echo('🔍 Fetching updates...\n')
    
    # Get recent updates
    url = f'https://api.telegram.org/bot{bot_token}/getUpdates?limit=100'
    response = httpx.get(url)
    
    if not response.is_success:
        typer.echo(f'❌ Error: {response.status_code} - {response.text}', err=True)
        raise typer.Exit(1)
    
    data = response.json()
    if not data.get('result'):
        typer.echo('No messages found. Make sure to:')
        typer.echo('1. Add the bot to your group')
        typer.echo('2. Send a message in the group')
        typer.echo('3. Try again within 24 hours')
        raise typer.Exit(1)
    
    typer.echo(f'Found {len(data["result"])} updates\n')
    
    chats_seen = {}
    recent_messages = []
    
    for update in data['result']:
        if 'message' in update:
            msg = update['message']
            chat = msg['chat']
            chat_id = chat['id']
            chat_type = chat['type']
            chat_title = chat.get('title', chat.get('first_name', 'Unknown'))
            
            if chat_id not in chats_seen:
                chats_seen[chat_id] = {
                    'type': chat_type,
                    'title': chat_title
                }
            
            # Track messages with topic info
            if msg.get('message_thread_id'):
                recent_messages.append({
                    'chat_id': chat_id,
                    'chat_title': chat_title,
                    'text': msg.get('text', '')[:50],
                    'thread_id': msg.get('message_thread_id'),
                })
    
    if not chats_seen:
        typer.echo('No chats found in recent updates.')
        raise typer.Exit(1)
    
    typer.echo('📱 Found chats:')
    typer.echo('-' * 50)
    for chat_id, info in chats_seen.items():
        icon = '👤' if info['type'] == 'private' else '👥'
        typer.echo(f'{icon} {info["title"]}')
        typer.echo(f'   Type: {info["type"]}')
        typer.echo(f'   Chat ID: {chat_id}')
        typer.echo()
    
    if recent_messages:
        typer.echo('\n🎯 Messages with topic IDs:')
        typer.echo('-' * 50)
        for msg in recent_messages[:5]:
            typer.echo(f'Chat: {msg["chat_title"]}')
            typer.echo(f'Text: "{msg["text"]}..."')
            typer.echo(f'Topic ID: {msg["thread_id"]}')
            typer.echo()
    
    typer.echo('\n📝 Configuration example:')
    typer.echo('[telegram_notifier.target]')
    typer.echo('id = "YOUR_CHAT_ID"')
    typer.echo('topic_id = YOUR_TOPIC_ID  # If using forum topics')


@doctor_app.command('bot-send-test')
def test_telegram_integration():
    """Send test messages to verify Telegram bot configuration.
    
    Sends a series of test messages to your configured chat to verify
    that your bot token and chat ID are working correctly.
    
    Example:
        $ synapse-pipeline doctor bot-send-test
        
        🧪 Testing Telegram Integration...
        
        Bot Token: 7250892957...nrG_U
        Chat ID: -1002682777986
        
        Test 1: Sending simple message...
        Result: ✅ Success
        
        Test 2: Sending markdown message...
        Result: ✅ Success
        
        🎉 Integration test complete!
    
    Note: This will send real messages to your configured chat!
    """
    settings = get_settings()
    bot_token = settings.telegram_notifier.bot_token
    chat_id = settings.telegram_notifier.target.id
    
    if not bot_token or not chat_id:
        typer.echo('❌ Error: Telegram credentials not configured!', err=True)
        typer.echo('\nPlease configure in config.toml:', err=True)
        typer.echo('  [telegram_notifier]', err=True)
        typer.echo('  bot_token = "your_bot_token"', err=True)
        typer.echo('  [telegram_notifier.target]', err=True)
        typer.echo('  id = "your_chat_id"', err=True)
        raise typer.Exit(1)
    
    typer.echo('🧪 Testing Telegram Integration...\n')
    typer.echo(f'Bot Token: {bot_token[:10]}...{bot_token[-5:]}')
    typer.echo(f'Chat ID: {chat_id}')
    typer.echo()
    
    # Confirm before sending
    if not typer.confirm('This will send test messages to your Telegram chat. Continue?'):
        typer.echo('Aborted.')
        raise typer.Abort()
    
    typer.echo()
    
    # Test 1: Simple message
    typer.echo('Test 1: Sending simple message...')
    result = send_telegram_notification(
        'Hello from Synapse Pipeline! 👋',
        bot_token=bot_token,
        chat_id=chat_id
    )
    typer.echo(f'Result: {"✅ Success" if result else "❌ Failed"}\n')
    
    if not result:
        raise typer.Exit(1)
    
    # Test 2: Markdown message
    typer.echo('Test 2: Sending markdown message...')
    markdown_msg = """*Synapse Pipeline Test* 🚀

This is a test of the notification system:
• **Bold text**
• _Italic text_
• `Code formatting`

Status: `OPERATIONAL`"""
    
    result = send_telegram_notification(
        markdown_msg,
        bot_token=bot_token,
        chat_id=chat_id
    )
    typer.echo(f'Result: {"✅ Success" if result else "❌ Failed"}\n')
    
    # Test 3: With topic ID if configured
    if settings.telegram_notifier.target.topic_id:
        typer.echo(f'Test 3: Sending to topic {settings.telegram_notifier.target.topic_id}...')
        result = send_telegram_notification(
            'Testing topic/thread notification 🎯',
            bot_token=bot_token,
            chat_id=chat_id,
            thread_id=settings.telegram_notifier.target.topic_id
        )
        typer.echo(f'Result: {"✅ Success" if result else "❌ Failed"}\n')
    
    typer.echo('🎉 Integration test complete!')


@doctor_app.command('generate-session')
def generate_telegram_session(
    output: str = typer.Option('clipboard', '--output', '-o', help='Output method: clipboard or env'),
):
    """Generate a Telegram session string for API access.
    
    This is a one-time setup to authenticate your Telegram account
    for use with the export commands.
    
    Prerequisites:
    - SYNAPSE_TELEGRAM__API_ID in .env or environment
    - SYNAPSE_TELEGRAM__API_HASH in .env or environment
    
    Example:
        $ synapse-pipeline doctor generate-session
        
        Generating Telegram session string...
        Using API_ID: 12345678
        
        Please enter your phone (or bot token): +1234567890
        Please enter the code you received: 12345
        
        ✅ Session string copied to clipboard!
        📋 Paste it into your .env file or password manager
    """
    import asyncio
    from telethon import TelegramClient
    from telethon.sessions import StringSession
    
    settings = get_settings()
    
    if not settings.telegram.api_id or not settings.telegram.api_hash:
        typer.echo('❌ Error: Telegram API credentials not configured', err=True)
        typer.echo('\nPlease add to your .env file:', err=True)
        typer.echo('SYNAPSE_TELEGRAM__API_ID=your_api_id', err=True)
        typer.echo('SYNAPSE_TELEGRAM__API_HASH=your_api_hash', err=True)
        typer.echo('\nGet these from: https://my.telegram.org/apps', err=True)
        raise typer.Exit(1)
    
    if output not in ['clipboard', 'env']:
        typer.echo('❌ Error: Invalid output method. Use --output=clipboard or --output=env', err=True)
        raise typer.Exit(1)
    
    async def generate():
        typer.echo('🔐 Generating Telegram session string...')
        typer.echo(f'Using API_ID: {settings.telegram.api_id}\n')
        
        try:
            client = TelegramClient(
                StringSession(),
                settings.telegram.api_id,
                settings.telegram.api_hash
            )
            
            await client.start()
            session_string = client.session.save()
            await client.disconnect()
            
            typer.echo('\n✅ Session string generated successfully!')
            
            # Handle different output methods
            success = False
            
            if output == 'clipboard':
                try:
                    import pyperclip
                    pyperclip.copy(session_string)
                    typer.echo('📋 Session string copied to clipboard!')
                    typer.echo('📋 Paste it into your password manager or GitHub secrets')
                    success = True
                except Exception as e:
                    typer.echo(f'⚠️  Could not copy to clipboard: {e}', err=True)
                    typer.echo('Falling back to .env file method...\n')
            
            if output == 'env' or (output == 'clipboard' and not success):
                # Append to .env file
                env_line = f'\nSYNAPSE_TELEGRAM__SESSION_STRING={session_string}\n'
                
                if Path('.env').exists():
                    # Check if already exists
                    env_content = Path('.env').read_text()
                    if 'SYNAPSE_TELEGRAM__SESSION_STRING' in env_content:
                        typer.echo('⚠️  SYNAPSE_TELEGRAM__SESSION_STRING already exists in .env')
                        if typer.confirm('Do you want to update it?'):
                            # Replace existing line
                            import re
                            new_content = re.sub(
                                r'^SYNAPSE_TELEGRAM__SESSION_STRING=.*$',
                                f'SYNAPSE_TELEGRAM__SESSION_STRING={session_string}',
                                env_content,
                                flags=re.MULTILINE
                            )
                            Path('.env').write_text(new_content)
                            typer.echo('✅ Updated session string in .env file')
                    else:
                        # Append new line
                        with open('.env', 'a') as f:
                            f.write(env_line)
                        typer.echo('✅ Added session string to .env file')
                else:
                    typer.echo('⚠️  No .env file found. Create one first with: cp .env.example .env')
            
        except Exception as e:
            typer.echo(f'\n❌ Error: {e}', err=True)
            raise typer.Exit(1)
    
    asyncio.run(generate())


if __name__ == '__main__':
    app()