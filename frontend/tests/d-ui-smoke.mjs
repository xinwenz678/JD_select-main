// Real browser smoke for the integrated MVP flow. Requires running backend + Vite.
import assert from 'node:assert/strict';
import { createRequire } from 'node:module';
import { mkdir, writeFile } from 'node:fs/promises';
import { fileURLToPath } from 'node:url';
import path from 'node:path';

const require = createRequire(import.meta.url);
const { chromium } = require(process.env.PLAYWRIGHT_MODULE_PATH || 'playwright');
const base = process.env.PREVIEW_URL || 'http://127.0.0.1:5173';
const output = path.join(path.dirname(fileURLToPath(import.meta.url)), 'artifacts');
await mkdir(output, { recursive: true });

const browser = await chromium.launch({ channel: 'msedge', headless: true });
const context = await browser.newContext({ viewport: { width: 1440, height: 1000 }, timezoneId: 'Asia/Shanghai' });
const page = await context.newPage();
const checks = [];
const pageErrors = [];
const apiRequests = [];
const apiResponses = [];
page.on('pageerror', (error) => pageErrors.push(error.message));
page.on('request', (request) => {
  const url = new URL(request.url());
  if (url.pathname.startsWith('/api/')) apiRequests.push({ method: request.method(), path: url.pathname });
});
page.on('response', (response) => {
  const url = new URL(response.url());
  if (url.pathname.startsWith('/api/')) apiResponses.push({ method: response.request().method(), path: url.pathname, status: response.status() });
});

async function visible(locator) { await locator.waitFor({ state: 'visible', timeout: 10000 }); }
async function noOverflow(label) {
  const dimensions = await page.evaluate(() => ({ width: innerWidth, scroll: document.documentElement.scrollWidth }));
  assert.ok(dimensions.scroll <= dimensions.width + 1, label + ': horizontal overflow ' + JSON.stringify(dimensions));
}
async function parseAndConfirmResume() {
  await page.getByRole('button', { name: '开始新建分析', exact: true }).click();
  await visible(page.getByRole('heading', { name: '录入并解析简历', exact: true }));
  assert.ok(await page.getByRole('button', { name: '解析简历', exact: true }).isDisabled());
  await page.getByRole('button', { name: '良好示例', exact: true }).click();
  const parseResponse = page.waitForResponse((response) => response.url().endsWith('/api/resumes/parse') && response.request().method() === 'POST');
  await page.getByRole('button', { name: '解析简历', exact: true }).click();
  assert.equal((await parseResponse).status(), 200);
  await visible(page.getByRole('heading', { name: '解析结果', exact: true }));
  await visible(page.getByText('Python', { exact: true }).first());
  const diagnoseResponse = page.waitForResponse((response) => response.url().endsWith('/api/resumes/diagnose') && response.request().method() === 'POST');
  await page.getByRole('button', { name: '运行诊断', exact: true }).click();
  assert.equal((await diagnoseResponse).status(), 200);
  await visible(page.getByRole('button', { name: '重新诊断', exact: true }));
  await page.getByRole('button', { name: '确认简历信息，进入岗位匹配 →', exact: true }).click();
  await visible(page.getByRole('heading', { name: '对照目标岗位', exact: true }));
}

