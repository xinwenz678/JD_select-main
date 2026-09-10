# A2–A3 验证记录

日期：2026-09-08。环境：Windows、Python 3.13、FastAPI 0.115.12、SQLAlchemy 2.0.40、pytest 8.3.5、httpx 0.28.1。

执行命令：

```powershell
backend/.venv/Scripts/python.exe -m pytest -c backend/pytest.ini backend/tests -q
```

结果：26 passed，耗时约 2.79 秒。覆盖健康检查、空库、记录新增/详情/更新/删除、重启持久化、默认 10 条和分页、相同时间稳定排序、错误分页、非法和不存在 UUID、空白/过长文本、分数范围及分项一致性、非法 JSON、快照不可修改、404/405、允许/拒绝源的 CORS 预检、错误跨域头、数据库 503、通用 500、异常信息不泄露、事务回滚及后续请求恢复、不同工作目录下的数据库路径。

首次测试中长文本用例自动生成的用例名引发测试准备错误，改为简短显式用例名后全部通过。

存在一条第三方弃用提示：Starlette TestClient 使用 AnyIO 的旧 BlockingPortal 别名；不影响本次测试结果。未为消除此提示扩大依赖升级范围。

未验证：PostgreSQL、成员 C 的算法与 POST /api/matches、完整前端业务闭环、部署并发、多用户权限。代码仍需另一位组员按计划复核。测试通过不等于这些工作已完成。
