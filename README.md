# Synapse Pipeline

Context syncing tool for remote teams that automatically generates organizational digests. It collects data from Telegram channels and meeting transcripts, transforms it into structured formats, generates team update digests using Claude, and distributes them via Google Drive.

## Features

- **Telegram API Integration**: Export messages directly from Telegram using telethon
- Transform Telegram JSON exports to clean markdown format
- Organize messages by channels/topics
- Preserve reactions, media references, and threading
- Batch processing support
- List available channels and authenticate with session strings
- Google Drive integration for downloading team data and uploading digests
- Automatic share link generation for uploaded digests

## Prerequisites

- Python 3.12+
- [rclone](https://rclone.org/install/) - Required for Google Drive integration
- [Claude API key](https://console.anthropic.com/) - Required for digest generation
- Google Cloud service account with Drive API access
- Telegram API credentials (free from telegram.org)

### Installing rclone

**macOS:**
```bash
brew install rclone
```

**Linux/Ubuntu:**
```bash
sudo apt-get install rclone
```

**Other platforms:**
See [rclone installation guide](https://rclone.org/install/)

## Installation

```bash
# Clone the repository
git clone https://github.com/yourusername/synapse-pipeline.git
cd synapse-pipeline

# Install dependencies using uv
uv sync
```

## Quick Start

### Step 1: Set Up Telegram API Access

#### Get API Credentials

1. Visit https://my.telegram.org/apps
2. Log in with your phone number
3. Create a new application:
   - **App title**: Synapse Pipeline (or your choice)
   - **Short name**: synapse
   - **Platform**: Other
4. Copy your `API ID` and `API Hash`

#### Generate Session String

After setting up your `.env` file with Telegram credentials, run:

```bash
synapse-pipeline doctor generate-session
```

This will:
- Prompt for your phone number
- Send a verification code to your Telegram  
- Generate a session string
- Show you the `SYNAPSE_TELEGRAM__SESSION_STRING` to add to `.env`

#### Find Channel IDs

To find channel IDs to export from:

```bash
synapse-pipeline list-channels
```

### Step 2: Set Up Google Drive

#### Create Service Account

1. Go to [Google Cloud Console](https://console.cloud.google.com)
2. Create a new project or select existing
3. Enable Google Drive API:
   - Go to "APIs & Services" → "Library"
   - Search for "Google Drive API"
   - Click "Enable"
4. Create a service account:
   - Go to "IAM & Admin" → "Service Accounts"
   - Click "Create Service Account"
   - Name it (e.g., "synapse-pipeline")
   - Skip optional permissions
   - Click "Done"
5. Create and download key:
   - Click on your service account
   - Go to "Keys" tab
   - Add Key → Create new key → JSON
   - Save as `service-account.json` in project root

#### Set Up Google Drive Folders

1. Create two folders in Google Drive:
   - **Team Data** (input folder for context data)
   - **Team Digests** (output folder for generated digests)
   
2. Get folder IDs:
   - Open each folder
   - Copy the ID from URL: `https://drive.google.com/drive/folders/[FOLDER_ID]`
   
3. Share folders with service account:
   - Find service account email in your JSON file (e.g., `synapse@project.iam.gserviceaccount.com`)
   - Share "Team Data" folder with **Viewer** access
   - Share "Team Digests" folder with **Editor** access

### Step 3: Configure Environment

1. Copy the example configuration:
   ```bash
   cp .env.example .env
   ```

2. Edit `.env` and fill in your credentials (the file contains detailed instructions for each setting)

3. Edit `config.toml` with your Google Drive folder IDs:
   ```toml
   [gdrive]
   team_data_folder_id = "your_input_folder_id"
   team_digests_folder_id = "your_output_folder_id"
   ```

### Step 4: Test Your Setup

Run each component to verify configuration:

```bash
# Test Telegram connection
synapse-pipeline list-channels

# Test Google Drive
synapse-pipeline download-gdrive ./test-download --since-days 1

# Test a full pipeline run
synapse-pipeline export-telegram --start 2025-06-01 --end 2025-06-07
synapse-pipeline batch-transform ./data/telegram -o ./output/transformed
```

## Usage

### Export messages from Telegram (API)

```bash
# Export last 7 days (default)
synapse-pipeline export-telegram

# Export specific date range
synapse-pipeline export-telegram --start 2025-06-01 --end 2025-06-30

# List available channels
synapse-pipeline list-channels
```

### Transform a single Telegram export

```bash
synapse-pipeline transform-telegram path/to/telegram_export.json -o output.md
```

### Batch transform multiple exports

```bash
synapse-pipeline batch-transform path/to/telegram_exports/ -o output_dir/
```

### Download team data from Google Drive

```bash
# Download files modified in the last 7 days (default)
synapse-pipeline download-gdrive ./downloaded-data

# Download files modified in the last 30 days
synapse-pipeline download-gdrive ./downloaded-data --since-days 30
```

### Upload team digest to Google Drive

```bash
# Upload a digest file
synapse-pipeline upload-digest ./output/team-digest.md

# Upload with a custom filename
synapse-pipeline upload-digest ./output/team-digest.md --filename "weekly-digest-2024-01-08.md"
```

### Send notifications via Telegram

```bash
# Send a message directly
synapse-pipeline notify "Team digest is ready!"

# Pipe message from another command
echo "Digest uploaded successfully" | synapse-pipeline notify

# Use custom bot credentials (overrides config)
synapse-pipeline notify "Hello team" --token BOT_TOKEN --chat CHAT_ID

# Send to a specific topic/thread
synapse-pipeline notify "New digest available" --thread THREAD_ID
```

## GitHub Actions Setup

The repository includes a GitHub Actions workflow for automated weekly digest generation.

### Configure Secrets

Go to Settings → Secrets and variables → Actions, and add:

| Secret Name | Description | Required |
|-------------|-------------|----------|
| `CLAUDE_API_KEY` | Your Anthropic API key | ✅ Yes |
| `TELEGRAM_API_ID` | From Telegram setup | ✅ Yes |
| `TELEGRAM_API_HASH` | From Telegram setup | ✅ Yes |
| `TELEGRAM_SESSION_STRING` | From Telegram setup | ✅ Yes |
| `TELEGRAM_CHANNEL_IDS` | Comma-separated list | ✅ Yes |
| `GDRIVE_SERVICE_ACCOUNT_B64` | Base64-encoded service account | ✅ Yes |
| `TELEGRAM_BOT_TOKEN` | For notifications | ❌ Optional |
| `TELEGRAM_CHAT_ID` | For notifications | ❌ Optional |
| `TELEGRAM_THREAD_ID` | For topic notifications | ❌ Optional |

**Important**: For `GDRIVE_SERVICE_ACCOUNT_B64`, encode your service account:
```bash
base64 -i service-account.json | tr -d '\n'
```

### Manual Workflow Trigger

1. Go to Actions tab
2. Select "Generate Team Digest"
3. Click "Run workflow"
4. Configure options:
   - `start_days_ago`: Number of days to look back (default: 7)
   - `skip_upload`: Skip Google Drive upload for testing
   - `skip_notify`: Skip Telegram notification for testing

## Development

```bash
# Run tests
uv run pytest

# Run linting
uv run ruff check src/

# Run type checking
uv run pyright
```