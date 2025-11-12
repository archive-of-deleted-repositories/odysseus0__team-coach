# Promptfoo Quick Start Guide

## 🚀 Running Your First Evaluation

### Step 1: Set Your API Key

```bash
export ANTHROPIC_API_KEY="your-claude-api-key-here"
```

### Step 2: Run the Evaluation

```bash
cd /path/to/synapse-pipeline
promptfoo eval
```

This will:
- Load the test cases from `promptfooconfig.yaml`
- Run Claude with your current prompt
- Execute all 4 test scenarios
- Generate a results report

### Step 3: View Results

```bash
promptfoo view
```

This opens an interactive web UI where you can:
- See pass/fail for each test
- Read the actual digest outputs
- Check character counts
- Review LLM rubric scores

## 📊 Understanding the Results

You'll see output like this:

```
✓ Test 1: Generate digest without feedback
  ✓ Character count < 4000 (3245 chars)
  ✓ Contains source citations
  ✓ Has proper structure
  ✓ LLM rubric: Quality check (score: 0.9)

✓ Test 2: Apply feedback corrections
  ✓ Acknowledges feedback
  ✓ Character count < 4000 (3512 chars)
  ✓ Demonstrates awareness

✓ Test 3: Adjust tone based on feedback
  ✓ Constructive tone
  ✓ Direct but not harsh

✓ Test 4: Handle large input
  ✓ Character count < 4000 (3987 chars)
  ✓ Prioritizes high-signal info
```

## 🔄 Testing a New Prompt Version

### Scenario: You want to improve the prompt

1. **Create a new version:**
   ```bash
   cp config/team_coach_prompt.md eval/prompts/team_coach_v2_shorter.md
   ```

2. **Edit the new version** to make it more concise

3. **Update promptfooconfig.yaml:**
   ```yaml
   prompts:
     - file://config/team_coach_prompt.md
       label: "current"
     - file://eval/prompts/team_coach_v2_shorter.md
       label: "v2-shorter"
   ```

4. **Run comparison:**
   ```bash
   promptfoo eval
   promptfoo view
   ```

5. **Review side-by-side:**
   - Which version has shorter outputs?
   - Which version scores higher on quality rubrics?
   - Are both under the character limit?

6. **Deploy the winner:**
   ```bash
   # If v2 is better:
   cp eval/prompts/team_coach_v2_shorter.md config/team_coach_prompt.md
   git add config/team_coach_prompt.md
   git commit -m "Upgrade to shorter prompt (v2)"
   ```

## 🎯 Common Use Cases

### Use Case 1: Check if prompt change breaks anything

```bash
# Before deploying prompt changes
promptfoo eval

# If all tests pass, safe to deploy
# If tests fail, iterate on the prompt
```

### Use Case 2: Compare 3+ versions

```yaml
prompts:
  - file://eval/prompts/v1_baseline.md
    label: "v1-baseline"
  - file://eval/prompts/v2_shorter.md
    label: "v2-shorter"
  - file://eval/prompts/v3_more_direct.md
    label: "v3-direct"
  - file://eval/prompts/v4_supportive.md
    label: "v4-supportive"
```

Then run `promptfoo eval` and see which version performs best across all tests.

### Use Case 3: Test with real production data

1. Export real data from a recent run:
   ```bash
   cp transformed_data/export_2025_01_20.md test_data/real_2025_01_20.md
   ```

2. Add test case:
   ```yaml
   - description: "Real data 2025-01-20"
     vars:
       telegram_data: file://test_data/real_2025_01_20.md
       FEEDBACK_SECTION: ""
     assert:
       - type: javascript
         value: output.length < 4000
   ```

3. Run: `promptfoo eval`

## ⚙️ Advanced: Custom Metrics

Want to track specific metrics? Create a custom evaluator:

```javascript
// eval/custom-evaluators/citation-count.js
module.exports = async (output, context) => {
  const citations = (output.match(/\[#/g) || []).length;
  const pass = citations >= 3;  // Require at least 3 citations

  return {
    pass,
    score: citations / 10,  // Normalize score
    reason: `Found ${citations} source citations`,
    namedScores: { citationCount: citations }
  };
};
```

Add to test:
```yaml
assert:
  - type: javascript
    value: file://eval/custom-evaluators/citation-count.js
```

## 🐛 Troubleshooting

### "Command not found: promptfoo"
```bash
# Reinstall globally
npm install -g promptfoo
```

### "ANTHROPIC_API_KEY not set"
```bash
export ANTHROPIC_API_KEY="sk-ant-..."
```

### "Evaluation taking too long"
- Reduce number of tests
- Use `--max-concurrency 1` to run tests sequentially
- Use cheaper model for initial testing (though we need Sonnet 4.5 for production)

### Tests failing unexpectedly
- Check the actual output in `promptfoo view`
- LLM rubrics can be variable - might need to adjust criteria
- Character counts can vary - check if close to limit

## 💡 Pro Tips

1. **Run often** - Promptfoo is fast, use it frequently during development
2. **Save versions** - Keep successful prompt versions in `eval/prompts/`
3. **Git track everything** - Prompts, test cases, and baseline results
4. **Use real data** - Test with actual Telegram exports to catch edge cases
5. **CI/CD** - The GitHub Action runs automatically on PR - check it before merging

## 📚 Next Steps

- Read the full [README](README.md) for detailed docs
- Check out [Promptfoo docs](https://promptfoo.dev/docs) for advanced features
- Explore the [CI/CD workflow](../.github/workflows/eval-prompts.yml)
