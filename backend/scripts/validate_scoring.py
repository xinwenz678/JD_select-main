"""C3 自查脚本：评分算法 5 个验收场景 + 确定性 + 边界 + 契约字段检查。

用法（在 JD_select 根目录或 backend 目录下均可）：
    python backend/scripts/validate_scoring.py
退出码：0 全部通过；1 存在问题（可接入 pytest）。

验证内容：
1. 完整匹配：Python/FastAPI/SQL/... 简历 + jd_001 -> 高分(>=80)、缺失为空；
2. 部分匹配：仅 Python/Excel 简历 + jd_001 -> 中低分、明确列出 FastAPI/SQL 差距；
3. 低匹配：市场运营简历 + jd_001 -> 低分(<40)，且不得虚假命中 Python/SQL；
4. 空输入：空简历 / 空 JD 均被拒绝（ValueError，接口层将转 422）；
5. 同义词：pytorch -> PyTorch 归一化后视为同一技能（jd_005）；
6. 确定性：同一输入两次评分结果一致；0<=score<=100；分项之和=总分；
7. 契约字段：score_breakdown 键名、algorithm_version 与冻结契约一致。
"""
from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]  # scripts -> backend -> 仓库根目录
BACKEND_DIR = REPO_ROOT / "backend"
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from app.services.jd_parser import parse_jd  # noqa: E402
from app.services.scoring import score_match, score_match_texts  # noqa: E402

SAMPLE_DIR = REPO_ROOT / "sample_data"

FULL_RESUME = """岗位：Python 后端开发工程师

工作经历
2022.06 - 至今 某互联网科技公司 后端开发工程师
负责公司核心业务系统的服务端设计与开发，使用 Python 编写高质量代码，基于 FastAPI 框架搭建并维护 RESTful API 服务，使用 Git 进行代码版本管理，参与 Code Review。
参与数据库表结构设计与 SQL 查询优化，配合 DBA 完成慢查询治理，将接口平均响应时间降低 40%。
熟悉 Docker 容器化部署，编写 Dockerfile 并维护 CI/CD 流水线。

项目经历
2023.01 - 2023.06 订单系统重构项目
主导订单系统重构，优化核心链路，支撑日均 10 万请求，系统可用性提升至 99.9%。
了解 Redis 缓存、Kafka 消息队列，掌握 MySQL 或 PostgreSQL 等关系型数据库。
"""

PARTIAL_RESUME = """岗位：数据分析实习生

实习经历
2023.07 - 2023.12 某电商公司 数据分析实习生
使用 Python 处理业务数据，使用 Excel 制作业务报表，支持周报月报的数据整理。
参与用户流失分析项目，通过数据分析发现关键问题，帮助业务方调整运营策略，活动转化率提升 15%。
"""

LOW_RESUME = """岗位：市场运营专员

工作经历
2021.03 - 至今 某教育公司 市场运营专员
负责用户社群的日常运营，策划线上活动，撰写推广文案，维护公众号与用户群。
使用 Excel 整理运营数据，制作日常数据报表，收集用户反馈并推动产品改进。
"""

SYNONYM_RESUME = """岗位：算法工程师

项目经历
使用 pytorch 训练图像分类模型，熟悉 tensorflow，了解机器学习与深度学习基础，熟练使用 Python 完成数据处理。
"""


def load_jd(name: str) -> dict:
    return parse_jd((SAMPLE_DIR / name).read_text(encoding="utf-8"))


def report(title: str, result: dict, problems: list[str]) -> None:
    """打印人工抽查结果：总分 / 分项 / 匹配 / 缺失。"""
    bd = result["score_breakdown"]
    print(f"  {title}: 总分 {result['score']} "
          f"(必需 {bd['required_skills']} + 加分 {bd['preferred_skills']} + 证据 {bd['evidence_quality']})")
    print(f"    匹配技能: {result['matched_skills']}")
    print(f"    缺失技能: {result['missing_skills']}")
    if result["suggestions"]:
        print(f"    建议: {result['suggestions'][0]}")


def check_contract(result: dict, problems: list[str]) -> None:
    if set(result["score_breakdown"].keys()) != {"required_skills", "preferred_skills", "evidence_quality"}:
        problems.append("score_breakdown 键名与冻结契约不一致")
    if result["algorithm_version"] != "rule-v1":
        problems.append(f"algorithm_version 应为 rule-v1，实际 {result['algorithm_version']}")
    if not (0 <= result["score"] <= 100):
        problems.append(f"分数越界：{result['score']}")
    if sum(result["score_breakdown"].values()) != result["score"]:
        problems.append("分项之和与总分不一致")


