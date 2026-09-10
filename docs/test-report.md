# MVP 本地候选测试报告

执行日期：2026-09-10  
测试对象：`JD_select-main` 本地整合候选  
结论：本地技术门禁通过，P0/P1 为 0；Git 提交身份与跨机冷启动待外部条件。

## 环境与隔离

- Windows 11 build 26200、Python 3.13.7、Node 24.19.0、Edge 152.0.4191.66。
- 后端集成和浏览器测试使用临时 SQLite、动态端口及合成数据；测试结束后停止本轮服务。
- 不读取或清空用户默认历史，不提交 `.env`、数据库、缓存或 `.runtime`。

## 自动化结果

| 检查 | 结果 |
|---|---:|
| 后端产品测试 | 91 passed |
| B 独立候选测试 | 19 passed |
| 后端总计 | 110 passed, 0 failed |
| 前端组件 | 12 passed, 0 failed |
| 真实浏览器 | 17 passed, 0 failed |
| 页面异常 | 0 |
| 非预期 console error | 0 |
| TypeScript / Vite build | passed |
| 规则边界 | passed |
| 既有 UI smoke | passed |
| 官方 `scripts/verify.ps1` | passed |
| npm audit | 0 vulnerabilities |

测试仅产生一条 Starlette/AnyIO 弃用警告，不影响功能与发布门禁。

## 五个核心场景

| 用例 | 实际 | 结论 |
|---|---|---|
| TC01 完整匹配 | 91 分；匹配 Excel/FastAPI/Python/SQL；缺失为空；11 条证据 | 通过 |
| TC02 部分匹配 | 40 分；匹配 Excel/Python；缺失 FastAPI/SQL；4 条证据 | 通过 |
| TC03 低匹配 | 1 分；无虚构匹配；缺失 FastAPI/Python/SQL；4 条证据 | 通过 |
| TC04 空输入 | 前端阻止提交并聚焦字段；后端空白/长度边界返回 422 | 通过 |
| TC05 同义词 | 80 分；`pytorch、JS` 归一化为 PyTorch/JavaScript；无缺失 | 通过 |

此外已通过：快速双击只有一个 POST、失败事务回滚、503/网络错误重试、草稿保留、历史空态、详情 404、UUID 刷新/复制/前后退、旧响应隔离、STAR 规则回退、模型成功/超时分支、320/390/720/1440px 布局和键盘操作。

## 缺陷关闭情况

RC-B01–RC-B07 全部关闭，详情见 `bug-list.md`。当前唯一外部交付项 RC-B08 是目录无 `.git`，无法给测试结果绑定提交哈希。真实模型分支已自动验证，实际供应商连接仍需要小组凭据。

## 可追溯证据

`docs/evidence/b-candidate/summary.json` 是完整 B 门禁汇总；`ui-report.json` 保存浏览器用例与合成 UUID；`pytest.json`、`candidate-tests.json`、`component-tests.json` 保存逐项结果；`npm-audit.json`、`api-inventory.json`、`official-verify.json` 保存依赖、接口和官方门禁事实。

本报告不得用于声称真实招聘准确率。匹配分用于辅助判断，不代表录用概率。
