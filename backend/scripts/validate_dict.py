"""C1 自查脚本：技能词典 + 同义词表 + 6 份样例 JD 三件套完整性校验。

用法（在 JD_select 根目录或 backend 目录下均可）：
    python backend/scripts/validate_dict.py
退出码：0 全部通过；1 存在问题（可接入 pytest）。
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]  # scripts -> backend -> 仓库根目录
BACKEND_DIR = REPO_ROOT / "backend"
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from app.services.skill_dict import extract_skills, validate_dictionary  # noqa: E402

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


def validate_samples() -> list[str]:
    problems: list[str] = []
    jd_files = sorted(SAMPLE_DIR.glob("jd_*.md"))
    if len(jd_files) < 5:
        problems.append(f"样例 JD 不足 5 份：当前 {len(jd_files)} 份")

    for path in jd_files:
        raw = path.read_text(encoding="utf-8")
        meta = parse_jd_header(raw)
        hits = extract_skills(raw)
        required = set(meta.get("required_skills", []))
        bonus = set(meta.get("bonus_skills", []))
        missing = sorted(required - set(hits))
        extras = sorted(set(hits) - required - bonus)

        print(f"[{path.name}] {meta.get('job_title', '(无标题)')}")
        print(f"  命中技能: {hits}")
        if missing:
            problems.append(f"{path.name}: 必需技能未命中 {missing}")
            print(f"  缺失(必需): {missing}")
        if extras:
            print(f"  额外命中(信息): {extras}")

    return problems


def main() -> int:
    print("=== 1. 词典/同义词表校验 ===")
    problems = validate_dictionary()
    for p in problems:
        print(f"  [问题] {p}")

    print("\n=== 2. 样例 JD 抽检 ===")
    problems += validate_samples()

    if problems:
        print(f"\n校验未通过，共 {len(problems)} 个问题。")
        return 1
    print("\n校验全部通过。")
    return 0


if __name__ == "__main__":
    sys.exit(main())
