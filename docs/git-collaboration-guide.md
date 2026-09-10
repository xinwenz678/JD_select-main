# JD Select 共享 Git 仓库操作指南

适用对象：四人小组；命令使用 Windows PowerShell。更新日期：2026-09-08。

## 1. 当前状态与阅读顺序

当前已建立本地 Git 仓库，默认分支是 `main`，已有前后端骨架和首次提交 `1cff13c`。同时提供了 `JD_select.bundle` 离线快照。**截至本指南编写时，尚未配置在线远程仓库 origin，因此目前没有可直接填写的真实克隆 URL。**

- 组长：先完成第 3 节发布和邀请，再把真实 HTTPS 地址发给组员。
- 组员：接受邀请后从第 4 节开始；已经收到 bundle 的人看第 5 节。
- 每天写代码：按第 7–10 节操作。
- 发生错误：查第 12 节。

本文 `YOUR_OWNER`、`YOUR_NAME` 和路径示例都需要替换，不能原样作为真实账号。每个 PowerShell 窗口里的变量独立，重新打开窗口后需重新设置 `$repoUrl`。

## 2. 先认识几个概念

| 名称 | 在本项目中的含义 |
|---|---|
| 工作区 | 电脑上的代码文件，保存文件只是改变工作区 |
| 暂存区 | 用 git add 选出准备放进下次提交的修改 |
| commit | 保存一个本地版本，还没有上传到网上 |
| origin | 在线仓库的本地别名；通过 remote -v 查看实际地址 |
| main | 小组共享的可运行主分支 |
| 功能分支 | 某项任务的开发分支，如 feat/b-resume-parser |
| push | 上传已提交的版本到远程分支，不包含未提交文件 |
| fetch | 下载远程提交与分支信息，不自动修改工作区 |
| pull | 获取远程更新并整合到当前分支 |
| Pull Request / PR | 请求别人审查并把你的分支合并到 main |

日常流程：获取最新 main → 创建任务分支 → 修改文件 → add → commit → push → PR → 复核合并 → 同步 main。

## 3. 组长首次发布在线仓库（只做一次）

### 3.1 创建空仓库

