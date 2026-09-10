# A5 安装、启动与运行说明

适用版本：当前成员 A 功能分支。功能范围：后端记录 CRUD、健康检查和前端连接检查；真实简历解析/评分尚待 B/C 接入。

## 1. 环境要求

| 项目 | 要求与用途 |
|---|---|
| 操作系统 | Windows 64 位；本次在现有 Windows 主机验证，未宣称其他系统已通过 |
| Python | 3.13.x，安装时加入 PATH；运行 FastAPI 和测试 |
| Node.js | 22.12+；本次验证 22.19.0 |
| npm | 随 Node 安装；本次验证 10.9.3，使用 npm.cmd 避免 npm.ps1 执行限制 |
| PowerShell | 脚本使用 Windows PowerShell 5.1 兼容语法；实际验收版本见 A5 验证记录 |
| Git | 共享仓库使用；从源码包安装无需 Git |
| 网络 | 首次安装需访问配置的 Python/npm 包源 |
| 数据库 | SQLite，随 Python 提供，不需要另装服务 |
| 硬件 | 建议至少 4 GB 可用内存、2 GB 可用磁盘空间；建议值，并非已测最低配置 |

## 2. 四个操作入口

从项目根目录在 PowerShell 中运行：

~~~powershell
.\scripts\check-env.ps1 -CheckPorts
.\scripts\setup.ps1
.\scripts\start.ps1
~~~

若 Windows 阻止本地脚本执行，可对这次进程使用：

~~~powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\scripts\setup.ps1
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\scripts\start.ps1
~~~

命令只对该进程指定执行策略，不要求修改系统级策略。脚本根据自身路径定位项目；使用绝对脚本路径时可从其他目录调用。
检查命令只检查环境/可选端口，不安装或修改配置。若 Python 不是 3.13，安装脚本会停止，请先切换 PATH 中的解释器。

### 安装

setup.ps1 默认建立 backend/.venv，安装后端运行及测试锁文件，执行 pip check 和版本核对；通过 npm ci --include=dev 安装前端锁定依赖。npm ci 会重新创建前端 node_modules，所以安装时先停止前端进程。

若 .env 不存在，从相应 .env.example 复制；已经存在则保留内容。不会删除或重建业务数据库。重复执行会重新核对/安装依赖，不覆盖用户配置。

只需要运行后端而不安装测试依赖，可加 -RuntimeOnly；前端构建工具仍然安装。verify.ps1 需要默认完整安装。

### 启动、停止与重启

start.ps1 启动后端 8000 和前端 5173，直到健康接口、前端 HTML、Vite /api 代理均验证成功，才显示访问地址：

- 前端：http://127.0.0.1:5173
- 接口文档：http://127.0.0.1:8000/docs
- 健康接口：http://127.0.0.1:8000/api/health

保持该终端打开；在同一终端按 Ctrl+C，会停止本次脚本创建的两个服务进程。端口已占用时直接报错，不终止其他进程。
再次执行 start.ps1 即重启。统一启动器不启用后端自动重载，修改 Python 后需重启；Vite 保留前端热更新。
如希望后端自动重载，可按 README 的手动方式在独立终端运行；不要同时运行两套占用相同端口的服务。

日志位于 .runtime/backend.log、.runtime/frontend.log，每次启动覆盖本次服务日志；异常退出时保留供排查，已被 Git 忽略。
启动器本身持续检查两个服务是否存活，一个提前退出时结束另一服务并返回非零退出码。它仅保证开发环境启动，不是生产进程管理器。

### 验证

~~~powershell
.\scripts\verify.ps1
~~~

依次执行：锁版本核对 → pip check → 后端测试 → 前端生产构建 → 启动并验证两个服务 → 自动停止。

运行前停止其他 8000/5173 服务。若已有服务运行且仅需要测试与构建，可用 -SkipSmoke，但不能据此声称已完成启动验证。
单独启动检查：

~~~powershell
.\scripts\start.ps1 -Smoke
~~~

## 3. 配置与数据位置

