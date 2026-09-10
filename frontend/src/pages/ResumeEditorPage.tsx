import { useEffect, useRef, useState } from 'react';
import type { ChangeEvent, FormEvent, KeyboardEvent } from 'react';
import { diagnoseResume, parseResume, uploadResumePdf } from '../services/api';
import { RESUME_SAMPLES } from '../services/resumeSamples';
import type {
  DiagnoseCategory,
  ParsedResume,
  ResumeDiagnoseResponse,
  ResumeParseResponse,
  ResumeSection,
  ResumeSectionKind,
} from '../types';
import { DIAGNOSE_CATEGORY_LABELS, SECTION_KIND_LABELS } from '../types';

/** 确认后回传给上层（岗位匹配/结果模块由成员 D/C 接线）的简历草稿。 */
export interface ConfirmedResumeDraft {
  text: string;
  parsed: ParsedResume;
  diagnosed: ResumeDiagnoseResponse | null;
  confirmedAt: string;
}

type Phase = 'editing' | 'parsing' | 'result' | 'confirming';

interface ResumeEditorPageProps {
  active?: boolean;
  onConfirm?: (draft: ConfirmedResumeDraft) => void;
}

const SECTION_ORDER: ResumeSectionKind[] = ['education', 'experience', 'projects', 'skills', 'other'];
const MAX_PDF_BYTES = 10 * 1024 * 1024;

function sectionLabel(kind: string): string {
  return SECTION_KIND_LABELS[kind as ResumeSectionKind] ?? kind;
}

function categoryLabel(category: DiagnoseCategory): string {
  return DIAGNOSE_CATEGORY_LABELS[category];
}

function SkillChips({ skills, onRemove }: { skills: readonly string[]; onRemove: (skill: string) => void }) {
  if (skills.length === 0) return <p className="muted">暂无技能词，可点击右侧“添加技能”。</p>;
  return (
    <ul className="chips" aria-label="识别到的技能">
      {skills.map((skill) => (
        <li key={skill} className="chip">
          <span>{skill}</span>
          <button type="button" className="chip-remove" aria-label={`移除 ${skill}`} onClick={() => onRemove(skill)}>×</button>
        </li>
      ))}
    </ul>
  );
}

function SkillSection({ section }: { section: ResumeSection }) {
  return (
    <div className="skill-lines">
      {section.lines.map((line, index) => <p key={`${line}-${index}`}>{line}</p>)}
    </div>
  );
}

