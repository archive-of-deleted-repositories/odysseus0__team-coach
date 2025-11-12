# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What This Project Is

Synapse Pipeline is a context syncing tool for remote teams that automatically generates organizational digests. It collects data from Telegram channels and meeting transcripts, transforms it into structured formats, generates team update digests using Claude, and distributes them via Google Drive.

**Key Innovation**: The system includes a feedback loop where team members can mention `@synapse_x_bot` in Telegram to provide corrections. These are automatically extracted and prepended to the digest generation prompt, creating a self-improving system.

## Prerequisites

- Python 3.12+
- rclone (install via `brew install rclone` on macOS or `apt-get install rclone` on Linux)
- Claude API key (required for digest generation - get from https://console.anthropic.com/)
- Google Cloud service account with Drive API access
- Promptfoo (`npm install -g promptfoo`) for LLM evaluation

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
synapse-pipeline export-telegram  # Export last 1 day from configured channels (optimized)
synapse-pipeline export-telegram --start 2025-06-01 --end 2025-06-30
synapse-pipeline list-channels  # List available Telegram channels

# CLI usage - Telegram transformation
synapse-pipeline transform-telegram input.json -o output.md
synapse-pipeline batch-transform input_dir/ -o output_dir/

# CLI usage - Feedback extraction
synapse-pipeline extract-feedback ./transformed_data --output feedback.txt
synapse-pipeline extract-feedback ./dir1 ./dir2 --export-json feedback.json

# CLI usage - Google Drive integration
synapse-pipeline download-gdrive ./downloaded-data --since-days 7
synapse-pipeline download-memory ./agent_memory --since-days 30
synapse-pipeline upload-digest ./output/digest.md --filename "weekly-digest.md"

# CLI usage - Notifications
synapse-pipeline notify "Team digest ready!"  # Send notification
echo "Digest uploaded" | synapse-pipeline notify  # Read from stdin

# Run Promptfoo evaluations
npx promptfoo eval --config promptfooconfig.yaml
npx promptfoo view  # View results in web UI
```

## Architecture

The codebase follows a pipeline architecture with clear separation:

1. **Data Collection** (`src/synapse/exporters/`) - ✅ Telegram API integration using telethon
2. **Transformation** (`src/synapse/transformers/`) - ✅ Telegram JSON to Markdown with full timestamps
3. **Feedback Processing** (`src/synapse/processors/`) - ✅ Extract and format bot mentions for prompt injection
4. **Upload/Distribution** (`src/synapse/uploaders/`) - ✅ Google Drive integration using rclone CLI
5. **Content Generation** - ✅ Claude API with agent memory and feedback-responsive prompts
6. **Evaluation** (`eval/`) - ✅ Promptfoo test suites for quality and feedback responsiveness

### Key Design Patterns

- **Pure Functions**: Core transformation logic uses pure functions without side effects
- **Pydantic Models**: All data structures use Pydantic for validation and serialization
- **Environment-based Config**: Settings use `pydantic-settings` with pattern `SYNAPSE_<SECTION>__<KEY>`
- **CLI Pattern**: Typer-based CLI with multi-directory support for feedback extraction
- **Feedback Loop**: Structured IMMEDIATE FEEDBACK sections prepended to prompts
- **LLM-as-Judge**: Promptfoo evaluates digest quality and feedback responsiveness

### Data Flow

```
Daily at 9 AM UTC:

1. Export Telegram (1 day) → JSON files → Transform → Markdown with [YYYY-MM-DD HH:MM] timestamps
2. Download meeting transcripts from Google Drive (last 7 days)
3. Extract @synapse_x_bot mentions → IMMEDIATE FEEDBACK section
4. Download agent memory (past digests, coaching corrections)
5. Generate digest with Claude:
   - Input: Current messages + transcripts + agent memory
   - Prompt: Team coach prompt + IMMEDIATE FEEDBACK (if any)
6. Evaluate with Promptfoo:
   - CI tests: Structure, format, no unauthorized content
   - Feedback tests: Did Claude acknowledge and apply corrections?
7. Upload digest + evaluation results → Google Drive
8. Save as agent memory for future context
9. Notify team on Telegram
```

### Feedback System (CRITICAL)

The feedback system allows the team to correct the bot by mentioning `@synapse_x_bot` in Telegram:

**How it works:**
1. Team member: `@synapse_x_bot your confusion is understandable, but Peeker is not live yet`
2. Extract-feedback job searches current day's Telegram messages
3. Finds bot mention with surrounding context (5 lines before/after)
4. Creates structured IMMEDIATE FEEDBACK section:
   ```markdown
   **IMMEDIATE FEEDBACK (1 item): Must address in today's digest**

   The team gave you direct corrections recently. You MUST acknowledge and apply these today:

   ### Immediate Feedback #1
   - **Source**: Coaching Reality Check (2025-11-12)
   - **File**: telegram_export_Flashbots_X_Core_week_2025-11-11.md

   **Context:**
   ```
   [Full conversation context around the mention]
   ```
   ```
5. This section is **prepended to the prompt** when generating today's digest
6. Promptfoo tests verify Claude acknowledged and applied the correction
7. Historical context provided naturally through agent_memory (coaching corrections, past digests)

**Key Files:**
- `src/synapse/processors/feedback_extractor.py` - Extract bot mentions from markdown
- `eval/generate-feedback-tests.js` - Generate Promptfoo test cases from feedback items
- `promptfooconfig-feedback-generated.yaml` - Generated test configuration

**Design Decisions:**
- Only extract IMMEDIATE feedback from current day (1-day exports)
- Agent memory already provides historical context naturally
- No separate HISTORICAL FEEDBACK section - keeps code simple
- Full timestamps `[YYYY-MM-DD HH:MM]` in messages for accurate date attribution

## Current State

### Completed Features
1. ✅ Telegram API integration (1-day exports for efficiency)
2. ✅ Google Drive integration (bidirectional sync + agent memory)
3. ✅ Claude API integration (digest generation with extended thinking)
4. ✅ GitHub Actions automation (scheduled + manual triggers)
5. ✅ Feedback extraction and prompt injection
6. ✅ Promptfoo evaluation framework (CI + feedback tests)
7. ✅ Agent memory system (context accumulation over time)

### Google Drive Integration Details

The Google Drive integration uses the rclone CLI directly via subprocess calls:
- **GoogleDriveUploader** class in `src/synapse/uploaders/gdrive.py`
- Automatically configures rclone with service account credentials
- Three folder structure:
  - `team_data_folder_id`: Input data (transcripts, context documents)
  - `team_digests_folder_id`: Generated digests + evaluation results
  - `agent_memory_folder_id`: Past digests + coaching corrections for context
- Downloads files modified within a specified time range
- Uploads digests and returns shareable links
- No Python wrapper dependencies - just direct CLI calls for reliability

## Testing

Tests use real data samples in `tests/data/`. The test suite covers:
- Telegram API authentication and export
- Telegram message parsing (all message types including reactions)
- Channel grouping and topic mapping
- Markdown formatting with full timestamps
- Batch processing
- Feedback extraction from multiple directories

### Promptfoo Evaluation

Two test suites run on every digest:

1. **CI Tests** (`promptfooconfig.yaml`):
   - **Deterministic checks**: Character limit, source citations, markdown structure (fast, free)
   - **Synthetic feedback tests**: Factual corrections and tone adjustments (llm-rubric)
   - Ensures feedback mechanism works even without real team mentions

2. **Feedback Tests** (`promptfooconfig-feedback-generated.yaml`):
   - Generated dynamically from `feedback_items.json`
   - Tests that Claude acknowledged and applied each real team correction
   - Uses `llm-rubric` for semantic evaluation
   - The primary value proposition of the system

Results uploaded to `team_digests_folder/evaluations/YYYY-MM-DD/` in Google Drive.

## Important Context

- This project was migrated from a complex MapReduce newsletter generator
- Focus is now solely on the data pipeline + feedback-responsive digest generation
- The `config/team_coach_prompt.md` contains the Team Coach prompt
- Python 3.12+ is strictly required
- Feedback system creates a self-improving loop: team corrections → prompt updates → better digests
- Agent memory provides natural historical context without complex extraction logic
