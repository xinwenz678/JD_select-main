import { fireEvent, render, screen } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import App from './App';

vi.mock('./pages/ResumeEditorPage', () => ({
  ResumeEditorPage: ({ onConfirm }: { onConfirm: (draft: unknown) => void }) => <button onClick={() => onConfirm({
    text: 'Python', parsed: { basic: { name: 'Test' }, skills: ['Python'] }, diagnosed: null, confirmedAt: 'now',
  })}>confirm-test-resume</button>,
}));
function response(data: unknown, status = 200) {
  return Promise.resolve(new Response(JSON.stringify(data), { status, headers: { 'Content-Type': 'application/json' } }));
}
describe('App routing and states', () => {
  beforeEach(() => { location.hash = '/'; vi.restoreAllMocks(); });
  it('renders empty history', async () => {
    vi.spyOn(globalThis, 'fetch').mockImplementation(() => response({ items: [], total: 0, limit: 10, offset: 0 }));
    render(<App />); fireEvent.click(screen.getByRole('button', { name: '历史记录' }));
    expect(await screen.findByText('还没有分析记录')).toBeInTheDocument();
  });
  it('renders zero score and confirmed evidence', async () => {
    const id='123e4567-e89b-42d3-a456-426614174000';
    vi.spyOn(globalThis, 'fetch').mockImplementation(() => response({ id, score: 0, matched_skills: [], missing_skills: [], suggestions: [], evidence_items: [{source:'confirmed_resume',category:'matched_skill',label:'SQL',line:null,text:'用户确认'}], algorithm_version:'rule-v1' }));
    location.hash='/results/'+id; render(<App />);
    expect(await screen.findByLabelText('匹配分 0')).toBeInTheDocument();
    expect(screen.getByText('无原文行号')).toBeInTheDocument();
  });
  it('shows invalid UUID as recoverable not-found', async () => {
    vi.spyOn(globalThis, 'fetch');
    location.hash='/results/not-a-uuid'; render(<App />);
    expect(await screen.findByText('这条分析记录不存在')).toBeInTheDocument();
  });
  it('synchronously locks duplicate match submissions', async () => {
    const fetchMock=vi.spyOn(globalThis, 'fetch').mockImplementation(() => new Promise<Response>(() => undefined));
    location.hash='/analysis/new'; render(<App />);
    fireEvent.click(screen.getByText('confirm-test-resume'));
    const jd=await screen.findByLabelText('岗位 JD');
    fireEvent.change(jd,{target:{value:'Python'}});
    const submit=screen.getByRole('button',{name:'开始匹配'});
    fireEvent.click(submit); fireEvent.click(submit);
    expect(fetchMock).toHaveBeenCalledTimes(1);
  });
});