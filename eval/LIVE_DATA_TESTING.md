# Live Data Testing with Promptfoo

Test your prompts against **real production data** from actual pipeline runs, not just synthetic test cases.

## Why Live Data Testing?

**Synthetic data** (like our test cases) is useful for development, but **live data** reveals:
- Real-world edge cases
- Actual message volumes and character counts
- Production feedback patterns
- Team communication style variations
- Unexpected data combinations

## Quick Start (3 Steps)

### Step 1: Fetch Latest Pipeline Data

```bash
# Install GitHub CLI if needed
brew install gh  # macOS
# or: sudo apt install gh  # Linux

# Authenticate
gh auth login

# Fetch latest data
./scripts/fetch-live-data.sh
```

This downloads:
- Latest `transformed_data/` (Telegram exports)
- Latest `gdrive_data/` (meeting notes, docs)
- Latest `feedback_section.txt` (bot mentions)

### Step 2: Setup Symlinks

```bash
./scripts/setup-live-data-links.sh
```

Creates `*_latest.*` symlinks pointing to most recent data.

### Step 3: Run Evaluation

```bash
export ANTHROPIC_API_KEY="your-key-here"
promptfoo eval --config promptfooconfig.live.yaml
promptfoo view
```

## What Gets Tested

The live data configuration (`promptfooconfig.live.yaml`) runs 3 tests:

### Test 1: Production Data As-Is
- Uses exact data from latest run
- Includes feedback if present
- Checks: character limit, citations, structure, quality

### Test 2: Strict Character Limit (3500)
- Same data with tighter constraint
- Tests prompt's ability to prioritize
- Ensures buffer for Telegram overhead

### Test 3: No Feedback Baseline
- Same data without feedback section
- Compares quality with/without feedback
- Validates core functionality

## Manual Workflow

### 1. Fetch Specific Run

```bash
# Find a specific run ID you want to test
gh run list --repo odysseus0/synapse-pipeline --workflow generate-digest.yml

# Fetch that specific run (edit the script temporarily)
# Or just fetch latest:
./scripts/fetch-live-data.sh
```

### 2. Inspect the Data

```bash
cd eval/test-data/live

# Check Telegram data
head -50 telegram_latest.md

# Check GDrive data
head -50 gdrive_latest.md

# Check feedback
cat feedback_latest.txt

# Check metadata
cat metadata.json
```

### 3. Run Evaluation

```bash
# From project root
export ANTHROPIC_API_KEY="your-key"
promptfoo eval --config promptfooconfig.live.yaml
```

### 4. Analyze Results

```bash
# Open web UI
promptfoo view

# Or check raw results
cat eval/results/live/evaluation.json | jq
```

## Automated Testing

### Weekly Automated Runs

The workflow `.github/workflows/eval-prompts-live.yml` runs automatically:
- **Schedule**: Every Monday at 9am UTC
- **Trigger**: `workflow_dispatch` (manual trigger available)

What it does:
1. Fetches latest successful pipeline run data
2. Runs evaluation with `promptfooconfig.live.yaml`
3. Posts results to workflow summary
4. Uploads data and results as artifacts
5. **Creates GitHub issue if tests fail**

### Manual Trigger

```bash
# Via GitHub CLI
gh workflow run eval-prompts-live.yml --repo odysseus0/synapse-pipeline

# Or via GitHub UI:
# Actions → "Evaluate Prompts with Live Data" → "Run workflow"
```

## Use Cases

### Use Case 1: Validate Before Deploy

```bash
# You've improved the prompt
vim config/team_coach_prompt.md

# Test with synthetic data
promptfoo eval

# Test with real production data
./scripts/fetch-live-data.sh
./scripts/setup-live-data-links.sh
promptfoo eval --config promptfooconfig.live.yaml

# If both pass, deploy!
git add config/team_coach_prompt.md
git commit -m "Improve prompt conciseness"
```

### Use Case 2: Debug Production Issue

