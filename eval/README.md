# Prompt Evaluation with Promptfoo

This directory contains evaluation infrastructure for testing and versioning the team coach prompt using [Promptfoo](https://promptfoo.dev/).

## Directory Structure

```
eval/
├── README.md                      # This file
├── prompts/                       # Versioned prompt templates
│   └── team_coach_v1_baseline.md  # Baseline prompt version
├── test-data/                     # Test datasets
├── custom-evaluators/             # Custom evaluation scripts
│   └── character-count.js         # Telegram char limit checker
└── results/                       # Evaluation outputs (gitignored)
```

## Quick Start

### 1. Setup

Ensure you have Promptfoo installed and your API key configured:

```bash
# Promptfoo should already be installed globally
promptfoo --version

# Set your Anthropic API key
export ANTHROPIC_API_KEY="your-key-here"
```

### 2. Run Evaluations

Run all test cases against the current prompt:

```bash
cd /path/to/synapse-pipeline
promptfoo eval
```

### 3. View Results

Open the interactive web UI to explore results:

```bash
promptfoo view
```

This will open a browser showing:
- Pass/fail status for each test
- Character counts
- LLM rubric scores
- Side-by-side comparison of outputs

## Common Workflows

### Compare Two Prompt Versions

1. Create a new prompt version:
```bash
cp config/team_coach_prompt.md eval/prompts/team_coach_v2_experiment.md
# Edit the new version...
```

2. Update `promptfooconfig.yaml` to include both versions:
```yaml
prompts:
  - file://config/team_coach_prompt.md
    label: "team-coach-current"
  - file://eval/prompts/team_coach_v2_experiment.md
    label: "team-coach-v2-experiment"
```

3. Run the evaluation:
```bash
promptfoo eval
```

4. Compare results in the web UI:
```bash
promptfoo view
```

You'll see a side-by-side comparison showing:
- Which version passes more tests
- Character count differences
- Quality score differences
- Actual output comparison

### Test Against Real Data

1. Add real Telegram export data to `test_data/`:
```bash
cp /path/to/real/export.md test_data/real_export_2025_01_15.md
```

2. Add a new test case in `promptfooconfig.yaml`:
```yaml
tests:
  - description: "Real data from 2025-01-15"
    vars:
      FEEDBACK_SECTION: ""
      telegram_data: file://test_data/real_export_2025_01_15.md
      date: "2025-01-15"
    assert:
      - type: javascript
        value: output.length < 4000
      - type: llm-rubric
        value: "Digest accurately summarizes the day's activity"
```

3. Run evaluation:
```bash
promptfoo eval
```

### Regression Testing (Before Deploying Changes)

Before deploying prompt changes to production:

```bash
# 1. Run full evaluation suite
promptfoo eval

# 2. Check that all critical tests pass
# 3. Review character counts
# 4. Compare quality scores

# 5. If satisfied, deploy the new prompt
cp eval/prompts/team_coach_v2.md config/team_coach_prompt.md
git add config/team_coach_prompt.md
git commit -m "Upgrade to team coach prompt v2"
```

## Test Cases Explained

### Test 1: Basic Digest Generation
- **Purpose**: Ensure basic functionality works
- **Checks**: Character limit, citations, structure, quality

### Test 2: Feedback Correction
- **Purpose**: Verify bot responds appropriately to corrections
- **Checks**: Acknowledges feedback, fixes errors, stays under limit

### Test 3: Tone Adjustment
- **Purpose**: Ensure bot can adjust tone based on feedback
- **Checks**: Maintains constructive tone, stays direct but supportive

### Test 4: Character Limit Stress Test
- **Purpose**: Verify prompt handles large inputs gracefully
- **Checks**: Hard character limit enforcement, prioritization

## Custom Evaluators

### character-count.js

Checks output against Telegram's 4096 character limit (using 4000 as safe threshold).

Returns:
- `pass`: Boolean - whether output is under limit
- `score`: 1.0 if pass, 0.0 if fail
- `reason`: Explanation of result
- `namedScores`:
  - `characterCount`: Total characters
  - `withinLimit`: 1 or 0
  - `overagePercent`: How much over limit (if applicable)

Usage in config:
```yaml
assert:
  - type: javascript
    value: file://eval/custom-evaluators/character-count.js
```

## CI/CD Integration

See `../.github/workflows/eval-prompts.yml` for automated evaluation on PRs.

## Tips

1. **Start Small**: Test with simple cases first, then add complexity
2. **Use Real Data**: Real Telegram exports reveal edge cases
3. **Version Everything**: Keep old prompt versions for comparison
4. **Iterate Quickly**: Promptfoo is fast - use it frequently
5. **Track Metrics**: Monitor character counts and quality scores over time

## Troubleshooting

### "No output from provider"
- Check your `ANTHROPIC_API_KEY` is set correctly
- Verify the API key has sufficient credits

### "Transform error"
- Check the `transform` function in `promptfooconfig.yaml`
- Ensure file paths are correct

### Tests failing unexpectedly
- Review outputs in `promptfoo view` to see actual vs expected
- LLM rubric scores can vary - consider adjusting criteria

## Resources

- [Promptfoo Documentation](https://promptfoo.dev/docs/intro)
- [Writing Assertions](https://promptfoo.dev/docs/configuration/expected-outputs)
- [Custom Evaluators](https://promptfoo.dev/docs/configuration/expected-outputs/javascript)
