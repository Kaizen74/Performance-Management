/**
 * Seniority classification — single source of truth for the frontend.
 *
 * The backend (GoalsTableProcessor._infer_seniority) emits exactly three
 * canonical values: 'senior management', 'team leader', and
 * 'individual contributor'. The dashboard filter, the Excel export's
 * "Score Distribution by Seniority" table, and the PDF report must all
 * bucket employees identically, otherwise the same upload produces
 * different headcounts in different views.
 *
 * Rules:
 *  1. A canonical backend value maps directly to its bucket — never re-derive.
 *  2. Free-text seniority from other sources falls back to pattern matching.
 *  3. Missing seniority is 'unspecified', NOT silently counted as an
 *     individual contributor (that inflated the IC bucket with every
 *     analysis that carried no employee context at all).
 */

export type SeniorityBucket =
  | 'senior_management'
  | 'team_leader'
  | 'individual_contributor'
  | 'unspecified';

export type SeniorityFilter = 'all' | SeniorityBucket;

/** Canonical values emitted by the backend, mapped to their bucket. */
const CANONICAL: Record<string, SeniorityBucket> = {
  'senior management': 'senior_management',
  'team leader': 'team_leader',
  'individual contributor': 'individual_contributor',
};

/**
 * Fallback patterns for free-text seniority values.
 * Ordered: senior management is checked before team leader, because
 * "senior manager" must not be caught by the bare "manager" pattern.
 */
const SENIOR_MANAGEMENT_PATTERNS = [
  'chief', 'ceo', 'cfo', 'coo', 'cto', 'cio', 'cmo', 'chro',
  'svp', 'evp', 'senior vice president', 'executive vice president',
  'managing director', 'president', 'global head', 'regional head',
  'country head', 'c-level', 'executive',
];

const TEAM_LEADER_PATTERNS = [
  'team leader', 'team lead', 'senior manager', 'manager', 'supervisor',
  'director', 'vice president', 'avp', 'head of', 'section head',
];

/**
 * Classify a seniority value into its bucket.
 * Returns 'unspecified' when no seniority information is available.
 */
export function categorizeSeniority(seniorityLevel?: string | null): SeniorityBucket {
  if (!seniorityLevel || !seniorityLevel.trim()) {
    return 'unspecified';
  }

  const level = seniorityLevel.toLowerCase().trim();

  // 1. Exact canonical match from the backend — authoritative.
  const canonical = CANONICAL[level];
  if (canonical) {
    return canonical;
  }

  // 2. Free-text fallback, most senior first.
  if (SENIOR_MANAGEMENT_PATTERNS.some((p) => level.includes(p))) {
    return 'senior_management';
  }
  if (TEAM_LEADER_PATTERNS.some((p) => level.includes(p))) {
    return 'team_leader';
  }

  // 3. A stated level that matches no leadership pattern is an IC.
  return 'individual_contributor';
}

export const SENIORITY_LABELS: Record<SeniorityFilter, string> = {
  all: 'All employees',
  senior_management: 'Senior management',
  team_leader: 'Team leaders',
  individual_contributor: 'Individual contributors',
  unspecified: 'Seniority not stated',
};

/** Display order for filter chips. */
export const SENIORITY_FILTER_ORDER: SeniorityFilter[] = [
  'all',
  'senior_management',
  'team_leader',
  'individual_contributor',
  'unspecified',
];
