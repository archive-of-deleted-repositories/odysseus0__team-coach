#!/bin/bash
# Create symlinks to make live data testing easier
# This creates *_latest.* symlinks pointing to the most recent data files

set -e

LIVE_DIR="eval/test-data/live"

if [ ! -d "$LIVE_DIR" ]; then
    echo "❌ Live data directory not found. Run scripts/fetch-live-data.sh first."
    exit 1
fi

cd "$LIVE_DIR"

# Find most recent files by date in filename
LATEST_TELEGRAM=$(ls -1 telegram_*.md 2>/dev/null | sort -r | head -n1)
LATEST_GDRIVE=$(ls -1 gdrive_*.md 2>/dev/null | sort -r | head -n1)
LATEST_FEEDBACK=$(ls -1 feedback_*.txt 2>/dev/null | sort -r | head -n1)

# Remove old symlinks
rm -f telegram_latest.md gdrive_latest.md feedback_latest.txt

# Create new symlinks
if [ -n "$LATEST_TELEGRAM" ]; then
    ln -s "$LATEST_TELEGRAM" telegram_latest.md
    echo "✓ Linked telegram_latest.md -> $LATEST_TELEGRAM"
fi

if [ -n "$LATEST_GDRIVE" ]; then
    ln -s "$LATEST_GDRIVE" gdrive_latest.md
    echo "✓ Linked gdrive_latest.md -> $LATEST_GDRIVE"
fi

if [ -n "$LATEST_FEEDBACK" ]; then
    ln -s "$LATEST_FEEDBACK" feedback_latest.txt
    echo "✓ Linked feedback_latest.txt -> $LATEST_FEEDBACK"
fi

echo ""
echo "✅ Symlinks created successfully"
echo "📊 Current setup:"
ls -lh *_latest.* 2>/dev/null || echo "No latest symlinks found"
