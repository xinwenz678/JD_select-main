# JD Select：AI 简历诊断与岗位匹配

React/TypeScript/Vite + FastAPI + SQLAlchemy/SQLite。支持文本/PDF 简历解析与诊断、确认技能、JD 匹配、原文证据、历史 UUID 详情和规则 STAR 建议。匹配分仅辅助判断，不代表录用概率。

当前是 A 更新后由 B 完成缺陷修复的本地候选。后端 110 项检查、前端 12 项组件检查、17 项真实浏览器检查、构建、规则边界和官方启动冒烟均已通过；详见 docs/b-final-progress.md。由于当前文件夹没有 `.git`，这些结果尚未绑定到可发布的提交哈希。

## 安装（Windows PowerShell）

需要 Python 3.13.x、Node 22.12+（含 npm）和 Git。终端先进入项目根目录。

```powershell
python --version
node --version
npm.cmd --version
powershell.exe -NoProfile -ExecutionPolicy Bypass -File scripts/setup.ps1
```

setup 创建 backend/.venv，安装后端开发锁依赖，执行 npm ci，并仅在 .env 不存在时复制模板。单次 Bypass 不改变系统全局策略。不要复制别人的 .venv/node_modules/.env/数据库。

后端配置 backend/.env；前端配置 frontend/.env，默认 VITE_API_BASE_URL=/api，API_PROXY_TARGET=http://127.0.0.1:8000。真实秘密不得放入 VITE_* 或提交到 Git。

## 启动、检查、停止

如果已经成功执行过一次安装，可直接双击根目录的 `启动项目.cmd`。看到启动成功提示后，用浏览器打开 http://127.0.0.1:5173；保持命令窗口开启，关闭服务时在该窗口按 Ctrl+C。

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File scripts/start.ps1
```

前端 http://127.0.0.1:5173；健康 http://127.0.0.1:8000/api/health；Swagger http://127.0.0.1:8000/docs；契约以 /openapi.json 为准。脚本拒绝占用的 8000/5173，不会主动结束其他实例。Ctrl+C 停止本次服务。

手动启动后端：在项目根目录执行：

```powershell
.\backend\.venv\Scripts\python.exe -m uvicorn app.main:app --app-dir backend --host 127.0.0.1 --port 8000
```

另开终端进入 frontend，执行 `npm.cmd run dev`。两个终端分别 Ctrl+C 停止。

## 功能验证

1. 新建分析，粘贴 sample_data/acceptance/cases.json 的合成简历或上传文本型 PDF（≤10MB、≤30页，不支持扫描 OCR）。
2. 解析并检查/修正技能，确认进入 JD 页；无技能也可以继续，不能要求用户虚构技能。
3. 输入 JD，开始匹配；请求中禁用重复提交，失败保留草稿，超时先查历史再主动重试。
4. 核对分数、分项、技能、缺口、建议和证据；人工新增技能标为用户确认，不伪造原文行号。
5. 历史打开服务端 UUID；复制 #/results/{UUID} 到新标签、刷新、前后退应恢复相同详情。
6. JD 页输入经历，生成 STAR 建议。未配置模型或调用失败/超时时使用确定性 `rule-fallback`；配置 OpenAI 兼容的 Key、Base URL 和模型名后调用 `/chat/completions`。建议不会自动覆盖原文，须人工核实事实与数字。

## 验证命令

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File scripts/verify.ps1
.\backend\.venv\Scripts\python.exe backend/scripts/validate_boundary.py
.\backend\.venv\Scripts\python.exe scripts/b-review.py
```

补充 B 脚本需要已安装 Edge（Playwright 已由前端锁安装），自建临时数据库及动态端口，执行后停止自己的服务，输出 docs/evidence/b-candidate。仅浏览器重测使用 `--ui-only`，不是完整门禁。测试有失败时返回非零。正式 Git 候选与另一台电脑冷启动仍需在仓库可用后完成，详见 docs/b-cold-start.md。

## 当前限制与常见故障

- npm.cmd 缺失：安装完整 Node/npm 并重开终端；仅有 node.exe 不足以跑官方安装脚本。
- pytest/pypdf 缺失：按更新后的 requirements-dev.lock.txt 重新安装，勿只复用旧环境。
- /api 连接失败：检查健康、API_PROXY_TARGET 和端口；日志在忽略目录 .runtime。
- 未识别出任何技能的 JD 会返回可读 422；请补充明确技能要求后重试。简历/JD 上限为 100000 字符，岗位名上限为 200 字符。
- 可选模型配置位于 `backend/.env`：`LLM_API_KEY`、`LLM_BASE_URL`、`LLM_MODEL`、`LLM_TIMEOUT_SECONDS`。留空不会影响 Level 1 主流程。
- SQLite 为本地演示存储；不删除用户数据库来获得“空历史”测试。
- docs/mvp-rc1.md 是 A 交付说明，旧报告是历史记录；最终通过数字以 B 当前证据为准。

## 交接

见 docs/b-final-progress.md、docs/b-handoff.md、docs/b-code-review.md、docs/b-requirements-traceability.md。当前文件夹无有效 Git 信息，不能从文件夹名字推断 main/提交。未自动提交、push、merge 或打标签。
