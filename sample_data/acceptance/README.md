# B 固定验收数据

日期：2026-09-10。全部为合成输入，不代表真实学生、招聘需求或市场统计。

`cases.json` 是机器可读的唯一输入与预期来源；不得为了当前算法通过而删除 SQL、改写并列技能或降低同义词要求。规则版本为 rule-v1，未来版本改变时由 A/B 共同评审预期。

| 场景 | 预期分数 | 必须匹配 | 必须缺失 | 证据 |
|---|---|---|---|---|
| TC01 完整 | 80–100 | Python/FastAPI/SQL/Excel | 无 | 简历第 3 行 |
| TC02 部分 | 30–60 | Python/Excel | FastAPI/SQL | 已有技能：简历第 3 行；缺口：JD 第 2 行 |
| TC03 低匹配 | 0–20 | 无 | Python/FastAPI/SQL | JD 第 2 行；不得生成简历技能命中 |
| TC04 空输入 | HTTP 422，无记录 | 不适用 | 不适用 | 分别测试空/纯空白简历和 JD |
| TC05 同义词 | 80，三种写法一致 | PyTorch/JavaScript | 无 | 简历第 3 行；重复技能不重复计分 |

范围是验收约束，不是用户界面的“高/中/低”产品阈值。每条 evidence 的 source、line、text 必须对应完整输入中的原始行，不能只验证数量。成功保存后详情内容应一致；相同输入重新提交应分数确定、记录 UUID 不同。

本次实际：TC01=91、TC02=50、TC03=1，但三者均漏掉 SQL，因此整体不通过。TC05 规范写法=80，pytorch/JS 并列写法=50，因此不通过。不能仅凭分数落在区间内宣布验收成功。

`star-comparison.json` 是人工核对的 STAR 建议基准，未知成果保留待填写，人工对照文件不是系统输出。本轮已用真实规则 STAR 接口验证无 Key 的确定性和 UI 不覆盖原文；当前没有 LLM 实现，不能声称有 Key/模型超时回退已通过。

执行：项目根目录用已安装开发锁依赖的 Python 运行 `python -m pytest -c backend/pytest.ini backend/tests/test_b_acceptance.py -q`。详细总门禁见 `scripts/b-review.py` 与 `docs/b-review-progress.md`。
