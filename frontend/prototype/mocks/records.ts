import type { HistoryDisplayItem, ResultDisplayData } from '../types';

// All entries are synthetic presentation fixtures. No parsing, scoring or saving occurs.
export const demoResults: readonly ResultDisplayData[] = [
  {
    id: 'demo-001',
    job_title: '数据分析实习生',
    score: 72,
    score_breakdown: { required_skills: 55, preferred_skills: 12, evidence_quality: 5 },
    matched_skills: ['Python', 'SQL'],
    missing_skills: ['Tableau'],
    suggestions: ['补充量化成果', '增加与 Tableau 相关的真实项目证据'],
    algorithm_version: 'rule-v1',
  },
  {
    id: 'demo-002',
    job_title: 'Python 后端实习生',
    score: 48,
    score_breakdown: { required_skills: 30, preferred_skills: 8, evidence_quality: 10 },
    matched_skills: ['Python', 'Excel'],
    missing_skills: ['FastAPI', 'SQL'],
    suggestions: ['补充能够体现 FastAPI 和 SQL 能力的真实项目经历'],
    algorithm_version: 'rule-v1',
  },
  {
    id: 'demo-003',
    job_title: '数据产品实习生',
    score: 0,
    score_breakdown: { required_skills: 0, preferred_skills: 0, evidence_quality: 0 },
    matched_skills: [],
    missing_skills: ['SQL', 'Python'],
    suggestions: [],
    algorithm_version: 'rule-v1',
  },
];

// Fixed, synthetic timestamps; result data deliberately has no invented evidence field.
const demoTimes = [
  '2026-09-08T02:20:00Z',
  '2026-09-08T01:10:00Z',
  '2026-09-07T08:30:00Z',
];

export const demoHistory: readonly HistoryDisplayItem[] = demoResults.map((result, index) => ({
  id: result.id,
  job_title: result.job_title,
  score: result.score,
  created_at: demoTimes[index],
}));

// Record identity never depends on its array position, even after sorting the list.
export function findDemoResult(id: string): ResultDisplayData | undefined {
  return demoResults.find((result) => result.id === id);
}
