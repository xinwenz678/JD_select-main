# 成员 D：GitHub 更新清单与提交说明

整理日期：2026-09-09。适用范围：将本机已完成的 D 侧成果提交到小组共享仓库供评审。

本文件是后续操作说明。本轮仅整理文档，没有执行 commit、push、merge 或创建远程 PR。

## 1. 你这次需要更新什么

你需要交付一份能运行的 D 侧前端 mock，以及对应的设计、测试、进度和演示材料。PR 应说明“D 侧 UI 和交付准备完成，真实业务接口待接入”。阶段估分为 18/25，是自评进度，不是正式验收得分。

当前源码来源是本机 `JD_select-main`。迁入 GitHub 仓库时，里面的 `frontend/`、`docs/` 等应对应仓库根目录的同名目录，不要再套一层 `JD_select-main/`，也不要提交另一个独立前端项目。

### 1.1 前端文件清单

以下是待迁移和评审的文件，不是 Git 自动生成的差异清单；取得共享仓库后，按实际 diff 决定哪些需要提交。

```text
frontend/index.html
frontend/public/favicon.svg
frontend/src/App.tsx
frontend/src/style.css
frontend/src/types.ts
frontend/src/pages/NewAnalysisPage.tsx
frontend/src/pages/ResultPage.tsx
frontend/src/pages/HistoryPage.tsx
frontend/src/components/StatePanel.tsx
frontend/src/components/SkillList.tsx
frontend/src/components/BackendStatus.tsx
frontend/src/mocks/records.ts
frontend/src/services/matchPreview.ts
frontend/tests/d-ui-smoke.mjs
```

| 文件组 | 本次提供的能力 | 合并时注意 |
|---|---|---|
| `NewAnalysisPage.tsx`、`matchPreview.ts` | JD/简历输入、空值校验、Loading、失败、重试、前端在途锁 | 解析区仍是占位，需接 B；模拟提交仅传递成功/失败选项，没有发送真实简历/JD |
| `ResultPage.tsx`、`SkillList.tsx`、`types.ts` | 总分、分项、技能、建议、版本、证据缺失提示 | `types.ts` 是本地展示模型，不是服务端 schema；真实字段由 A/C 确认 |
| `HistoryPage.tsx` | 最多展示传入列表前 10 条、时间、按 `id` 打开详情和空态 | 当前 fixture 只有 3 条；最近排序、真实 10 条和持久化尚待验收 |
| `App.tsx`、`style.css` | 三页导航、共享草稿和页面布局 | 与 B/A 的入口、样式改动逐段合并，不能整文件覆盖团队更新 |
| `BackendStatus.tsx` | 复用原有健康检查服务 | `services/api.ts` 中的 `getHealth` 继续保留，无需为此次成果覆盖它 |
| `records.ts`、测试脚本 | 固定示例、边界用例和浏览器复验 | 保留 mock 标识，固定 72 分不能用于算法验收 |

### 1.2 文档与交付准备

```text
docs/user-flow.md
docs/ux-design.md
docs/test-plan.md
docs/test-report.md
docs/bug-list.md
docs/demo-script.md
docs/subtitles-draft.srt
docs/delivery-checklist.md
docs/d-progress-final.md
docs/d-github-update-guide.md
docs/team-integration-plan.md
scripts/verify-delivery.ps1
delivery/README.md
```

同时评审并合入以下共享文件中的 D 侧增量：

- `README.md`：当前三页入口、运行方法、mock 范围和文档导航。
- `handoff.md`：D 已完成事项、验证证据、未完成事项及依赖。
- `.gitignore`：与 D 侧测试产物相关的忽略规则。

共享 README/handoff 应保留 A/B/C 已有内容。里面“本机不是有效 Git 仓库”等描述只适用于这份下载目录，不能直接写成 GitHub 共享仓库也没有 Git。`docs/d-progress-plan.md` 是较早阶段评估，可作为历史记录保留，但最新进度以 `d-progress-final.md` 为准。

`MVP_TASK_PLAN.md`、前后端依赖清单和锁文件是已有项目基线；本次没有新增业务依赖，不应因为复制目录而无故覆盖团队版本。发现版本不一致先与 A 对齐。

### 1.3 不要放入此次提交的内容

- `node_modules/`、`dist/`、`.venv/`、缓存、日志、本机数据库和 `.env`；保留共享的 `.env.example`。
- 外层 `output/`、`JD_select-main/output/` 中的重复草稿、备份和旧前端目录。
- 本机空 `.git` 文件夹，以及临时包管理器文件。
- 真实个人简历、密钥或未脱敏数据。
- 尚未生成的正式 MP4、源码交付 ZIP 和团队报告，不用空文件冒充完成。

当前 `.gitignore` 只明确忽略了部分产物，并没有自动排除所有 `output/` 内容。因此本次按文件暂存，避免使用 `git add .` 打包整份工作区。

## 2. 测试证据怎么放到 GitHub

当前报告引用 `frontend/tests/artifacts/report.json` 和截图，但这个目录被 `.gitignore` 排除。只提交测试报告会导致别人无法打开这些本地证据。

