# D 侧 Result / History 独立预览

这是可运行的 React / TypeScript / Vite 页面代码。实际项目源码尚未提供，所以当前放在独立目录，未接入原项目。所有数据均为本地合成样例，没有后端、解析、评分、持久化或新增公共 API。

## 运行

Node.js 22.12+，本次实际使用 Node 24.19.0、pnpm 11.19.0。在本目录运行：

```powershell
pnpm install --frozen-lockfile
pnpm run dev
```

本机 pnpm 没有加入 PATH 时可使用已存在的运行时：

```powershell
& 'C:/Users/starry/.cache/codex-runtimes/codex-primary-runtime/dependencies/bin/fallback/pnpm.cmd' install --frozen-lockfile
& 'C:/Users/starry/.cache/codex-runtimes/codex-primary-runtime/dependencies/bin/fallback/pnpm.cmd' run dev
```

- 结果页：[示例结果](http://127.0.0.1:5173/#/results/demo-001)
- 历史页：[示例历史](http://127.0.0.1:5173/#/history)
- 缺失详情：[不存在的示例](http://127.0.0.1:5173/#/results/missing-demo)
- 用页面上方的“演示状态”切换 normal / loading / error / empty；错误重试回到正常示例，空态进入未接入的新建分析占位。

端口已占用会明确退出，不切换到其他端口，也不会终止其他服务。停止当前服务用 Ctrl+C。当前预览无 .env 要求。

构建：

```powershell
pnpm run build
pnpm run preview
```

构建产物在 dist/。preview 使用 4173 端口。这里使用独立 pnpm-lock.yaml，因为本机运行时提供 pnpm；接回原项目时保留原项目依赖和 package-lock.json，不复制这套独立预览的依赖配置覆盖它。

## 代码边界

| 文件 | 职责 |
|---|---|
| src/pages/ResultPage.tsx | 总分、分项、技能、建议、版本、证据缺失提示及各种页面状态；用 props 接收展示数据和回调 |
| src/pages/HistoryPage.tsx | 最近最多 10 条、按本地时区显示时间、id 详情回调、空/错/加载状态 |
| src/components/StatePanel.tsx | 共用 Loading、Error、Empty、Not Found 提示与恢复操作 |
| src/components/SkillList.tsx | 技能列表和局部空态 |
| src/mocks/records.ts | 用户给定 demo-001 与另外两条固定合成样例；按 id 查找；不是算法验收数据 |
| src/types.ts | 仅用于本地组件的展示类型，不是新公共 API 契约 |
| src/App.tsx | 独立预览壳、hash 导航、演示状态工具；提供重新分析未接入占位 |
| src/styles.css | 桌面/窄屏布局、长文本换行、焦点与状态样式 |
| verification/smoke.mjs | 可复验的浏览器检查，使用已有 Playwright，不增加业务依赖 |

“修改后重新分析”已经连接到显式的未接入占位，不伪造简历输入、解析或匹配。取得原项目后由已有 B/D 新建分析页面承接回调。Result 缺少原文证据时不会编造 evidence 字段；真实 suggestions 对象、列表封装、保存状态等须经实际契约适配后接入。

## 实际验证

- TypeScript 严格检查和 Vite 生产构建通过。
- Microsoft Edge 152.0.4191.62 无头浏览器：18 组检查通过。
- 结果全字段、mock 标识、评分局限、证据缺失提示可见。
- Result/History 的 loading/error/empty 状态及恢复入口可操作；不残留其他记录的分数。
- 历史列表反转顺序后仍按 id 打开正确详情；详情刷新、前进/后退正常；UTC 时间按 Asia/Shanghai 测试环境转换。
- 零分保持 0；空技能和空建议显示提示；不存在或编码损坏的 id 有明确恢复入口。
- 在 1440/1024/768/390/320 CSS 像素宽度检查结果、历史、错误、空态，无横向溢出；320 宽度长标题与长英文技能换行检查通过。
- 导航后焦点到标题，Tab 可进入演示状态选择；这不等于完整辅助技术验收。
- 全程 0 个 pageerror、0 个 console.error、0 个 /api/ 请求。
- 已人工查看桌面结果及手机历史截图；证据见 verification/ 下 PNG 和 report.json。

运行浏览器检查（需先启动 dev 服务，本机已存在 Edge 与 Playwright）：

```powershell
$env:PLAYWRIGHT_MODULE_PATH = 'C:/Users/starry/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/playwright'
node verification/smoke.mjs
```

其他机器可令 PLAYWRIGHT_MODULE_PATH 指向已有 Playwright 包，或使用可解析的 playwright 安装。脚本不会修改真实数据库或后端。

仍待验证：原项目真实启动、后端接口、B 的输入与修正、C 的算法、匹配在途防重复提交、真实保存/历史读取、200% 浏览器缩放、完整屏幕阅读器检查。以上不能由 mock 验证替代。

## 接回原项目

先核对实际 docs/、schema、组件、样式与导航。优先复用 ResultPage/HistoryPage 的展示逻辑，将回调接到已有页面；样式需按原项目约定合并或限定作用域。不要直接用本预览的 App、package.json 或全局 CSS 覆盖原项目入口与配置。公共字段冲突标记“待 A/B/C/D 联调确认”。
