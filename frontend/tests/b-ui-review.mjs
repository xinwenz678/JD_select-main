// Run only against the isolated services owned by scripts/b-review.py.
import assert from 'node:assert/strict';
import { createRequire } from 'node:module';
import { mkdir, readFile, writeFile } from 'node:fs/promises';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const require = createRequire(import.meta.url);
const { chromium } = require(process.env.PLAYWRIGHT_MODULE_PATH || 'playwright');
const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '../..');
const output = path.resolve(root, process.env.B_REVIEW_EVIDENCE || 'docs/evidence/b-candidate');
const base = process.env.PREVIEW_URL;
assert.ok(base && process.env.B_REVIEW_ISOLATED === '1', 'Use scripts/b-review.py; do not write synthetic records into the user database.');
const data = JSON.parse(await readFile(path.join(root, 'sample_data/acceptance/cases.json'), 'utf8'));
await mkdir(output, { recursive: true });
const browser = await chromium.launch({ channel: 'msedge', headless: true });
const checks = [];
const errors = [];
const consoleErrors = [];
let current;

async function check(id, title, action) {
  const context = await browser.newContext({ viewport: { width: 1440, height: 1000 }, timezoneId: 'Asia/Shanghai' });
  const page = await context.newPage();
  page.setDefaultTimeout(15000);
  page.on('pageerror', error => errors.push({ id, message: error.message }));
  page.on('console', message => { if (message.type() === 'error') consoleErrors.push({ id, message: message.text(), path: message.location().url ? new URL(message.location().url).pathname : '', expected: ['UI04', 'UI06', 'UI07', 'RECOVERY', 'TIMEOUT'].includes(id) && /Failed to load resource|net::ERR_FAILED/.test(message.text()) }); });
  current = page;
  try {
    await page.goto(base);
    const detail = await action(page);
    checks.push({ id, title, status: 'passed', detail });
  } catch (error) {
    await page.screenshot({ path: path.join(output, `${id}.png`), fullPage: true }).catch(() => {});
    checks.push({ id, title, status: 'failed', detail: String(error.message).split('\n').slice(0, 6).join('\n') });
  } finally { await context.close(); }
}

async function parse(page, text) {
  await page.getByRole('button', { name: '开始新建分析', exact: true }).click();
  await page.getByLabel('简历原文', { exact: true }).fill(text);
  await page.getByRole('button', { name: '解析简历', exact: true }).click();
  await page.getByRole('heading', { name: '解析结果', exact: true }).waitFor();
}
async function confirm(page, jd = data.cases[0].jd_text, title = '合成验收岗位') {
  await page.getByRole('button', { name: '确认简历信息，进入岗位匹配 →', exact: true }).click();
  await page.getByLabel('岗位 JD', { exact: true }).fill(jd);
  await page.getByLabel('岗位名称（可选）', { exact: true }).fill(title);
}
async function submit(page, double = false) {
  const pending = page.waitForResponse(response => new URL(response.url()).pathname === '/api/matches' && response.request().method() === 'POST');
  pending.catch(() => {}); // A failed earlier assertion must not crash the remaining suite.
  const button = page.getByRole('button', { name: /^(开始匹配|重试匹配)$/ });
  if (double) await button.evaluate(button => { button.click(); button.click(); });
  else await button.click();
  const response = await pending;
  assert.equal(response.status(), 200);
  const result = await response.json();
  await page.getByLabel(`匹配分 ${result.score}`, { exact: true }).waitFor();
  return result;
}

