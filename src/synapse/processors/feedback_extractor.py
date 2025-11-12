"""Extract bot mentions from transformed Telegram messages for coach feedback."""

import json
import re
from datetime import datetime, timedelta
from pathlib import Path


def extract_bot_mentions(
    transformed_dir: Path,
    bot_pattern: str = "@synapse_x_bot",
    context_lines: int = 5,
    immediate_days: int = 1,
) -> str:
    """
    Scan transformed markdown files for bot mentions and extract with context.
    Separates immediate feedback (must address today) from historical context.

    Args:
        transformed_dir: Directory containing transformed Telegram markdown files
        bot_pattern: Pattern to search for (default: @synapse_coach)
        context_lines: Number of lines before/after mention to include (default: 5)
        immediate_days: Number of days to consider as "immediate" feedback (default: 1)

    Returns:
        Formatted feedback section ready to add to coach prompt, or empty string if no mentions found
    """
    mentions = []

    # Calculate cutoff for immediate vs historical
    immediate_cutoff = datetime.now() - timedelta(days=immediate_days)

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

        # Parse date from filename (used as fallback)
        file_date = None
        date_match = re.search(r'(\d{4}-\d{2}-\d{2})', md_file.name)
        if date_match:
            try:
                file_date = datetime.strptime(date_match.group(1), '%Y-%m-%d')
            except ValueError:
                pass

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

                # Parse actual message date from timestamp in line (format: [YYYY-MM-DD HH:MM])
                message_date = file_date  # Fallback to file date
                timestamp_match = re.search(r'\[(\d{4}-\d{2}-\d{2}) (\d{2}:\d{2})\]', line)
                if timestamp_match:
                    try:
                        date_str = timestamp_match.group(1)
                        message_date = datetime.strptime(date_str, '%Y-%m-%d')
                    except ValueError:
                        pass

                # Determine if feedback is immediate based on actual message date
                is_immediate = message_date and message_date >= immediate_cutoff if message_date else False

                # Format date for display
                week_date = message_date.strftime('%Y-%m-%d') if message_date else "Unknown Date"

                mentions.append({
                    'file': md_file.name,
                    'channel': channel,
                    'week_date': week_date,
                    'line_num': i + 1,
                    'context': '\n'.join(context_block),
                    'mention_line': line,
                    'is_immediate': is_immediate,
                    'file_date': message_date.isoformat() if message_date else None
                })

            except Exception as e:
                print(f"Warning: Error processing line {i} in {md_file}: {e}")
                continue

    if not mentions:
        return ""

    # Only include immediate feedback (within the cutoff period)
    immediate_mentions = [m for m in mentions if m['is_immediate']]

    if not immediate_mentions:
        return ""

    # Format as a natural coaching section
    output_lines = []
    output_lines.append(f"**IMMEDIATE FEEDBACK ({len(immediate_mentions)} item(s)): Must address in today's digest**")
    output_lines.append("")
    output_lines.append("The team gave you direct corrections recently. You MUST acknowledge and apply these today:")
    output_lines.append("")

    for idx, mention in enumerate(immediate_mentions, 1):
        output_lines.append(f"### Immediate Feedback #{idx}")
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


