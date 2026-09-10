# B 需求—修复—测试追踪

日期：2026-09-10。依据外部 `remaining-work-plan.md` 的 B13–B18。测试数据均为合成数据。

| 需求 | 实现/修复 | 证据 | 结论 |
|---|---|---|---|
| A13 确认技能/姓名 | 技能规范化、空集合语义、确认来源、姓名快照 | `test_b_candidate.py`、UI A13 | 通过 |
| A14 重复/恢复/回滚 | 同步锁、禁用态、草稿保留、可读错误、事务回滚 | UI03/04/07、ApiReview、后端回滚用例 | 通过 |
| A15 稳定详情 | UUID hash、刷新/复制/前后退、404、旧响应隔离、真实重试 | UI A15/RECOVERY、BReview | 通过 |
| A16 统一门禁 | Vitest/RTL/jsdom、构建、真实 Playwright、官方 verify | 12/12 组件、17/17 浏览器、verify 通过 | 通过 |
| A17 STAR | OpenAI 兼容分支、无配置/超时回退、原文对比与人工核实 | 后端模型成功/超时测试、UI STAR | 代码路径通过；真实供应商 smoke 待凭据 |
| A18 正式入口 | 旧原型归档、正式入口与 README 更新 | 引用检查、构建、浏览器检查 | 通过 |
| 五场景/证据 | 固定输入、分数/缺口/证据/历史/详情 | `test_b_acceptance.py`、UI-TC01/02/03/05、UI02 | 通过 |
| 输入上限/错误 | 422 边界、未知技能 JD 不保存 | oversized/unknown JD 测试 | 通过 |
| B16 冷启动 | 同机干净安装与官方启动 smoke | clean-install、official-start/verify | 同机通过；跨机待 Git |
| B18 发布门禁 | audit、锁、pip、tests、build、API、E2E | `summary.json`、`npm-audit.json` | 技术门禁通过；Git 身份待仓库 |

当前没有未解决 P0/P1。不能把“本地技术门禁通过”改写为“GitHub 已发布”；后者需要真实提交哈希。