以下网页步骤以 GitHub 为例。登录自己的账号，打开 [创建仓库](https://github.com/new)，选择所有者，填写名称 `JD_select`；小组内部协作可选择 Private。因为本地已有代码与历史，创建时不要初始化 README、.gitignore 或 License。

创建完成后，在仓库页面复制 HTTPS 克隆地址，例如：

```text
https://github.com/YOUR_OWNER/JD_select.git
```

这只是格式示例，不是本项目已经存在的地址。操作参考：[GitHub 创建仓库说明](https://docs.github.com/en/repositories/creating-and-managing-repositories/creating-a-new-repository)。

如果小组选择 Gitee，用该平台创建空仓库后复制其 HTTPS 地址；下面的 Git 命令相同，网页邀请和认证入口以 Gitee 当前界面为准。

### 3.2 上传已经初始化的本地仓库

组长在当前项目电脑打开 PowerShell：

若首次执行 git status 出现 `detected dubious ownership`，这是本机隔离账号创建仓库所致。先按第 12 节同名小节为 `D:/JD_select` 设置精确路径信任，再继续下面的命令。

```powershell
Set-Location D:\JD_select
git status
git branch --show-current
git log -1 --oneline
git remote -v
```

当前预期：分支为 main，有首次提交，remote -v 没有输出。然后把下面地址改成刚创建的真实地址：

```powershell
$repoUrl = "https://github.com/YOUR_OWNER/JD_select.git"
git remote add origin $repoUrl
git push -u origin main
```

如果首次操作触发登录，完成 Git Credential Manager 的浏览器登录。Git for Windows 包含 GCM，可管理 HTTPS 认证；不是把 git config 中的姓名当作登录账号。参考：[GitHub HTTPS 凭据说明](https://docs.github.com/en/get-started/git-basics/caching-your-github-credentials-in-git)。

若 origin 已存在，先用 `git remote -v` 核对，不要重复 add；确认确实需要改地址时用 `git remote set-url origin $repoUrl`。若 push 被拒绝，先查第 12 节，不要强推覆盖已有远程历史。

成功后刷新网页，应看到 frontend、backend、README.md 等。执行：

```powershell
git branch -vv
git ls-remote --heads origin main
```

第二条应返回一个提交哈希和 refs/heads/main。网页与命令都能看到 main 后，在线发布才算完成。

### 3.3 邀请另外三位组员

在 GitHub 仓库 Settings 中找到 Collaborators，添加组员各自的 GitHub 用户名或邮箱，发送邀请。组员接受邀请后，再用自己的账号克隆和推送。参考：[邀请协作者](https://docs.github.com/en/repositories/managing-your-repositorys-settings-and-features/repository-access-and-collaboration/inviting-collaborators-to-a-personal-repository)。

把“真实仓库 URL、main 为主分支、各人任务分工”发在群里。本文只说明操作，没有替你们创建在线仓库或发送邀请。

## 4. 组员第一次连接在线仓库

### 4.1 检查工具

安装 Git for Windows、Node.js 22.12+ 和 Python 3.13 后，重新打开 PowerShell：

```powershell
git --version
node --version
npm.cmd --version
python --version
```

工具安装入口见 [Git 官网](https://git-scm.com/install/windows)、[Node.js 官网](https://nodejs.org/)、[Python 官网](https://www.python.org/downloads/)。后两者的项目版本要求来自本仓库 README。

### 4.2 克隆到自己的电脑

选择一个用于存放项目的父目录。以下将项目放在用户目录下，避免依赖电脑是否有 D 盘：

```powershell
Set-Location $env:USERPROFILE
$repoUrl = "https://github.com/YOUR_OWNER/JD_select.git"
git clone $repoUrl JD_select
Set-Location JD_select
git remote -v
git branch --show-current
```

clone 会创建 JD_select 文件夹，并自动设置 origin。目标目录如果已存在且非空，请先确认是否已有仓库，或改用新目录名；不要覆盖自己的旧代码。clone 完成后不需要再 git init。

### 4.3 设置自己的提交署名

在刚克隆的项目目录内执行，使用自己的姓名和邮箱：

```powershell
git config user.name "你的姓名"
git config user.email "你的提交邮箱"
git config --get user.name
git config --get user.email
```

这是本仓库的提交署名，不会修改其他项目的配置，也不会给你远程写权限。远程权限来自账号及组长邀请。

## 5. 收到 JD_select.bundle 时怎么操作

bundle 是包含 Git 历史的离线文件，可以克隆；它本身不是可供四人持续 push 的服务器。参考：[Git bundle 文档](https://git-scm.com/docs/git-bundle)。

假设文件放在 Downloads，目标项目目录尚不存在：

```powershell
Set-Location $env:USERPROFILE
git clone "$env:USERPROFILE\Downloads\JD_select.bundle" JD_select
Set-Location JD_select
git log -1 --oneline
git remote -v
```

此时 origin 通常指向本机 bundle 文件。可以先开发和 commit，但在线上传前，要把 origin 改成组长发布的地址：

```powershell
$repoUrl = "https://github.com/YOUR_OWNER/JD_select.git"
git remote set-url origin $repoUrl
git fetch origin
git branch --set-upstream-to=origin/main main
git remote -v
```

这里假定组长已经把同一份项目历史推到了远程 main。若 origin/main 不存在，请先让组长完成首次发布。没有本地新增提交时，可在干净的 main 执行 `git pull --ff-only`；已有自己的提交时先保留为功能分支并走 PR，不要覆盖远程。

**在线克隆和 bundle 克隆二选一即可，不需要做两次。**

## 6. 运行刚拿到的前后端项目

在仓库根目录打开第一个终端：

```powershell
python -m venv backend/.venv
backend/.venv/Scripts/python.exe -m pip install -r backend/requirements.txt
if (-not (Test-Path backend/.env)) {
    Copy-Item backend/.env.example backend/.env
}
backend/.venv/Scripts/python.exe -m uvicorn app.main:app --app-dir backend --host 127.0.0.1 --port 8000 --reload
```

在仓库根目录再开第二个终端：

```powershell
Set-Location frontend
npm.cmd ci
if (-not (Test-Path .env)) {
    Copy-Item .env.example .env
}
npm.cmd run dev
```

打开 http://127.0.0.1:5173，点击“检查后端连接”，应显示 ok。后端文档在 http://127.0.0.1:8000/docs。两个终端分别按 Ctrl+C 停止。

以后启动不必重新建虚拟环境；拉取后依赖清单变动时再安装。每人的 .env 独立，新增配置应同步修改 .env.example；VITE_* 是浏览器可见配置。详细变量含义见 [项目 README](../README.md)。

## 7. 每次开始任务：先同步再建分支

在项目根目录执行，先确认 status 没有未提交修改：

```powershell
git status
git switch main
git pull --ff-only origin main
git switch -c feat/b-resume-parser
```

`feat/b-resume-parser` 是成员 B 开发简历解析的示例。建议分支命名：

| 成员 | 本轮分支示例 |
|---|---|
| A | feat/a-history-storage |
| B | feat/b-resume-parser |
| C | feat/c-match-scoring |
| D | feat/d-result-page |

一个任务一个分支。同一任务第二天继续时用 `git switch feat/b-resume-parser`，不要再次加 -c。其他成员不要直接往你的分支提交；需要改同一契约时先约定字段和职责。

如果 status 有未提交修改，先 commit，或按第 11 节暂存工作，再切换和同步。

## 8. 把自己的代码上传到仓库

下面以成员 B 为例，假设新建了 `backend/app/services/resume_parser.py`。

### 8.1 在克隆的项目目录里开发

新代码放进对应模块目录。若代码原先在另一个文件夹，把所需源码复制到当前功能分支的对应目录，检查依赖和接口；不要复制对方的 .git、.venv 或 node_modules。

### 8.2 检查与验证

```powershell
git branch --show-current
git status
git diff
```

git diff 显示已跟踪文件的未暂存修改；新文件要先查看内容，add 后再用 git diff --cached 检查。

修改前端时，在 frontend 执行 `npm.cmd run build`。修改后端时启动服务并验证对应接口；已有测试后再运行相关测试。本骨架目前没有配置 pytest 或前端 test 命令，不能把不存在的测试算作通过。

### 8.3 选择文件并创建本地提交

仅当示例文件实际存在且属于本次任务时执行；否则替换成自己修改的真实路径：

```powershell
git add backend/app/services/resume_parser.py
git diff --cached
git commit -m "feat: add resume text parser"
```

多个文件可一次写在 add 后面。删除文件也用其原路径执行 git add，以记录删除。修改依赖时，将依赖声明和对应锁文件一起提交。

### 8.4 上传当前功能分支

```powershell
git push -u origin feat/b-resume-parser
```

-u 会设置该分支的远程跟踪关系。以后仍在此分支时，新增修改按以下循环：

```powershell
git add backend/app/services/resume_parser.py
git commit -m "fix: handle empty resume input"
git push
```

commit 成功只代表本机已保存；push 成功才代表远程分支收到提交，仍不代表已合并 main。

### 8.5 确认上传成功

```powershell
git status
git log -1 --oneline
git ls-remote --heads origin feat/b-resume-parser
```

远程分支返回的哈希应与本地最新提交对应。再到网页切换至该功能分支，确认文件和提交说明存在。不要只在 main 页面查找尚未合并的代码。

## 9. 提交 PR，让代码进入 main

以 GitHub 为例：进入仓库 Pull requests → New pull request，选择 base 为 main、compare 为自己的功能分支，检查差异并创建 PR。参考：[GitHub 创建 PR](https://docs.github.com/en/pull-requests/how-tos/create-pull-requests/creating-a-pull-request)。

PR 描述可以直接套用：

```text
目的：支持粘贴简历后的分段解析。
改动：新增解析服务；补齐空文本处理。
验证：写明实际执行的命令、输入和结果。
接口影响：列出新增/变更字段；无变更则填写“无”。
需要复核：请另一位成员核对接口和示例输出。
```

收到修改意见后，在原分支继续修改、commit、push，现有 PR 会更新。由另一人检查后，在网页合并；有冲突则先处理第 10 节。

PR 显示 Merged 后，每人都可获取合并后的代码：

```powershell
git switch main
git pull --ff-only origin main
```

下一项任务从这个最新 main 创建新分支。旧功能分支可暂时保留，避免新手误删尚有工作内容的分支。日常开发不直接 push main；组长首次发布 main 是初始化步骤。

## 10. 开发中同步队友代码与解决冲突

### 10.1 把最新 main 合入自己的功能分支

先提交当前工作，使工作区干净。在功能分支执行：

```powershell
git switch feat/b-resume-parser
git fetch origin
git merge --no-edit origin/main
```

无冲突时，验证功能后 git push。这里的 merge 不会把你的功能分支反向合并进远程 main，仍需 PR。

### 10.2 出现冲突时

git status 会列出冲突文件。用编辑器打开，常见标记如下：

```text
<<<<<<< HEAD
自己分支的内容
=======
main 中的内容
>>>>>>> origin/main
```

与负责该文件的队友核对，整理出最终内容，删除三行标记。两边逻辑可能都需要保留，不要机械地整段接受某一方。解决全部文件后：

```powershell
git add backend/app/services/resume_parser.py
git status
git commit -m "merge: resolve resume parser conflict with main"
git push
```

上面的文件名同样需替换成实际冲突文件；所有冲突解决后再 commit。重新运行相关功能验证。若 merge 打开提交消息编辑器，保存并关闭即可；`--no-edit` 用于无冲突情况下避免额外编辑。

如果暂时无法确定正确结果，可在尚未完成的 merge 中执行 `git merge --abort`，退出本次合并后与队友协商。正因为开始前已提交工作，这个恢复路径更清楚。参考：[Git merge 文档](https://git-scm.com/docs/git-merge)。

## 11. 常用补救：保留已有工作

| 情况 | 处理 |
|---|---|
| add 选错文件，还没 commit | git restore --staged 路径，只取消暂存，文件内容保留 |
| 临时切换任务但代码未完成 | git stash push -u -m "resume work in progress"；回到原分支后 git stash pop |
| 写到 main，但还没 commit | git switch -c feat/b-resume-parser，把当前修改带到新分支后提交 |
| main 已有自己的未推送提交 | 先 git switch -c feat/b-resume-parser，再推送此功能分支并提 PR；保留本地 main，后续由熟悉 Git 的成员协助整理 |
| 想查看此前提交 | git log --oneline -10；git show 提交哈希 |
| 已合并代码需要撤回 | 与复核者确认要撤销的提交，在新分支用 git revert 提交哈希，再提 PR |

stash -u 包含未跟踪文件但不包含被忽略的 .env 等文件；pop 也可能有冲突，按第 10 节检查，冲突未处理前不要删除 stash。普通提交的 revert 会产生一个新的撤销提交；合并提交需要额外选择父分支，不要直接套用普通提交示例。

## 12. 常见错误与排查

### Failed to connect to github.com port 443（本机已验证）

2026-09-08 更新：当前 origin 已设置为 `https://github.com/thereisnoans/JD_select.git`，覆盖本文早期“尚无远程地址”的描述。本机 DNS 可解析 GitHub，但 HTTPS 直连超时；Windows 系统代理为 `127.0.0.1:7897`，Git 未配置代理。临时指定该 HTTP 代理后，GitHub 返回 200 OK，git ls-remote origin 成功退出且无引用输出（当前未列出远程分支）。这验证了读连接，不代表已验证 push 写权限。

保持本机代理软件运行，在项目 PowerShell 中执行以下方案。此处是操作说明，本次诊断未保存代理或推送。

```powershell
Set-Location D:\JD_select
git config --local http.proxy http://127.0.0.1:7897
git config --local --get http.proxy
git ls-remote origin
git push -u origin main
```

`--local` 只设置本项目；`http.proxy` 同样适用于 HTTPS 远程。第二条查询应输出代理地址。空仓库 ls-remote 可以成功但不输出内容；在 PowerShell 中紧接着检查 `$LASTEXITCODE`，0 表示成功。push 若提示登录，完成自己的 GitHub 登录；403 等权限问题另按下文排查。

仅临时使用可执行 `git -c http.proxy=http://127.0.0.1:7897 push -u origin main`。以后代理端口变化，更新同一个配置；恢复可直连网络且不再需要代理时，用 `git config --local --unset http.proxy` 撤销。7897 是本机实际检测并验证的端口，其他组员应使用各自的真实代理端口。

无需重建仓库或关闭 SSL 校验：本次超时发生在连接阶段。参考：[GitHub 网络排查](https://docs.github.com/en/get-started/using-github/troubleshooting-connectivity-problems)。

### Repository not found / 403 / Authentication failed

先 git remote -v 核对地址，确认登录的是收到邀请的账号、邀请已经接受且有写权限。能在浏览器登录不一定代表命令行使用同一账号。GitHub HTTPS 可通过 GCM 浏览器登录；账号密码不能直接替代其 Git 认证凭据。按第 3.2 节官方文档排查认证，不把 token 写进仓库 URL 或提交文件。

### remote origin already exists

说明已经设置 origin。查看 git remote -v；地址正确就跳过 add，需要替换时执行 git remote set-url origin 真实地址。bundle 克隆属于需要换成在线地址的常见情况。

### src refspec main does not match any

检查 git branch --show-current 和 git log -1，通常是分支名不同或没有提交。本项目初始分支应为 main；组员应克隆现有项目，不要另建空仓库冒充本项目历史。

### non-fast-forward / failed to push some refs

当前分支的远程已有你本地没有的提交。保存本地工作后，在对应分支执行：

```powershell
git fetch origin
git merge --no-edit origin/feat/b-resume-parser
```

将示例分支名换为被拒绝的功能分支。解决冲突、验证后重新 push。若组长首次推 main 就遇到此错误，检查在线仓库是否自动创建了 README 或其实已有代码；先确认正确历史，不要强推或盲目合并无关历史。

### Your local changes would be overwritten / pull 无法快进

前者先 commit 或 stash；后者说明历史已分叉，检查 git log --oneline --graph --all -15。功能分支按第 10 节 merge，本地 main 若有个人提交按第 11 节保留分支再整理。

### 文件没有上传

运行 git status 和 git diff --cached，确认文件已 add、commit、push；确认网页查看正确分支。用 git check-ignore -v 文件路径查是否被忽略。当前 .env、虚拟环境、node_modules、数据库以及根目录课程/简历附件均按项目规则忽略。新增需要共享的配置说明放进 .env.example。

### detected dubious ownership

本项目创建电脑曾因隔离账号创建 .git 出现所有者不同。仅在确认该目录确实是自己的项目时，可对单条命令加参数：

报错里的仓库所有者是 Windows 账号 `CodexSandboxOnline`，当前操作账号是 `lq280`，两者 SID 不同。Git 默认拒绝使用其他用户拥有的仓库。这与 GitHub 登录、提交署名、代码内容无关，也不代表仓库损坏。

本机长期使用的推荐处理：在自己的普通 PowerShell 中执行一次：

```powershell
git config --global --add safe.directory "D:/JD_select"
Set-Location D:\JD_select
git status
```

`--global` 表示写入当前用户的 Git 配置，信任范围仍只有指定项目路径；它不更改文件所有者、不修改代码，也不授予远程仓库权限。首次配置命令成功一般没有输出。运行 `git config --global --get-all safe.directory` 可确认列表包含 `D:/JD_select`。不要把路径写成带 Markdown 转义的 `D:/JD\_select`。

不想保存配置时，可仅对本次调用指定：

```powershell
git -c safe.directory=D:/JD_select status
```

其他命令同理把参数放在 git 后面。路径换成实际可信项目路径；正常在自己账号下 clone 的组员通常不需要此参数。

依据：[Git safe.directory 官方说明](https://git-scm.com/docs/git-config#Documentation/git-config.txt-safedirectory)。该设置需放在受保护的配置作用域；不要改用 `--local`，也不需要把所有仓库设为通配符信任。

### npm 在 PowerShell 提示脚本执行受限

使用 npm.cmd ci 和 npm.cmd run dev。本指南的后端启动命令直接使用虚拟环境里的 python.exe，无需运行 Activate.ps1。

## 13. 每天可照抄的操作卡

下列是“新任务”的例子，运行前确认在仓库根目录，分支名和 add 路径换成自己的真实任务。

```powershell
# 开始前：status 应无未提交修改
git status
git switch main
git pull --ff-only origin main
git switch -c feat/b-resume-parser

# 编写和验证代码后
git status
git diff
git add backend/app/services/resume_parser.py
git diff --cached
git commit -m "feat: add resume parser"
git push -u origin feat/b-resume-parser

# 网页创建 PR，另一人复核合并后
git switch main
git pull --ff-only origin main
```

继续昨天的任务：switch 到已有功能分支 → 提交当前工作 → fetch → merge origin/main → 开发验证 → add / commit / push。

本指南的命令是操作说明，不表示远程已经发布、邀请已经接受或 PR 已经合并；最终以 git remote -v、远程分支和平台页面为准。