```bash
# Team reports: "Friday's digest was too long"
# Fetch Friday's data specifically:

gh run list --repo odysseus0/synapse-pipeline --created 2025-01-17
# Note the run ID

# Edit scripts/fetch-live-data.sh to use that RUN_ID
./scripts/fetch-live-data.sh

# Test with that data
./scripts/setup-live-data-links.sh
promptfoo eval --config promptfooconfig.live.yaml
promptfoo view

# See the actual character count and identify why it was long
```

### Use Case 3: Compare Prompt Versions on Real Data

```bash
# Fetch real data
./scripts/fetch-live-data.sh
./scripts/setup-live-data-links.sh

# Edit promptfooconfig.live.yaml to add multiple prompts:
# prompts:
#   - file://config/team_coach_prompt.md
#     label: "current"
#   - file://eval/prompts/team_coach_v2_shorter.md
#     label: "v2-shorter"

# Run comparison
promptfoo eval --config promptfooconfig.live.yaml
promptfoo view

# See which version handles real data better
```

### Use Case 4: Build Test Dataset from Real Data

```bash
# Fetch several days of data
./scripts/fetch-live-data.sh  # Gets latest

# Keep the files (they're dated)
cp eval/test-data/live/telegram_2025-01-20.md eval/test-data/telegram_prod_jan20.md
cp eval/test-data/live/telegram_2025-01-21.md eval/test-data/telegram_prod_jan21.md

# Add to regular promptfooconfig.yaml as test cases
# Now you have real production examples in your regression suite!
```

## Interpreting Results

### All Tests Pass ✅
- Prompt handles real data well
- Character limits respected
- Quality maintained
- Safe to deploy

### Character Limit Failures ❌
- Prompt produces too-long outputs with real volumes
- **Action**: Reduce output verbosity, tighten bullet points

### Quality Failures ❌
- Digest doesn't accurately reflect activity
- Missing important information
- Poor prioritization
- **Action**: Adjust prompt instructions, improve examples

### Structure Failures ❌
- Missing headers or citations
- Format issues
- **Action**: Strengthen format requirements in prompt

## Tips

1. **Test Weekly** - Run against latest data every week to catch drift
2. **Keep Historical Data** - Save interesting edge cases for regression tests
3. **Use Artifacts** - GitHub workflow artifacts preserve the exact data tested
4. **Compare Trends** - Track character counts over time to spot bloat
5. **Debug Locally** - Download artifacts and test locally for faster iteration

## Troubleshooting

### "No successful workflow runs found"
- Wait for next digest generation run
- Or trigger one manually

### "GitHub CLI not authenticated"
```bash
gh auth login
gh auth status
```

### "Permission denied downloading artifacts"
- Ensure `GITHUB_TOKEN` has `actions:read` permission
- Check repo access

### "Evaluation takes too long"
- Real data tests are slower (more content)
- Normal runtime: 2-5 minutes for 3 tests
- Use `--max-concurrency 1` if hitting rate limits

## Cost Considerations

Live data tests use more tokens because:
- Real data is longer than synthetic
- Multiple test scenarios
- Character counts are higher

**Estimated cost per run**: $1.50-$3.00 USD
**Recommended frequency**: Weekly automated + as-needed manual

## Advanced: Historical Backtesting

Want to test how prompt changes would have performed historically?

```bash
# Fetch multiple historical runs
for run_id in 123456 123457 123458; do
  # Edit script to use each run_id
  ./scripts/fetch-live-data.sh

  # Rename the files to keep them
  RUN_DATE=$(jq -r '.run_date' eval/test-data/live/metadata.json)
  cp eval/test-data/live/telegram_latest.md eval/test-data/archive/telegram_${RUN_DATE}.md
done

# Create config that tests against all archived dates
# Compare prompt versions across multiple days of real data
```

## Integration with CI/CD

The live data workflow creates issues on failure. When you see one:

1. Click the workflow run link
2. Download the artifacts (data + results)
3. Test locally: `promptfoo view` with the downloaded data
4. Identify the issue
5. Fix the prompt
6. Re-test with same data
7. Deploy fix
8. Close issue

---

**Next Steps:**
1. Run `./scripts/fetch-live-data.sh` to get started
2. Explore the data in `eval/test-data/live/`
3. Run your first live evaluation
4. Check the weekly automation is working

**Questions?** See [README.md](README.md) for general Promptfoo docs.
