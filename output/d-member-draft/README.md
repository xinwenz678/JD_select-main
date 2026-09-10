# D 侧阶段交付说明

日期：2026-09-08。

## 当前结果

用户流程、三个页面低保真信息架构、TC01–TC10 验收计划已完成草稿。随后已新增可运行的 [Result/History 独立 React 预览](frontend/README.md)，构建与 18 组浏览器检查通过。尚未并入实际项目；原项目启动与真实业务验收仍未完成。

本次实际工作目录为 `C:/Users/starry/Documents/ChatGPT/xxxtsx`。检查时根目录仅有空 `.git/` 和 `output/`；`git status --short --branch`、`git log -5 --oneline`、`git branch -r` 均提示不是 Git 仓库。不存在 backend/、frontend/ 或 docs/，附件 handoff 提到的 D:/JD_select 也不存在。截图显示的目录结构不能替代本机源码检查。

已请求实际项目目录或仓库地址；当前环境阻塞不是后端/前端代码故障，不能据此断言原项目无法运行。常见用户目录与 D 盘可读取范围内按项目标识文件搜索未发现源码；系统拒绝访问区域未绕过，不声称完整检索了所有位置。

## 新增文件

- [docs/user-flow.md](docs/user-flow.md)：主流程、页面状态、异常恢复、职责与接口待确认项。
- [docs/ux-design.md](docs/ux-design.md)：三个核心页面线框图、字段映射、按钮、正常/加载/错误/空态、mock 与响应式要求。
- [docs/test-plan.md](docs/test-plan.md)：TC01–TC10、脱敏合成输入、UI01–UI07、执行与缺陷记录模板。
- 本 README：本地阻塞、交付范围、附件启动方式和接续步骤。
- frontend/：ResultPage、HistoryPage、共用状态/技能组件、mock、预览壳、样式、独立依赖与浏览器验证脚本。具体清单见 frontend/README.md。

文件全部写入 `output/d-member-draft/`。没有修改附件、此次工作前的 output 文件、后端、数据库、评分算法、简历解析器或公共接口；只新增独立预览的依赖配置和锁文件，没有修改原项目依赖。未初始化新仓库，未切换/修改 main，未提交、push 或 merge。

## 实际验证

| 检查 | 结果 |
|---|---|
| 四份文字附件读取 | 已完成：MVP_TASK_PLAN、README、handoff、a4-integration-checklist |
| 实际项目 docs/ 阅读 | 阻塞：当前无该目录，不能以新草稿替代读取已有项目文档 |
| Git 分支、提交、变更、远程分支 | 无法获取：当前不是有效 Git 仓库 |
| 前后端依赖完整性 | 无法检查：无依赖文件及源码 |
| 前后端启动、health、docs、matches | 未执行：无可启动项目；没有调用可能属于其他进程的 localhost 服务 |
| 三份文档检查 | 文件存在、代码围栏数量为偶数、相对文档链接有效 |
| TC01–TC10 内容检查 | 10 个编号齐全，各含前置条件、输入、操作步骤、预期及未执行标记 |
| 独立预览的浏览器、控制台、响应式、构建 | 已执行：TypeScript/Vite 构建通过；18 组浏览器检查通过；320–1440 宽度无横向溢出；无控制台错误或 /api/ 请求 |
| 原项目的前端验证 | 未执行：原项目源码缺失，不能以独立预览替代 |
| 真实解析、评分与自动保存 | 未执行；mock 不能作为通过证据 |

## 附件 README 的启动方式（尚未在本机项目验证）

以下命令必须先进入包含 backend/ 与 frontend/ 的真实项目根目录再执行。环境要求来自附件：Node.js 22.12+、npm、Python 3.13、Git；本次未核对项目当前依赖版本。

首次配置后端：

```powershell
python -m venv backend/.venv
backend/.venv/Scripts/python.exe -m pip install -r backend/requirements.txt
if (-not (Test-Path backend/.env)) {
    Copy-Item backend/.env.example backend/.env
}
backend/.venv/Scripts/python.exe -m uvicorn app.main:app --app-dir backend --host 127.0.0.1 --port 8000 --reload
```

另开 PowerShell，在实际项目根目录启动前端：

```powershell
cd frontend
npm.cmd ci
if (-not (Test-Path .env)) {
    Copy-Item .env.example .env
}
npm.cmd run dev
```

已有环境时可跳过创建虚拟环境和安装依赖。已有 .env 不覆盖。附件前端地址为 http://127.0.0.1:5173，后端文档地址为 http://127.0.0.1:8000/docs。已有正式依赖或运行说明与附件不一致时记录差异，优先核查当前代码，不擅自升级依赖。

取得源码后，在确认启动的是本项目服务的前提下检查 GET /api/health、GET /docs、GET /openapi.json，按当前 OpenAPI 列出的能力只读核查 GET /api/matches 与详情。没有 POST /api/matches 时记录缺失，不将存储创建接口当成匹配，不为“跑通”自行补接口或写入样例记录。

## 接续工作与成员依赖

1. 用户提供实际源码位置；先读适用 AGENTS.md、当前 docs/、README、前后端依赖、公共 schema 和页面入口，报告真实 Git 与运行状态。
2. 依据现有对应文档合入本草稿；如当前处于 main，在修改源码前建立 D 的个人工作分支，保留原有未提交变更，不合并或推送。
3. 已独立完成 Result/History mock；取得原项目后先报告实际要修改的文件，再复用原项目组件、导航及依赖接入，不覆盖已有入口。
4. 接入后重新验证字段、状态、窄屏、控制台、id 导航；本轮只证明独立预览，不声称真实联调通过。
5. A：实际历史、错误、时区、保存/重试语义与重新分析原文；B：简历解析编辑组件和修正后的有效输入；C：真实算法、词典、样例分数、证据与建议结构。
6. 以上公共字段及行为冲突统一标记“待 A/B/C/D 联调确认”。不将附件 A2–A3 的他人验证记录写成本机验证，不开展今天未授权的大规模联调。

## 建议的 commit message

当前尚无可提交的实际仓库。待用户检查且文档合入后可用：

```text
docs(d): add MVP user flow, page wireframes and acceptance plan
```

上面的 message 适用于文档单独提交。独立页面接回原项目且经用户检查后，可另用：

```text
feat(d): add mock result and history pages with preview states
```

不会自动执行提交。
