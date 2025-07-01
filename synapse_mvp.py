#!/usr/bin/env python3
"""
Synapse Pipeline MVP - Everything in one file
Run daily to generate team digests from Telegram + Google Drive
"""

import os
import json
import subprocess
from datetime import datetime, timedelta
from pathlib import Path
import asyncio
import httpx

# Config from environment
TELEGRAM_API_ID = os.getenv('TELEGRAM_API_ID')
TELEGRAM_API_HASH = os.getenv('TELEGRAM_API_HASH')
TELEGRAM_SESSION = os.getenv('TELEGRAM_SESSION_STRING')
TELEGRAM_CHANNEL = os.getenv('TELEGRAM_CHANNEL_ID', '-1002682777986')

BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
CHAT_ID = os.getenv('TELEGRAM_CHAT_ID', '-1002682777986')
TOPIC_ID = os.getenv('TELEGRAM_TOPIC_ID', '2457')

GDRIVE_SERVICE_ACCOUNT = os.getenv('GDRIVE_SERVICE_ACCOUNT_PATH', './service-account.json')
GDRIVE_FOLDER_ID = os.getenv('GDRIVE_FOLDER_ID', '11oFJlobneHfKILYpjIB9J_uHtYr-8TZT')
GDRIVE_OUTPUT_FOLDER = os.getenv('GDRIVE_OUTPUT_FOLDER', '19v2W2C0DlSgh-9HneDSJTP42fbunqzTQ')

CLAUDE_API_KEY = os.getenv('CLAUDE_API_KEY')

# Working directories
WORK_DIR = Path('./digest_workspace')
WORK_DIR.mkdir(exist_ok=True)


async def export_telegram():
    """Export Telegram messages from last 24 hours"""
    print("📱 Exporting Telegram messages...")
    
    from telethon import TelegramClient
    from telethon.sessions import StringSession
    
    client = TelegramClient(StringSession(TELEGRAM_SESSION), TELEGRAM_API_ID, TELEGRAM_API_HASH)
    await client.start()
    
    messages = []
    cutoff = datetime.now() - timedelta(days=1)
    
    async for message in client.iter_messages(TELEGRAM_CHANNEL, offset_date=cutoff):
        if message.text:
            messages.append({
                'date': message.date.isoformat(),
                'from': getattr(message.sender, 'username', 'Unknown'),
                'text': message.text
            })
    
    await client.disconnect()
    
    # Save as simple JSON
    output_file = WORK_DIR / 'telegram_export.json'
    with open(output_file, 'w') as f:
        json.dump({'messages': messages}, f, indent=2)
    
    print(f"✅ Exported {len(messages)} messages")
    return output_file


def download_gdrive():
    """Download files from Google Drive modified in last 24 hours"""
    print("📂 Downloading from Google Drive...")
    
    # Setup rclone config
    config = f"""[gdrive]
type = drive
scope = drive
service_account_file = {GDRIVE_SERVICE_ACCOUNT}
"""
    config_file = WORK_DIR / 'rclone.conf'
    config_file.write_text(config)
    
    # Download recent files
    cmd = [
        'rclone', 'copy', 
        f'gdrive:', 
        str(WORK_DIR / 'gdrive_data'),
        '--config', str(config_file),
        '--drive-root-folder-id', GDRIVE_FOLDER_ID,
        '--max-age', '1d'
    ]
    
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"⚠️  rclone error: {result.stderr}")
    
    # List what we got
    downloaded = list((WORK_DIR / 'gdrive_data').rglob('*'))
    print(f"✅ Downloaded {len([f for f in downloaded if f.is_file()])} files")
    return WORK_DIR / 'gdrive_data'


def transform_data():
    """Transform Telegram and GDrive data to markdown"""
    print("🔄 Transforming data...")
    
    output = []
    
    # Process Telegram data
    telegram_file = WORK_DIR / 'telegram_export.json'
    if telegram_file.exists():
        with open(telegram_file) as f:
            data = json.load(f)
            
        output.append("## Telegram Messages\n")
        for msg in data.get('messages', [])[:20]:  # Limit to recent 20
            date = msg['date'].split('T')[0]
            output.append(f"**{msg['from']}** ({date}): {msg['text']}\n")
    
    # Process GDrive files
    output.append("\n## Team Documents\n")
    gdrive_dir = WORK_DIR / 'gdrive_data'
    for file in gdrive_dir.rglob('*.md'):
        output.append(f"\n### {file.name}\n")
        content = file.read_text()[:1000]  # First 1000 chars
        output.append(content + "\n")
    
    # Save transformed data
    output_file = WORK_DIR / 'all_data.md'
    output_file.write_text('\n'.join(output))
    
    print(f"✅ Transformed data saved")
    return output_file