def extract_bot_mentions_from_dirs(
    transformed_dirs: list[Path],
    bot_pattern: str = "@synapse_x_bot",
    context_lines: int = 5,
    immediate_days: int = 1,
) -> str:
    """
    Scan multiple directories for bot mentions and extract with context.
    Separates immediate feedback (must address today) from historical context.

    Args:
        transformed_dirs: List of directories containing transformed Telegram markdown files
        bot_pattern: Pattern to search for (default: @synapse_x_bot)
        context_lines: Number of lines before/after mention to include (default: 5)
        immediate_days: Number of days to consider as "immediate" feedback (default: 1)

    Returns:
        Formatted feedback section ready to add to coach prompt, or empty string if no mentions found
    """
    all_mentions = []
    immediate_cutoff = datetime.now() - timedelta(days=immediate_days)

    # Process each directory
    for transformed_dir in transformed_dirs:
        if not transformed_dir.exists():
            print(f"Warning: Directory not found: {transformed_dir}")
            continue

        md_files = sorted(transformed_dir.glob("*.md"))

        for md_file in md_files:
            try:
                content = md_file.read_text(encoding='utf-8')
            except Exception as e:
                print(f"Warning: Could not read {md_file}: {e}")
                continue

            # Parse date from filename (used as fallback)
            file_date = None
            date_match = re.search(r'(\d{4}-\d{2}-\d{2})', md_file.name)
            if date_match:
                try:
                    file_date = datetime.strptime(date_match.group(1), '%Y-%m-%d')
                except ValueError:
                    pass

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

                    # Parse actual message date from timestamp in line (format: [YYYY-MM-DD HH:MM])
                    message_date = file_date  # Fallback to file date
                    timestamp_match = re.search(r'\[(\d{4}-\d{2}-\d{2}) (\d{2}:\d{2})\]', line)
                    if timestamp_match:
                        try:
                            date_str = timestamp_match.group(1)
                            message_date = datetime.strptime(date_str, '%Y-%m-%d')
                        except ValueError:
                            pass

                    # Determine if feedback is immediate based on actual message date
                    is_immediate = message_date and message_date >= immediate_cutoff if message_date else False

                    # Format date for display
                    week_date = message_date.strftime('%Y-%m-%d') if message_date else "Unknown Date"

                    all_mentions.append({
                        'file': md_file.name,
                        'channel': channel,
                        'week_date': week_date,
                        'line_num': i + 1,
                        'context': '\n'.join(context_block),
                        'mention_line': line,
                        'is_immediate': is_immediate,
                        'file_date': message_date.isoformat() if message_date else None
                    })

                except Exception as e:
                    print(f"Warning: Error processing line {i} in {md_file}: {e}")
                    continue

    if not all_mentions:
        return ""

    # Only include immediate feedback (within the cutoff period)
    immediate_mentions = [m for m in all_mentions if m['is_immediate']]

    if not immediate_mentions:
        return ""

    # Format as a natural coaching section
    output_lines = []
    output_lines.append(f"**IMMEDIATE FEEDBACK ({len(immediate_mentions)} item(s)): Must address in today's digest**")
    output_lines.append("")
    output_lines.append("The team gave you direct corrections recently. You MUST acknowledge and apply these today:")
    output_lines.append("")

    for idx, mention in enumerate(immediate_mentions, 1):
        output_lines.append(f"### Immediate Feedback #{idx}")
        output_lines.append(f"- **Source**: {mention['channel']} ({mention['week_date']})")
        output_lines.append(f"- **File**: {mention['file']}")
        output_lines.append("")
        output_lines.append("**Context:**")
        output_lines.append("```")
        output_lines.append(mention['context'])
        output_lines.append("```")
        output_lines.append("")

    return '\n'.join(output_lines)


def export_feedback_from_dirs(
    transformed_dirs: list[Path],
    output_path: Path,
    bot_pattern: str = "@synapse_x_bot",
    context_lines: int = 5,
    immediate_days: int = 1,
) -> None:
    """
    Export structured feedback items from multiple directories as JSON for Promptfoo testing.
    Each feedback item becomes a separate test case.

    Args:
        transformed_dirs: List of directories containing transformed Telegram markdown files
        output_path: Where to save the JSON file
        bot_pattern: Bot mention pattern to search for
        context_lines: Number of context lines
        immediate_days: Days to consider as immediate feedback
    """
    mentions = []
    immediate_cutoff = datetime.now() - timedelta(days=immediate_days)

    # Process each directory
    for transformed_dir in transformed_dirs:
        if not transformed_dir.exists():
            continue

        md_files = sorted(transformed_dir.glob("*.md"))

        for md_file in md_files:
            try:
                content = md_file.read_text(encoding='utf-8')
            except Exception:
                continue

            # Parse date from filename (used as fallback)
            file_date = None
            date_match = re.search(r'(\d{4}-\d{2}-\d{2})', md_file.name)
            if date_match:
                try:
                    file_date = datetime.strptime(date_match.group(1), '%Y-%m-%d')
                except ValueError:
                    pass

            lines = content.split('\n')

            # Find bot mentions
            for i, line in enumerate(lines):
                if bot_pattern.lower() not in line.lower():
                    continue

                # Extract context
                context_start = max(0, i - context_lines)
                context_end = min(len(lines), i + context_lines + 1)
                context_block = '\n'.join(lines[context_start:context_end])

                # Get channel
                channel = "Unknown Channel"
                for j in range(i, -1, -1):
                    if lines[j].startswith("## "):
                        channel = lines[j].replace("## ", "").strip()
                        break

                # Parse actual message date from timestamp in line (format: [YYYY-MM-DD HH:MM])
                message_date = file_date  # Fallback to file date
                timestamp_match = re.search(r'\[(\d{4}-\d{2}-\d{2}) (\d{2}:\d{2})\]', line)
                if timestamp_match:
                    try:
                        date_str = timestamp_match.group(1)
                        message_date = datetime.strptime(date_str, '%Y-%m-%d')
                    except ValueError:
                        pass

                # Determine if feedback is immediate based on actual message date
                is_immediate = message_date and message_date >= immediate_cutoff if message_date else False

                mentions.append({
                    'id': f"{md_file.stem}_{i}",
                    'file': md_file.name,
                    'channel': channel,
                    'date': message_date.isoformat() if message_date else None,
                    'line_num': i + 1,
                    'context': context_block,
                    'mention_line': line.strip(),
                    'is_immediate': is_immediate,
                    'category': 'immediate' if is_immediate else 'historical'
                })

    # Save as JSON
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump({
            'extracted_at': datetime.now().isoformat(),
            'immediate_cutoff_days': immediate_days,
            'total_mentions': len(mentions),
            'immediate_count': sum(1 for m in mentions if m['is_immediate']),
            'historical_count': sum(1 for m in mentions if not m['is_immediate']),
            'mentions': mentions
        }, f, indent=2, ensure_ascii=False)


