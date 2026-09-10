import { StatePanel } from '../components/StatePanel';
import { SkillList } from '../components/SkillList';
import { displayScore, displayTitle } from '../types';
import type { EvidenceItem, PreviewState, ResultDisplayData } from '../types';

interface ResultPageProps {
  result?: ResultDisplayData;
  state: PreviewState;
  notFound?: boolean;
  onRetry: () => void;
  onBack: () => void;
  onReanalyze: () => void;
}


const CATEGORY_LABELS: Record<EvidenceItem['category'], string> = {
  matched_skill: '匹配技能',
  required_skill: '岗位要求',
  quantified_result: '量化成果',
  action_verb: '动作动词',
};
function points(value: number | null | undefined): string {
  return typeof value === 'number' && Number.isFinite(value) && value >= 0
    ? `${value} 分`
    : '暂未提供';
}

export function ResultPage({ result, state, notFound, onRetry, onBack, onReanalyze }: ResultPageProps) {
  if (state === 'loading') return <StatePanel kind="loading" title="正在加载匹配结果…" description="请稍候，正在读取服务端记录。" actions={<button className="button secondary" onClick={onBack}>返回历史记录</button>} />;
  if (state === 'error') return <StatePanel kind="error" title="匹配结果加载失败" description="请检查后端连接后重试。" actions={<><button className="button primary" onClick={onRetry}>重试</button><button className="button secondary" onClick={onBack}>返回历史记录</button></>} />;
  if (notFound) return <StatePanel kind="not-found" title="这条分析记录不存在" description="未找到这个 id 对应的分析记录，请从历史记录重新选择。" actions={<><button className="button primary" onClick={onBack}>返回历史记录</button><button className="button secondary" onClick={onReanalyze}>新建分析</button></>} />;
  if (state === 'empty' || !result) return <StatePanel kind="empty" title="暂无匹配结果" description="请先完成一轮简历与岗位匹配。" actions={<button className="button primary" onClick={onReanalyze}>新建分析</button>} />;

  const breakdown = result.score_breakdown;
  return (
    <>
      <section className="result-summary panel" aria-label="结果概览">
        <div className="summary-copy">
          <p className="eyebrow">岗位匹配概览</p>
          <h2 className="job-title">{displayTitle(result.job_title)}</h2>
          <p className="muted">先看技能契合情况，再结合真实经历判断下一步。</p>
          <span className="save-label">分析记录 · 已保存</span>
        </div>
        <div className="score-block">
          <span className="score-caption">匹配分</span>
          <div className="score-value" aria-label={`匹配分 ${displayScore(result.score)}`}>
            <strong>{displayScore(result.score)}</strong>
            {displayScore(result.score) !== '暂无评分' && <span>/ 100</span>}
          </div>
        </div>
      </section>
      <p className="disclaimer"><span aria-hidden="true">ⓘ</span><span>匹配分用于辅助判断，不代表录用概率</span></p>

      <section className="panel" aria-labelledby="breakdown-heading">
        <div className="section-heading"><h2 id="breakdown-heading">分项得分</h2><span className="muted small">了解各维度的得分</span></div>
        <dl className="breakdown-grid">
          <div><dt>必需技能</dt><dd>{points(breakdown?.required_skills)}</dd><span>岗位核心能力的契合情况</span></div>
          <div><dt>加分技能</dt><dd>{points(breakdown?.preferred_skills)}</dd><span>岗位额外要求的契合情况</span></div>
          <div><dt>经历证据质量</dt><dd>{points(breakdown?.evidence_quality)}</dd><span>经历与成果的支撑情况</span></div>
        </dl>
      </section>

      <div className="two-column">
        <SkillList title="匹配技能" skills={result.matched_skills ?? []} tone="matched" emptyText="暂无匹配技能" />
        <SkillList title="缺失技能" skills={result.missing_skills ?? []} tone="missing" emptyText="未发现缺失技能" />
      </div>

      <section className="panel" aria-labelledby="suggestions-heading">
        <div className="section-heading"><h2 id="suggestions-heading">改进建议</h2><span className="muted small">以真实经历为基础</span></div>
        {result.suggestions?.length ? <ol className="suggestions">{result.suggestions.map((suggestion, index) => <li key={`${index}-${suggestion}`}><span className="suggestion-number" aria-hidden="true">{String(index + 1).padStart(2, '0')}</span><span>{suggestion}</span></li>)}</ol> : <p className="muted">暂无改进建议</p>}
      </section>

      <section className="panel evidence" aria-labelledby="evidence-heading">
        <div className="section-heading"><h2 id="evidence-heading">评分依据 / 原文证据</h2><span className="tag-neutral">{result.evidence_items?.length ?? 0} 条</span></div>
        {result.evidence_items?.length ? (
          <ol className="evidence-list">
            {result.evidence_items.map((item, index) => (
              <li key={item.source + '-' + item.category + '-' + item.line + '-' + item.label + '-' + index}>
                <div className="evidence-meta">
                  <span className="evidence-source">{item.source === 'resume' ? '简历原文' : item.source === 'jd' ? '岗位 JD' : '用户确认'}</span>
                  <span>{CATEGORY_LABELS[item.category]}</span><strong>{item.label}</strong><span>{item.line ? ('第 ' + item.line + ' 行') : '无原文行号'}</span>
                </div>
                <blockquote>“{item.text}”</blockquote>
              </li>
            ))}
          </ol>
        ) : <p className="muted">当前记录没有可定位的原文证据。</p>}
      </section>

      <div className="result-meta"><span>算法版本：<strong>{result.algorithm_version?.trim() || '版本信息暂未提供'}</strong></span><span>记录 id：{result.id}</span>{result.confirmed_name?.trim() && <span>候选人：<strong>{result.confirmed_name.trim()}</strong></span>}</div>
      <div className="actions footer-actions"><button className="button secondary" onClick={onBack}>返回历史记录</button><button className="button primary" onClick={onReanalyze}>修改后重新分析 <span aria-hidden="true">→</span></button></div>
    </>
  );
}
