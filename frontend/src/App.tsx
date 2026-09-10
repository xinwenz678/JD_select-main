import { useEffect, useRef, useState } from 'react';
import type { FormEvent } from 'react';
import { ResumeEditorPage } from './pages/ResumeEditorPage';
import type { ConfirmedResumeDraft } from './pages/ResumeEditorPage';
import { ResultPage } from './pages/ResultPage';
import { HistoryPage } from './pages/HistoryPage';
import { createMatch, createStarSuggestion, getMatch, getMatches } from './services/api';
import type { HistoryDisplayItem, ResultDisplayData, StarSuggestion } from './types';

type View = 'home' | 'resume' | 'jd' | 'result' | 'history';
type Route = { view: View; id?: string };
const UUID_RE = /^[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i;

function readRoute(): Route {
  const hash = location.hash.replace(/^#/, '') || '/';
  if (hash === '/' || hash === '/home') return { view: 'home' };
  if (hash === '/analysis/new') return { view: 'resume' };
  if (hash === '/analysis/jd') return { view: 'jd' };
  if (hash === '/history') return { view: 'history' };
  if (hash.startsWith('/results/')) {
    try { return { view: 'result', id: decodeURIComponent(hash.slice(9)) }; }
    catch { return { view: 'result', id: 'invalid-encoding' }; }
  }
  return { view: 'home' };
}
function navigate(path: string) { if (location.hash === '#' + path) window.dispatchEvent(new HashChangeEvent('hashchange')); else location.hash = path; }

export default function App() {
  const [route, setRoute] = useState<Route>(readRoute);
  const [draft, setDraft] = useState<ConfirmedResumeDraft|null>(null);
  const [jdText,setJdText]=useState(''), [jobTitle,setJobTitle]=useState('');
  const [result,setResult]=useState<ResultDisplayData>(), [history,setHistory]=useState<HistoryDisplayItem[]>([]);
  const [busy,setBusy]=useState(false), [error,setError]=useState(''), [notFound,setNotFound]=useState(false);
  const [experience,setExperience]=useState(''), [star,setStar]=useState<StarSuggestion>(), [starBusy,setStarBusy]=useState(false);
  const submitting = useRef(false);
  const starLock = useRef(false);
  const [retry, setRetry] = useState(0);
  const [matching, setMatching] = useState(false);
  const [starError, setStarError] = useState('');

  useEffect(() => { const onHash=()=>setRoute(readRoute()); addEventListener('hashchange', onHash); if (!location.hash) navigate('/'); return()=>removeEventListener('hashchange', onHash); }, []);
  useEffect(() => {
    let active = true;
    setError(''); setNotFound(false); setBusy(false);
    if (route.view === 'history') {
      setBusy(true);
      getMatches().then(page => { if (active) setHistory(page.items); })
        .catch(reason => { if (active) setError(reason instanceof Error ? reason.message : '历史记录加载失败。'); })
        .finally(() => { if (active) setBusy(false); });
    } else if (route.view === 'result') {
      setResult(undefined);
      if (!route.id || !UUID_RE.test(route.id)) { setNotFound(true); return; }
      setBusy(true);
      getMatch(route.id).then(value => { if (active) setResult(value); })
        .catch(reason => { if (!active) return; const message = reason instanceof Error ? reason.message : '结果加载失败。'; if (/404|不存在/.test(message)) setNotFound(true); else setError(message); })
        .finally(() => { if (active) setBusy(false); });
    }
    return () => { active = false; };
  }, [route.view, route.id, retry]);
  useEffect(() => { setStar(undefined); setStarError(''); }, [experience, jdText]);

  function confirmResume(value:ConfirmedResumeDraft){ setDraft(value); setError(''); navigate('/analysis/jd'); }
  async function submitMatch(event:FormEvent){
    event.preventDefault(); if(submitting.current)return;
    if(!draft){navigate('/analysis/new');return;} if(!jdText.trim()){setError('请先输入岗位 JD。');document.getElementById('jd-text')?.focus();return;}
    const originHash=location.hash; submitting.current=true;setMatching(true);setError('');
    try { const value=await createMatch(draft.text,jdText,jobTitle,draft.parsed.skills,draft.parsed.basic.name); if (location.hash===originHash) navigate('/results/'+value.id); }
    catch(reason){setError(reason instanceof Error?reason.message:'匹配失败，请稍后重试。');}
    finally{submitting.current=false;setMatching(false);}
  }
  async function generateStar(){
    if(starLock.current)return;
    if(!experience.trim()||!jdText.trim()){setStarError('请先填写岗位 JD 和一段待优化经历。');return;}
    starLock.current=true;setStarBusy(true);setStarError('');setStar(undefined);
    try{setStar(await createStarSuggestion(experience,jdText));}
    catch(reason){setStarError(reason instanceof Error?reason.message:'建议生成失败，匹配仍可继续。');}
    finally{starLock.current=false;setStarBusy(false);}
  }
  const view=route.view;
  return (
    <>
      <header className="topbar">
        <button type="button" className="brand" disabled={matching} onClick={()=>navigate('/')}>
          <span className="brand-mark" aria-hidden="true">J</span>
          <span className="brand-copy"><strong>JD Select</strong><span>AI 简历诊断与岗位匹配</span></span>
        </button>
        <nav aria-label="主导航">
          <button disabled={matching} aria-current={view==='home'?'page':undefined} className={'nav-link'+(view==='home'?' active':'')} onClick={()=>navigate('/')}>首页</button>
          <button disabled={matching} aria-current={view==='resume'||view==='jd'?'page':undefined} className={'nav-link'+(view==='resume'||view==='jd'?' active':'')} onClick={()=>navigate('/analysis/new')}>新建分析</button>
          <button disabled={matching} aria-current={view==='history'?'page':undefined} className={'nav-link'+(view==='history'?' active':'')} onClick={()=>navigate('/history')}>历史记录</button>
        </nav>
      </header>
      <main className="page">
        {view==='home'&&(
          <>
            <section className="home-hero">
              <div className="hero-copy">
                <p className="eyebrow">清晰证据 · 确定规则 · 本地保存</p>
                <h1>让简历与岗位要求<br/><span>真正对得上。</span></h1>
                <p className="hero-lead">从简历解析、技能确认到岗位差距，一次分析给出分数、证据和下一步改进方向。</p>
                <div className="actions hero-actions">
                  <button className="button primary" onClick={()=>navigate('/analysis/new')}>开始新建分析 <span aria-hidden="true">→</span></button>
                  <button className="button hero-secondary" onClick={()=>navigate('/history')}>查看历史记录</button>
                </div>
                <ul className="hero-facts" aria-label="产品特点">
                  <li><strong>0</strong><span>无需登录</span></li>
                  <li><strong>3</strong><span>步完成分析</span></li>
                  <li><strong>100%</strong><span>证据可追溯</span></li>
                </ul>
              </div>
              <div className="hero-preview" aria-label="分析内容预览">
                <div className="preview-head"><span className="preview-dot"/><span>岗位匹配概览</span><span className="preview-status">已保存</span></div>
                <div className="preview-score"><strong>技能</strong><span>逐项核对</span></div>
                <div className="preview-bars" aria-hidden="true"><i/><i/><i/></div>
                <div className="preview-tags"><span>匹配技能</span><span>缺失技能</span><span>原文证据</span></div>
                <p>每个判断都能回到简历或 JD 原文。</p>
              </div>
            </section>
            <section className="home-workflow" aria-labelledby="workflow-title">
              <div className="home-section-title"><p className="eyebrow">工作流程</p><h2 id="workflow-title">三步得到可解释的匹配结果</h2></div>
              <ol className="workflow-grid">
                <li><span>01</span><div><h3>录入简历</h3><p>粘贴文本或上传 PDF，检查结构化解析结果。</p></div></li>
                <li><span>02</span><div><h3>确认并匹配</h3><p>修正技能、输入目标 JD，提交确定性规则分析。</p></div></li>
                <li><span>03</span><div><h3>查看证据</h3><p>核对分项得分、技能缺口、原文依据与建议。</p></div></li>
              </ol>
            </section>
            <aside className="home-note"><span aria-hidden="true">✓</span><p><strong>你的判断始终优先。</strong> 系统不会把匹配分解释为录用概率，STAR 建议也需要人工核实后再使用。</p></aside>
          </>
        )}
        <div hidden={view!=='resume'}><ResumeEditorPage onConfirm={confirmResume} active={view==='resume'}/></div>
        {view==='jd'&&(
          <>
            <header className="page-intro analysis-intro">
              <div><p className="eyebrow">新建分析 · 第 2 步 / 共 3 步</p><h1>对照目标岗位</h1><p className="muted">同一份 JD 同时用于岗位匹配和 STAR 定向建议，两项功能互不影响。</p></div>
              <span className="draft-ready">✓ 已确认 {draft?.parsed.skills.length ?? 0} 项技能</span>
            </header>
            <div className="analysis-workspace">
              <form className="panel match-form" onSubmit={submitMatch} noValidate>
                <div className="section-heading"><div><span className="feature-number">01</span><h2>岗位匹配</h2><p className="muted small">生成分数、技能差距和原文证据，并自动保存。</p></div></div>
                {!draft&&<p className="field-error" role="alert">当前标签页还没有已确认简历，请返回新建分析。</p>}
                <label className="field" htmlFor="job-title"><span className="field-label">岗位名称 <span className="muted">（可选）</span></span><input aria-label="岗位名称（可选）" disabled={matching} id="job-title" value={jobTitle} onChange={e=>setJobTitle(e.target.value)} maxLength={200} placeholder="例如：Python 后端实习生"/></label>
                <label className="field" htmlFor="jd-text"><span className="field-label">岗位 JD <span className="required">*</span></span><textarea aria-label="岗位 JD" disabled={matching||starBusy} id="jd-text" value={jdText} onChange={e=>setJdText(e.target.value)} rows={11} required placeholder="粘贴岗位职责、任职要求与加分项…"/><span className="field-help">请保留原始换行，便于证据定位。</span></label>
                {error&&<p className="field-error" role="alert">{error}</p>}
                <div className="actions match-actions"><button type="button" disabled={matching} className="button secondary" onClick={()=>navigate('/analysis/new')}><span aria-hidden="true">←</span> 返回修改简历</button><button type="submit" className="button primary" disabled={matching||!draft}>{matching?'分析并保存中…':error?'重试匹配':'开始匹配'}</button></div>
                <p className="form-footnote"><span aria-hidden="true">ⓘ</span>超时可能已经保存；主动重试前请先查看历史记录。</p>
              </form>
              <section className="panel star-panel">
                <div className="section-heading"><div><span className="feature-number">02</span><h2>STAR 定向优化</h2><p className="muted small">整理表达结构，不会改写或覆盖你的简历原文。</p></div><span className="rule-badge">规则版</span></div>
                <label className="field" htmlFor="experience"><span className="field-label">待优化经历</span><textarea aria-label="待优化经历" disabled={starBusy} id="experience" value={experience} onChange={e=>setExperience(e.target.value)} rows={8} placeholder="粘贴一段真实项目或实习经历…"/><span className="field-help">建议稿不会自动保存，请核实事实和数字。</span></label>
                <button type="button" className="button secondary star-action" disabled={starBusy} onClick={generateStar}>{starBusy?'生成中…':'生成优化建议'}</button>
                {starError&&<p role="alert" className="field-error">{starError}</p>}
                {star&&<div className="star-result"><p className="disclaimer">{star.notice}</p><div className="compare-grid"><div><h3>原始描述</h3><p>{star.original}</p></div><div className="suggested-copy"><h3>STAR 建议稿</h3><p>{star.optimized_draft}</p></div></div><div className="star-meta"><p><strong>建议强化关键词</strong><span>{star.jd_keywords.join('、')||'未识别'}</span></p><p><strong>建议核实的量化项</strong><span>{star.metric_prompts.join('、')}</span></p></div><p className="source-note">来源：{star.source==='llm'?'兼容模型':'本地规则回退'}</p></div>}
              </section>
            </div>
          </>
        )}
        {view==='result'&&<ResultPage result={result} state={busy?'loading':error?'error':result?'normal':'empty'} notFound={notFound} onRetry={()=>setRetry(value=>value+1)} onBack={()=>navigate('/history')} onReanalyze={()=>navigate('/analysis/new')}/>} 
        {view==='history'&&<HistoryPage items={history} state={busy?'loading':error?'error':history.length?'normal':'empty'} onOpen={id=>navigate('/results/'+id)} onNewAnalysis={()=>navigate('/analysis/new')} onRetry={()=>setRetry(value=>value+1)}/>} 
      </main>
      <footer className="page-footer"><span className="footer-mark">JD</span><span>匹配分用于辅助判断，不代表录用概率</span></footer>
    </>
  );
}
