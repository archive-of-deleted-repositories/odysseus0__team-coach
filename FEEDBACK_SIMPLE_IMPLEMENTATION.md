# Simple Feedback Implementation for Synapse-Pipeline

## Approach

Instead of complex feedback detection and classification, we'll take a simpler approach:

1. **Scan** transformed Telegram messages for bot mentions (`@synapse_coach`)
2. **Extract** those messages with surrounding context
3. **Prepend** to the Claude prompt before digest generation
4. Let **Claude Code** naturally incorporate the feedback

## Implementation

### Step 1: Add Simple Feedback Extractor

**New file**: `src/synapse/processors/feedback_extractor.py`

```python
"""Extract bot mentions from transformed Telegram messages."""

from pathlib import Path
import re
from datetime import datetime


def extract_bot_mentions(
    transformed_dir: Path,
    bot_pattern: str = "@synapse_coach"
) -> str:
    """
    Scan transformed markdown files for bot mentions and extract with context.

    Returns a formatted string ready to prepend to Claude prompt.
    """
    mentions = []

    # Find all markdown files
    md_files = sorted(transformed_dir.glob("*.md"))

    for md_file in md_files:
        content = md_file.read_text(encoding='utf-8')
        lines = content.split('\n')

        # Find lines with bot mentions
        for i, line in enumerate(lines):
            if bot_pattern.lower() in line.lower():
                # Extract context (5 lines before, the mention, 5 lines after)
                context_start = max(0, i - 5)
                context_end = min(len(lines), i + 6)
                context_lines = lines[context_start:context_end]

                # Get channel name if available (from ## headers)
                channel = "Unknown Channel"
                for j in range(i, -1, -1):
                    if lines[j].startswith("## "):
                        channel = lines[j].replace("## ", "").strip()
                        break

                mentions.append({
                    'file': md_file.name,
                    'channel': channel,
                    'line_num': i + 1,
                    'context': '\n'.join(context_lines)
                })

    if not mentions:
        return ""

    # Format for Claude
    output = ["# 🔔 FEEDBACK FROM TEAM", ""]
    output.append("The following messages mention you (@synapse_coach) and likely contain feedback about your digests.")
    output.append("Please review and incorporate any corrections or suggestions into today's digest.")
    output.append("")

    for idx, mention in enumerate(mentions, 1):
        output.append(f"## Feedback {idx}")
        output.append(f"**Source**: {mention['file']} - {mention['channel']}")
        output.append(f"**Line**: {mention['line_num']}")
        output.append("")
        output.append("```")
        output.append(mention['context'])
        output.append("```")
        output.append("")

    return '\n'.join(output)


def save_feedback_section(feedback_text: str, output_path: Path) -> None:
    """Save the extracted feedback to a file."""
    output_path.write_text(feedback_text, encoding='utf-8')
```

### Step 2: Add CLI Command

**Update**: `src/synapse/cli.py`

Add after the other commands:

```python
@app.command()
def extract_feedback(
    transformed_dir: Path = typer.Argument(..., help='Directory with transformed markdown'),
    output_file: Path = typer.Option(Path('feedback_section.txt'), '--output', '-o', help='Output file'),
    bot_pattern: str = typer.Option("@synapse_coach", '--bot-pattern', '-b', help='Bot mention pattern'),
):
    """Extract bot mentions from transformed Telegram messages."""
    from synapse.processors.feedback_extractor import extract_bot_mentions, save_feedback_section

    typer.echo(f'🔍 Scanning {transformed_dir} for "{bot_pattern}" mentions...')

    feedback_text = extract_bot_mentions(transformed_dir, bot_pattern)

    if not feedback_text:
        typer.echo('✅ No feedback mentions found.')
        # Create empty file so workflow doesn't fail
        output_file.write_text("", encoding='utf-8')
        return

    # Count mentions
    mention_count = feedback_text.count("## Feedback")
    typer.echo(f'✅ Found {mention_count} feedback mention(s)')

    # Save to file
    save_feedback_section(feedback_text, output_file)
    typer.echo(f'📄 Feedback saved to {output_file}')
