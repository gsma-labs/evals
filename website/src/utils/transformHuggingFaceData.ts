import type { LeaderboardEntry } from '../types/leaderboard';

/**
 * Raw row data from HuggingFace dataset API
 */
interface HuggingFaceRow {
  model: string;
  teleqna: [number, number, number] | null; // [score, stderr, n_samples]
  telelogs: [number, number, number] | null;
  telemath: [number, number, number] | null;
  '3gpp_tsg': [number, number, number] | null;
  date: string;
}

/**
 * Response structure from HuggingFace datasets API /rows endpoint
 */
interface HuggingFaceResponse {
  rows: Array<{
    row_idx: number;
    row: HuggingFaceRow;
    truncated_cells: string[];
  }>;
}

/**
 * Parse model name and provider from combined string
 * e.g., "gpt-5.2 (OpenAI)" → { model: "gpt-5.2", provider: "OpenAI" }
 */
function parseModelAndProvider(combined: string): { model: string; provider: string } {
  const match = combined.match(/^(.+?)\s*\(([^)]+)\)$/);
  if (match) {
    return { model: match[1].trim(), provider: match[2].trim() };
  }
  // Fallback if no provider in parentheses
  return { model: combined, provider: 'Unknown' };
}

/**
 * Calculate mean score from available benchmark scores
 */
function calculateMean(scores: (number | null)[]): number | null {
  const validScores = scores.filter((s): s is number => s !== null);
  if (validScores.length === 0) return null;
  return validScores.reduce((sum, s) => sum + s, 0) / validScores.length;
}

/**
 * Transform HuggingFace API response to LeaderboardEntry array
 */
export function transformHuggingFaceData(response: HuggingFaceResponse): LeaderboardEntry[] {
  const entries: LeaderboardEntry[] = response.rows.map((item) => {
    const row = item.row;
    const { model, provider } = parseModelAndProvider(row.model);

    const teleqna = row.teleqna?.[0] ?? null;
    const teleqna_stderr = row.teleqna?.[1] ?? null;
    const telelogs = row.telelogs?.[0] ?? null;
    const telelogs_stderr = row.telelogs?.[1] ?? null;
    const telemath = row.telemath?.[0] ?? null;
    const telemath_stderr = row.telemath?.[1] ?? null;
    const tsg = row['3gpp_tsg']?.[0] ?? null;
    const tsg_stderr = row['3gpp_tsg']?.[1] ?? null;

    const mean = calculateMean([teleqna, telelogs, telemath, tsg]);

    return {
      rank: 0, // Will be assigned after sorting
      model,
      provider,
      repo: '',
      mean,
      teleqna,
      teleqna_stderr,
      telelogs,
      telelogs_stderr,
      telemath,
      telemath_stderr,
      tsg,
      tsg_stderr,
    };
  });

  // Sort by mean score descending and assign ranks
  entries.sort((a, b) => {
    if (a.mean === null && b.mean === null) return 0;
    if (a.mean === null) return 1;
    if (b.mean === null) return -1;
    return b.mean - a.mean;
  });

  entries.forEach((entry, index) => {
    entry.rank = index + 1;
  });

  return entries;
}
