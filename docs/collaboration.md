# 四人协作

首次使用 Git 请先阅读 [详细操作指南](git-collaboration-guide.md)，涵盖连接、分支、上传、PR 和冲突处理。

- A：平台与持久化；B：简历；C：匹配；D：结果体验与验收。
- `main` 保持可运行。每项工作从最新 `main` 创建 `feat/任务名` 分支。
- 修改公共 schema 或 API 时同时通知调用方；通过 Pull Request 合并，由另一人复核。
- 不共享虚拟环境或 node_modules；每人在本机安装锁定依赖。
- 进度、剩余任务和已验证事实记录在 `handoff.md`。

```powershell
git switch main
git pull --ff-only
git switch -c feat/resume-parser
# 完成开发后明确选择本次修改的文件
git add backend/app/services/
git commit -m "feat: add resume parser"
git push -u origin feat/resume-parser
```

远程托管接通后，仓库所有者在托管平台邀请其余三位成员。
