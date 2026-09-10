import { afterEach, expect, it, vi } from 'vitest';
import { createMatch } from './services/api';

afterEach(() => { vi.restoreAllMocks(); vi.useRealTimers(); });

it('aborts a stalled request after 30 seconds and explains uncertain saving', async () => {
  vi.useFakeTimers();
  vi.spyOn(globalThis, 'fetch').mockImplementation((_url, init) => new Promise((_resolve, reject) => {
    init?.signal?.addEventListener('abort', () => reject(new DOMException('aborted', 'AbortError')));
  }));
  const request = createMatch('合成简历', 'Python');
  const assertion = expect(request).rejects.toThrow('请先查看历史记录');
  await vi.advanceTimersByTimeAsync(30_000);
  await assertion;
  expect(vi.getTimerCount()).toBe(0);
});

it('turns network failures into a readable recoverable message', async () => {
  vi.spyOn(globalThis, 'fetch').mockRejectedValue(new TypeError('Failed to fetch'));
  await expect(createMatch('合成简历', 'Python')).rejects.toThrow('无法连接服务');
});

it('preserves platform errors and confirmed skills in the request', async () => {
  const fetchMock = vi.spyOn(globalThis, 'fetch').mockResolvedValue(new Response(JSON.stringify({ error: { message: '数据库暂不可用' } }), { status: 503 }));
  await expect(createMatch('合成简历', 'Python', '岗位', ['SQL'])).rejects.toThrow('数据库暂不可用');
  expect(JSON.parse(fetchMock.mock.calls[0][1]?.body as string).confirmed_skills).toEqual(['SQL']);
});
