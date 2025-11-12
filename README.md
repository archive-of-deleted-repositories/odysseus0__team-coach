# Synapse Pipeline

Context syncing tool for remote teams that automatically generates organizational digests. It collects data from Telegram channels and meeting transcripts, transforms it into structured formats, generates team update digests using Claude, and distributes them via Google Drive.

## Features

- **Telegram API Integration**: Export messages directly from Telegram using telethon
- **Feedback Loop System**: Team members can mention `@synapse_x_bot` to provide corrections that are automatically extracted and incorporated into future digests
- Transform Telegram JSON exports to clean markdown format with full timestamps
- Organize messages by channels/topics
- Preserve reactions, media references, and threading
- Batch processing support
- List available channels and authenticate with session strings
- **Agent Memory System**: Past digests and coaching corrections accumulate as context over time
- Google Drive integration for downloading team data and uploading digests
- Automatic share link generation for uploaded digests
- **LLM Evaluation**: Promptfoo test suites verify digest quality and feedback responsiveness

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

### Extract feedback mentions

```bash
# Extract from current day's Telegram messages
synapse-pipeline extract-feedback ./transformed_data --output feedback.txt

# Extract from multiple directories (e.g., current + historical)
synapse-pipeline extract-feedback ./transformed_data ./agent_memory --export-json feedback.json
```

## How the Feedback Loop Works

The system includes a self-improving feedback mechanism:

1. **Team gives correction**: Mention `@synapse_x_bot` in Telegram with your feedback
   ```
   @synapse_x_bot you're being too optimistic - we haven't validated PMF yet
   ```

2. **Automatic extraction**: The pipeline extracts bot mentions with surrounding context

3. **Prompt injection**: Corrections are prepended to the digest generation prompt:
   ```markdown
   **IMMEDIATE FEEDBACK (1 item): Must address in today's digest**

   The team gave you direct corrections recently. You MUST acknowledge and apply these today:

   ### Immediate Feedback #1
   - **Source**: Team Channel (2025-11-12)
   [Full conversation context]
   ```

4. **Verified application**: Promptfoo tests verify Claude acknowledged and applied the correction

5. **Long-term memory**: Agent memory accumulates coaching corrections for ongoing context

This creates a feedback loop where the bot learns from team corrections over time.

## LLM Evaluation with Promptfoo

