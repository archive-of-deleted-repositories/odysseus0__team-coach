# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What This Project Is

Synapse Pipeline is a context syncing tool for remote teams that automatically generates organizational digests. It collects data from Telegram channels and meeting transcripts, transforms it into structured formats, generates team update digests using Claude, and distributes them via Google Drive.

## Prerequisites

- Python 3.12+
- rclone (install via `brew install rclone` on macOS or `apt-get install rclone` on Linux)
- Claude API key (required for digest generation - get from https://console.anthropic.com/)
- Google Cloud service account with Drive API access

## Commands

```bash
# Install dependencies
uv sync

# Run tests
uv run pytest
uv run pytest tests/test_telegram.py::test_specific  # Run specific test

# Lint and type check
uv run ruff check src/
uv run pyright

# CLI usage - Telegram API export
synapse-pipeline export-telegram  # Export last 7 days from configured channels
synapse-pipeline export-telegram --start 2025-06-01 --end 2025-06-30
synapse-pipeline list-channels  # List available Telegram channels

# CLI usage - Telegram transformation
synapse-pipeline transform-telegram input.json -o output.md
synapse-pipeline batch-transform input_dir/ -o output_dir/

# CLI usage - Google Drive integration
synapse-pipeline download-gdrive ./downloaded-data --since-days 7
synapse-pipeline upload-digest ./output/digest.md --filename "weekly-digest.md"
```

## Architecture

The codebase follows a pipeline architecture with clear separation:

1. **Data Collection** (`src/synapse/exporters/`) - ✅ Telegram API integration using telethon (implemented)
2. **Transformation** (`src/synapse/transformers/`) - ✅ Currently implements Telegram JSON to Markdown conversion
3. **Upload/Distribution** (`src/synapse/uploaders/`) - ✅ Implemented Google Drive integration using rclone CLI
4. **Content Generation** - ✅ Integrated Claude API for generating team digests (via demo script)

### Key Design Patterns

- **Pure Functions**: Core transformation logic in `telegram.py` uses pure functions without side effects
- **Pydantic Models**: All data structures use Pydantic for validation and serialization
- **Environment-based Config**: Settings use `pydantic-settings` with pattern `SYNAPSE_<SECTION>__<KEY>`
- **CLI Pattern**: Typer-based CLI provides `transform-telegram` and `batch-transform` commands

### Data Flow

```
Telegram API → export_telegram_channels() → JSON files
                                         ↓
Telegram Export → parse_telegram_export() → TelegramMessage objects
                                         → group_by_channel()
                                         → format_to_markdown() → Team Digest
```

## Current Sprint (MVP)

The project is in an MVP sprint focusing on:
1. ✅ Telegram API integration (programmatic export) - COMPLETED
2. ✅ Google Drive integration (bidirectional sync) - COMPLETED
3. ✅ Claude API integration for content generation - COMPLETED (via demo script)
4. ✅ GitHub Actions automation - COMPLETED

### Google Drive Integration Details

The Google Drive integration uses the rclone CLI directly via subprocess calls:
- **GoogleDriveUploader** class in `src/synapse/uploaders/gdrive.py`
- Automatically configures rclone with service account credentials
- Downloads files modified within a specified time range
- Uploads digests and returns shareable links
- No Python wrapper dependencies - just direct CLI calls for reliability

See `CONTEXT.md` for detailed sprint goals and priorities.

## Testing

Tests use real data samples in `tests/data/`. The test suite comprehensively covers:
- Telegram API authentication and export
- Telegram message parsing (all message types)
- Channel grouping and topic mapping
- Markdown formatting
- Batch processing

## Important Context

- This project was migrated from a complex MapReduce newsletter generator
- Focus is now solely on the data pipeline for team context syncing
- The `demo_agentic_newsletter/` folder contains a working example of Claude-based content generation
- Python 3.12+ is strictly required