| 文件/变量 | 含义 |
|---|---|
| backend/.env | 后端配置，由 Settings 读取，不依赖当前工作目录 |
| APP_NAME、APP_ENV | 应用名称、环境标记 |
| DATABASE_URL | 默认 sqlite:///./jd_select.db，实际位于 backend/jd_select.db |
| CORS_ORIGINS | JSON 数组，默认 localhost:5173 与 127.0.0.1:5173 |
| LLM_API_KEY / LLM_BASE_URL / LLM_MODEL | 可选 OpenAI 兼容 STAR 建议；任一留空时使用本地规则回退 |
| LLM_TIMEOUT_SECONDS | 模型调用超时秒数，默认 8，范围大于 0 且不超过 30 |
| frontend/.env / VITE_API_BASE_URL | 浏览器请求前缀，默认 /api |
| API_PROXY_TARGET | Vite 开发代理目标，默认 http://127.0.0.1:8000 |

当前启动器使用固定的 8000/5173。如果自行改动代理目标或 CORS，请使它们与服务端口一致，否则 readiness 验证可能失败。VITE_* 为公开前端配置，不放密钥。
SQLite 首次启动自动创建目录和表；重启保留数据。create_all 不处理表结构迁移。
首次运行不自动导入样例。若要演示记录新增/查询，使用 docs/api.md 的明确操作步骤。

## 4. 依赖锁与维护

- frontend/package.json 声明直接依赖，package-lock.json 锁完整前端依赖树，安装使用 npm ci。
- backend/requirements.txt 声明运行直接依赖；requirements.lock.txt 补全间接依赖。
- backend/requirements-dev.txt 声明测试依赖；requirements-dev.lock.txt 引用运行锁并补齐测试间接依赖。
- scripts/check-lock.py 递归检查引用及冲突，并确认当前已安装版本逐项等于锁定版本；不把无关额外包误当作缺失依赖。

| 依赖类别 | 主要包 | 用途 |
|---|---|---|
| Web 服务 | FastAPI、Starlette、Uvicorn | 路由、HTTP/CORS、服务进程 |
| 配置校验 | Pydantic、pydantic-settings、python-dotenv | 输入/输出和环境变量解析 |
| 数据存储 | SQLAlchemy、greenlet | Session、模型、SQLite 存取 |
| 测试 | pytest、httpx | 自动化及 TestClient |
| 前端 | React、React DOM | 组件界面 |
| 构建 | TypeScript、Vite、React 插件 | 类型检查、开发代理和构建 |

锁文件是 Windows/Python 3.13 的已验证版本集合，不是供应链哈希锁。升级依赖时先改直接声明，在干净环境解析并同步相关间接固定版本，再运行 setup 和 verify；不要把当前机器所有无关包直接混进锁文件。
新增配置项时更新 .env.example 和文档，不替队友覆盖 .env。

## 5. 常见问题

| 现象 | 处理 |
|---|---|
| 找不到 python.exe/node.exe/npm.cmd | 安装对应工具并重新打开终端，运行 check-env |
| Python 版本不符 | 使用 Python 3.13；若旧 .venv 用其他版本建立，保留旧环境另行重建到正确环境后再安装 |
| pip/npm 下载失败 | 查看失败包和源地址，检查当前网络；安装失败后可以重试 setup |
| 8000/5173 被占用 | 先在自己已有服务终端 Ctrl+C，不自动杀占用者 |
| 后端先退出 | 查 backend.log，检查 .env JSON 格式、数据库路径和权限 |
| 健康正常但代理检查失败 | 查 frontend.log，确认 API_PROXY_TARGET 指向 127.0.0.1:8000 |
| 锁版本检查不通过 | 按锁文件重新运行 setup；若是有意升级，先同步锁并验证 |
| pytest 不存在 | 安装默认开发依赖，不使用 RuntimeOnly |
| 前端构建成功却不能访问 API | 生产构建不包含 Vite 开发代理，生产部署需另配 /api 反向代理 |
| SQLite 被锁定 | 停止重复后端进程，检查是否有其他程序长时间占用数据库，再重试 |
| GitHub 推送超时 | 参照 git-collaboration-guide.md 中已验证的本机代理方案；包源连接与 Git 代理是不同配置 |

## 6. 干净安装验收边界

A5 验收要求使用源码、模板和锁文件创建全新的虚拟环境与 node_modules；不能复制旧环境或实际 .env。
同机全新目录证明安装流程不依赖旧目录残留，但不等于另一台电脑验证。最终合并后，仍需队友按本文在其电脑复验。
运行时间和结果见 a5-verification.md；完整简历匹配闭环不在本轮 A5 启动检查范围内。