def check_full_match(problems: list[str]) -> None:
    print("=== 场景 1：完整匹配（Python/FastAPI/SQL 简历 + jd_001）===")
    result = score_match(FULL_RESUME, load_jd("jd_001_backend_python.md"))
    report("完整匹配", result, problems)
    ok = result["score"] >= 80 and not result["missing_skills"]
    print(f"  {'通过' if ok else '失败'}: 高分(>=80)且无缺失 | 得分 {result['score']}")
    if not ok:
        problems.append("完整匹配：未达到高分且无缺失")
    check_contract(result, problems)


def check_partial_match(problems: list[str]) -> None:
    print("\n=== 场景 2：部分匹配（仅 Python/Excel 简历 + jd_001）===")
    result = score_match(PARTIAL_RESUME, load_jd("jd_001_backend_python.md"))
    report("部分匹配", result, problems)
    ok = (10 <= result["score"] < 60
          and "FastAPI" in result["missing_skills"] and "SQL" in result["missing_skills"])
    print(f"  {'通过' if ok else '失败'}: 明确列出 FastAPI/SQL 差距 | 得分 {result['score']}")
    if not ok:
        problems.append("部分匹配：未明确列出 FastAPI/SQL 差距")
    check_contract(result, problems)


def check_low_match(problems: list[str]) -> None:
    print("\n=== 场景 3：低匹配（市场运营简历 + jd_001）===")
    result = score_match(LOW_RESUME, load_jd("jd_001_backend_python.md"))
    report("低匹配", result, problems)
    fake = {"Python", "SQL", "FastAPI"} & set(result["matched_skills"])
    ok = result["score"] < 40 and not fake
    print(f"  {'通过' if ok else '失败'}: 低分(<40)且无虚假命中 | 得分 {result['score']}, 虚假命中={sorted(fake)}")
    if not ok:
        problems.append("低匹配：分数过高或出现虚假命中")
    check_contract(result, problems)


def check_empty_input(problems: list[str]) -> None:
    print("\n=== 场景 4：空输入 ===")
    jd = load_jd("jd_001_backend_python.md")
    cases = [
        ("空简历", lambda: score_match("   ", jd)),
        ("空JD", lambda: score_match_texts(FULL_RESUME, "")),
        ("空JD(仅空白)", lambda: score_match_texts(FULL_RESUME, "  \n  ")),
    ]
    for name, fn in cases:
        try:
            fn()
        except ValueError:
            print(f"  通过: {name} 被拒绝（ValueError）")
        else:
            print(f"  失败: {name} 未被拒绝")
            problems.append(f"空输入：{name} 未被拒绝")


def check_synonym_and_determinism(problems: list[str]) -> None:
    print("\n=== 场景 5：同义词 + 确定性 ===")
    jd = load_jd("jd_005_ml_engineer.md")
    result = score_match(SYNONYM_RESUME, jd)
    report("同义词", result, problems)
    ok = "PyTorch" in result["matched_skills"] and "PyTorch" not in result["missing_skills"]
    print(f"  {'通过' if ok else '失败'}: pytorch 归一化为 PyTorch | 匹配={result['matched_skills']}")
    if not ok:
        problems.append("同义词：pytorch 未归一化命中 PyTorch")

    again = score_match(SYNONYM_RESUME, jd)
    if again["score"] != result["score"]:
        problems.append(f"确定性失败：两次评分不一致 {result['score']} != {again['score']}")
        print(f"  失败: 两次评分不一致")
    else:
        print(f"  通过: 同输入两次评分一致（{result['score']}）")
    check_contract(result, problems)
    check_contract(again, problems)


def main() -> int:
    problems: list[str] = []
    check_full_match(problems)
    check_partial_match(problems)
    check_low_match(problems)
    check_empty_input(problems)
    check_synonym_and_determinism(problems)

    if problems:
        print(f"\n校验未通过，共 {len(problems)} 个问题。")
        for p in problems:
            print(f"  [问题] {p}")
        return 1
    print("\n校验全部通过。")
    return 0


if __name__ == "__main__":
    sys.exit(main())
