import type {
  ResumeDiagnoseResponse,
  ResumePdfUploadResponse,
  ResumeParseResponse,
  HistoryDisplayItem,
  ResultDisplayData,
  StarSuggestion,
} from '../types';

const baseUrl = (import.meta.env.VITE_API_BASE_URL || '/api').replace(/\/$/, '');

export async function getHealth(): Promise<{ status: string; version: string }> {
  const response = await fetch(`${baseUrl}/health`);
  if (!response.ok) throw new Error(`HTTP ${response.status}`);
  return response.json();
}

/** 把 FastAPI 校验错误的 detail（字符串或数组）整理成可读文案。 */
async function describeError(response: Response): Promise<string> {
  let detail: unknown;
  try {
    const data: unknown = await response.json();
    if (data && typeof data === 'object') {
      if ('detail' in data) detail = (data as { detail: unknown }).detail;
      else if ('error' in data) {
        const error = (data as { error?: unknown }).error;
        if (error && typeof error === 'object' && 'message' in error) detail = (error as { message: unknown }).message;
      }
    }
  } catch {
    // 响应体不是 JSON 时忽略，回退到 HTTP 状态码
  }
  if (Array.isArray(detail)) {
    const messages = detail
      .map((entry) => (entry && typeof entry === 'object' && typeof (entry as { msg?: unknown }).msg === 'string'
        ? (entry as { msg: string }).msg
        : JSON.stringify(entry)))
      .filter(Boolean);
    if (messages.length > 0) return messages.join('；');
  }
  if (typeof detail === 'string' && detail.trim()) return detail;
  return `HTTP ${response.status}`;
}

async function requestJson<T>(path: string, init?: RequestInit): Promise<T> {
  const controller = new AbortController();
  const timer = window.setTimeout(() => controller.abort(), 30_000);
  try {
    const response = await fetch(baseUrl + path, { ...init, signal: controller.signal });
    if (!response.ok) throw new Error(await describeError(response));
    return await response.json() as T;
  } catch (reason) {
    if (controller.signal.aborted) throw new Error('请求超时，结果状态尚未确认。请先查看历史记录，再决定是否重试。');
    if (reason instanceof TypeError) throw new Error('暂时无法连接服务，请检查网络或后端后重试。');
    throw reason;
  } finally { window.clearTimeout(timer); }
}
async function postJson<T>(path: string, body: unknown): Promise<T> {
  return requestJson<T>(path, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body) });
}

/** 解析简历文本，返回结构化区块与技能（B2）。 */
export function parseResume(text: string): Promise<ResumeParseResponse> {
  return postJson<ResumeParseResponse>('/resumes/parse', { text });
}

/** 上传文本型 PDF，在后端提取文字并复用现有简历解析器。 */
export async function uploadResumePdf(file: File): Promise<ResumePdfUploadResponse> {
  return requestJson<ResumePdfUploadResponse>('/resumes/upload-pdf', { method: 'POST', headers: { 'Content-Type': 'application/pdf' }, body: file });
}

/** 对简历原文做确定性规则诊断（B4）。 */
export function diagnoseResume(text: string): Promise<ResumeDiagnoseResponse> {
  return postJson<ResumeDiagnoseResponse>('/resumes/diagnose', { text });
}

export interface RecordPage { items: HistoryDisplayItem[]; total: number; limit: number; offset: number; }
export function createMatch(resumeText: string, jdText: string, jobTitle = '', confirmedSkills?: string[], confirmedName?: string | null): Promise<ResultDisplayData> {
  return postJson<ResultDisplayData>('/matches', { resume_text: resumeText, jd_text: jdText, job_title: jobTitle, confirmed_skills: confirmedSkills, confirmed_name: confirmedName });
}
export function createStarSuggestion(experience: string, jdText: string): Promise<StarSuggestion> {
  return postJson<StarSuggestion>('/suggestions/star', { experience, jd_text: jdText });
}
export async function getMatches(): Promise<RecordPage> {
  return requestJson<RecordPage>('/matches?limit=10');
}
export async function getMatch(id: string): Promise<ResultDisplayData> {
  return requestJson<ResultDisplayData>('/matches/' + encodeURIComponent(id));
}
