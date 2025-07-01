# GitHub Actions Workflows

This directory contains automated workflows for the Synapse Pipeline project.

## Available Workflows

### generate-digest.yml
Full end-to-end team digest generation workflow that:
1. Exports Telegram messages from configured channels
2. Downloads team data from Google Drive
3. Transforms data to markdown format
4. Generates team digest using Claude
5. Uploads digest to Google Drive
6. Sends notification via Telegram bot

## Required Secrets

To run these workflows, you need to configure the following secrets in your GitHub repository settings:

### Telegram API (for exporting messages)
- `TELEGRAM_API_ID` - Your Telegram API ID
- `TELEGRAM_API_HASH` - Your Telegram API Hash
- `TELEGRAM_SESSION_STRING` - Session string for authentication
- `TELEGRAM_CHANNEL_IDS` - Comma-separated list of channel IDs to export

### Google Drive
- `GDRIVE_SERVICE_ACCOUNT_B64` - Base64-encoded service account JSON (recommended)
  - To encode: `base64 -i service-account.json | tr -d '\n'`

### Claude API
- `CLAUDE_API_KEY` - Your Anthropic API key for content generation

### Telegram Bot (for notifications)
- `TELEGRAM_BOT_TOKEN` - Your Telegram bot token
- `TELEGRAM_CHAT_ID` - The chat/channel ID to send notifications to
- `TELEGRAM_THREAD_ID` - (Optional) Thread ID for forum-style groups

## Setting Up Secrets

1. Go to your repository on GitHub
2. Navigate to Settings → Secrets and variables → Actions
3. Click "New repository secret"
4. Add each secret with its corresponding value

### Example: Setting up CLAUDE_API_KEY

```bash
# The value should be your actual Claude API key
# Format: sk-ant-xxxxx...
```

## Workflow Schedule

The digest generation workflow runs:
- **Automatically**: Every Monday at 12:00 UTC
- **Manually**: Via the Actions tab with customizable parameters

## Manual Workflow Execution

1. Go to the Actions tab in your repository
2. Select "Generate Team Digest" workflow
3. Click "Run workflow"
4. Configure optional parameters:
   - `start_days_ago`: Number of days ago to start (default: 7)
   - `skip_upload`: Skip Google Drive upload for testing (default: false)
   - `skip_notify`: Skip Telegram notification for testing (default: false)

## Integration Status

| Component | Status | Notes |
|-----------|--------|-------|
| Digest Generation | ✅ Ready | Using Claude API |
| Telegram Export | ✅ Ready | Via Telegram API |
| Google Drive Sync | ✅ Ready | Upload/Download via rclone |
| Notifications | ✅ Ready | Via Telegram Bot API |

## Environment Variables

The workflows use the following environment variables (set automatically):
- `GITHUB_WORKSPACE` - Repository root directory
- `GITHUB_RUN_ID` - Unique workflow run identifier
- `GITHUB_SHA` - Commit SHA that triggered the workflow

## Troubleshooting

### Common Issues

1. **Authentication failures**
   - Verify all API credentials and tokens are correct
   - Check Telegram session string is valid
   - Ensure bot has permissions in target chat

2. **Google Drive errors**
   - Verify service account has access to folder IDs in config.toml
   - Check service account JSON is valid
   - Ensure rclone is properly installed

3. **Missing dependencies**
   - The workflow installs rclone and Python dependencies automatically
   - Uses Python 3.12 and uv for dependency management

4. **Claude API errors**
   - Verify API key has sufficient credits
   - Check rate limits haven't been exceeded

## Development

To test workflows locally:

```bash
# Install act (GitHub Actions local runner)
brew install act  # macOS
# or
curl https://raw.githubusercontent.com/nektos/act/master/install.sh | sudo bash  # Linux

# Run workflow locally
act -j generate-digest --secret-file .env.secrets
```

Create `.env.secrets` file (don't commit this!):
```
CLAUDE_API_KEY=your-api-key-here
```

## Local Testing

To test individual components before running the full workflow:

```bash
# Test Telegram export
synapse-pipeline export-telegram --start 2025-06-01 --end 2025-06-07

# Test Google Drive
synapse-pipeline download-gdrive ./data --since-days 7
synapse-pipeline upload-digest ./output/test.md

# Test notifications
synapse-pipeline notify "Test message from GitHub Actions"
```

## Future Enhancements

Potential improvements:
1. Add more output formats (PDF, HTML)
2. Support multiple Claude models
3. Implement retry logic for API failures
4. Add metrics and monitoring
5. Support custom digest templates