```

### Step 3: Update Workflow

**Update**: `.github/workflows/generate-digest.yml`

Add new job after `transform-data`:

```yaml
  # NEW: Extract Feedback (Quick and Simple)
  extract-feedback:
    name: Extract Bot Feedback
    runs-on: ubuntu-latest
    timeout-minutes: 2
    needs: transform-data
    if: needs.transform-data.outputs.transform-status == 'success'
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

      - name: Extract Feedback Mentions
        run: |
          uv run synapse-pipeline extract-feedback \
            ./transformed_data \
            --output feedback_section.txt \
            --bot-pattern "@synapse_coach"

          # Show what was found (for debugging)
          if [ -s feedback_section.txt ]; then
            echo "::notice::Feedback mentions detected"
            head -n 20 feedback_section.txt
          else
            echo "::notice::No feedback mentions found"
          fi

      - name: Upload Feedback Section
        uses: actions/upload-artifact@v4
        with:
          name: feedback-section-${{ github.run_id }}
          path: feedback_section.txt
          retention-days: 7
```

Then update the `generate-digest` job:

```yaml
  generate-digest:
    name: Generate Team Digest with Claude
    runs-on: ubuntu-latest
    timeout-minutes: 15
    needs: [transform-data, export-gdrive, extract-feedback]  # ADD extract-feedback
    # ... rest of the job ...

    steps:
      # ... existing steps ...

      - name: Download Feedback Section
        uses: actions/download-artifact@v4
        with:
          name: feedback-section-${{ github.run_id }}
          path: ./

      # ... download other artifacts ...

      - name: Prepare prompt
        run: |
          DIGEST_DATE=$(date +%Y-%m-%d)
          DIGEST_FILE="digest_${DIGEST_DATE}.md"
          echo "DIGEST_FILE=$DIGEST_FILE" >> $GITHUB_ENV

          # Create combined prompt with feedback at the top
          cat > combined_prompt.txt <<EOF
          $(cat feedback_section.txt 2>/dev/null || echo "")

          ---

          Write the digest to a file named: $DIGEST_FILE

          Available data folders:
          - transformed_data/ - Today's Telegram messages
          - gdrive_data/ - Recent Google Drive documents
          - agent_memory/ - Your persistent memory (read/write)

          $(cat config/team_coach_prompt.md)
          EOF

          echo "::notice::Prompt prepared with feedback section"

      # ... rest of the steps unchanged ...
```

### Step 4: Test Locally

Create a test file to verify the extractor works:

**Test file**: `test_transformed_data/test_messages.md`

```markdown
# Telegram Export Transcript

Week of January 15, 2025

## Engineering Updates

[14:25] alice: We're making progress on the API refactor
[14:30] bob: How's the timeline looking?
[14:32] alice: @synapse_coach you said in yesterday's digest that the API refactor was complete, but that's not accurate. We're still working on it. Please be more careful about checking PR status before reporting completion.
[14:35] bob: Good catch Alice

## Product Discussions

[15:30] charlie: The new feature is coming along nicely
[15:45] dana: @synapse_coach I noticed the tone in the last digest was pretty harsh about the delayed feature launch. Could you be more constructive? We're working through challenges and would appreciate a more supportive framing.
[15:50] charlie: +1 to that
```

Then test:

```bash
cd synapse-pipeline
uv run synapse-pipeline extract-feedback ./test_transformed_data -o test_feedback.txt
cat test_feedback.txt
```

Expected output should show both feedback mentions with context.

## Benefits of This Approach

1. **Simple**: No complex classification, no LLM calls for feedback processing
2. **Fast**: Just regex + text extraction (< 1 second)
3. **Transparent**: Claude sees the raw feedback in context
4. **Flexible**: Claude can interpret and apply feedback naturally
5. **No state management**: Feedback is just part of today's prompt

## Limitations

- Feedback isn't persisted in agent memory (but Claude can write to agent_memory if it wants to remember)
- No structured classification (but Claude can do that itself if needed)
- Only detects mentions from current run (but that's probably fine - old feedback is likely already incorporated)

## When to Use Complex Approach

Consider the full feedback detection system from FEEDBACK_CORRECTION_DESIGN.md if:
- You want persistent feedback tracking across runs
- You need structured analytics on feedback types
- You want to validate feedback was incorporated (LLM-as-judge)
- You want feedback history separate from daily messages

## Next Steps

1. Implement `feedback_extractor.py`
2. Add `extract-feedback` CLI command
3. Test locally with sample data
4. Add workflow job
5. Test in CI with sample Telegram messages containing @mentions
6. Deploy!

This can be done in a few hours vs a few weeks for the full system.
