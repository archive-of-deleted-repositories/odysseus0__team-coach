# Telegram Bot Setup Guide

## Quick Setup

### 1. Create Your Bot

1. Open Telegram and search for @BotFather
2. Send `/newbot` and follow the prompts
3. Save your bot token (looks like: `1234567890:ABCdefGHIjklMNOpqrsTUVwxyz`)

### 2. Get Your Chat ID (Recommended Method)

1. **For group chats, prepare your bot FIRST**:
   - **Option A (Recommended)**: Plan to add bot as admin
   - **Option B**: Disable privacy mode:
     1. Message @BotFather
     2. Send `/mybots` → Select your bot
     3. Bot Settings → Group Privacy → Turn off
     4. ⚠️ Must do this BEFORE adding bot to group!

2. **Add your bot to the target chat**:
   - For personal notifications: Start a chat with your bot
   - For group notifications: Add bot to the group (as admin if using Option A)

3. **Send a test message** to the bot or in the group

4. **Run the doctor command**:
   ```bash
   synapse-pipeline doctor bot-list-chats
   ```
   
   This will show all chats where your bot has received messages:
   ```
   📱 Found chats:
   --------------------------------------------------
   👥 Flashbots_X Core
      Type: supergroup
      Chat ID: -1002682777986
   ```

5. **Copy the Chat ID** (negative numbers for groups)

### Alternative Methods

<details>
<summary>Other ways to get chat ID</summary>

#### For Personal Chats Only
- Search for @userinfobot on Telegram
- It will reply with your user ID

#### Manual API Method
- Visit: `https://api.telegram.org/bot<YOUR_BOT_TOKEN>/getUpdates`
- Look for `"chat":{"id":YOUR_CHAT_ID}` in the response
</details>

### 3. Configure Environment

Add to your `.env` file:

```bash
SYNAPSE_TELEGRAM_NOTIFIER__BOT_TOKEN=your_bot_token_here
```

Add to your `config.toml` (or use environment variables):

```toml
[telegram_notifier.target]
id = "-1002682777986"  # Your chat ID from step 2
topic_id = 2457       # Optional: For forum topics only
```

### 4. Test Your Bot

```bash
synapse-pipeline doctor bot-send-test
```

You should receive test messages in your configured chat!

## Troubleshooting

- **Bot not receiving messages in groups?** Make sure bot is admin or has Group Privacy disabled in @BotFather
- **No chats showing up?** Send a message to the bot first, then try again
- **Wrong chat?** Use `SYNAPSE_TELEGRAM_NOTIFIER__CHAT_ID` env var to override config.toml