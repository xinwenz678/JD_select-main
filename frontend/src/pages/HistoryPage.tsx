import { StatePanel } from '../components/StatePanel';
import { displayScore, displayTitle } from '../types';
import type { HistoryDisplayItem, PreviewState } from '../types';

interface HistoryPageProps {
  items: readonly HistoryDisplayItem[];
  state: PreviewState;
  onOpen: (id: string) => void;
  onNewAnalysis: () => void;
  onRetry: () => void;
}

export function displayTime(value: string | null | undefined): string {
  if (!value) return '时间暂未提供';
  const date = new Date(value);
  return Number.isNaN(date.getTime()) ? '时间暂未提供' : new Intl.DateTimeFormat('zh-CN', {
    year: 'numeric', month: '2-digit', day: '2-digit', hour: '2-digit', minute: '2-digit', hour12: false,
  }).format(date);
}

export function HistoryPage({ items, state, onOpen, onNewAnalysis, onRetry }: HistoryPageProps) {
  if (state === 'loading') return <StatePanel kind="loading" title="正在加载历史记录…" description="正在读取服务端保存的分析记录。" />;
  if (state === 'error') return <StatePanel kind="error" title="历史记录加载失败" description="请检查后端连接后重试。" actions={<button className="button primary" onClick={onRetry}>重新加载</button>} />;
  if (state === 'empty' || items.length === 0) return <StatePanel kind="empty" title="还没有分析记录" description="完成一次分析后，可在这里回顾岗位匹配情况。完成的分析会自动保存在这里。" actions={<button className="button primary" onClick={onNewAnalysis}>新建分析</button>} />;

  const recent = items.slice(0, 10);
  return (
    <section className="panel history-panel" aria-labelledby="recent-heading">
      <div className="section-heading history-heading"><div><h2 id="recent-heading">最近分析 <span className="count">{recent.length} 条</span></h2><p className="muted small">最多展示最近 10 条 · 时间按浏览器本地时区显示</p></div><button className="button primary" onClick={onNewAnalysis}>新建分析 <span aria-hidden="true">＋</span></button></div>
      <div className="history-columns" aria-hidden="true"><span>岗位名称</span><span>匹配分</span><span>创建时间</span><span>操作</span></div>
      <ul className="history-list">
        {recent.map((item) => (
          <li className="history-row" key={item.id}>
            <div className="history-job"><strong>{displayTitle(item.job_title)}</strong><span className="muted small">{item.id}</span></div>
            <div className="history-score"><span className="mobile-label">匹配分</span><strong>{displayScore(item.score)}</strong>{displayScore(item.score) !== '暂无评分' && <span className="muted small"> / 100</span>}</div>
            <div className="history-time"><span className="mobile-label">创建时间</span><time dateTime={item.created_at && !Number.isNaN(Date.parse(item.created_at)) ? item.created_at : undefined}>{displayTime(item.created_at)}</time></div>
            <button className="detail-link" onClick={() => onOpen(item.id)} aria-label={`查看${displayTitle(item.job_title)}详情`}>查看详情 <span aria-hidden="true">↗</span></button>
          </li>
        ))}
      </ul>
      <p className="history-footnote muted small">显示服务端最近保存的分析记录。</p>
    </section>
  );
}