export function ResumeEditorPage({ onConfirm, active = true }: ResumeEditorPageProps) {
  const [text, setText] = useState('');
  const [phase, setPhase] = useState<Phase>('editing');
  const [error, setError] = useState('');
  const [parsed, setParsed] = useState<ResumeParseResponse | null>(null);
  const [diagnosed, setDiagnosed] = useState<ResumeDiagnoseResponse | null>(null);
  const [diagnosing, setDiagnosing] = useState(false);
  const [skills, setSkills] = useState<string[]>([]);
  const [newSkill, setNewSkill] = useState('');
  const [editableName, setEditableName] = useState('');
  const [draft, setDraft] = useState<ConfirmedResumeDraft | null>(null);
  const [uploading, setUploading] = useState(false);
  const [uploadedFileName, setUploadedFileName] = useState('');
  const fileInputRef = useRef<HTMLInputElement>(null);

  useEffect(() => { if (active) setPhase(value => value === 'confirming' ? 'result' : value); }, [active]);

  const resume: ParsedResume | null = parsed?.resume ?? null;
  const rawLines = text.split(/\r?\n/);

  function loadSample(sampleId: string) {
    const sample = RESUME_SAMPLES.find((item) => item.id === sampleId);
    if (!sample) return;
    setText(sample.text);
    setError('');
    setPhase('editing');
    setParsed(null);
    setDiagnosed(null);
    setDraft(null);
    setUploadedFileName('');
  }

  async function handleParse(event: FormEvent) {
    event.preventDefault();
    if (!text.trim()) {
      setError('请先粘贴或输入简历文本（至少包含姓名与一段经历）。');
      return;
    }
    setError('');
    setPhase('parsing');
    try {
      const result = await parseResume(text);
      setParsed(result);
      setDiagnosed(null);
      setSkills([...result.resume.skills]);
      setEditableName(result.resume.basic.name ?? '');
      setDraft(null);
      setPhase('result');
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : '解析失败，请检查后端服务后重试。');
      setPhase('editing');
    }
  }

  async function handlePdfUpload(event: ChangeEvent<HTMLInputElement>) {
    const file = event.target.files?.[0];
    event.target.value = '';
    if (!file) return;
    if (!file.name.toLowerCase().endsWith('.pdf')) {
      setError('请选择 PDF 格式的简历文件。');
      return;
    }
    if (file.size > MAX_PDF_BYTES) {
      setError('PDF 文件不能超过 10 MB。');
      return;
    }

    setUploading(true);
    setError('');
    try {
      const result = await uploadResumePdf(file);
      setText(result.text);
      setParsed({
        schema_version: result.schema_version,
        algorithm_version: result.algorithm_version,
        resume: result.resume,
      });
      setDiagnosed(null);
      setSkills([...result.resume.skills]);
      setEditableName(result.resume.basic.name ?? '');
      setDraft(null);
      setUploadedFileName(`${file.name} · ${result.pages} 页`);
      setPhase('result');
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : 'PDF 上传失败，请稍后重试。');
    } finally {
      setUploading(false);
    }
  }

  async function handleDiagnose() {
    if (!resume) return;
    setDiagnosing(true);
    setError('');
    try {
      const result = await diagnoseResume(text);
      setDiagnosed(result);
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : '诊断失败，请稍后重试。');
    } finally {
      setDiagnosing(false);
    }
  }

  function removeSkill(skill: string) {
    setSkills((current) => current.filter((item) => item !== skill));
  }

  function addSkill() {
    const trimmed = newSkill.trim();
    if (!trimmed) return;
    setSkills((current) => (current.includes(trimmed) ? current : [...current, trimmed]));
    setNewSkill('');
  }

  function handleSkillKeyDown(event: KeyboardEvent<HTMLInputElement>) {
    if (event.key === 'Enter') {
      event.preventDefault();
      addSkill();
    }
  }

  function resetToText() {
    setPhase('editing');
    setError('');
    setDraft(null);
  }

  function handleConfirm() {
    if (!parsed || !resume) return;
    const merged: ParsedResume = {
      ...resume,
      basic: {
        ...resume.basic,
        name: editableName.trim() || null,
      },
      skills: [...skills],
    };
    const confirmed: ConfirmedResumeDraft = {
      text,
      parsed: merged,
      diagnosed,
      confirmedAt: new Date().toISOString(),
    };
    setDraft(confirmed);
    setPhase('confirming');
    onConfirm?.(confirmed);
  }

  const orderedSections = (resume ? [...resume.sections].sort((a, b) => SECTION_ORDER.indexOf(a.kind as ResumeSectionKind) - SECTION_ORDER.indexOf(b.kind as ResumeSectionKind)) : []);

  return (
    <section className="resume-page" aria-label="简历录入与解析">
      <header className="page-intro">
        <p className="eyebrow">新建分析 · 第 1 步 / 共 3 步</p>
        <h1>录入并解析简历</h1>
        <p className="muted">可粘贴简历文本或上传 PDF。系统按规则识别教育、经历、项目与技能区块（确定性算法，不上传第三方）。</p>
        <ol className="steps" aria-label="新建分析步骤">
          <li className="active">① 简历录入与确认</li>
          <li>② 岗位 JD 与定向建议</li>
          <li>③ 匹配结果与证据</li>
        </ol>
      </header>

      {phase !== 'confirming' && (
        <>
          <form onSubmit={handleParse} className="panel resume-form">
            <div className="section-heading">
              <div>
                <h2>简历内容</h2>
                <p className="muted small">上传文本型 PDF，或直接粘贴纯文本简历；脱敏样例仅用于演示。</p>
              </div>
              <span className="count">{text.length} 字</span>
            </div>

            <div className="sample-row" aria-label="载入演示样例">
              <span className="muted small">快速体验：</span>
              {RESUME_SAMPLES.map((sample) => (
                <button key={sample.id} type="button" className="button ghost small" disabled={uploading || diagnosing || phase === 'parsing'} title={sample.description} onClick={() => loadSample(sample.id)}>
                  {sample.label}
                </button>
              ))}
              {text && <button type="button" className="button ghost small" disabled={uploading || diagnosing || phase === 'parsing'} onClick={() => { setText(''); setDraft(null); setParsed(null); setDiagnosed(null); setUploadedFileName(''); setPhase('editing'); setError(''); }}>清空</button>}
            </div>

            <div className="pdf-upload" aria-label="上传 PDF 简历">
              <div>
                <strong>上传 PDF 简历</strong>
                <p className="muted small">支持文本型 PDF，最大 10 MB、30 页；扫描件暂不支持 OCR。</p>
                {uploadedFileName && <p className="upload-success" role="status">已读取：{uploadedFileName}</p>}
              </div>
              <input
                ref={fileInputRef}
                className="visually-hidden"
                type="file"
                accept="application/pdf,.pdf"
                onChange={handlePdfUpload}
                aria-label="选择 PDF 简历"
                disabled={uploading || phase === 'parsing' || diagnosing}
              />
              <button
                type="button"
                className="button secondary"
                onClick={() => fileInputRef.current?.click()}
                disabled={uploading || phase === 'parsing' || diagnosing}
              >
                {uploading ? '正在读取 PDF…' : '选择 PDF 文件'}
              </button>
            </div>

            <label className="field">
              <span className="field-label">简历原文 <span className="required">*</span></span>
              <textarea
                value={text}
                onChange={(event) => { setText(event.target.value); setUploadedFileName(''); setParsed(null); setDiagnosed(null); setDraft(null); setPhase('editing'); setError(''); }}
                disabled={uploading || diagnosing || phase === 'parsing'}
                placeholder={'示例格式：\n姓名\n电话/邮箱\n\n教育背景\n2021.09 - 2025.06  XX大学  计算机科学与技术  本科\n\n实习经历\n2024.06 - 2024.09  XX科技  后端实习生\n负责订单模块接口开发，使用 Python/FastAPI\n修复线上缺陷 12 个，接口响应时间下降 30%'}
                rows={12}
                spellCheck={false}
                aria-label="简历原文"
              />
            </label>

            {error && <p role="alert" className="form-error">{error}</p>}

            <div className="actions form-actions">
              <button type="submit" className="button primary" disabled={phase === 'parsing' || uploading || !text.trim()}>
                {phase === 'parsing' ? '正在解析…' : '解析简历'}
              </button>
            </div>
          </form>

          {phase === 'result' && resume && (
            <div className="parse-result">
              <section className="panel" aria-labelledby="parse-overview-heading">
                <div className="section-heading">
                  <div>
                    <h2 id="parse-overview-heading">解析结果</h2>
                    <p className="muted small">算法 {parsed?.algorithm_version} · schema {parsed?.schema_version}。绿色条目可编辑后再确认。</p>
                  </div>
                  <span className="tag-neutral">{resume.sections.length} 个区块 · {skills.length} 项技能</span>
                </div>

                <div className="basic-editor">
                  <label className="field inline">
                    <span className="field-label">姓名</span>
                    <input value={editableName} onChange={(event) => setEditableName(event.target.value)} aria-label="姓名" />
                  </label>
                  <div className="contact-readonly">
                    <span className="muted small">{resume.basic.contact.email ? `邮箱：${resume.basic.contact.email}` : ''}</span>
                    <span className="muted small">{resume.basic.contact.phone ? `电话：${resume.basic.contact.phone}` : ''}</span>
                  </div>
                </div>

                {resume.warnings.length > 0 && (
                  <ul className="warnings">
                    {resume.warnings.map((warning) => <li key={warning}>{warning}</li>)}
                  </ul>
                )}

                <ul className="section-cards">
                  {orderedSections.map((section) => {
                    const isSkills = section.kind === 'skills';
                    return (
                      <li key={`${section.kind}-${section.line_start}`} className={`section-card kind-${section.kind}`}>
                        <header className="section-card-head">
                          <span className="kind-badge">{sectionLabel(section.kind)}</span>
                          <span className="muted small">{section.heading || sectionLabel(section.kind)} · 第 {section.line_start}–{section.line_end} 行</span>
                        </header>
                        {isSkills ? (
                          <div className="skill-editor">
                            <SkillChips skills={skills} onRemove={removeSkill} />
                            <div className="chip-input-row">
                              <input
                                value={newSkill}
                                onChange={(event) => setNewSkill(event.target.value)}
                                onKeyDown={handleSkillKeyDown}
                                placeholder="手动补充技能，如 SQL"
                                aria-label="添加技能"
                              />
                              <button type="button" className="button secondary small" onClick={addSkill} disabled={!newSkill.trim()}>添加</button>
                              <button type="button" className="button ghost small" onClick={() => setSkills([...resume.skills])} disabled={skills.join('|') === resume.skills.join('|')}>恢复解析结果</button>
                            </div>
                          </div>
                        ) : (
                          <SkillSection section={section} />
                        )}
                      </li>
                    );
                  })}
                </ul>
              </section>

              <section className="panel diagnose-panel" aria-labelledby="diagnose-heading">
                <div className="section-heading">
                  <div>
                    <h2 id="diagnose-heading">简历质量诊断</h2>
                    <p className="muted small">规则扫描经历行中的量化成果、动作动词与结构缺失（B4 确定性规则）。</p>
                  </div>
                  {!diagnosed && (
                    <button type="button" className="button secondary" onClick={handleDiagnose} disabled={diagnosing}>
                      {diagnosing ? '诊断中…' : '运行诊断'}
                    </button>
                  )}
                  {diagnosed && <button type="button" className="button ghost" onClick={handleDiagnose} disabled={diagnosing}>重新诊断</button>}
                </div>

                {error && <p role="alert" className="form-error">{error}</p>}

                {!diagnosed && !diagnosing && <p className="muted">点击“运行诊断”查看这份简历的量化亮点与可改进点。</p>}
                {diagnosing && <p className="muted">正在扫描经历正文…</p>}

                {diagnosed && (
                  <>
                    <dl className="diag-summary">
                      <div className="diag-total"><dt>诊断项</dt><dd>{diagnosed.summary.total}</dd></div>
                      <div className="diag-count quantified"><dt>{categoryLabel('quantified')}</dt><dd>{diagnosed.summary.quantified}</dd></div>
                      <div className="diag-count action_verb"><dt>{categoryLabel('action_verb')}</dt><dd>{diagnosed.summary.action_verb}</dd></div>
                      <div className="diag-count suggestion"><dt>{categoryLabel('suggestion')}</dt><dd>{diagnosed.summary.suggestion}</dd></div>
                    </dl>

                    {diagnosed.diagnoses.length > 0 ? (
                      <ul className="diagnoses">
                        {diagnosed.diagnoses.map((item, index) => {
                          const quote = item.line != null ? rawLines[item.line - 1]?.trim() : null;
                          return (
                            <li key={`${item.category}-${item.line ?? 'global'}-${index}`} className={`diagnosis category-${item.category}`}>
                              <div className="diagnosis-main">
                                <span className="diag-cat">{categoryLabel(item.category)}</span>
                                <p>{item.message}</p>
                              </div>
                              {item.suggestion && <p className="diag-suggestion">建议：{item.suggestion}</p>}
                              {(item.line != null || item.section) && (
                                <p className="diag-location muted small">
                                  定位：{item.section ? `${sectionLabel(item.section)}` : '简历整体'}
                                  {item.line != null ? ` · 原文第 ${item.line} 行` : ''}
                                </p>
                              )}
                              {quote && <blockquote className="diag-quote">“{quote}”</blockquote>}
                            </li>
                          );
                        })}
                      </ul>
                    ) : (
                      <p className="muted">未发现明显问题，简历结构完整、量化与动词使用良好。</p>
                    )}
                  </>
                )}
              </section>

              <div className="actions step-actions">
                <button type="button" className="button secondary" onClick={resetToText}>← 修改原文重新解析</button>
                <button type="button" className="button primary" onClick={handleConfirm}>
                  确认简历信息，进入岗位匹配 →
                </button>
              </div>
              {skills.length === 0 && <p className="muted small center-hint">未识别技能也可继续匹配；系统会如实显示缺口。</p>}
            </div>
          )}
        </>
      )}

      {phase === 'confirming' && draft && resume && (
        <section className="panel confirm-banner" role="status">
          <h2>简历已确认</h2>
          <p>已保存结构化简历草稿（{draft.parsed.sections.length} 个区块、{draft.parsed.skills.length} 项技能），供后续岗位匹配使用。</p>
          <dl className="confirm-summary">
            <div><dt>姓名</dt><dd>{draft.parsed.basic.name ?? '未提供'}</dd></div>
            <div><dt>识别技能</dt><dd>{draft.parsed.skills.length > 0 ? draft.parsed.skills.join('、') : '无'}</dd></div>
            <div><dt>诊断项</dt><dd>{draft.diagnosed ? `${draft.diagnosed.summary.total} 项` : '未运行'}</dd></div>
            <div><dt>确认时间</dt><dd>{new Date(draft.confirmedAt).toLocaleString('zh-CN')}</dd></div>
          </dl>
          <div className="actions">
            <button type="button" className="button secondary" onClick={() => setPhase('result')}>← 返回修改</button>
            <button type="button" className="button primary" onClick={() => setPhase('result')} aria-disabled="true" disabled title="第 2 步岗位 JD 输入与匹配页由成员 D/C 接入">
              下一步：粘贴岗位 JD（待 D/C 接入）
            </button>
          </div>
        </section>
      )}
    </section>
  );
}
