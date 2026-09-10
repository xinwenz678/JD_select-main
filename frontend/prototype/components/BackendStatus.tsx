import { useRef, useState } from 'react';
import { getHealth } from '../services/api';

// Retains the original app's only real request. No business API calls are added.
export function BackendStatus() {
  const [status, setStatus] = useState('后端连接尚未检查');
  const [loading, setLoading] = useState(false);
  const busy = useRef(false);

  async function checkBackend() {
    if (busy.current) return;
    busy.current = true;
    setLoading(true);
    setStatus('正在检查后端连接…');
    try {
      const result = await getHealth();
      setStatus(`后端状态：${result.status}，版本：${result.version}`);
    } catch {
      setStatus('后端未连接，请启动 FastAPI 后重试。');
    } finally {
      busy.current = false;
      setLoading(false);
    }
  }

  return (
    <section className="backend-status" aria-label="后端连接检查">
      <div><strong>开发环境</strong><p role="status">{status}</p></div>
      <button className="button secondary" onClick={checkBackend} disabled={loading}>{loading ? '检查中…' : '检查后端连接'}</button>
      <p className="backend-caption">连接成功仅代表健康检查可用；解析、匹配和历史保存仍待接入。</p>
    </section>
  );
}