def export_feedback_for_testing(
    transformed_dir: Path,
    output_path: Path,
    bot_pattern: str = "@synapse_x_bot",
    context_lines: int = 5,
    immediate_days: int = 1,
) -> None:
    """
    Export structured feedback items as JSON for Promptfoo testing.
    Each feedback item becomes a separate test case.

    Args:
        transformed_dir: Directory containing transformed Telegram markdown files
        output_path: Where to save the JSON file
        bot_pattern: Bot mention pattern to search for
        context_lines: Number of context lines
        immediate_days: Days to consider as immediate feedback
    """
    mentions = []

    # Calculate cutoff
    immediate_cutoff = datetime.now() - timedelta(days=immediate_days)

    # Find all markdown files
    md_files = sorted(transformed_dir.glob("*.md"))

    for md_file in md_files:
        try:
            content = md_file.read_text(encoding='utf-8')
        except Exception:
            continue

        # Parse date from filename (used as fallback)
        file_date = None
        date_match = re.search(r'(\d{4}-\d{2}-\d{2})', md_file.name)
        if date_match:
            try:
                file_date = datetime.strptime(date_match.group(1), '%Y-%m-%d')
            except ValueError:
                pass

        lines = content.split('\n')

        # Find bot mentions
        for i, line in enumerate(lines):
            if bot_pattern.lower() not in line.lower():
                continue

            # Extract context
            context_start = max(0, i - context_lines)
            context_end = min(len(lines), i + context_lines + 1)
            context_block = '\n'.join(lines[context_start:context_end])

            # Get channel
            channel = "Unknown Channel"
            for j in range(i, -1, -1):
                if lines[j].startswith("## "):
                    channel = lines[j].replace("## ", "").strip()
                    break

            # Parse actual message date from timestamp in line (format: [YYYY-MM-DD HH:MM])
            message_date = file_date  # Fallback to file date
            timestamp_match = re.search(r'\[(\d{4}-\d{2}-\d{2}) (\d{2}:\d{2})\]', line)
            if timestamp_match:
                try:
                    date_str = timestamp_match.group(1)
                    message_date = datetime.strptime(date_str, '%Y-%m-%d')
                except ValueError:
                    pass

            # Determine if feedback is immediate based on actual message date
            is_immediate = message_date and message_date >= immediate_cutoff if message_date else False

            mentions.append({
                'id': f"{md_file.stem}_{i}",
                'file': md_file.name,
                'channel': channel,
                'date': message_date.isoformat() if message_date else None,
                'line_num': i + 1,
                'context': context_block,
                'mention_line': line.strip(),
                'is_immediate': is_immediate,
                'category': 'immediate' if is_immediate else 'historical'
            })

    # Save as JSON
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump({
            'extracted_at': datetime.now().isoformat(),
            'immediate_cutoff_days': immediate_days,
            'total_mentions': len(mentions),
            'immediate_count': sum(1 for m in mentions if m['is_immediate']),
            'historical_count': sum(1 for m in mentions if not m['is_immediate']),
            'mentions': mentions
        }, f, indent=2, ensure_ascii=False)
