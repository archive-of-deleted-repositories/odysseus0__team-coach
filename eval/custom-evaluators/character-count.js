/**
 * Custom evaluator to check character count against Telegram limits
 *
 * This ensures digests stay under the 4096 character Telegram limit.
 * We use 4000 as the threshold to leave buffer for markdown.
 */

module.exports = async (output, context) => {
  const charCount = output.length;
  const limit = context.vars.charLimit || 4000;

  const pass = charCount < limit;
  const score = pass ? 1.0 : 0.0;

  return {
    pass,
    score,
    reason: pass
      ? `Character count ${charCount} is under limit of ${limit}`
      : `Character count ${charCount} exceeds limit of ${limit} by ${charCount - limit} characters`,
    namedScores: {
      characterCount: charCount,
      withinLimit: pass ? 1 : 0,
      overagePercent: pass ? 0 : ((charCount - limit) / limit) * 100
    }
  };
};