The system uses [Promptfoo](https://promptfoo.dev) to evaluate digest quality and verify that Claude responds appropriately to team feedback.

### Current Evaluations

Two test suites run automatically on every digest generation:

#### 1. CI Tests (`promptfooconfig.yaml`)

Four test scenarios covering structure and feedback adherence:

**Deterministic checks** (fast, free):
- **Character limit**: Must be under 4000 characters
- **Source citations**: Should include `[#` citation markers
- **Proper markdown structure**: Verifies `## 📅 Daily Digest` header

**Feedback adherence checks** (llm-rubric):
- **Factual correction test**: Verify Claude fixes incorrect claims when corrected
- **Tone adjustment test**: Verify Claude adjusts tone based on team feedback

These synthetic feedback tests ensure the feedback mechanism works even when there are no real team mentions.

#### 2. Feedback Tests (`promptfooconfig-feedback-generated.yaml`)

**Dynamically generated** tests that verify Claude acknowledged and applied team corrections:

- Generated from `feedback_items.json` (extracted bot mentions)
- Uses `llm-rubric` assertions for semantic evaluation
- Each feedback item becomes a separate test case
- Tests check if Claude:
  - Acknowledged the specific correction
  - Applied the correction to the digest
  - Didn't repeat the mistake the team pointed out

**Example test**: If team said `@synapse_x_bot Peeker is not live yet`, the test verifies Claude doesn't claim Peeker has launched.

### Where Evaluations Are Stored

Evaluation results are uploaded to three locations:

**1. Google Drive** (`team_digests_folder`):
```
team_digests_folder/
  evaluations/
    2025-11-12/
      ci-evaluation.json          # CI test results
      feedback-evaluation.json    # Feedback test results
    summary_2025-11-12.txt         # Human-readable summary
```

**2. GitHub Actions artifacts** (7-day retention):
- `evaluation-results-{run_id}` - Contains all JSON results and summary

**3. Local directory** (when running manually):
- `eval/results/` - Test outputs and detailed results

### Running Evaluations Locally

```bash
# Install Promptfoo globally
npm install -g promptfoo

# Run CI tests
npx promptfoo eval --config promptfooconfig.yaml

# Run feedback tests (if feedback exists)
npx promptfoo eval --config promptfooconfig-feedback-generated.yaml

# View results in web UI
npx promptfoo view

# Run evaluations with specific number of workers
npx promptfoo eval --config promptfooconfig.yaml -j 1  # Sequential execution
```

### Adding New Evaluations

#### Method 1: Add to existing CI test suite

Edit `promptfooconfig.yaml`:

```yaml
tests:
  - vars:
      digest: file://path/to/test-digest.md
    assert:
      - type: llm-rubric
        value: The digest should mention project milestones
      - type: not-contains
        value: "CONFIDENTIAL"
      - type: javascript
        value: output.length > 100
```

#### Method 2: Create new test configuration

1. **Create new config file** (e.g., `promptfooconfig-custom.yaml`):

```yaml
prompts:
  - file://config/team_coach_prompt.md

providers:
  - id: anthropic:messages:claude-sonnet-4-5-20250929
    config:
      temperature: 1.0
      max_tokens: 16000

tests:
  - vars:
      current_messages: file://path/to/messages.md
    assert:
      - type: llm-rubric
        value: Your custom evaluation criteria here
```

2. **Add to workflow** (`.github/workflows/generate-digest.yml`):

```yaml
- name: Run Custom Evaluation
  run: |
    npx promptfoo eval --config promptfooconfig-custom.yaml -j 1
```

3. **Upload results**:

```yaml
- name: Upload Custom Results
  run: |
    uv run synapse-pipeline upload-digest eval/results/custom-evaluation.json \
      --filename "evaluations/${EVAL_DATE}/custom-evaluation.json"
```

#### Method 3: Dynamic test generation (like feedback tests)

1. **Create test generator script** (`eval/generate-my-tests.js`):

```javascript
const fs = require('fs');
const yaml = require('js-yaml');

// Load your test data
const testData = require('./my-test-data.json');

// Generate test cases
const tests = testData.items.map(item => ({
  vars: {
    current_messages: `Test case: ${item.description}`,
  },
  assert: [
    {
      type: 'llm-rubric',
      value: item.criteria
    }
  ]
}));

// Create config
const config = {
  prompts: ['file://config/team_coach_prompt.md'],
  providers: ['anthropic:messages:claude-sonnet-4-5-20250929'],
  tests: tests,
  outputPath: './eval/results/my-evaluation.json'
};

// Write config
fs.writeFileSync(
  'promptfooconfig-my-generated.yaml',
  yaml.dump(config)
);
```

2. **Add to workflow**:

```yaml
- name: Generate and Run Custom Tests
  run: |
    node eval/generate-my-tests.js
    npx promptfoo eval --config promptfooconfig-my-generated.yaml -j 1
```

### Assertion Types

Promptfoo supports multiple assertion types:

- `llm-rubric`: Use another LLM to evaluate the output semantically
- `contains` / `not-contains`: Check for specific strings
- `regex`: Pattern matching
- `javascript`: Custom JavaScript validation functions
- `python`: Custom Python validation scripts
- `similarity`: Check semantic similarity to expected output
- `cost`: Verify API cost constraints
- `latency`: Verify response time

See [Promptfoo assertions docs](https://promptfoo.dev/docs/configuration/expected-outputs/) for complete reference.

### Best Practices

1. **Use `llm-rubric` for semantic checks**: Great for verifying intent and meaning
2. **Use `contains`/`regex` for structural checks**: Fast and deterministic
3. **Keep tests focused**: One clear criterion per assertion
4. **Test both positive and negative cases**: Verify what should AND shouldn't be in output
5. **Run tests sequentially** (`-j 1`) to avoid rate limits and ensure consistent results
6. **Store test data separately**: Keep test inputs and expected outputs in version control

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