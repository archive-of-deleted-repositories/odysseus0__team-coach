# Testing Guide

This directory contains all tests for Synapse Pipeline, organized by test type.

## Test Structure

```
tests/
├── unit/                     # Fast, isolated tests (no external dependencies)
├── integration/              # Tests that use external services
├── e2e/                      # End-to-end pipeline tests
└── data/                     # Test fixtures and sample data
```

## Running Tests

### Unit Tests (Fast, No External Dependencies)
```bash
# Run all unit tests
pytest tests/unit

# Run specific unit test
pytest tests/unit/test_telegram_transformer.py
```

### Integration Tests (Require External Services)
Integration tests are marked with `@pytest.mark.integration` and skipped by default.

```bash
# Run all integration tests
pytest -m integration

# Run specific integration test suite
pytest tests/integration/test_gdrive.py -v
```

**Note**: Integration tests require real credentials and will FAIL FAST if not configured.

## Available Integration Tests

### E2E Tests (Full Pipeline)
```bash
# Run end-to-end tests
pytest tests/e2e -v
```

## Integration Test Details

### 1. Telegram Exporter (`integration/test_telegram_exporter.py`)
Tests real Telegram API operations:
- Lists available channels
- Exports recent messages
- Handles reactions and media
- Tests error scenarios

**Required Environment Variables:**
```bash
SYNAPSE_TELEGRAM__API_ID=your_api_id
SYNAPSE_TELEGRAM__API_HASH=your_api_hash
SYNAPSE_TELEGRAM__SESSION_STRING=your_session_string
SYNAPSE_TELEGRAM__CHANNEL_IDS=-1001234567890,-1009876543210
```

### 2. Google Drive (`integration/test_gdrive.py`)
Tests real Google Drive operations:
- Downloads files from folders
- Uploads files and generates share links
- Tests error handling

**Required Environment Variables:**
```bash
SYNAPSE_GDRIVE__SERVICE_ACCOUNT_PATH=./service-account.json
SYNAPSE_GDRIVE__TEAM_DATA_FOLDER_ID=your_input_folder_id
SYNAPSE_GDRIVE__TEAM_DIGESTS_FOLDER_ID=your_output_folder_id
```

### 3. Telegram Notifier (`integration/test_telegram_notifier.py`)
Tests real Telegram Bot API:
- Sends notifications
- Tests threading/topics
- Verifies markdown formatting

**Required Environment Variables:**
```bash
SYNAPSE_TELEGRAM_BOT_TOKEN=your_bot_token
SYNAPSE_TELEGRAM_CHAT_ID=your_chat_id
```

## Running Integration Tests

### Run unit tests only (default):
```bash
uv run pytest  # Integration tests are skipped by default
```

### Run integration tests only:
```bash
uv run pytest -m integration -v
```

### Run ALL tests (unit + integration):
```bash
uv run pytest -m "" -v  # Empty marker runs everything
```

### Run specific integration test:
```bash
uv run pytest tests/test_telegram_exporter_integration.py -v
```

### Test credentials before running tests:
```bash
# Test Telegram credentials
python tests/test_telegram_exporter_integration.py

# Test Google Drive credentials  
python tests/test_gdrive_integration.py
```

## Setting Up Test Accounts

### Telegram Test Setup
1. Create a test Telegram account (or use existing)
2. Create test channels/groups for exports
3. Add some test messages and reactions
4. Generate session string using the exporter module

### Google Drive Test Setup
1. Create a test Google Cloud project
2. Enable Drive API
3. Create service account and download JSON key
4. Create test folders in Drive
5. Share folders with service account email

### Telegram Bot Test Setup
1. Create test bot via @BotFather
2. Create test group/channel
3. Add bot to group with appropriate permissions

## Best Practices

1. **Use test accounts** - Never use production credentials
2. **Clean up** - Tests should clean up created data when possible
3. **Idempotent** - Tests should work when run multiple times
4. **Time-boxed** - Limit date ranges to recent data to avoid large exports
5. **Fail fast** - Tests should fail immediately when setup is incorrect

## CI/CD Considerations

These tests are NOT run in GitHub Actions by default because:
- They require real credentials
- They make external API calls
- They can be rate-limited
- They may incur costs

To run in CI/CD:
1. Store credentials as secrets
2. Run on schedule rather than every commit
3. Use dedicated test accounts
4. Monitor for failures due to API changes