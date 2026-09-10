"""C2 自查脚本：JD 解析 + 必需/加分技能识别 对照 YAML 标准答案验证。

用法（在 JD_select 根目录或 backend 目录下均可）：
    python backend/scripts/validate_jd_parser.py
退出码：0 全部通过；1 存在问题（可接入 pytest）。

验证内容：
1. 6 份样例 JD：解析出的 required_skills / bonus_skills 与 YAML 头标注
   （required_skills / bonus_skills）严格一致，且无标注外技能（防虚假命中）；
2. 否定词合成用例：无需 / 无要求 / 不要求 应归入 negated_skills，
   既不计入必需也不计入加分；
3. 同义词/大小写归一化由 jd_005 的 “pytorch -> PyTorch” 隐式覆盖。
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]  # scripts -> backend -> 仓库根目录
BACKEND_DIR = REPO_ROOT / "backend"
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from app.services.jd_parser import parse_jd  # noqa: E402

SAMPLE_DIR = REPO_ROOT / "sample_data"


def parse_jd_header(md_text: str) -> dict:
    """解析样例 JD 文件头部的最小 YAML 子集（--- 到首个空行之间）。"""
    result: dict = {}
    for line in md_text.splitlines():
        if line.startswith("---"):
            continue
        if line.strip() == "":
            break
        m = re.match(r"^([a-z_]+):\s*(.*)$", line.strip())
        if not m:
            continue
        key, value = m.groups()
        if key in ("required_skills", "bonus_skills"):
            result[key] = [v.strip() for v in value.strip("[]").split(",") if v.strip()]
        else:
            result[key] = value.strip().strip('"')
    return result


# 否定词合成用例：(JD 片段, 应被归入否定的技能)
NEGATION_CASES = [
    ("无需熟悉 Docker 或掌握 Kubernetes，具备基本运维常识即可", {"Docker", "Kubernetes"}),
    ("本岗位对 Nginx 配置无要求", {"Nginx"}),
    ("不要求掌握 CI/CD 流水线搭建", {"CI/CD"}),
]


def check_sample(path: Path, problems: list[str]) -> None:
    raw = path.read_text(encoding="utf-8")
    meta = parse_jd_header(raw)
    result = parse_jd(raw)

    expected_required = set(meta.get("required_skills", []))
    expected_bonus = set(meta.get("bonus_skills", []))
    got_required = {s["name"] for s in result["required_skills"]}
    got_bonus = {s["name"] for s in result["bonus_skills"]}
    got_all = got_required | got_bonus

    print(f"[{path.name}] {result['job_title']}")
    print(f"  必需: {sorted(got_required)}")
    print(f"  加分: {sorted(got_bonus)}")
    if result["negated_skills"]:
        print(f"  否定: {sorted(s['name'] for s in result['negated_skills'])}")

    if got_required != expected_required:
        problems.append(
            f"{path.name}: 必需不一致 | 标注={sorted(expected_required)} 解析={sorted(got_required)}"
        )
    if got_bonus != expected_bonus:
        problems.append(
            f"{path.name}: 加分不一致 | 标注={sorted(expected_bonus)} 解析={sorted(got_bonus)}"
        )
    if got_all != expected_required | expected_bonus:
        problems.append(f"{path.name}: 存在标注外技能 | {sorted(got_all - expected_required - expected_bonus)}")

    # 人工抽查辅助：打印每条技能的信号与证据（每个技能只列 1 条）
    for item in result["required_skills"] + result["bonus_skills"] + result["negated_skills"]:
        print(f"    - [{item['signal']}] {item['name']} | {item['evidence']}")


def check_negation(problems: list[str]) -> None:
    print("\n=== 否定词合成用例 ===")
    for text, expected in NEGATION_CASES:
        result = parse_jd(text)
        negated = {s["name"] for s in result["negated_skills"]}
        required = {s["name"] for s in result["required_skills"]}
        bonus = {s["name"] for s in result["bonus_skills"]}
        ok = expected <= negated and not (expected & required) and not (expected & bonus)
        print(f"  {'通过' if ok else '失败'}: 期望否定 {sorted(expected)} | 实际否定={sorted(negated)}")
        if not ok:
            problems.append(f"否定词用例失败: {text!r}")


def main() -> int:
    print("=== 1. 6 份样例 JD 解析 vs YAML 标准答案 ===")
    problems: list[str] = []
    jd_files = sorted(SAMPLE_DIR.glob("jd_*.md"))
    if len(jd_files) < 5:
        problems.append(f"样例 JD 不足 5 份：当前 {len(jd_files)} 份")
    for path in jd_files:
        check_sample(path, problems)
        print()

    check_negation(problems)

    if problems:
        print(f"\n校验未通过，共 {len(problems)} 个问题。")
        for p in problems:
            print(f"  [问题] {p}")
        return 1
    print("\n校验全部通过。")
    return 0


if __name__ == "__main__":
    sys.exit(main())
