# Promptfoo Setup Complete ✅

## What We Built

A complete prompt evaluation and versioning system using **Promptfoo** - the industry-standard framework for testing and comparing LLM prompts.

## 📁 Files Created

### Core Configuration
- **promptfooconfig.yaml** - Main config with 4 comprehensive test scenarios
- **.gitignore** - Updated to exclude results and node_modules

### Documentation
- **eval/README.md** - Complete documentation (workflows, troubleshooting, tips)
- **eval/QUICKSTART.md** - Quick start guide with examples
- **PROMPTFOO_SETUP_SUMMARY.md** - This file

### Test Infrastructure
- **eval/prompts/team_coach_v1_baseline.md** - Baseline prompt version for comparison
- **eval/custom-evaluators/character-count.js** - Custom evaluator for Telegram 4096 char limit
- **eval/test-data/** - Directory for test datasets (empty, ready for real data)

### CI/CD
- **.github/workflows/eval-prompts.yml** - Automated testing on PRs that modify prompts

## 🎯 Test Scenarios

### 1. Basic Digest Generation
Tests core functionality without feedback:
- ✅ Character limit (< 4000 chars)
- ✅ Source citations present `[#channel]`
- ✅ Proper structure (header format)
- ✅ Overall quality (LLM rubric)

### 2. Feedback Correction
Tests bot's ability to apply corrections:
- ✅ Acknowledges team feedback
- ✅ Fixes reported errors
- ✅ Stays under character limit

### 3. Tone Adjustment
Tests bot's ability to modulate tone:
- ✅ Adjusts from harsh to constructive
- ✅ Maintains directness
- ✅ Responds appropriately to feedback

### 4. Character Limit Stress Test
Tests behavior with large inputs:
- ✅ Hard character limit enforcement
- ✅ Prioritization of high-signal content

## 🚀 How to Use

### Quick Start (3 steps)

```bash
# 1. Set your API key
export ANTHROPIC_API_KEY="your-key-here"

# 2. Run evaluation
cd /path/to/synapse-pipeline
promptfoo eval

# 3. View results
promptfoo view
```

### Compare Two Prompt Versions

```bash
# 1. Create new version
cp config/team_coach_prompt.md eval/prompts/team_coach_v2.md
# Edit the new version...

# 2. Add to promptfooconfig.yaml
# (Add the new prompt file to the prompts list)

# 3. Run comparison
promptfoo eval
promptfoo view  # See side-by-side comparison
```

### Test with Real Data

```bash
# 1. Add real Telegram export
cp transformed_data/export_2025_01_20.md test_data/

# 2. Add test case to promptfooconfig.yaml

# 3. Run evaluation
promptfoo eval
```

## 📊 What You Get

### Interactive Web UI
- Side-by-side prompt comparison
- Pass/fail status for each test
- Actual digest outputs
- Character count metrics
- Quality scores

### Automated PR Checks
- Runs automatically when prompts are modified
- Posts results as PR comment
- Uploads detailed results as artifacts
- Prevents regressions before merge

### Version Control
- All prompts Git-tracked in `eval/prompts/`
- Historical comparison capability
- Rollback to previous versions anytime

## 💡 Common Workflows

### Before Deploying Prompt Changes
```bash
# Make changes to prompt
vim config/team_coach_prompt.md

# Test changes
promptfoo eval

# Review results
promptfoo view

# If all tests pass, commit
git add config/team_coach_prompt.md
git commit -m "Improve prompt conciseness"
```

### A/B Testing Prompts
```bash
# Add both versions to promptfooconfig.yaml
# Run evaluation
promptfoo eval

# Compare metrics:
# - Which has shorter outputs?
# - Which scores higher on quality?
# - Which better handles feedback?

# Deploy the winner
```

### Regression Testing
```bash
# Before each release:
promptfoo eval

# Ensure:
# - All tests pass
# - Character counts reasonable
# - Quality scores maintained
# - No unexpected behavior changes
```

## 🎨 Customization

### Add Custom Evaluator

```javascript
// eval/custom-evaluators/my-metric.js
module.exports = async (output, context) => {
  const myScore = /* your logic */;

  return {
    pass: myScore > threshold,
    score: myScore,
    reason: "Explanation",
    namedScores: { myMetric: myScore }
  };
};
```

### Add Test Scenario

```yaml
# In promptfooconfig.yaml
tests:
  - description: "My new test"
    vars:
      telegram_data: file://test_data/my_data.md
      FEEDBACK_SECTION: ""
    assert:
      - type: javascript
        value: /* assertion */
```

## 📈 Benefits

1. **Prevent Regressions** - Catch issues before production
2. **Data-Driven Decisions** - Compare prompts objectively
3. **Fast Iteration** - Test changes in seconds
4. **Version Control** - Track all prompt changes
5. **Team Collaboration** - Non-technical stakeholders can review in UI
6. **Automated Quality Gates** - CI/CD integration ensures quality

## 🔧 Technical Details

- **Framework**: Promptfoo 0.119.5
- **LLM**: Claude Sonnet 4.5 (with extended thinking)
- **Test Runner**: Node.js-based CLI
- **Results Format**: JSON + interactive HTML
- **CI/CD**: GitHub Actions
- **Languages**: YAML (config), JavaScript (evaluators), Markdown (prompts)

## 📚 Resources

- [Promptfoo Documentation](https://promptfoo.dev/docs/intro)
- [Quick Start Guide](eval/QUICKSTART.md)
- [Full Documentation](eval/README.md)
- [GitHub Actions Workflow](.github/workflows/eval-prompts.yml)

## 🎉 Next Steps

1. **Set your API key**: `export ANTHROPIC_API_KEY="..."`
2. **Run first evaluation**: `promptfoo eval`
3. **Explore results**: `promptfoo view`
4. **Add real test data** to `test_data/`
5. **Experiment with prompt versions**
6. **Iterate and improve**

---

**Questions?** See `eval/README.md` for troubleshooting and advanced usage.

**Ready to test?** Run `promptfoo eval` and see the magic happen! ✨
