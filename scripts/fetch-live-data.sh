#!/bin/bash
# Fetch latest pipeline data from GitHub Actions artifacts for evaluation

set -e

REPO="odysseus0/synapse-pipeline"
WORKFLOW_NAME="generate-digest.yml"
OUTPUT_DIR="eval/test-data/live"

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${BLUE}📥 Fetching latest pipeline data for evaluation...${NC}"

# Check for GitHub CLI
if ! command -v gh &> /dev/null; then
    echo -e "${RED}❌ GitHub CLI (gh) not found. Install with: brew install gh${NC}"
    exit 1
fi

# Check authentication
if ! gh auth status &> /dev/null; then
    echo -e "${RED}❌ Not authenticated with GitHub. Run: gh auth login${NC}"
    exit 1
fi

# Create output directory
mkdir -p "$OUTPUT_DIR"
rm -rf "$OUTPUT_DIR"/*  # Clean old data

# Get the latest successful workflow run
echo -e "${BLUE}🔍 Finding latest successful digest generation run...${NC}"
RUN_ID=$(gh run list \
    --repo "$REPO" \
    --workflow "$WORKFLOW_NAME" \
    --status success \
    --limit 1 \
    --json databaseId \
    --jq '.[0].databaseId')

if [ -z "$RUN_ID" ]; then
    echo -e "${RED}❌ No successful workflow runs found${NC}"
    exit 1
fi

RUN_DATE=$(gh run view "$RUN_ID" --repo "$REPO" --json createdAt --jq '.createdAt' | cut -d'T' -f1)
echo -e "${GREEN}✓ Found run #${RUN_ID} from ${RUN_DATE}${NC}"

# Download transformed Telegram data artifact
echo -e "${BLUE}📦 Downloading transformed-data artifact...${NC}"
if gh run download "$RUN_ID" \
    --repo "$REPO" \
    --name "transformed-data-${RUN_ID}" \
    --dir "$OUTPUT_DIR/telegram" 2>/dev/null; then
    echo -e "${GREEN}✓ Downloaded Telegram data${NC}"

    # Combine all markdown files into one
    cat "$OUTPUT_DIR"/telegram/*.md > "$OUTPUT_DIR/telegram_${RUN_DATE}.md" 2>/dev/null || true
    rm -rf "$OUTPUT_DIR/telegram"
else
    echo -e "${RED}⚠ No transformed Telegram data found${NC}"
    touch "$OUTPUT_DIR/telegram_${RUN_DATE}.md"  # Create empty file
fi

# Download GDrive data artifact
echo -e "${BLUE}📦 Downloading gdrive-data artifact...${NC}"
if gh run download "$RUN_ID" \
    --repo "$REPO" \
    --name "gdrive-data-${RUN_ID}" \
    --dir "$OUTPUT_DIR/gdrive" 2>/dev/null; then
    echo -e "${GREEN}✓ Downloaded GDrive data${NC}"

    # Combine all files
    find "$OUTPUT_DIR/gdrive" -type f -exec cat {} \; > "$OUTPUT_DIR/gdrive_${RUN_DATE}.md" 2>/dev/null || true
    rm -rf "$OUTPUT_DIR/gdrive"
else
    echo -e "${RED}⚠ No GDrive data found${NC}"
    touch "$OUTPUT_DIR/gdrive_${RUN_DATE}.md"  # Create empty file
fi

# Download feedback section if available
echo -e "${BLUE}📦 Downloading feedback-section artifact...${NC}"
if gh run download "$RUN_ID" \
    --repo "$REPO" \
    --name "feedback-section-${RUN_ID}" \
    --dir "$OUTPUT_DIR/feedback" 2>/dev/null; then
    echo -e "${GREEN}✓ Downloaded feedback section${NC}"

    mv "$OUTPUT_DIR/feedback/feedback_section.txt" "$OUTPUT_DIR/feedback_${RUN_DATE}.txt" 2>/dev/null || touch "$OUTPUT_DIR/feedback_${RUN_DATE}.txt"
    rm -rf "$OUTPUT_DIR/feedback"
else
    echo -e "${RED}⚠ No feedback section found${NC}"
    touch "$OUTPUT_DIR/feedback_${RUN_DATE}.txt"
fi

# Create metadata
cat > "$OUTPUT_DIR/metadata.json" <<EOF
{
  "run_id": "$RUN_ID",
  "run_date": "$RUN_DATE",
  "fetched_at": "$(date -u +%Y-%m-%dT%H:%M:%SZ)",
  "repo": "$REPO",
  "workflow": "$WORKFLOW_NAME"
}
EOF

# Print summary
echo ""
echo -e "${GREEN}✅ Live data fetched successfully!${NC}"
echo -e "${BLUE}📊 Summary:${NC}"
echo "  Run ID: $RUN_ID"
echo "  Date: $RUN_DATE"
echo "  Location: $OUTPUT_DIR/"
echo ""
echo "Files created:"
ls -lh "$OUTPUT_DIR"/*.md "$OUTPUT_DIR"/*.txt 2>/dev/null | awk '{print "  " $9 " (" $5 ")"}'
echo ""
echo -e "${BLUE}💡 Next steps:${NC}"
echo "  1. Review data: ls -l $OUTPUT_DIR/"
echo "  2. Run evaluation: promptfoo eval --config promptfooconfig.live.yaml"
echo "  3. View results: promptfoo view"
