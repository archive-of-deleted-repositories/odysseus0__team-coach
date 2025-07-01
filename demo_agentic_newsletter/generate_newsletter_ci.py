#!/usr/bin/env python3
"""
CI-friendly newsletter generation script.
This script simulates the Claude CLI behavior for GitHub Actions.
"""

import os
import sys
from pathlib import Path
from datetime import datetime, timezone
import json

def read_sample_data(data_dir: Path) -> dict:
    """Read all sample data files"""
    data = {
        "meeting_transcripts": [],
        "telegram_chats": []
    }
    
    for file_path in data_dir.glob("*.txt"):
        content = file_path.read_text()
        if "telegram" in file_path.name.lower():
            data["telegram_chats"].append({
                "filename": file_path.name,
                "content": content
            })
        else:
            data["meeting_transcripts"].append({
                "filename": file_path.name,
                "content": content
            })
    
    return data

def generate_newsletter_content(data: dict) -> str:
    """
    Generate newsletter content based on sample data.
    In production, this would use the Claude API directly.
    """
    
    # For CI demo purposes, we'll create a simplified version
    # In production, this would make actual Claude API calls
    
    newsletter = f"""# Team Newsletter - Week of {datetime.now().strftime('%B %d, %Y')}

## 📍 The Week's Highlights

Based on the analysis of {len(data['meeting_transcripts'])} meeting transcripts and {len(data['telegram_chats'])} chat logs:

- **Engineering Focus**: The team discussed MapReduce implementation for data processing pipelines
- **Key Decision**: Moving forward with Python-based implementation using asyncio
- **New Initiative**: Implementing automated context syncing for remote team collaboration

## 🎯 Progress & Momentum

### Completed This Week
- ✅ Finalized architecture for the Synapse Pipeline project
- ✅ Set up initial Telegram data transformer with Pydantic models
- ✅ Created proof-of-concept for agentic newsletter generation

### In Progress
- 🔄 Telegram API integration using telethon library
- 🔄 Google Drive bidirectional sync implementation
- 🔄 GitHub Actions automation setup

## 💡 Interesting Discussions

### Data Pipeline Architecture
The team debated between a traditional ETL approach vs. a more modern streaming architecture. The consensus was to start with batch processing and evolve towards streaming as needed.

### Context Management
Interesting discussion about how to maintain team context in a remote-first environment. The Synapse project aims to solve this by automatically generating digests from various communication channels.

## 🚧 Heads Up

- **Dependency Update**: Python 3.12 is now required for all team members
- **API Changes**: The Telegram export format may change in the next sprint
- **Resource Planning**: We'll need additional Claude API credits for production usage

## 🎪 The Human Side

The team showed great enthusiasm for automating repetitive tasks. Quote from the engineering meeting: "If we can automate context sharing, we can focus more on building and less on status updates."

## 🔗 Resources to Check Out

- [Telegram Bot API Documentation](https://core.telegram.org/bots/api)
- [Google Drive API Python Quickstart](https://developers.google.com/drive/api/quickstart/python)
- [GitHub Actions Best Practices](https://docs.github.com/en/actions/guides)

---
*Generated automatically by Synapse Pipeline - Your AI-powered team context manager*
"""
    
    return newsletter

def main():
    """Main entry point for CI newsletter generation"""
    
    # Check if we're in the right directory
    script_dir = Path(__file__).parent
    sample_data_dir = script_dir / "sample_data"
    
    if not sample_data_dir.exists():
        print(f"Error: Sample data directory not found at {sample_data_dir}")
        sys.exit(1)
    
    print("Reading sample data...")
    data = read_sample_data(sample_data_dir)
    print(f"Found {len(data['meeting_transcripts'])} meeting transcripts and {len(data['telegram_chats'])} chat logs")
    
    print("Generating newsletter content...")
    newsletter_content = generate_newsletter_content(data)
    
    # Write output
    output_path = script_dir / "newsletter_output.md"
    output_path.write_text(newsletter_content)
    print(f"Newsletter generated successfully: {output_path}")
    
    # Also create a JSON metadata file for CI purposes
    metadata = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "input_files": len(data['meeting_transcripts']) + len(data['telegram_chats']),
        "output_file": str(output_path),
        "ci_mode": True
    }
    
    metadata_path = script_dir / "newsletter_metadata.json"
    metadata_path.write_text(json.dumps(metadata, indent=2))
    print(f"Metadata saved: {metadata_path}")

if __name__ == "__main__":
    main()