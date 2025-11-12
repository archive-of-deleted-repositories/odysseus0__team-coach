# Feedback Correction System Design for Synapse-Pipeline

## Executive Summary

This document outlines the design for adapting the feedback correction system from `synapse` (meeting transcript analysis) to `synapse-pipeline` (team digest generation). The system will detect bot mentions in Telegram messages, extract feedback, and incorporate corrections into future digest generation.

## Current Architecture Analysis

### How Digests Are Generated

**synapse-pipeline** uses Claude Code (via `anthropics/claude-code-base-action@beta`) to generate digests:

1. **Data Collection** (Parallel):
   - Export Telegram messages for date range
   - Download Google Drive documents

2. **Transformation**:
   - Convert Telegram JSON to markdown transcripts
   - Parse messages into structured format

3. **Digest Generation** (The Key Phase):
   - Downloads "agent memory" from Google Drive (persistent coaching notes)
   - Provides Claude Code with:
     - `transformed_data/` - Today's Telegram messages
     - `gdrive_data/` - Recent documents
     - `agent_memory/` - Bot's persistent memory/notes
     - `config/team_coach_prompt.md` - System prompt
   - Claude Code runs autonomously with allowed tools: `LS`, `Read`, `Write`
   - Claude writes digest to `digest_YYYY-MM-DD.md`
   - Agent memory is uploaded back to Google Drive

4. **Distribution**:
   - Upload digest to Google Drive
   - Send notification via Telegram bot

### Key Differences from synapse

| Aspect | synapse (local) | synapse-pipeline |
|--------|----------------|------------------|
| **LLM** | Gemini (pydantic-ai) | Claude (Claude Code Action) |
| **Architecture** | MapReduce (Map→Reduce phases) | Linear pipeline (Export→Transform→Generate) |
| **Output** | Individual person profiles | Team digest |
| **Feedback Source** | Meeting transcripts with @bot | Telegram messages with @bot |
| **State** | Stateless per run | Stateful (agent_memory folder) |
| **Execution** | Python script | GitHub Actions workflow |

## Design: Feedback Correction for synapse-pipeline

### Goals

1. **Detect bot mentions** in Telegram messages with correction feedback
2. **Extract and classify feedback** (factual correction, tone adjustment, etc.)
3. **Store feedback** in agent memory for Claude Code to access
4. **Guide Claude Code** to incorporate corrections in future digests

### Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│ NEW: Feedback Detection Phase (after Transform, before Gen) │
└─────────────────────────────────────────────────────────────┘
                           │
                           ▼
          ┌────────────────────────────────┐
          │  Scan transformed_data/*.md    │
          │  for @synapse_coach mentions   │
          └────────────────────────────────┘
                           │
                           ▼
          ┌────────────────────────────────┐
          │  Extract feedback messages     │
          │  with context (date, channel)  │
          └────────────────────────────────┘
                           │
                           ▼
          ┌────────────────────────────────┐
          │  Classify feedback type        │
          │  (using Claude/Gemini API)     │
          └────────────────────────────────┘
                           │
                           ▼
          ┌────────────────────────────────┐
          │  Write feedback_log.md         │
          │  to agent_memory/feedback/     │
          └────────────────────────────────┘
                           │
                           ▼
          ┌────────────────────────────────┐
          │  Claude Code reads feedback    │
          │  during digest generation      │
          └────────────────────────────────┘
```

### Implementation Plan

#### Phase 1: Add Feedback Detection Module

**New File**: `src/synapse/processors/feedback_detector.py`

Based on `synapse/src/synapse/processors/feedback.py`, adapted for synapse-pipeline:

```python
"""Detect and process feedback from Telegram messages."""

from pathlib import Path
from pydantic import BaseModel

class FeedbackMention(BaseModel):
    """Detected bot mention with feedback."""
    date: str
    channel: str
    author: str
    message: str
    context_before: list[str]  # Previous messages for context

class FeedbackLog(BaseModel):
    """Processed feedback ready for agent memory."""
    detected_at: str  # ISO timestamp
    source_channel: str
    feedback_type: str  # "factual_correction" | "tone_adjustment" | etc.
    original_issue: str
    requested_change: str
    context: str

async def scan_for_feedback(
    transformed_dir: Path,
    bot_name: str = "@synapse_coach"
) -> list[FeedbackMention]:
    """Scan transformed markdown files for bot mentions."""
    # Read all .md files in transformed_dir
    # Parse for messages containing bot_name
    # Extract surrounding context
    pass

async def classify_feedback(
    mention: FeedbackMention
) -> FeedbackLog:
    """Use LLM to classify and structure the feedback."""
    # Similar to synapse's classify_feedback_type
    # But adapted for digest feedback vs profile feedback
    pass

async def write_feedback_log(
    feedback_logs: list[FeedbackLog],
    agent_memory_dir: Path
) -> Path:
    """Write feedback log to agent memory."""
    # Create agent_memory/feedback/feedback_YYYY-MM-DD.md
    # Format for easy Claude Code consumption
    pass
```

#### Phase 2: Add Workflow Step

**Update**: `.github/workflows/generate-digest.yml`

Add new job between `transform-data` and `generate-digest`:

```yaml
  # NEW JOB: Detect Feedback
  detect-feedback:
    name: Detect Bot Feedback from Messages
    runs-on: ubuntu-latest
    timeout-minutes: 5
    needs: [transform-data]
    if: needs.transform-data.outputs.transform-status == 'success'
    outputs:
      feedback-detected: ${{ steps.detect.outputs.detected }}
      feedback-count: ${{ steps.detect.outputs.count }}
    steps:
      - name: Checkout Repository
        uses: actions/checkout@v4

      - name: Setup uv Environment
        uses: ./.github/actions/setup-uv-env

      - name: Download Transformed Data
        uses: actions/download-artifact@v4
        with:
          name: transformed-data-${{ github.run_id }}
          path: transformed_data/

      - name: Download Current Agent Memory
        run: |
          # Need service account setup here too
          echo '${{ secrets.GDRIVE_SERVICE_ACCOUNT_B64 }}' | base64 -d > service-account.json
          uv run synapse-pipeline download-memory ./agent_memory

      - name: Detect and Process Feedback
        id: detect
        env:
          CLAUDE_API_KEY: ${{ secrets.CLAUDE_API_KEY }}
        run: |
          # Run feedback detection
          uv run synapse-pipeline detect-feedback \
            ./transformed_data \
            ./agent_memory

          # Check if feedback was found
          if [ -f "./agent_memory/feedback/feedback_$(date +%Y-%m-%d).md" ]; then
            echo "detected=true" >> $GITHUB_OUTPUT
            COUNT=$(grep -c "##" "./agent_memory/feedback/feedback_$(date +%Y-%m-%d).md" || echo "0")
            echo "count=$COUNT" >> $GITHUB_OUTPUT
            echo "::notice::Found $COUNT feedback mentions"
          else
            echo "detected=false" >> $GITHUB_OUTPUT
            echo "count=0" >> $GITHUB_OUTPUT
          fi

      - name: Upload Updated Agent Memory
        uses: actions/upload-artifact@v4
        with:
          name: agent-memory-with-feedback-${{ github.run_id }}
          path: agent_memory/
          retention-days: 7
```

Then update `generate-digest` job to download `agent-memory-with-feedback` instead of downloading fresh from Google Drive.

#### Phase 3: Update Team Coach Prompt

**Update**: `config/team_coach_prompt.md`

Add section about feedback:

```markdown
## Incorporating Feedback

Check `agent_memory/feedback/` for any recent feedback about your digests.

When you find feedback:
1. **Review the original issue** - What was incorrect or could be improved?
2. **Understand the requested change** - What specifically should change?
3. **Apply going forward** - Incorporate this into your coaching style and future digests
4. **Document in your notes** - Update relevant coaching notes to remember this correction

Feedback is a gift. Use it to improve your coaching effectiveness.
```

#### Phase 4: Add CLI Command

**Update**: `src/synapse/cli.py`

Add new command:

```python
@app.command()
def detect_feedback(
    transformed_dir: Path = typer.Argument(..., help='Directory with transformed markdown'),
    agent_memory_dir: Path = typer.Argument(..., help='Agent memory directory'),
    bot_name: str = typer.Option("@synapse_coach", '--bot-name', '-b', help='Bot mention name'),
):
    """Detect bot mentions and process feedback from transformed messages."""
    from synapse.processors.feedback_detector import (
        scan_for_feedback,
        classify_feedback,
        write_feedback_log
    )

    typer.echo(f'🔍 Scanning for {bot_name} mentions...')

    mentions = asyncio.run(scan_for_feedback(transformed_dir, bot_name))

    if not mentions:
        typer.echo('No feedback mentions found.')
        return

    typer.echo(f'Found {len(mentions)} feedback mention(s)')

    # Classify each mention
    feedback_logs = []
    for mention in mentions:
        typer.echo(f'  📝 Processing feedback from {mention.author} in #{mention.channel}')
        feedback_log = asyncio.run(classify_feedback(mention))
        feedback_logs.append(feedback_log)

    # Write to agent memory
    feedback_file = asyncio.run(write_feedback_log(feedback_logs, agent_memory_dir))
    typer.echo(f'✅ Feedback log written to {feedback_file}')
```

### Feedback Log Format

**File**: `agent_memory/feedback/feedback_YYYY-MM-DD.md`

```markdown
# Feedback Log - January 15, 2025

This file contains feedback about your digests from team members.
Review each item and incorporate the corrections into your future coaching.

---

## Feedback #1: Factual Correction

**Detected**: 2025-01-15 14:32 UTC
**Source**: #engineering-updates
**From**: @alice

### Original Issue
You stated that the API refactor was completed, but it's still in progress.

### Requested Change
Be more careful about distinguishing "work in progress" from "completed work".
Check the actual PR status before reporting completion.

### Context
```
[14:25] alice: We're making progress on the API refactor
[14:30] synapse_coach (in digest): ✅ API refactor completed by Alice
[14:32] alice: @synapse_coach that's not accurate - we're still working on it.
               Please don't report things as complete until the PR is merged.
```

### Your Action
- Update your coaching notes to verify PR/task status before reporting completion
- Use qualifiers like "in progress", "nearing completion" for unmerged work
- Check your persistent memory for similar corrections in the past

---

## Feedback #2: Tone Adjustment

**Detected**: 2025-01-15 15:45 UTC
**Source**: #product-discussions
**From**: @bob

### Original Issue
The digest tone was too harsh when describing the delayed feature launch.

### Requested Change
Be more empathetic and constructive when discussing setbacks. Focus on what's being
done to address issues rather than just highlighting the problem.

### Context
```
[15:30] synapse_coach (in digest): ⚠️ Feature launch delayed again. Third delay this month.
[15:45] bob: @synapse_coach this comes across as critical rather than supportive.
             We're working through challenges - can you frame it more constructively?
```

### Your Action
- Reframe setbacks as challenges being addressed
- Highlight mitigation efforts and learnings
- Maintain your direct style but add empathy and forward-looking perspective
```

### Configuration

**Add to**: `config.toml`

```toml
[feedback]
enabled = true
bot_mention_pattern = "@synapse_coach"  # Configurable bot name
feedback_memory_dir = "agent_memory/feedback"
max_context_lines = 5  # Lines before/after mention to capture
```

**Add to**: `.env.example`

```bash
# Feedback Detection (optional - defaults work for most cases)
SYNAPSE_FEEDBACK__ENABLED=true
SYNAPSE_FEEDBACK__BOT_MENTION_PATTERN="@synapse_coach"
```

## Testing Strategy

### Unit Tests

1. **Feedback Detection**:
   - Test parsing markdown with @mentions
   - Test extracting context correctly
   - Test handling no mentions gracefully

2. **Feedback Classification**:
   - Mock LLM responses
   - Test different feedback types
   - Verify output format

3. **Feedback Log Writing**:
   - Test file creation in agent_memory
   - Test appending multiple feedbacks
   - Test date-based organization

### Integration Tests

1. **End-to-End Pipeline**:
   - Create test Telegram export with @synapse_coach mention
   - Transform to markdown
   - Run feedback detection
   - Verify feedback log created
   - Verify format readable by Claude Code

2. **Workflow Testing**:
   - Use `workflow_dispatch` with test data
   - Enable `skip_upload` and `skip_notify` for testing
   - Verify feedback detection step runs
   - Check artifacts contain feedback logs

## Rollout Plan

### Phase 1: Core Implementation (Week 1)
- [ ] Implement `feedback_detector.py` module
- [ ] Add `detect-feedback` CLI command
- [ ] Write unit tests
- [ ] Test locally with sample data

### Phase 2: Workflow Integration (Week 2)
- [ ] Add `detect-feedback` job to workflow
- [ ] Update `generate-digest` to use feedback-augmented memory
- [ ] Update `team_coach_prompt.md` with feedback instructions
- [ ] Test in workflow with `skip_upload=true`

### Phase 3: Prompt Enhancement (Week 3)
- [ ] Monitor initial Claude Code responses to feedback
- [ ] Refine feedback log format based on Claude's usage
- [ ] Add examples of good feedback incorporation to prompt
- [ ] Document feedback best practices for team

### Phase 4: Live Deployment (Week 4)
- [ ] Enable in production workflow
- [ ] Monitor first week of feedback detection
- [ ] Gather team feedback on digest improvements
- [ ] Iterate on feedback classification prompts

## Success Metrics

1. **Detection Accuracy**: % of @synapse_coach mentions correctly detected
2. **Classification Quality**: Human review of feedback classification accuracy
3. **Incorporation Rate**: Evidence of corrections in subsequent digests
4. **Team Satisfaction**: Feedback from team on digest quality improvement

## Open Questions

1. **Bot Mention Pattern**: Should we use `@synapse_coach` or allow variations like `@coach` or `@synapse`?
2. **Feedback Persistence**: How long should feedback logs be retained in agent memory?
3. **LLM Choice**: Use Claude (consistent with digest generation) or Gemini (faster/cheaper) for classification?
4. **Scope of Feedback**: Should we detect feedback about past digests, or only about ongoing coaching?

## Next Steps

1. Review this design with team
2. Answer open questions
3. Set up development branch
4. Begin Phase 1 implementation
5. Create test data for validation