try {
  await page.goto(base, { waitUntil: 'networkidle' });
  await visible(page.getByRole('heading', { name: /让简历与岗位要求/ }));
  await parseAndConfirmResume();
  checks.push('Resume: real parse and diagnose APIs, editable result, confirmation and JD transition');

  const title = 'UI Smoke Python 后端工程师';
  const jd = ['Python 后端工程师', '必须掌握 Python、FastAPI、SQL、Kubernetes', '熟悉 Docker 可加分'].join('\n');
  await page.getByLabel('岗位名称（可选）', { exact: true }).fill(title);
  await page.getByLabel('岗位 JD', { exact: true }).fill(jd);

  await page.route('**/api/matches', (route) => route.fulfill({ status: 503, contentType: 'application/json', body: '{"detail":"smoke 模拟服务暂不可用"}' }));
  await page.getByRole('button', { name: /^(开始匹配|重试匹配)$/ }).click();
  await visible(page.getByText('smoke 模拟服务暂不可用', { exact: true }));
  assert.equal(await page.getByLabel('岗位 JD', { exact: true }).inputValue(), jd);
  await page.unroute('**/api/matches');
  checks.push('Match failure: readable server error and retained JD input');

  const matchResponsePromise = page.waitForResponse((response) => response.url().endsWith('/api/matches') && response.request().method() === 'POST' && response.status() === 200);
  matchResponsePromise.catch(() => {});
  await page.getByRole('button', { name: /^(开始匹配|重试匹配)$/ }).click();
  const matchResponse = await matchResponsePromise;
  const match = await matchResponse.json();
  assert.ok(match.id);
  assert.ok(match.score >= 0 && match.score <= 100);
  assert.ok(match.evidence_items.length >= 4);
  assert.ok(match.evidence_items.some((item) => item.source === 'resume' && item.label === 'Python' && item.line === 11));
  assert.ok(match.evidence_items.some((item) => item.source === 'jd' && item.label === 'Kubernetes' && item.line === 2));
  await visible(page.getByRole('heading', { name: title, exact: true }));
  await visible(page.getByRole('heading', { name: '评分依据 / 原文证据', exact: true }));
  await visible(page.getByText('简历原文', { exact: true }).first());
  await visible(page.getByText('岗位 JD', { exact: true }).first());
  await visible(page.getByText('第 11 行', { exact: true }).first());
  await visible(page.getByText('负责订单模块接口开发与联调，使用 Python/FastAPI', { exact: false }).first());
  await page.screenshot({ path: path.join(output, 'real-result-desktop.png'), fullPage: true });
  checks.push('Result: real score, saved id, matched/missing skills and line-addressable resume/JD evidence');

  const listPromise = page.waitForResponse((response) => response.url().includes('/api/matches?limit=10') && response.status() === 200);
  await page.getByRole('button', { name: '历史记录', exact: true }).click();
  await listPromise;
  const row = page.locator('.history-row').filter({ hasText: match.id });
  await visible(row);
  const detailPromise = page.waitForResponse((response) => response.url().endsWith('/api/matches/' + match.id) && response.status() === 200);
  await row.getByRole('button', { name: '查看' + title + '详情', exact: true }).click();
  await detailPromise;
  await visible(page.getByRole('heading', { name: title, exact: true }));
  await visible(page.getByText('第 11 行', { exact: true }).first());
  checks.push('History: newly saved record appears in recent list and detail preserves evidence');

  for (const width of [390, 320]) {
    await page.setViewportSize({ width, height: 900 });
    await noOverflow(width + 'px result');
  }
  await page.screenshot({ path: path.join(output, 'real-result-mobile.png'), fullPage: true });
  checks.push('Responsive: evidence result has no horizontal overflow at 390px and 320px');

  assert.deepEqual(pageErrors, []);
  assert.ok(apiRequests.some((item) => item.path === '/api/resumes/parse'));
  assert.ok(apiRequests.some((item) => item.path === '/api/resumes/diagnose'));
  assert.ok(apiRequests.some((item) => item.path === '/api/matches' && item.method === 'POST'));
  const report = {
    status: 'passed',
    scope: 'integrated MVP real browser flow',
    browser: await browser.version(),
    recordId: match.id,
    score: match.score,
    evidenceCount: match.evidence_items.length,
    checks,
    pageErrors,
    apiRequests,
    apiResponses,
  };
  await writeFile(path.join(output, 'report.json'), JSON.stringify(report, null, 2) + '\n');
  console.log(JSON.stringify(report, null, 2));
} finally {
  await browser.close();
}