def generate_digest():
    """Generate digest using Claude"""
    print("🤖 Generating digest with Claude...")
    
    # Create prompt file
    prompt = """Analyze the team data below and create a daily digest with these sections:

## 📅 Daily Digest - [Today's Date]
### 🎯 Key Updates
### 💬 Discussion Highlights  
### 🚀 Action Items
### 📊 Quick Metrics

Keep it concise and actionable. Focus on what matters for team coordination.

---
TEAM DATA:
"""
    
    prompt_file = WORK_DIR / 'prompt.md'
    data_file = WORK_DIR / 'all_data.md'
    
    # Combine prompt with data
    full_prompt = prompt + '\n' + data_file.read_text()
    prompt_file.write_text(full_prompt)
    
    # Call Claude
    digest_file = WORK_DIR / f'digest_{datetime.now().date()}.md'
    cmd = [
        'claude', '--model', 'sonnet',
        '-p', f'Generate a team digest and save it to {digest_file.name}',
        '--allowedTools', 'LS', 'Read', 'Write'
    ]
    
    result = subprocess.run(cmd, stdin=open(prompt_file), capture_output=True, text=True)
    
    # Check if digest was created
    if not digest_file.exists():
        print("⚠️  Claude didn't create digest file, using fallback")
        digest_file.write_text("# Daily Digest\n\nError generating digest. Check logs.")
    
    print("✅ Digest generated")
    return digest_file


def upload_to_gdrive(file_path):
    """Upload digest to Google Drive"""
    print("☁️  Uploading to Google Drive...")
    
    config_file = WORK_DIR / 'rclone.conf'
    filename = file_path.name
    
    cmd = [
        'rclone', 'copyto',
        str(file_path),
        f'gdrive:{filename}',
        '--config', str(config_file),
        '--drive-root-folder-id', GDRIVE_OUTPUT_FOLDER
    ]
    
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode == 0:
        print(f"✅ Uploaded to Google Drive")
        return f"https://drive.google.com/drive/folders/{GDRIVE_OUTPUT_FOLDER}"
    else:
        print(f"⚠️  Upload failed: {result.stderr}")
        return None


def send_telegram_notification(message):
    """Send notification to Telegram"""
    print("📨 Sending Telegram notification...")
    
    url = f'https://api.telegram.org/bot{BOT_TOKEN}/sendMessage'
    data = {
        'chat_id': CHAT_ID,
        'text': message,
        'parse_mode': 'Markdown'
    }
    
    if TOPIC_ID:
        data['message_thread_id'] = TOPIC_ID
    
    response = httpx.post(url, json=data)
    if response.is_success:
        print("✅ Notification sent!")
    else:
        print(f"⚠️  Failed to send: {response.text}")


async def main():
    """Run the full pipeline"""
    print("🚀 Starting Synapse Pipeline MVP\n")
    
    try:
        # 1. Export Telegram data
        if TELEGRAM_SESSION:
            await export_telegram()
        else:
            print("⚠️  No Telegram session, skipping export")
        
        # 2. Download Google Drive data
        if Path(GDRIVE_SERVICE_ACCOUNT).exists():
            download_gdrive()
        else:
            print("⚠️  No service account, skipping GDrive")
        
        # 3. Transform data
        transform_data()
        
        # 4. Generate digest
        digest_file = generate_digest()
        
        # 5. Upload to Google Drive (optional)
        gdrive_link = None
        if Path(GDRIVE_SERVICE_ACCOUNT).exists():
            gdrive_link = upload_to_gdrive(digest_file)
        
        # 6. Send to Telegram
        digest_content = digest_file.read_text()
        if gdrive_link:
            digest_content += f"\n\n[View in Google Drive]({gdrive_link})"
        
        if BOT_TOKEN:
            send_telegram_notification(digest_content)
        else:
            print("⚠️  No bot token, skipping notification")
            print("\n--- DIGEST CONTENT ---")
            print(digest_content)
        
        print("\n✅ Pipeline complete!")
        
    except Exception as e:
        print(f"\n❌ Pipeline failed: {e}")
        # Send error notification if possible
        if BOT_TOKEN:
            send_telegram_notification(f"❌ Pipeline failed: {e}")
        raise


if __name__ == '__main__':
    # Quick test mode for development
    if os.getenv('TEST_MODE'):
        print("🧪 Test mode - only sending notification")
        send_telegram_notification("Test notification from MVP pipeline")
    else:
        asyncio.run(main())