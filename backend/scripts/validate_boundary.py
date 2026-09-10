"""C5 自查脚本：边界与回归测试（一键跑完 C1 + C2 + C3 + 边界用例）。

用法（在 JD_select 根目录或 backend 目录下均可）：
    python backend/scripts/validate_boundary.py
退出码：0 全部通过；1 存在问题（可接入 pytest）。

覆盖内容：
A. 大小写归一化：python/PYTHON/Fastapi/PYTORCH 均能命中规范名；
B. 同义词归一化：golang/js/cpp/k8s/自然语言处理/大模型/AI Agent/提示词工程；
C. 词边界防误报（C1 最核心）：Nginx≠Gin、JavaScript≠Java、GitHub≠Git、
   MySQL≠SQL、Google≠Go，同时 Gin/node 正常命中；
D. 子串模式合理命中：Python3→Python、CI/CD、Spring Boot 不误中 Spring；
E. C2 句级信号词边界：否定词 / “X 或 Y”并列 / 逗号句“加分”串扰回归 /
   顿号不切句 / JD 大写；
F. C3 评分边界：大小写简历、同义词简历、空输入拒绝、0-100 越界、确定性；
G. 全量回归：自动重跑 validate_dict / validate_jd_parser / validate_scoring。
"""
from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]  # scripts -> backend -> 仓库根目录
BACKEND_DIR = REPO_ROOT / "backend"
SCRIPTS_DIR = BACKEND_DIR / "scripts"
for p in (str(BACKEND_DIR), str(SCRIPTS_DIR)):
    if p not in sys.path:
        sys.path.insert(0, p)

from app.services.jd_parser import classify_skills  # noqa: E402
from app.services.scoring import score_match_texts  # noqa: E402
from app.services.skill_dict import extract_skills  # noqa: E402

import validate_dict as v_dict  # noqa: E402
import validate_jd_parser as v_jd  # noqa: E402
import validate_scoring as v_score  # noqa: E402


