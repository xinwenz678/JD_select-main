# 成员 D 阶段测试报告

测试日期：2026-09-09  
测试对象：`JD_select-main` 开发骨架、D 侧 mock 页面、真实健康检查  
结论级别：阶段通过；不代表业务端到端通过

## 1. 测试范围

已测试：

- FastAPI 健康接口、Swagger 文档和 Vite `/api` 代理。
- 新建分析输入与 mock 提交状态：空输入、Loading、失败、输入保留、重试、成功跳转、当前在途重复点击拦截。
- Result 的总分、分项、技能、建议、版本、证据缺失提示和评分局限说明。
- History 的正常、Loading、Error、Empty、按 `id` 查看详情、不存在详情、重排、刷新及前进/后退。
- 0 分、缺字段、空数组、非法时间、长文本、键盘焦点和多种窗口宽度。

未测试：真实简历解析、真实岗位解析与匹配、自动保存、真实历史接口、高/中/低算法正确性、真实业务接口防重复、目标演示浏览器的 200% 手工缩放和完整屏幕阅读器流程。自动化已覆盖 200% 缩放等效的 720 CSS 像素视口。

## 2. 环境

| 项目 | 实际环境 |
|---|---|
| 操作系统 | Windows，本地开发环境 |
| Python | 3.13.7 |
| 后端 | FastAPI 0.115.12、Uvicorn 0.34.2 |
| 前端 | React 19.1.0、TypeScript 5.8.3、Vite 6.4.3 |
| 浏览器 | Microsoft Edge 152.0.4191.62（自动化） |
| 前端地址 | `http://127.0.0.1:5173` |
| 后端地址 | `http://127.0.0.1:8000` |
| Git | 当前工作区不是有效 Git 仓库；父目录 `.git` 为空，`git status` 失败，无法记录分支和提交哈希 |

## 3. 构建与接口结果

| 检查 | 实际结果 | 状态 |
|---|---|---|
| 后端依赖 `pip check` | `No broken requirements found` | 通过 |
| 前端 TypeScript | `tsc --noEmit` 通过 | 通过 |
| Vite 生产构建 | 39 个模块构建成功 | 通过 |
| `GET /api/health` | HTTP 200，`status=ok`、`version=0.1.0` | 通过 |
| `GET /docs` | HTTP 200 | 通过 |
| 前端代理 `/api/health` | HTTP 200 | 通过 |
| OpenAPI 路径 | 仅 `/api/health` | 已确认限制 |
| `GET /api/matches` | HTTP 404 | 阻塞，等待 A/C |

## 4. 浏览器检查结果

自动化报告：[frontend/tests/artifacts/report.json](../frontend/tests/artifacts/report.json)。共 25 项检查通过：

1. Result 所需字段、mock 说明、评分说明与证据缺失提示。
2. Result 和 History 的 Loading/Error/Empty 及恢复，不显示旧分数。
3. History 三条固定记录、UTC 转上海测试时区、稳定 `id`、列表重排、刷新和前进/后退。
4. 0 分与缺失评分区分；空技能、空建议、缺字段和非法时间有可读占位。
5. 不存在及编码损坏的详情 id 不崩溃、不回退到其他记录。
6. 新建分析空输入焦点、mock Loading、失败、重试、成功跳转和同时重复点击抑制。
7. 输入在当前 React 会话中保留，刷新清空；合成预设结构在输入改变后移除。
8. 1440、1024、768、390、320 CSS 像素宽度及 1440 物理像素下 200% 浏览器缩放等效的 720 CSS 像素视口中，新建、结果、历史、错误、空态无横向溢出。
9. 320 宽度下超长岗位名与连续英文技能可换行。
10. 导航后焦点进入标题，键盘焦点样式可见。
11. 业务页面没有发出业务 API 请求。
12. 真实健康检查的 Loading、成功、并发点击抑制、模拟 503 和恢复后重试。

自动化期间：`pageerror=0`、非预期 `console.error=0`。模拟健康接口 503 时产生 1 条预期浏览器网络错误。共记录 3 次用户动作触发的 `/api/health`；没有 `/api/matches` 等业务请求。

## 5. TC01–TC10 状态

| 用例 | 当前状态 | 原因/证据 |
|---|---|---|
| TC01 完整匹配 | 阻塞 | C 的真实匹配未提供；mock 72 分不能作为证据 |
| TC02 部分匹配 | 阻塞 | 同上，且中等分区间待 C 确认 |
| TC03 低匹配 | 阻塞 | 同上，需核查不能虚构技能 |
| TC04 空输入 | 阶段通过 | mock 提交会阻止空简历/JD、提示并聚焦；真实请求校验待接口接入 |
| TC05 同义词 | 阻塞 | 等待 C 的词典与归一化实现 |
| TC06 Loading | 阶段通过 | mock 提交 Loading 和按钮锁定通过；真实请求生命周期待验证 |
| TC07 接口失败 | 部分通过 | mock 匹配失败/重试和真实健康失败/重试通过；业务接口失败待验证 |
| TC08 空历史 | 阶段通过 | mock 空态和恢复入口通过；真实列表待 A |
| TC09 详情不存在 | 阶段通过 | mock id、恢复、重排和刷新通过；真实 404 格式待 A |
| TC10 重复提交 | 阶段通过 | mock 匹配同时点击仅启动一次；真实保存幂等待 A/C |

“阶段通过”只说明 D 的前端状态和交互已经准备好，不等于正式业务验收通过。

## 6. 缺陷结论

在已经验证的 D 侧 mock 页面范围内，未发现未关闭的 P0/P1 UI 缺陷。整个系统不能据此宣称“严重 Bug 为 0”，因为真实解析、匹配、保存和历史尚未进入测试范围。

当前依赖、开放问题和已关闭的 D 侧问题见 [Bug/阻塞清单](bug-list.md)。

## 7. 复验命令

在前后端运行时，于 `frontend` 目录执行：

```powershell
node node_modules/typescript/bin/tsc --noEmit
node node_modules/vite/bin/vite.js build
$env:PLAYWRIGHT_MODULE_PATH = 'C:/Users/starry/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/playwright'
node tests/d-ui-smoke.mjs
```

其他机器需要把 `PLAYWRIGHT_MODULE_PATH` 改为本机 Playwright 包位置。
