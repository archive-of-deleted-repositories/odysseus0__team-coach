# Synapse Pipeline

## What This Project Is

Synapse Pipeline is a context syncing tool for remote teams. It automatically generates organizational digests that keep everyone up to speed on what's happening across different channels and meetings.

The pipeline:
1. **Collects** conversations from Telegram channels and meeting transcripts from Google Drive
2. **Transforms** raw data into clean, structured formats
3. **Generates** team update digests using Claude Code - summarizing key discussions, decisions, and activities
4. **Distributes** these updates via Google Drive so remote team members stay informed

It runs automatically via GitHub Actions, ensuring the entire organization stays synchronized without manual effort.

## ⚠️ IMPORTANT: Manual Step Required

**Meeting notes/transcripts must be manually moved to the coordination folder!**

Meeting organizers save notes to their private folders by default. For the pipeline to process them:
1. Meeting organizers must manually move/copy their notes
2. Destination: `Flashbots_X/Coordination Agent/context_data/`
3. Without this step, the pipeline won't see new meeting data

## Current MVP Sprint (Ship Tonight)

**Goal**: Fully automated pipeline that generates team update digests using Claude

**MVP Deliverables (in priority order)**:

1. **Telegram API Export** ⏳
   - Implement programmatic export using telethon
   - Replace manual JSON export process
   - Export from specific groups/channels on schedule
   
2. **Google Drive Integration** ⏳
   - Download meeting transcripts from Flashbots_X/Coordination Agent/inputs/
   - Upload generated content to Flashbots_X/Coordination Agent/outputs/
   - Use rclone for reliable sync
   
3. **Content Generation** ⏳
   - Integrate Claude API to generate team update digests
   - Summarize key discussions, decisions, and activities from all sources
   - Simple but functional output that keeps remote team members informed
   
4. **GitHub Actions** ⏳
   - Only after 1-3 are working
   - Orchestrate the full pipeline
   - Scheduled runs (daily/weekly)

5. **Notifications (Optional)** 🔔
   - Send digest notifications to team members
   - Nice-to-have for MVP, not required
   - Could use email, Slack, or Telegram bot

**Sprint Goal:** Deliver a fully automated context syncing pipeline that:
1. Programmatically exports conversations from Telegram channels
2. Pulls meeting transcripts from Google Drive
3. Generates comprehensive team update digests using Claude
4. Saves digests to Google Drive for team distribution
5. Runs automatically via GitHub Actions to keep everyone synchronized

**Key Requirement:** Must include automated content generation - this is a core requirement even for MVP.

## Architecture

```
synapse-pipeline/
├── src/synapse/
│   ├── exporters/      # Telegram API integration (telethon)
│   ├── transformers/   # Data transformation (telegram.py)
│   └── uploaders/      # Google Drive integration
```

## Current Implementation Status

### ✅ Completed
- ✅ Telegram JSON → Markdown transformation
- ✅ CLI with single file and batch processing
- ✅ All tests passing
- ✅ Type checking and linting clean
- ✅ Minimal dependencies

### ⏳ In Progress (MVP)
1. Telegram API integration (programmatic export)
2. Google Drive integration (rclone for bidirectional sync)
3. Content generation integration (Claude Code API)
4. GitHub Actions setup (orchestrate the full pipeline)

## Commands

```bash
# Install
uv sync

# Transform single file
synapse-pipeline transform-telegram input.json -o output.md

# Batch transform
synapse-pipeline batch-transform input_dir/ -o output_dir/

# Run tests
uv run pytest

# Lint & type check
uv run ruff check src/
uv run pyright
```

## Historical Context: Migration from Original Synapse

This project was created by migrating essential components from the original Synapse project:

### Why We Migrated
- Original Synapse was an LLM-powered newsletter generator using MapReduce pattern
- User discovered that Gemini Deep Research can handle the newsletter generation better  
- Decision made to focus solely on data pipeline, leaving content analysis to specialized tools

### What Was Migrated
1. **Telegram Parser** (`src/synapse/transformers/telegram.py`)
   - Converts Telegram JSON exports to clean markdown
   - Handles reactions, media references, threading, and channel organization
   - Well-tested with real data

2. **Test Data** (in `tests/data/`)
   - Real Telegram export samples
   - Topic mapping CSV for channel organization

3. **Configuration Pattern**
   - Pydantic settings with environment variable support
   - Clean separation of concerns

### What Was Left Behind
- MapReduce implementation
- Complex LLM agent orchestration
- Programmatic newsletter generation (replaced by Gemini Deep Research)

The migration is now complete, and this pipeline serves as the data preparation layer for external content generation tools.

## Demo Agentic Newsletter

The `demo_agentic_newsletter/` folder contains a working example of agent-based newsletter generation:

### Contents:
- **`generate_newsletter.sh`** - Shell script that orchestrates the newsletter generation
- **`newsletter_agent_prompt.md`** - Agent prompt configuration for Claude
- **`newsletter_prompt.md`** - Newsletter generation template
- **`sample_data/`** - Example inputs including:
  - All-hands meeting transcripts
  - Engineering meeting transcripts  
  - Telegram weekly transcripts

This approach proved that simple agent-based processing works well and serves as a reference implementation for the MVP's content generation component.

## Future Integration

While the MVP uses Claude for generating team update digests, the long-term plan is to potentially integrate with Gemini Deep Research for more comprehensive organizational intelligence and insights.

## Important Notes

- This project completely replaces the old Synapse project
- Focus is on reliable data pipeline automation
- Keep it simple and maintainable
- All credentials stored as GitHub Secrets for security
- Meeting organizers must manually move/copy their notes to `Flashbots_X/Coordination Agent/context_data/` folder before the pipeline runs

## MVP Status & Roadmap

### ✅ Completed (MVP Ready)
- Telegram API export with session strings
- Google Drive bidirectional sync
- Telegram bot notifications
- GitHub Actions automation
- All core CLI commands working
- Unit tests for each component

### 🚨 Critical for MVP (Still Needed)
1. **Quick Start Guide** - Simple setup instructions for:
   - Getting Telegram API credentials
   - Creating Google service account
   - Setting up Telegram bot
   - Configuring GitHub Secrets

2. **Basic E2E Test** - One integration test verifying the pipeline works end-to-end (with mocked external services)

3. **Update CLAUDE.md** - Change "planned" to "implemented" for completed features

### 🔄 Nice-to-Have (Skip for MVP)
- Retry logic for transient failures
- Comprehensive error handling and recovery
- Configuration validation command
- Structured logging and monitoring
- Architecture diagrams
- Detailed troubleshooting guide
- Claude API integration into main pipeline (demo script works fine)
- Resume capability for partial failures
- Metrics and observability