def main() -> int:
    problems: list[str] = []

    def check(name: str, cond: bool, detail: str = "") -> None:
        ok = bool(cond)
        print(f"  {'通过' if ok else '失败'}: {name}" + (f" | {detail}" if detail else ""))
        if not ok:
            problems.append(f"{name}：{detail}")

    print("=== A. 大小写归一化 ===")
    check("python 小写命中 Python", "Python" in extract_skills("熟悉 python 开发"))
    check("PYTHON 大写命中 Python", "Python" in extract_skills("熟悉 PYTHON 开发"))
    check("Fastapi 混写命中 FastAPI", "FastAPI" in extract_skills("使用 fastapi 框架"))
    check("PYTORCH 全大写命中 PyTorch", "PyTorch" in extract_skills("使用 PYTORCH 训练"))

    print("\n=== B. 同义词归一化 ===")
    check("golang -> Go", "Go" in extract_skills("使用 golang 开发"))
    check("GOLANG 大写 -> Go", "Go" in extract_skills("使用 GOLANG 开发"))
    check("js -> JavaScript", "JavaScript" in extract_skills("熟练使用 js"))
    check("cpp -> C++", "C++" in extract_skills("熟悉 cpp"))
    check("k8s -> Kubernetes", "Kubernetes" in extract_skills("部署到 k8s"))
    check("自然语言处理 -> NLP", "NLP" in extract_skills("研究自然语言处理"))
    check("大模型 -> LLM", "LLM" in extract_skills("开发大模型应用"))
    check("AI Agent -> Agent", "Agent" in extract_skills("搭建 AI Agent"))
    check("提示词工程 -> Prompt", "Prompt" in extract_skills("熟悉提示词工程"))

    print("\n=== C. 词边界防误报 ===")
    check("Nginx 不命中 Gin", "Gin" not in extract_skills("使用 Nginx 反向代理"))
    check("JavaScript 不命中 Java", "Java" not in extract_skills("使用 JavaScript 开发"))
    check("GitHub 不命中 Git", "Git" not in extract_skills("使用 GitHub 托管代码"))
    check("MySQL 不命中 SQL", "SQL" not in extract_skills("使用 MySQL 数据库"))
    check("Google 不命中 Go", "Go" not in extract_skills("对接 Google API"))
    check("Gin 框架正常命中 Gin", "Gin" in extract_skills("使用 Gin 框架"))
    check("node 正常命中 Node.js", "Node.js" in extract_skills("使用 node 开发"))

    print("\n=== D. 子串模式合理命中 ===")
    check("Python3 -> Python", "Python" in extract_skills("使用 Python3 编写"))
    check("CI/CD 正常命中", "CI/CD" in extract_skills("维护 CI/CD 流水线"))
    _boot = extract_skills("基于 Spring Boot 开发")
    check("Spring Boot 正常命中", "Spring Boot" in _boot, str(_boot))
    check("Spring Boot 不误中 Spring", "Spring" not in _boot, str(_boot))

    print("\n=== E. C2 句级信号词边界 ===")
    _r = classify_skills("无需熟悉 Docker 或掌握 Kubernetes，具备基本运维常识即可")
    check("「无需」Docker/Kubernetes 归否定",
          _r.get("Docker") == "negated" and _r.get("Kubernetes") == "negated", str(_r))
    _r = classify_skills("掌握 MySQL 或 PostgreSQL 等关系型数据库")
    check("「MySQL 或 PostgreSQL」并列归加分",
          _r.get("MySQL") == "bonus" and _r.get("PostgreSQL") == "bonus", str(_r))
    _r = classify_skills("熟悉 CI/CD 流程，有 Jenkins 使用经验者加分")
    check("CI/CD 不被逗号句「加分」误伤", _r.get("CI/CD") == "required", str(_r))
    check("同句 Jenkins 正常加分", _r.get("Jenkins") == "bonus", str(_r))
    _r = classify_skills("了解 Redis 缓存、Kafka 消息队列者加分")
    check("顿号不切句、整体判加分",
          _r.get("Redis") == "bonus" and _r.get("Kafka") == "bonus", str(_r))
    _r = classify_skills("使用 PYTHON 编写高质量代码")
    check("JD 大写 PYTHON 命中且归必需", _r.get("Python") == "required", str(_r))

    print("\n=== F. C3 评分边界 ===")
    _jd = "岗位：后端 任职要求 1. 熟悉 Python、FastAPI；2. 熟练使用 SQL"
    _res1 = score_match_texts("使用 PYTHON 开发，熟悉 fastapi 与 sql", _jd)
    check("大小写简历命中且无缺失",
          "Python" in _res1["matched_skills"] and "FastAPI" in _res1["matched_skills"]
          and "SQL" in _res1["matched_skills"] and not _res1["missing_skills"], str(_res1["matched_skills"]))
    _jd2 = "岗位：后端 任职要求 1. 熟悉 Go 与 C++；2. 掌握 Kubernetes"
    _res2 = score_match_texts("会 golang 和 cpp，熟悉 k8s 部署", _jd2)
    check("同义词简历命中",
          "Go" in _res2["matched_skills"] and "C++" in _res2["matched_skills"]
          and "Kubernetes" in _res2["matched_skills"], str(_res2["matched_skills"]))
    try:
        score_match_texts("", _jd)
        check("空简历被拒绝", False, "未抛异常")
    except ValueError:
        check("空简历被拒绝", True)
    try:
        score_match_texts("熟悉 Python 开发", "")
        check("空 JD 被拒绝", False, "未抛异常")
    except ValueError:
        check("空 JD 被拒绝", True)
    check("分数 0-100 且分项之和=总分",
          0 <= _res1["score"] <= 100 and sum(_res1["score_breakdown"].values()) == _res1["score"])
    _again = score_match_texts("使用 PYTHON 开发，熟悉 fastapi 与 sql", _jd)
    check("确定性：同输入同分", _again["score"] == _res1["score"],
          f"{_res1['score']} vs {_again['score']}")

    print("\n=== G. 全量回归（C1/C2/C3 验证脚本）===")
    for name, mod in (("C1 词典", v_dict), ("C2 JD 解析", v_jd), ("C3 评分", v_score)):
        rc = mod.main()
        print(f"  [{name}] 退出码 {rc}")
        if rc != 0:
            problems.append(f"全量回归失败：{name}")

    if problems:
        print(f"\nC5 校验未通过，共 {len(problems)} 个问题。")
        for p in problems:
            print(f"  [问题] {p}")
        return 1
    print("\nC5 边界与回归：校验全部通过。")
    return 0


if __name__ == "__main__":
    sys.exit(main())
