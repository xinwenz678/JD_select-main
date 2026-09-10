export type MatchPreviewOutcome = 'success' | 'failure';

/**
 * UI-only delay/failure simulator. It does not parse, score, save, or call an API.
 * Replace the caller with C's confirmed service after the shared contract is ready.
 */
export async function runMatchPreview(outcome: MatchPreviewOutcome): Promise<void> {
  performance.mark('jd-select:mock-match-start');
  await new Promise((resolve) => window.setTimeout(resolve, 700));
  if (outcome === 'failure') throw new Error('Simulated match failure');
}
