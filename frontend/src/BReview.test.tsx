import { act, cleanup, fireEvent, render, screen, waitFor } from '@testing-library/react';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import App from './App';

const firstId = '123e4567-e89b-42d3-a456-426614174001';
const secondId = '123e4567-e89b-42d3-a456-426614174002';
const response = (body: unknown, status = 200) => new Response(JSON.stringify(body), { status });
const record = (id: string, score = 0) => ({ id, score, job_title: id, matched_skills: [], missing_skills: [], suggestions: [], evidence_items: [], algorithm_version: 'rule-v1' });

describe('B independent route and recovery regression checks', () => {
  beforeEach(() => { history.replaceState(null, '', '/#/'); vi.restoreAllMocks(); });
  afterEach(() => { cleanup(); vi.restoreAllMocks(); });

  it('actually refetches history when retry is clicked', async () => {
    const fetchMock = vi.spyOn(globalThis, 'fetch')
      .mockResolvedValueOnce(response({ error: { message: '服务失败' } }, 503))
      .mockResolvedValue(response({ items: [], total: 0 }));
    history.replaceState(null, '', '/#/history'); render(<App />);
    fireEvent.click(await screen.findByRole('button', { name: '重新加载' }));
    expect(await screen.findByText('还没有分析记录')).toBeInTheDocument();
    expect(fetchMock).toHaveBeenCalledTimes(2);
  });

  it('actually refetches detail after a recoverable error', async () => {
    const fetchMock = vi.spyOn(globalThis, 'fetch')
      .mockResolvedValueOnce(response({ error: { message: '服务失败' } }, 503))
      .mockResolvedValue(response(record(firstId)));
    history.replaceState(null, '', '/#/results/' + firstId); render(<App />);
    fireEvent.click(await screen.findByRole('button', { name: '重试' }));
    expect(await screen.findByLabelText('匹配分 0')).toBeInTheDocument();
    expect(fetchMock).toHaveBeenCalledTimes(2);
  });

  it('ignores an older detail response after navigating to another UUID', async () => {
    let finishFirst!: (value: Response) => void;
    vi.spyOn(globalThis, 'fetch').mockImplementation(url => String(url).endsWith(firstId)
      ? new Promise(resolve => { finishFirst = resolve; }) : Promise.resolve(response(record(secondId, 80))));
    history.replaceState(null, '', '/#/results/' + firstId); render(<App />);
    await waitFor(() => expect(finishFirst).toBeDefined());
    act(() => { history.replaceState(null, '', '/#/results/' + secondId); dispatchEvent(new HashChangeEvent('hashchange')); });
    expect(await screen.findByLabelText('匹配分 80')).toBeInTheDocument();
    await act(async () => { finishFirst(response(record(firstId, 10))); });
    expect(screen.queryByLabelText('匹配分 10')).not.toBeInTheDocument();
    expect(screen.getByLabelText('匹配分 80')).toBeInTheDocument();
  });

  it('renders malformed percent encoding as not-found without crashing', async () => {
    const fetchMock = vi.spyOn(globalThis, 'fetch');
    history.replaceState(null, '', '/#/results/%E0%A4%A'); render(<App />);
    expect(await screen.findByText('这条分析记录不存在')).toBeInTheDocument();
    expect(fetchMock).not.toHaveBeenCalled();
  });

  it('distinguishes a missing score from zero', async () => {
    vi.spyOn(globalThis, 'fetch').mockResolvedValue(response({ id: firstId }));
    history.replaceState(null, '', '/#/results/' + firstId); render(<App />);
    expect(await screen.findByLabelText('匹配分 暂无评分')).toBeInTheDocument();
    expect(screen.queryByLabelText('匹配分 0')).not.toBeInTheDocument();
    expect(screen.getByText('当前记录没有可定位的原文证据。')).toBeInTheDocument();
  });
});
