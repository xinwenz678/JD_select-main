/**
 * 前端公共类型与展示工具（B3 补建，供各页面共享）。
 *
 * 说明：
 * - Result/History 相关类型对齐 MVP_TASK_PLAN 冻结契约中 `POST /api/matches`
 *   的响应结构与历史记录列表项，供结果页/历史页（成员 D）接入真实接口后复用；
 * - Resume/Diagnose 类型对齐后端 `backend/app/schemas/resume.py`
 *   （resume-v1 / rule-v1），即 `POST /api/resumes/parse` 与
 *   `POST /api/resumes/diagnose` 的响应结构。
 * 字段与后端保持一致后再改，改动需通知 A（契约维护）。
 */

// ---------- 结果页 / 历史页展示类型（对齐 /api/matches 契约） ----------

export type PreviewState = 'normal' | 'loading' | 'error' | 'empty' | 'ready';

export interface HistoryDisplayItem {
  id: string;
  job_title?: string | null;
  score?: number | null;
  created_at?: string | null;
}

export interface ScoreBreakdown {
  required_skills: number | null;
  preferred_skills: number | null;
  evidence_quality: number | null;
}


export interface EvidenceItem {
  source: 'resume' | 'jd' | 'confirmed_resume';
  category: 'matched_skill' | 'required_skill' | 'quantified_result' | 'action_verb';
  label: string;
  line: number | null;
  text: string;
}
export interface ResultDisplayData {
  id: string;
  job_title?: string | null;
  score?: number | null;
  score_breakdown?: ScoreBreakdown | null;
  matched_skills?: string[] | null;
  missing_skills?: string[] | null;
  suggestions?: string[] | null;
  evidence_items?: EvidenceItem[] | null;
  confirmed_skills?: string[] | null;
  confirmed_name?: string | null;
  algorithm_version?: string | null;
}

export function displayScore(value: number | null | undefined): string {
  return typeof value === 'number' && Number.isFinite(value) && value >= 0
    ? String(Math.round(value))
    : '暂无评分';
}

export function displayTitle(value: string | null | undefined): string {
  const text = (value ?? '').trim();
  return text || '未命名岗位';
}

// ---------- 简历解析类型（对齐 backend schemas/resume.py） ----------

export type ResumeSectionKind = 'education' | 'experience' | 'projects' | 'skills' | 'other';

export interface ContactInfo {
  email: string | null;
  phone: string | null;
}

export interface BasicInfo {
  name: string | null;
  contact: ContactInfo;
}

export interface ResumeSection {
  kind: ResumeSectionKind;
  heading: string;
  line_start: number;
  line_end: number;
  lines: string[];
}

export interface ParsedResume {
  basic: BasicInfo;
  sections: ResumeSection[];
  skills: string[];
  warnings: string[];
}

export interface ResumeParseResponse {
  schema_version: string;
  algorithm_version: string;
  resume: ParsedResume;
}

export interface ResumePdfUploadResponse extends ResumeParseResponse {
  text: string;
  pages: number;
}

/** 简历区块类别的中文标签（教育/经历/项目/技能/其他）。 */
export const SECTION_KIND_LABELS: Record<ResumeSectionKind, string> = {
  education: '教育背景',
  experience: '实习经历',
  projects: '项目经历',
  skills: '专业技能',
  other: '其他',
};

// ---------- 简历诊断类型（对齐 backend schemas/resume.py B4） ----------

export type DiagnoseCategory = 'quantified' | 'action_verb' | 'suggestion';

export const DIAGNOSE_CATEGORY_LABELS: Record<DiagnoseCategory, string> = {
  quantified: '量化亮点',
  action_verb: '动作动词',
  suggestion: '改进建议',
};

export interface DiagnoseItem {
  category: DiagnoseCategory;
  message: string;
  suggestion: string;
  line: number | null;
  section: string | null;
}

export interface DiagnoseSummary {
  total: number;
  quantified: number;
  action_verb: number;
  suggestion: number;
}

export interface ResumeDiagnoseResponse {
  schema_version: string;
  algorithm_version: string;
  summary: DiagnoseSummary;
  diagnoses: DiagnoseItem[];
}

export interface StarSuggestion {
  original: string;
  star: { situation: string; task: string; action: string; result: string };
  optimized_draft: string;
  jd_keywords: string[];
  metric_prompts: string[];
  source: 'rule-fallback' | 'llm';
  notice: string;
}
