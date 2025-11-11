"""Extract bot mentions from transformed Telegram messages for coach feedback."""

from datetime import datetime
from pathlib import Path


def extract_bot_mentions(
    transformed_dir: Path,
    bot_pattern: str = "@synapse_x_bot",
    context_lines: int = 5,
) -> str:
    """
    Scan transformed markdown files for bot mentions and extract with context.

    Args:
        transformed_dir: Directory containing transformed Telegram markdown files
        bot_pattern: Pattern to search for (default: @synapse_coach)
        context_lines: Number of lines before/after mention to include (default: 5)

    Returns:
        Formatted feedback section ready to add to coach prompt, or empty string if no mentions found
    """
    mentions = []

    # Find all markdown files
    md_files = sorted(transformed_dir.glob("*.md"))

    if not md_files:
        return ""

    for md_file in md_files:
        try:
            content = md_file.read_text(encoding='utf-8')
        except Exception as e:
            print(f"Warning: Could not read {md_file}: {e}")
            continue

        lines = content.split('\n')

        # Find lines with bot mentions (case-insensitive)
        for i, line in enumerate(lines):
            try:
                if bot_pattern.lower() not in line.lower():
                    continue

                # Extract context (N lines before, the mention, N lines after)
                context_start = max(0, i - context_lines)
                context_end = min(len(lines), i + context_lines + 1)
                context_block = lines[context_start:context_end]

                # Get channel name from nearest ## header above
                channel = "Unknown Channel"
                for j in range(i, -1, -1):
                    if lines[j].startswith("## "):
                        channel = lines[j].replace("## ", "").strip()
                        break

                # Get date from file or transcript header
                week_date = "Unknown Date"
                for line_content in lines[:10]:  # Check first 10 lines for date
                    if "Week of" in line_content:
                        week_date = line_content.replace("Week of", "").strip()
                        break

                mentions.append({
                    'file': md_file.name,
                    'channel': channel,
                    'week_date': week_date,
                    'line_num': i + 1,
                    'context': '\n'.join(context_block),
                    'mention_line': line
                })

            except Exception as e:
                print(f"Warning: Error processing line {i} in {md_file}: {e}")
                continue

    if not mentions:
        return ""

    # Format as a natural coaching section
    output_lines = []

    # Don't include header - this will be integrated naturally into the prompt
    output_lines.append(f"**IMPORTANT: The team mentioned you {len(mentions)} time(s) this week.**")
    output_lines.append("")
    output_lines.append("These are direct messages from the team about your coaching. Read them carefully:")
    output_lines.append("")

    for idx, mention in enumerate(mentions, 1):
        output_lines.append(f"### Team Mention #{idx}")
        output_lines.append(f"- **Source**: {mention['channel']} ({mention['week_date']})")
        output_lines.append(f"- **File**: {mention['file']}")
        output_lines.append("")
        output_lines.append("**Context:**")
        output_lines.append("```")
        output_lines.append(mention['context'])
        output_lines.append("```")
        output_lines.append("")

    return '\n'.join(output_lines)


def save_feedback_section(feedback_text: str, output_path: Path) -> None:
    """
    Save the extracted feedback section to a file.

    Args:
        feedback_text: The formatted feedback text
        output_path: Where to save the feedback
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(feedback_text, encoding='utf-8')
