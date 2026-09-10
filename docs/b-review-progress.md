# 成员 B：A 更新版复核与本轮进度（历史复现记录）

> 2026-09-10 后续更新：本文件保留修复前的失败基线。用户已要求 B 直接修复 A 的问题，RC-B01–RC-B07 现已全部关闭；最终结果为后端 110/110、组件 12/12、浏览器 17/17，完整门禁通过。当前结论请以 `b-final-progress.md`、`bug-list.md` 和 `b-handoff.md` 为准。

日期：2026-09-10。对象：用户确认的 JD_select-main 文件夹。结论：**本轮可执行的 B 测试、前端修复和交接已完成；候选暂不签收，未满足全部 B 任务的发布完成定义。**

## 已实际完成

- 建立 A 更新版的 SHA256 源码基线，读取候选说明，核对实际契约、事务、路由、依赖和 STAR；不是照抄 A 的通过数字。
- 按现有锁重新安装前端依赖，补齐后端 pypdf；新增 13 个后端候选检查、8 个独立组件检查，浏览器检查扩展到 17 项。
- 修复历史/详情重试不发请求、旧响应覆盖当前 UUID、非法编码 URL 白屏、返回修改丢草稿、旧解析未失效、空技能不能继续、网络/超时提示、请求中输入/导航、窄屏长标题及 favicon 404。
- 保留 A 的确认技能字段、hash 路由、PDF 上传与规则 STAR；增加 STAR 在编辑输入后清除旧建议，避免误用旧结果。
- 将无正式引用的 4 个旧原型移入 frontend/prototype；修复根 README 再次被样例说明覆盖的问题。
- 重做首页和 JD 工作区的信息层级：首页增加产品价值、三步流程与结果预览；JD/STAR 改为桌面双栏、移动端单栏，清楚区分“自动保存的匹配结果”和“需人工核实的规则建议”。新增品牌标识、状态徽章、焦点样式与移动端布局，并保存桌面/手机截图。
- 新增根目录 `启动项目.cmd`。项目依赖安装完成后可双击启动，浏览器打开 http://127.0.0.1:5173；实际使用同一 `scripts/start.ps1`，方便非开发成员演示。
- 官方 setup 在同机干净源码副本安装成功，耗时 397.28 秒；官方 start -Smoke 通过，退出后 8000/5173 均释放。副本未复制 .venv/node_modules/.env/数据库。
- 形成失败用例、依赖审计、源码差异、真实 UUID/截图和交接清单；没有自动提交、push、merge 或打标签。

## 最终实测

| 检查 | 结果 | 证据（docs/evidence/b-candidate/） |
|---|---|---|
| backend/tests | 86 通过、5 失败 | pytest.json |
| backend/review_tests | 10 通过、5 失败 | candidate-tests.json |
| 后端合计 | 96 通过、10 失败 | 上两份记录；106 个检查 |
| 前端组件 | 12 通过、0 失败 | component-tests.json；A 原有 4 + B 新增 8 |
| B 浏览器业务检查 | 17 通过、0 失败 | ui-report.json |
| 页面异常/非预期 console error | 0 / 0 | ui-report.json；故障注入产生的预期网络错误单列 |
| 既有真实 smoke | 通过 | existing-smoke.json |
| tsc / Vite build / 规则边界 / pip check / 锁校验 | 通过 | summary.json |
| health / docs / OpenAPI | 通过 | api-inventory.json |
| 官方干净安装 / 官方启动冒烟 | 通过 | clean-install.json、official-start.json |
| 官方 verify | 非零，被后端失败断言拦住 | official-verify.json |
| 补充完整门禁 | 非零，后端缺陷未修 | summary.json |
| npm audit | 3 项：moderate 1、high 1、critical 1 | npm-audit.json；开发依赖，未自动升级 |

四个非空主场景 UI 读取真实 API 并按 UUID 查看详情。TC01=91、TC02=50、TC03=1，三者的算法检查因漏 SQL 不通过；TC05 规范写法=80，但别名写法=50。**界面正确显示错误的算法输出，不能算五场景验收通过。** 空输入四个变体及前端拦截通过。真实截图是隔离数据库中的合成输入，服务停止后测试 UUID 不属于用户默认历史。

测试过程还修正了测试工具自身的问题：历史按钮名定位不准确、长参数自动生成超长测试 ID、断言失败后的悬空响应等待。这些不计为产品缺陷。收到版本的 5 项独立组件检查中，3 项复现真实回归，1 项为定位器问题，1 项通过；修正后的断言和产品一起复跑全绿。不能把中间失败截图当作最终状态。

