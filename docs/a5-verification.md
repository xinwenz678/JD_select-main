# A5 验证记录

日期：2026-09-08。被测源码基于 A2–A3 分支，新增 scripts 和两份完整后端依赖锁。
验收方式：在项目 tmp 下创建唯一的新目录，只复制源码、模板和锁文件；未复制 .env、.venv、node_modules、数据库或 .git。
安装可使用包管理器下载缓存，但虚拟环境和前端依赖目录均重新建立。

## 环境

- Windows 当前主机，Python 3.13.0、Node.js 22.19.0、npm 10.9.3。
- 首次 setup 使用 PowerShell 7.6.5；完整 verify 和修复后的重复 setup 使用 Windows PowerShell 5.1。
- SQLite 本地文件；未使用外部模型服务。

## 实际结果

| 检查 | 结果 |
|---|---|
| PowerShell 脚本语法解析 | 通过 |
| 完整后端锁定依赖 | 24 个运行/测试包版本逐项一致 |
| 仅运行依赖核对 | 17 个包版本一致 |
| 全新安装 | 创建全新 .venv 和 node_modules，pip check 通过 |
| npm 安装审计 | 0 vulnerabilities |
| 后端测试 | 26 passed，4.56 秒；一条原有第三方弃用提示 |
| TypeScript 与前端构建 | 通过，Vite 构建 1.48 秒 |
| 真实健康请求 | /api/health 返回 status=ok、database=ok |
| 前端与代理 | 首页包含 root，5173/api/health 经 Vite 转发验证成功 |
| 自动停止 | smoke 结束停止本次两个服务 |
| Ctrl+C 停止 | 交互终端发出 Ctrl+C，输出 Project server processes stopped / Stopped；随后实测 8000/5173 均可绑定 |
| 重复安装保留配置 | 两份 .env 加入自定义标记后，重复 setup 前后 SHA256 一致 |
| 端口冲突 | 先占用 8000，启动器非零退出并明确报告 busy；原监听器仍存活 |
| 后端启动失败 | 仅对子进程注入非法 CORS JSON，非零退出且指出日志位置；8000/5173 均释放 |

测试初次使用 Windows PowerShell 5.1 重复 setup 时暴露 python -c 引号剥离，已修正 check-env.ps1 的引号写法并复验成功。

## 如何复现

~~~powershell
.\scripts\setup.ps1
.\scripts\verify.ps1
~~~

重复安装与失败路径检查均只在本次临时目录中执行，未修改原项目实际 .env 或业务数据。

## 结论范围

已验证 A5 的安装、版本核对、构建、服务启动/代理与失败处理。本轮不是完整简历匹配端到端验收，也不是另一台电脑或生产环境验收；最终整合代码仍需队友复验。
交互停止在终端 PTY 中发送 Ctrl+C 复验，端口释放检查通过。
临时目录在证据整理后清理，保留源码脚本和本记录供复现。
