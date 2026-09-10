> B 复核更新（2026-09-10）：A 交付后的 RC-B01–RC-B07 已由 B 修复。当前后端 110/110、组件 12/12、浏览器 17/17、构建、规则边界、audit 和官方 verify 均通过。最新事实见 b-final-progress.md；由于目录没有 `.git`，仍需先绑定提交哈希再创建标签。

# mvp-rc1 候选说明

更新时间：2026-09-10

A13–A18 已实现，当前是候选版本，仍需成员 B 非作者复核后再打标签。

- A13：匹配接口接收 confirmed_skills/confirmed_name；原文继续保存。新增技能无原文证据时使用 confirmed_resume，line 为 null。
- A14：同步提交锁、加载禁用、失败输入保留；事务失败不保存半条记录。
- A15：稳定 hash 路由覆盖首页、新建、历史和 UUID 详情；刷新、复制链接、前进后退可恢复同一记录。
- A16：Vitest、React Testing Library、jest-dom、jsdom 已锁定，npm test 已接入 scripts/verify.ps1，真实 smoke 保留。
- A17：POST /api/suggestions/star 返回原文、STAR 四部分、JD 关键词、量化提示、来源和人工核实提示；不会自动覆盖原文。无配置/失败/超时走确定性 rule-fallback，配置兼容模型时走 LLM 分支。
- A18：已删除未引用的旧 NewAnalysisPage、matchPreview、mock records 和 BackendStatus。

冻结：resume-v1、rule-v1。验证：后端 77 passed；前端 4 passed；生产构建、依赖锁、pip check、真实 smoke 通过。

复验重点：删除/新增确认技能；快速双击；失败后历史总数；恢复服务后重试；详情复制/刷新/404；STAR 不覆盖原文。
