# B 冷启动与运行说明复核

日期：2026-09-10。结论：同机干净依赖安装、官方启动冒烟完成；GitHub 全新克隆与另一台电脑验收未完成。

环境：Windows 11 build 26200，Python 3.13.7，Node 24.19.0，Git 2.50.1.windows.1，Edge 152.0.4191.66。详见 evidence/b-candidate/environment.json。

1. 原目录没有可用 npm.cmd，下载并校验 npm 10.9.3 包的 SHA512，作为 .runtime 下的独立测试工具；仅子进程 PATH 添加薄包装入口，不改变系统配置或产品锁。
2. 从源码构造同机副本，未复制 .venv/node_modules/.env/数据库。运行官方 setup.ps1：成功，397.28 秒，锁校验/pip check/npm ci 通过。随后升级并锁定 Vitest 4.1.11、Playwright 1.63.0，当前 npm audit 为 0。
3. 修复过程中将相关源码/测试同步到副本；因此这是安装及本机启动复核，不是从某个 Git 哈希开始的严格冻结冷启动。
4. 缺陷修复后官方 verify.ps1 已复跑通过：后端产品测试 91 项、前端组件 12 项、构建和启动 smoke 全部通过。完整 B 门禁另含 19 项候选测试与 17 项真实浏览器检查，也全部通过。
5. 官方 start.ps1 -Smoke 成功，health、前端 HTML、Vite /api 代理检查通过；结束后 8000/5173 可绑定，说明端口已释放。未结束其他实例。
6. B 浏览器在独立临时数据库/端口完成真实匹配、历史和 STAR；真实输入与记录不会写入用户日常数据库。
7. git status/log/branch 均返回 not a git repository。尝试只读连接 handoff 中历史仓库，GitHub 443 连接失败，没有获得或假造候选哈希。

证据：clean-install.json、official-verify.json、official-start.json、environment.json 和 B 测试结果。397.28 秒仅是安装步骤，不是完整验收总耗时；未声明满足“另一台机器 15 分钟”。

待办：仓库维护者提供确切候选哈希与可访问仓库后，在另一台电脑全新克隆，按 README 从安装到匹配/历史/刷新/停止完整计时，保存同一候选证据。当前本地 P0/P1 已清零。