try {
  await check('UI01', '空历史可恢复', async page => {
    await page.screenshot({ path: path.join(output, 'home-desktop.png'), fullPage: true });
    await page.setViewportSize({ width: 390, height: 900 });
    assert.ok(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth + 1));
    await page.screenshot({ path: path.join(output, 'home-mobile.png'), fullPage: true });
    await page.setViewportSize({ width: 1440, height: 1000 });
    await page.getByRole('button', { name: '历史记录', exact: true }).click();
    await page.getByRole('heading', { name: '还没有分析记录', exact: true }).waitFor();
  });
  for (const index of [0, 1, 2, 4]) {
    const scenario = data.cases[index];
    await check(`UI-${scenario.id}`, `${scenario.name}实际 API 结果与页面一致（算法另验）`, async page => {
      await parse(page, scenario.variants[0].resume_text);
      await confirm(page, scenario.jd_text, scenario.job_title);
      const result = await submit(page);
      await page.getByRole('heading', { name: '评分依据 / 原文证据', exact: true }).waitFor();
      await page.screenshot({ path: path.join(output, `${scenario.id}-result.png`), fullPage: true });
      await page.getByRole('button', { name: '历史记录', exact: true }).click();
      const row = page.locator('.history-row').filter({ hasText: result.id });
      await row.waitFor();
      await row.getByRole('button').click();
      await page.getByLabel(`匹配分 ${result.score}`, { exact: true }).waitFor();
      return { uuid: result.id, score: result.score, matched: result.matched_skills, missing: result.missing_skills, evidenceCount: result.evidence_items.length };
    });
  }
  await check('UI02', '空输入拦截与字段焦点', async page => {
    await page.getByRole('button', { name: '开始新建分析', exact: true }).click();
    assert.ok(await page.getByRole('button', { name: '解析简历', exact: true }).isDisabled());
    await page.getByLabel('简历原文', { exact: true }).fill(data.cases[0].variants[0].resume_text);
    await page.getByRole('button', { name: '解析简历', exact: true }).click();
    await confirm(page, ' \n ');
    let posts = 0;
    page.on('request', req => { if (new URL(req.url()).pathname === '/api/matches' && req.method() === 'POST') posts++; });
    await page.getByRole('button', { name: '开始匹配', exact: true }).click();
    await page.getByRole('alert').waitFor();
    assert.equal(await page.evaluate(() => document.activeElement.id), 'jd-text');
    assert.equal(posts, 0);
  });
  await check('UI03', '同步双击只产生一个 POST 和一条记录', async page => {
    await parse(page, data.cases[0].variants[0].resume_text);
    await confirm(page);
    let posts = 0;
    const before = await (await page.request.get(`${base}/api/matches`)).json();
    await page.route('**/api/matches', async route => { posts++; await new Promise(resolve => setTimeout(resolve, 300)); await route.continue(); });
    const pending = submit(page, true);
    pending.catch(() => {});
    await page.getByRole('button', { name: '分析并保存中…', exact: true }).waitFor();
    assert.ok(await page.getByLabel('岗位 JD', { exact: true }).isDisabled());
    assert.ok(await page.getByRole('button', { name: '历史记录', exact: true }).isDisabled());
    await pending;
    const after = await (await page.request.get(`${base}/api/matches`)).json();
    assert.equal(posts, 1);
    assert.equal(after.total - before.total, 1);
  });
  await check('UI04', '平台统一 503 错误可读、草稿保留、真实重试成功', async page => {
    await parse(page, data.cases[1].variants[0].resume_text);
    await page.getByLabel('姓名', { exact: true }).fill('合成已确认姓名');
    await confirm(page, data.cases[1].jd_text, '合成保留岗位');
    await page.route('**/api/matches', route => route.fulfill({ status: 503, contentType: 'application/json', body: JSON.stringify({ error: { code: 'DATABASE_ERROR', message: '数据库暂不可用，请稍后重试', details: [] } }) }));
    await page.getByRole('button', { name: '开始匹配', exact: true }).click();
    await page.getByRole('alert').filter({ hasText: '数据库暂不可用' }).waitFor();
    assert.equal(await page.getByLabel('岗位 JD', { exact: true }).inputValue(), data.cases[1].jd_text);
    await page.getByRole('button', { name: '返回修改简历', exact: true }).click();
    assert.equal(await page.getByLabel('姓名', { exact: true }).inputValue(), '合成已确认姓名');
    assert.equal(await page.getByLabel('简历原文', { exact: true }).inputValue(), data.cases[1].variants[0].resume_text);
    await confirm(page);
    await page.unroute('**/api/matches');
    await submit(page);
  });
  await check('UI05', '修改原文后旧解析结果失效', async page => {
    await parse(page, data.cases[0].variants[0].resume_text);
    await page.getByLabel('简历原文', { exact: true }).fill('完全不同的合成简历');
    assert.equal(await page.getByRole('heading', { name: '解析结果', exact: true }).count(), 0);
    assert.equal(await page.getByRole('button', { name: '确认简历信息，进入岗位匹配 →', exact: true }).count(), 0);
  });
  await check('UI06', '详情 404 不显示旧分数且能恢复', async page => {
    await page.getByRole('button', { name: '历史记录', exact: true }).click();
    await page.locator('.history-row').first().waitFor();
    await page.route('**/api/matches/*', route => route.fulfill({ status: 404, contentType: 'application/json', body: JSON.stringify({ error: { code: 'NOT_FOUND', message: '记录不存在', details: [] } }) }));
    await page.locator('.history-row').first().getByRole('button').click();
    await page.getByRole('heading', { name: '这条分析记录不存在', exact: true }).waitFor();
    assert.equal(await page.locator('.score-value').count(), 0);
    await page.getByRole('button', { name: '返回历史记录', exact: true }).click();
    await page.locator('.history-list').waitFor();
  });
  await check('UI07', '网络错误可读并解除在途锁', async page => {
    await parse(page, data.cases[1].variants[0].resume_text); await confirm(page);
    await page.route('**/api/matches', route => route.abort('failed'));
    await page.getByRole('button', { name: '开始匹配', exact: true }).click();
    await page.getByRole('alert').filter({ hasText: '无法连接' }).waitFor();
    assert.ok(await page.getByRole('button', { name: '重试匹配', exact: true }).isEnabled());
  });
  await check('UI08', '320/390/720/1440 窗口、长岗位名称可读', async page => {
    await parse(page, data.cases[0].variants[0].resume_text); await confirm(page, data.cases[0].jd_text, '合成超长岗位'.repeat(15));
    await submit(page);
    for (const width of [1440, 1024, 768, 720, 390, 320]) {
      await page.setViewportSize({ width, height: 900 });
      const size = await page.evaluate(() => ({ scroll: document.documentElement.scrollWidth, width: innerWidth }));
      assert.ok(size.scroll <= size.width + 1, `${width}px result overflow`);
    }
    await page.screenshot({ path: path.join(output, 'result-mobile.png'), fullPage: true });
    await page.getByRole('button', { name: '历史记录', exact: true }).click();
    await page.locator('.history-list').waitFor();
    assert.ok(await page.locator('.history-job strong').first().evaluate(e => getComputedStyle(e).whiteSpace !== 'nowrap'));
    await page.screenshot({ path: path.join(output, 'history-mobile.png'), fullPage: true });
  });
  await check('A13', '删除已确认 Python 后匹配不再命中 Python', async page => {
    await parse(page, '合成学生\n技能\nPython\nSQL');
    await page.getByRole('button', { name: '移除 Python', exact: true }).click();
    await confirm(page, '必须掌握 Python。\n必须掌握 SQL。');
    const result = await submit(page);
    assert.ok(!result.matched_skills.includes('Python'), 'A13 unresolved: edited skills are still ignored by matching');
  });
  await check('A15', '结果 URL 含服务端 UUID，刷新保留同一结果', async page => {
    await parse(page, data.cases[1].variants[0].resume_text); await confirm(page);
    const result = await submit(page);
    const stableUrl = page.url().includes(result.id);
    await page.reload();
    await page.getByLabel(`匹配分 ${result.score}`, { exact: true }).waitFor();
    const sameResult = await page.getByLabel(`匹配分 ${result.score}`, { exact: true }).isVisible();
    assert.ok(stableUrl && sameResult, `stableUrl=${stableUrl}, sameResultAfterRefresh=${sameResult}`);
    const copy = await page.context().newPage();
    await copy.goto(page.url());
    await copy.getByLabel(`匹配分 ${result.score}`, { exact: true }).waitFor();
    assert.ok((await copy.locator('.result-meta').innerText()).includes(result.id));
    await copy.close();
    await page.getByRole('button', { name: '历史记录', exact: true }).click();
    await page.locator('.history-list').waitFor();
    await page.goBack();
    await page.getByLabel(`匹配分 ${result.score}`, { exact: true }).waitFor();
    await page.goForward();
    await page.locator('.history-list').waitFor();
  });
  await check('STAR', '真实规则 STAR 不覆盖原文，编辑后不残留旧建议', async page => {
    await parse(page, data.cases[0].variants[0].resume_text); await confirm(page);
    const original = '参与课程报名系统，负责接口测试。';
    await page.getByLabel('待优化经历', { exact: true }).fill(original);
    const response = page.waitForResponse(r => r.url().endsWith('/api/suggestions/star') && r.request().method() === 'POST');
    await page.getByRole('button', { name: '生成优化建议', exact: true }).click();
    const actual = await (await response).json();
    await page.getByRole('heading', { name: 'STAR 建议稿', exact: true }).waitFor();
    assert.equal(actual.source, 'rule-fallback');
    assert.equal(await page.getByLabel('待优化经历', { exact: true }).inputValue(), original);
    assert.equal(actual.original, original);
    assert.equal((await (await page.request.get(`${base}/api/matches`)).json()).items.some(item => item.id === actual.id), false);
    await page.screenshot({ path: path.join(output, 'star-comparison.png'), fullPage: true });
    await page.getByLabel('待优化经历', { exact: true }).fill('另一个合成经历');
    assert.equal(await page.locator('.star-result').count(), 0);
    await submit(page);
    return { source: actual.source, original: actual.original, keywords: actual.jd_keywords };
  });
  await check('RECOVERY', '历史与详情错误都能实际重新请求', async page => {
    let fail = true;
    await page.route('**/api/matches?*', route => fail ? route.fulfill({ status: 503, json: { error: { message: '服务暂不可用' } } }) : route.continue());
    await page.getByRole('button', { name: '历史记录', exact: true }).click();
    await page.getByRole('button', { name: '重新加载', exact: true }).waitFor();
    fail = false;
    await page.getByRole('button', { name: '重新加载', exact: true }).click();
    await page.locator('.history-list').waitFor();
    let detailFail = true;
    await page.route('**/api/matches/*', route => detailFail ? route.fulfill({ status: 503, json: { error: { message: '服务暂不可用' } } }) : route.continue());
    await page.locator('.history-row').first().getByRole('button').click();
    await page.getByRole('button', { name: '重试', exact: true }).waitFor();
    detailFail = false;
    await page.getByRole('button', { name: '重试', exact: true }).click();
    await page.locator('.score-value').waitFor();
  });
  await check('KEYBOARD', '键盘入口与表单操作可用', async page => {
    const start = page.getByRole('button', { name: '开始新建分析', exact: true });
    await start.focus(); await page.keyboard.press('Enter');
    await page.getByLabel('简历原文', { exact: true }).fill(data.cases[0].variants[0].resume_text);
    await page.getByRole('button', { name: '解析简历', exact: true }).focus(); await page.keyboard.press('Enter');
    await page.getByRole('heading', { name: '解析结果', exact: true }).waitFor();
    await page.getByRole('button', { name: '确认简历信息，进入岗位匹配 →', exact: true }).focus(); await page.keyboard.press('Enter');
    await page.getByLabel('岗位 JD', { exact: true }).fill(data.cases[0].jd_text);
    const match = page.getByRole('button', { name: '开始匹配', exact: true });
    await match.focus();
    assert.notEqual(await match.evaluate(e => getComputedStyle(e).outlineStyle), 'none');
    await page.keyboard.press('Enter');
    await page.locator('.score-value').waitFor();
  });
} finally {
  const report = { status: checks.some(c => c.status === 'failed') || errors.length || consoleErrors.some(e => !e.expected) ? 'failed' : 'passed', scope: 'B candidate review, isolated real backend; algorithm correctness checked separately', browser: browser.version(), checks, pageErrors: errors, consoleErrors };
  await writeFile(path.join(output, 'ui-report.json'), JSON.stringify(report, null, 2) + '\n');
  console.log(JSON.stringify({ status: report.status, passed: checks.filter(c => c.status === 'passed').length, failed: checks.filter(c => c.status === 'failed').map(c => ({ id: c.id, detail: c.detail })), pageErrors: errors }, null, 2));
  process.exitCode = report.status === 'passed' ? 0 : 1;
  await browser.close();
}
