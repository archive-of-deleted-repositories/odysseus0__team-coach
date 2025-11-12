#!/usr/bin/env node
/**
 * Generate Promptfoo test cases from feedback items JSON
 * Usage: node eval/generate-feedback-tests.js [feedback_items.json] [digest_path]
 */

const fs = require('fs');
const path = require('path');
const yaml = require('js-yaml');

// Parse command line arguments
const feedbackJsonPath = process.argv[2] || 'eval/test-data/live/feedback_items.json';
const digestPath = process.argv[3] || 'eval/test-data/test-run/digest_2025-11-12.md';

console.log('Generating feedback test cases...');
console.log('Feedback JSON:', feedbackJsonPath);
console.log('Digest path:', digestPath);

// Read feedback items
let feedbackData;
try {
  const feedbackJson = fs.readFileSync(feedbackJsonPath, 'utf-8');
  feedbackData = JSON.parse(feedbackJson);
  console.log(`Found ${feedbackData.total_mentions} feedback items (${feedbackData.immediate_count} immediate, ${feedbackData.historical_count} historical)`);
} catch (error) {
  console.error('Error reading feedback JSON:', error.message);
  console.error('Make sure the feedback JSON file exists at:', feedbackJsonPath);
  process.exit(1);
}

// Build test cases
const tests = [];

// Add per-feedback-item tests
feedbackData.mentions.forEach((mention, index) => {
  const testCase = {
    description: `${mention.category === 'immediate' ? '[IMMEDIATE]' : '[HISTORICAL]'} Feedback from ${mention.channel} on ${mention.date || 'unknown date'}`,
    vars: {
      digest_output: `file://${digestPath}`,
      feedback_id: mention.id,
      feedback_channel: mention.channel,
      feedback_date: mention.date,
      feedback_line: mention.mention_line,
      feedback_context: mention.context,
      is_immediate: mention.is_immediate
    },
    assert: [
      {
        type: 'llm-rubric',
        value: `Evaluate whether the digest appropriately responds to this ${mention.is_immediate ? 'IMMEDIATE' : 'HISTORICAL'} feedback:

**Feedback:** ${mention.mention_line}

**Context:**
${mention.context}

**Source:** ${mention.channel} (${mention.date || 'unknown date'})

**Evaluation Criteria:**

${mention.is_immediate ?
`For IMMEDIATE feedback (from yesterday), the digest MUST:
1. Show clear awareness of this correction
2. Avoid repeating the error mentioned in the feedback
3. Demonstrate the requested change in focus, tone, or accuracy
4. Provide evidence that the bot learned from this correction

This is a STRICT requirement - immediate feedback should always be addressed.` :
`For HISTORICAL feedback (older than 1 day), the digest should:
1. Not repeat the same mistake that was corrected previously
2. Show general awareness if the issue is still relevant
3. No need to explicitly acknowledge (may already be resolved)

This is a SOFT requirement - avoid regression, not mandatory acknowledgment.`}

Pass if digest handles this feedback appropriately for its category (immediate vs historical).
Fail if immediate feedback is ignored, or if historical errors are repeated.`
      }
    ]
  };

  tests.push(testCase);
});

// Add aggregate tests for overall feedback responsiveness
tests.push({
  description: 'Overall immediate feedback responsiveness',
  vars: {
    digest_output: `file://${digestPath}`,
    immediate_count: feedbackData.immediate_count,
    immediate_items: feedbackData.mentions.filter(m => m.is_immediate).map(m => m.mention_line).join('\n- ')
  },
  assert: [
    {
      type: 'llm-rubric',
      value: `Evaluate overall responsiveness to ALL immediate feedback items.

Total immediate feedback items: {{immediate_count}}

Immediate feedback list:
- {{immediate_items}}

Criteria:
1. The digest should show evidence of addressing ALL immediate corrections
2. Changes should be visible in content, tone, focus, or accuracy
3. The bot should not repeat ANY errors that were corrected yesterday
4. If no immediate feedback exists (count = 0), pass by default

Pass if digest addresses all immediate feedback comprehensively.
Fail if any immediate feedback is ignored or contradicted.`
    }
  ]
});

tests.push({
  description: 'Historical feedback patterns check',
  vars: {
    digest_output: `file://${digestPath}`,
    historical_count: feedbackData.historical_count,
    historical_items: feedbackData.mentions.filter(m => !m.is_immediate).map(m => m.mention_line).join('\n- ')
  },
  assert: [
    {
      type: 'llm-rubric',
      value: `Check that historical feedback patterns are not repeated.

Total historical feedback items: {{historical_count}}

Historical feedback list (may already be resolved):
- {{historical_items}}

Criteria:
1. The digest should not repeat past mistakes mentioned in historical feedback
2. No need to explicitly acknowledge historical items unless issue persists
3. Historical context prevents regression, not mandatory to address
4. If no historical feedback exists (count = 0), pass by default

Pass if digest doesn't repeat historical errors.
Fail if digest makes the same mistakes that were corrected in the past.`
    }
  ]
});

// Build the complete config
const config = {
  description: 'Feedback Responsiveness Evaluation - Auto-Generated Per-Feedback-Item Tests',
  prompts: ['{{digest_output}}'],
  providers: ['echo'],
  defaultTest: {
    options: {
      provider: 'anthropic:messages:claude-sonnet-4-5-20250929'
    }
  },
  tests: tests,
  outputPath: 'eval/results/feedback-evaluation.json'
};

// Write the generated config
const outputPath = 'promptfooconfig-feedback-generated.yaml';
try {
  const yamlContent = yaml.dump(config, { lineWidth: -1 });
  fs.writeFileSync(outputPath, yamlContent);
  console.log(`✅ Generated ${tests.length} test cases`);
  console.log(`📝 Config written to: ${outputPath}`);
  console.log('');
  console.log('To run the evaluation:');
  console.log(`  npx promptfoo eval --config ${outputPath} -j 1`);
} catch (error) {
  console.error('Error writing config:', error.message);
  process.exit(1);
}