提交前，建议将本次 JSON 报告及桌面/手机代表截图复制到 `docs/evidence/d-ui-2026-09-09/`，检查只含合成数据后提交，并把测试报告中的证据链接改到该目录。此目录是待提交时建立的建议位置，本轮尚未创建。也可使用团队已有的测试产物存放方式，并在 PR 中给出可访问链接。

证据说明写清：这是本机 2026-09-09 的 mock 检查，共 25 项；由于本机无有效 Git 元数据，原始结果没有可关联的提交哈希。迁入共享仓库后还要在实际提交上复验，不能把本机旧报告当作共享分支的运行结果。

## 3. 在有效共享仓库里怎样提交

### 第一步：让 A/组长给出基线

需要取得共享仓库 URL、你的写入权限或团队指定的 PR 提交方式、基线分支、基线提交哈希、PR 目标分支和评审人。

当前在本机执行 `git status` 仍返回 `not a git repository`，所以不能直接从这份下载目录推送。应取得带历史的共享仓库，再迁入文件；不通过重新 `git init` 制造另一套项目历史。

以下命令是供你之后执行的模板，尖括号内容必须替换为 A 确认的实际值：

```powershell
git clone <共享仓库URL> JD_select
cd JD_select
git fetch origin
git switch -c codex/d-result-experience origin/<已确认的基线分支>
git status --short --branch
```

`codex/d-result-experience` 是建议的新个人分支名；若团队已指定成员分支名称则沿用。PR 目标由 A 确认，可能是集成分支或 `main`，不要自行假定。

### 第二步：按清单迁入并检查差异

将第 1 节列出的文件映射到共享仓库同名位置。若目标已有 B/A 的同名改动，先对比再合入 D 的部分。尤其检查 `App.tsx`、`NewAnalysisPage.tsx`、`style.css`、README 和 handoff。

```powershell
git diff --stat
git diff -- frontend/src/App.tsx frontend/src/pages/NewAnalysisPage.tsx frontend/src/style.css
git diff -- README.md handoff.md .gitignore
```

### 第三步：在迁入后的版本运行验证

- 按共享 README 安装依赖并启动前后端；不要复制本机 `node_modules` 或虚拟环境。
- 在 `frontend` 目录运行 `npm.cmd ci`、`npm.cmd run build`。
- 检查新建分析、结果、历史，确认 mock 状态和真实连接状态表述一致。
- 浏览器脚本需要可用的 Playwright 和 Edge；现有 `package.json` 并未声明 Playwright，不能把 `npm ci` 成功当作已具备浏览器测试环境。使用组内统一安装位置，并设置 `PLAYWRIGHT_MODULE_PATH` 后运行 `node tests/d-ui-smoke.mjs`，详见 [测试报告](test-report.md)。
- 该脚本还会检查真实 `/api/health`，运行前需启动后端。当前脚本固定检查 mock 数据，不适用于直接验收真实匹配模式。

### 第四步：明确暂存、提交，再推送成员分支

按清单逐个或按确认无其他改动的目录暂存；下面只示范单个文件，不是一键提交脚本：

```powershell
git add frontend/src/pages/ResultPage.tsx
# 继续逐项暂存已检查的 D 文件
git diff --cached --name-status
git diff --cached --check
git diff --cached
git commit -m "feat(frontend): add D mock result history and submission states"
git push -u origin codex/d-result-experience
```

推送的是个人分支。随后发起 PR 并请 A/B/C 审查相关部分；集成和最终合入 `main` 由组内流程执行。这里提供的是后续操作步骤，助手本轮未执行这些命令。

## 4. 可以直接使用的 PR 说明

**建议标题：** `feat(frontend): 完成 D 侧三页 mock、提交状态与验收材料`

**建议正文：**

> 新增新建分析、匹配结果和历史记录三页体验。新建页支持空输入提示、Loading、失败重试和在途防重复；结果页展示总分、分项、技能缺口、建议、版本和评分说明；历史按记录 id 打开详情。
>
> 补齐用户流程、信息架构、TC01–TC10 测试计划、阶段测试报告、Bug 清单、演示脚本、字幕草稿、交付预检和 D 进度说明。未修改数据库、解析算法、评分算法和公共 API。
>
> 本机 mock 验证：TypeScript 检查和 Vite 构建通过，浏览器 25 项检查通过，无页面异常或非预期控制台错误。真实业务接口、评分、自动保存和历史持久化尚未验收。
>
> 共享分支复验：提交哈希、执行命令、实际结果与证据链接待提交人运行后填写，不预填通过。
>
> 请 A 审查基线、导航与整合入口；B 审查新建分析页与解析编辑组件的衔接；C 审查 Result 字段适配需求。待确认点见 `docs/team-integration-plan.md`。

## 5. GitHub 上还应同步的进度

- 在已有 D 任务/Issue 中更新 D1–D6 状态，附 PR 链接；如团队尚无任务记录，可把本 PR 作为 D 侧进度入口。
- D1 标为设计完成；D2/D3/D4 写明“mock 就绪、真实接口待接入”；D5 写“UI 阶段验证完成、真实主场景待验”；D6 写“脚本和字幕草稿就绪、正式成片待制作”。
- 将 A/B/C 的具体依赖放到已有对应任务中，链接 [团队协作与整合计划](team-integration-plan.md)，避免只写“等接口”。
- 只有在真实链路通过后，再更新为正式完成；72% 是当前 D 侧估算进度。