## 尚需 A 修复 / 小组确认

1. P1：并列短技能 SQL/JS 被归一化抹掉分隔符，匹配与缺口漏项。
2. P1：confirmed_skills 的 python/sql 与 Python/SQL 得分不一致。
3. P1：非空但无词典技能的 JD 返回 500，预期可读 400/422。
4. P1：过长 resume_text/jd_text/job_title 返回 500；应在请求边界给出 422，不能走内部异常。
5. 依赖风险：Vitest 3.2.4、@vitest/mocker、Playwright 1.55.0 的审计告警。A 评估并更新锁文件后，B 复验，不运行 audit fix --force。
6. STAR 当前始终 rule-fallback；规则响应和不覆盖原文已验收，未实现真实 LLM 调用，因此没有“有 Key 模型成功/超时回退已通过”的证据。
7. confirmed_name 被接收但未用于保存/恢复；请 A 说明姓名修正的产品语义，不把“发送了字段”写成“已持久化”。
8. 无有效 Git 仓库/候选哈希。只读探测历史 GitHub 地址连接 443 失败，未核验 main/origin/main，也未完成另一台电脑的全新克隆验收。

## B 任务完成度与计划对照

继续按用户原先指定的新计划 B13–B18 记录；本地 docs/remaining-work-plan.md 仍是 B7–B12 的另一版分工，已映射同类工作，未擅自将两版分数相加。

| 任务 | 当前状态 |
|---|---|
| B13 基线/矩阵（4 点） | 本地复核完成，需求、失败用例、Bug、负责人可追踪 |
| B14 固定数据（4 点） | 完成；五场景、证据、STAR 人工基准保留，待 A 确认修复后的预期 |
| B15 自动化/复核（5 点） | 已执行并修复前端；因后端/依赖风险未关闭，未达到全绿验收 |
| B16 冷启动（4 点） | 同机干净安装与官方启动完成；Git 克隆/跨机/完整 15 分钟未完成 |
| B17 冻结五场景（5 点） | 已执行本地候选检查，判定不通过；修复后须重新冻结并复验 |
| B18 发布交接（3 点） | 交接和证据已完成；Git 核验与发布签收未完成 |

对应本地另一版：B7/B8 的恢复和路由修复通过，B9 组件测试通过但整体 verify 失败；B10 原型归档完成；B11 响应式/键盘/真实 UI 通过但五场景算法未通过；B12 同机启动完成，候选未签收。

## 修改文件与提交范围

前端修改：frontend/src/App.tsx、services/api.ts、pages/ResumeEditorPage.tsx、style.css、frontend/index.html。根目录新增 `启动项目.cmd`。没有改后端主实现、schema、数据库、算法或依赖锁；39 个受保护基线文件哈希未变。

测试：新增 frontend/src/BReview.test.tsx、ApiReview.test.ts、backend/review_tests/test_b_candidate.py；更新 frontend/tests/b-ui-review.mjs、d-ui-smoke.mjs、scripts/b-review.py。既有 test_b_acceptance.py 和五场景预期未降低。

归档：NewAnalysisPage.tsx、matchPreview.ts、mocks/records.ts、BackendStatus.tsx 从 src 移到 frontend/prototype 对应子目录，新增说明。

文档：README、handoff、docs/mvp-rc1、bug-list、b-review-progress、b-handoff、b-code-review、b-cold-start、b-requirements-traceability；验收样例说明与 STAR 基准状态更新。新证据在 docs/evidence/b-candidate。完整日志、工具、环境与干净副本仅在 .runtime，不提交。

当前 Git 状态：not a git repository，分支/提交/远程引用均无法验证。未来建议分三次审查提交：`fix(ui): restore candidate recovery and stable result navigation`、`test: add independent B candidate acceptance coverage`、`docs: record candidate review and release blockers`。

## 运行与下一步

第一次使用先在根目录运行 `powershell.exe -NoProfile -ExecutionPolicy Bypass -File scripts/setup.ps1`。以后可直接双击 `启动项目.cmd`，看到成功提示后打开 http://127.0.0.1:5173；保留命令窗口，按 Ctrl+C 停止。手动后端：`.\backend\.venv\Scripts\python.exe -m uvicorn app.main:app --app-dir backend --host 127.0.0.1 --port 8000`；前端进入 frontend 执行 `npm.cmd run dev`。详细步骤见 README。

先把 b-handoff.md 和失败用例交给 A；A 修复并提供候选哈希后，B 在同一版本重跑，不要覆盖 A 新文件或只挑通过项。C/D 可用本轮证据写方法和真实问题，但最终测试数字/截图必须注明候选未签收。
