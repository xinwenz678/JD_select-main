import { useRef, useState } from 'react';
import type { FormEvent } from 'react';
import type { MatchPreviewOutcome } from '../services/matchPreview';

export interface AnalysisDraft {
  resume: string;
  jd: string;
}

interface NewAnalysisPageProps {
  draft: AnalysisDraft;
  onChange: (draft: AnalysisDraft) => void;
  onViewExample: () => void;
  onSubmitPreview: (outcome: MatchPreviewOutcome) => Promise<void>;
}

const sampleResume = '教育：信息管理专业在读。\n技能：Python、SQL。\n项目：使用 Python 清洗 1200 条合成数据，使用 SQL 查询数据并完成课程分析报告。';
const sampleJd = '岗位：数据分析实习生\n必需技能：Python、SQL。\n加分技能：Tableau。\n工作内容：清洗数据、编写查询和呈现分析结果。';

type SubmitState = 'idle' | 'loading' | 'error';

// UI state prototype only. B's parser and C's matching are deliberately not reimplemented.
export function NewAnalysisPage({ draft, onChange, onViewExample, onSubmitPreview }: NewAnalysisPageProps) {
  const isSample = draft.resume === sampleResume && draft.jd === sampleJd;
  const [outcome, setOutcome] = useState<MatchPreviewOutcome>('success');
  const [submitState, setSubmitState] = useState<SubmitState>('idle');
  const [fieldErrors, setFieldErrors] = useState<{ resume?: string; jd?: string }>({});
  const busy = useRef(false);
  const resumeInput = useRef<HTMLTextAreaElement>(null);
  const jdInput = useRef<HTMLTextAreaElement>(null);

  function updateDraft(next: AnalysisDraft) {
    onChange(next);
    setSubmitState('idle');
    setFieldErrors((current) => ({
      resume: next.resume.trim() ? undefined : current.resume,
      jd: next.jd.trim() ? undefined : current.jd,
    }));
  }

  function fillSample() {
    updateDraft({ resume: sampleResume, jd: sampleJd });
    setFieldErrors({});
  }

  async function submitPreview(event?: FormEvent, retryAsSuccess = false) {
    event?.preventDefault();
    if (busy.current) return;

    const nextErrors = {
      resume: draft.resume.trim() ? undefined : '请先输入简历内容。',
      jd: draft.jd.trim() ? undefined : '请先输入岗位 JD。',
    };
    setFieldErrors(nextErrors);
    if (nextErrors.resume || nextErrors.jd) {
      (nextErrors.resume ? resumeInput.current : jdInput.current)?.focus();
      return;
    }

    busy.current = true;
    setSubmitState('loading');
    try {
      await onSubmitPreview(retryAsSuccess ? 'success' : outcome);
    } catch {
      setSubmitState('error');
    } finally {
      busy.current = false;
    }
  }

  return (
    <>
      <div className="prototype-note">
        <strong>输入与提交状态原型</strong>
        <p>文本只保留在当前页面会话中，刷新后清空。提交使用本地延迟模拟，不调用解析、匹配或保存接口。</p>
      </div>
      <form onSubmit={submitPreview} noValidate>
        <section className="panel" aria-labelledby="resume-heading">
          <div className="section-heading"><h2 id="resume-heading">01 · 输入简历</h2><button type="button" className="text-button" onClick={fillSample}>填入合成示例</button></div>
          <label className="field-label" htmlFor="resume-text">简历内容</label>
          <textarea ref={resumeInput} id="resume-text" value={draft.resume} onChange={(event) => updateDraft({ ...draft, resume: event.target.value })} aria-describedby={`resume-hint${fieldErrors.resume ? ' resume-error' : ''}`} aria-invalid={Boolean(fieldErrors.resume)} placeholder="在这里粘贴教育、经历、项目和技能等简历内容" rows={7} />
          <p id="resume-hint" className="field-hint">{draft.resume.trim() ? '内容仅用于输入区域体验，不会上传或自动解析。' : '请先输入简历内容。'}</p>
          {fieldErrors.resume && <p id="resume-error" className="field-error" role="alert">{fieldErrors.resume}</p>}
          <button type="button" className="button secondary" disabled>解析简历（待接入 B）</button>
        </section>

        <section className="panel" aria-labelledby="parsed-heading">
          <div className="section-heading"><h2 id="parsed-heading">02 · 查看并修正解析结果</h2><span className="tag-neutral">解析与编辑待接入</span></div>
          {isSample ? (
            <div className="sample-sections"><p className="muted small">以下为合成样例的预设结构展示，并非解析输出。真实编辑组件由 B 提供。</p><dl><div><dt>教育</dt><dd>信息管理专业在读</dd></div><div><dt>经历</dt><dd>样例未提供</dd></div><div><dt>项目</dt><dd>合成数据清洗与课程分析报告</dd></div><div><dt>技能</dt><dd>Python、SQL</dd></div></dl></div>
          ) : <p className="muted">尚无解析结果。接入后会在此展示教育、经历、项目与技能，并支持确认修正。</p>}
        </section>

        <section className="panel" aria-labelledby="jd-heading">
          <div className="section-heading"><h2 id="jd-heading">03 · 输入岗位 JD</h2></div>
          <label className="field-label" htmlFor="jd-text">岗位 JD</label>
          <textarea ref={jdInput} id="jd-text" value={draft.jd} onChange={(event) => updateDraft({ ...draft, jd: event.target.value })} aria-describedby={`jd-hint${fieldErrors.jd ? ' jd-error' : ''}`} aria-invalid={Boolean(fieldErrors.jd)} placeholder="粘贴岗位职责、必需技能和加分要求" rows={5} />
          <p id="jd-hint" className="field-hint">{draft.jd.trim() ? '正式接口接入后，将使用团队确认的有效输入。' : '请先输入岗位 JD。'}</p>
          {fieldErrors.jd && <p id="jd-error" className="field-error" role="alert">{fieldErrors.jd}</p>}
          <div className="mock-submit-controls">
            <label htmlFor="mock-outcome">本次模拟结果</label>
            <select id="mock-outcome" value={outcome} onChange={(event) => { setOutcome(event.target.value as MatchPreviewOutcome); setSubmitState('idle'); }} disabled={submitState === 'loading'}>
              <option value="success">成功：进入固定结果</option>
              <option value="failure">失败：显示错误与重试</option>
            </select>
            <button type="submit" className="button primary" disabled={submitState === 'loading'}>{submitState === 'loading' ? '模拟匹配中…' : '开始模拟匹配'}</button>
          </div>
          <p className="field-hint">这是 UI 状态演示。成功时打开固定 demo-001，分数与当前输入无关，也不会保存记录。</p>
          {submitState === 'loading' && <p className="submission-status" role="status">正在模拟匹配，请稍候。重复提交已锁定。</p>}
          {submitState === 'error' && <div className="submission-error" role="alert"><div><strong>模拟匹配失败</strong><p>这是本地失败状态，不是后端报错。输入内容已保留。</p></div><button type="button" className="button secondary" onClick={() => submitPreview(undefined, true)}>重试并查看成功状态</button></div>}
        </section>
      </form>

      <section className="panel demo-entry"><div><h2>直接查看结果体验</h2><p className="muted">无需填写输入即可打开固定的 72 分示例。该入口不展示提交过程。</p></div><button className="button primary" onClick={onViewExample}>打开固定结果示例 <span aria-hidden="true">→</span></button></section>
    </>
  );
}
