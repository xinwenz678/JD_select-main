"""评分算法（C3 交付）：简历技能 × JD 必需/加分 → 0-100 可解释匹配分。

评分公式 v1（项目冻结契约，见 docs/requirements.md）：
    总分 = 必需技能覆盖率(60) + 加分技能覆盖率(20) + 经历证据质量(20)

    - 必需技能覆盖率：命中必需技能数 / JD 必需总数 × 60
      （JD 必需为空 => 该项满分 60，无必需即无缺失）
    - 加分技能覆盖率：命中加分技能数 / JD 加分总数 × 20
      （JD 加分为空 => 该项满分 20，无加分项即不失分）
    - 经历证据质量（20）：
        量化成果   10 分：命中“数字+量词 / 动词+数字”证据条数 × 2，封顶 10
        动作动词    5 分：命中的强动词种数 × 1，封顶 5
        项目/实习   5 分：命中的经历区块类别数 × 2，封顶 5

可解释性约定：
1. 纯规则、无外部 API、同输入必同输出（确定性）；
2. 技能未命中绝不猜测为已掌握——matched/missing 严格按 C1 词典提取结果计算；
3. 返回 score_breakdown 与 evidence_detail，结果页可逐项展示“评分依据”；
4. 结果页需展示“匹配分用于辅助判断，不代表录用概率”。

已知边界（写入 C6 算法文档）：
- 量化分按“去重证据片段数”计，同一数字可能同时命中“动词+数字”与“裸百分比”
  两条（如“提升 30%”），属可接受的轻微上浮，有封顶；
- 简历技能列表当前直接复用 C1 extract_skills 从简历文本提取；
  待 B 的简历结构化解析器接入后，可传入其解析结果替换（接口已留 resume_skills 参数）。
"""
from __future__ import annotations

import json
import re
from pathlib import Path

# 允许本文件被 scripts/ 下的脚本以绝对路径直接运行
if __package__ in (None, ""):
    import sys
    _BACKEND_DIR = Path(__file__).resolve().parents[2]  # services -> app -> backend
    if str(_BACKEND_DIR) not in sys.path:
        sys.path.insert(0, str(_BACKEND_DIR))

from app.services.jd_parser import parse_jd  # noqa: E402
from app.services.skill_dict import canonicalize_skills, extract_skills, normalize  # noqa: E402

DATA_DIR = Path(__file__).resolve().parents[1] / "data"
RULES_FILE = DATA_DIR / "scoring_rules.json"

_cache: dict = {"rules": None}


def load_rules() -> dict:
    """加载评分规则（动作动词 / 量化模式 / 经历区块词），结果缓存。"""
    if _cache["rules"] is None:
        with RULES_FILE.open(encoding="utf-8") as f:
            _cache["rules"] = json.load(f)
    return _cache["rules"]


def _evidence_score(resume_text: str) -> dict:
    """经历证据质量评分，返回 (quant, verbs, sections, total) 及命中明细。

    - quant：任一量化模式命中的“证据片段”去重计数，每条 2 分封顶 10；
    - verbs：命中的强动词种数，每种 1 分封顶 5；
    - sections：命中的经历区块类别数（project/internship/work），每类 2 分封顶 5。
    """
    rules = load_rules()
    norm = normalize(resume_text)

    quant_phrases: set[str] = set()
    for pat_str in rules["quant_patterns"]:
        for m in re.finditer(pat_str, resume_text):
            phrase = normalize(m.group(0))
            if phrase:
                quant_phrases.add(phrase)
    quant_score = min(10, 2 * len(quant_phrases))

    verbs_hit = [v for v in rules["action_verbs"] if normalize(v) in norm]
    verbs_score = min(5, len(verbs_hit))

    sections = rules["evidence_sections"]
    section_hits = [
        cat for cat, kws in sections.items() if any(normalize(k) in norm for k in kws)
    ]
    sections_score = min(5, 2 * len(section_hits))

    return {
        "quant": quant_score,
        "verbs": verbs_score,
        "sections": sections_score,
        "total": quant_score + verbs_score + sections_score,
        "quant_hits": sorted(quant_phrases)[:8],
        "verb_hits": verbs_hit,
        "section_hits": section_hits,
    }


def _build_suggestions(missing: list[str], evidence: dict, jd_result: dict) -> list[str]:
    """规则化改进建议：缺技能 > 缺量化 > 动词单一 > 缺经历区块。最多 6 条。"""
    suggestions: list[str] = []
    jd_evidence = {s["name"]: s.get("evidence", "") for s in jd_result.get("required_skills", [])}
    for name in missing:
        tail = f"（JD 依据：{jd_evidence.get(name, '')}）" if jd_evidence.get(name) else ""
        suggestions.append(
            f"简历缺少岗位必需技能「{name}」，建议补充相关项目经历或在技能清单中体现{tail}"
        )
    if evidence["quant"] < 10:
        suggestions.append("经历描述缺少量化成果，建议为关键成果补充数字，如「提升 30%」「处理 10000 条」")
    if evidence["verbs"] < 3:
        suggestions.append(
            f"动作动词较单一（当前 {evidence['verbs']} 种），建议使用「主导/负责/优化/搭建」等强动词"
        )
    if evidence["sections"] == 0:
        suggestions.append("未检测到项目/实习/工作经历描述，建议补充以支撑技能证据")
    return suggestions[:6]



def _evidence_items(resume_text: str, jd_text: str, matched: list[str], missing: list[str], evidence: dict) -> list[dict]:
    """Build stable, line-addressable evidence from the original inputs."""
    items: list[dict] = []
    resume_lines, jd_lines = resume_text.splitlines(), jd_text.splitlines()

    def add(source: str, category: str, label: str, line_number: int | None, text: str) -> None:
        item = {"source": source, "category": category, "label": label, "line": line_number, "text": text.strip()}
        if item not in items:
            items.append(item)

    for skill in matched:
        located = False
        for number, line in enumerate(resume_lines, 1):
            if skill in extract_skills(line):
                add("resume", "matched_skill", skill, number, line)
                located = True
                break
        if not located:
            add("confirmed_resume", "matched_skill", skill, None, "用户在解析结果中确认添加的技能")
    for skill in missing:
        for number, line in enumerate(jd_lines, 1):
            if skill in extract_skills(line):
                add("jd", "required_skill", skill, number, line)
                break
    for category, hit_key in (("quantified_result", "quant_hits"), ("action_verb", "verb_hits")):
        for hit in evidence[hit_key]:
            for number, line in enumerate(resume_lines, 1):
                if normalize(hit) in normalize(line):
                    add("resume", category, hit, number, line)
                    break
    return items
def score_match(resume_text: str, jd_result: dict, jd_text: str = "", resume_skills: list[str] | None = None) -> dict:
    """C3 主入口：简历文本 + JD 解析结果 -> 匹配分与差距清单（契约对齐 /api/matches）。

    参数：
        resume_text: 简历原文（技能由 C1 extract_skills 提取；B 的解析器接入后可替换）
        jd_result:   jd_parser.parse_jd() 的输出（required/bonus/negated 技能及证据）

    返回结构对齐项目冻结契约：
        score / score_breakdown / matched_skills / missing_skills /
        resume_sections / job_skills / suggestions / algorithm_version（另附 evidence_detail 供 UI 展示评分依据）。
    """
    if not resume_text or not resume_text.strip():
        raise ValueError("简历文本不能为空")
    required = [s["name"] for s in jd_result.get("required_skills", [])]
    bonus = [s["name"] for s in jd_result.get("bonus_skills", [])]
    if not required and not bonus:
        raise ValueError("JD 解析结果为空：请检查 JD 文本是否有效")

    effective_skills = set(
        extract_skills(resume_text)
        if resume_skills is None
        else canonicalize_skills(resume_skills)
    )
    req_set, bonus_set = set(required), set(bonus)

    required_score = 60 if not required else round(60 * len(effective_skills & req_set) / len(required))
    bonus_score = 20 if not bonus else round(20 * len(effective_skills & bonus_set) / len(bonus))
    evidence = _evidence_score(resume_text)

    matched = sorted(effective_skills & (req_set | bonus_set))
    missing = [s for s in required if s not in effective_skills]
    suggestions = _build_suggestions(missing, evidence, jd_result)

    score = required_score + bonus_score + evidence["total"]  # 天然 0-100

    return {
        "score": score,
        "score_breakdown": {
            "required_skills": required_score,
            "preferred_skills": bonus_score,
            "evidence_quality": evidence["total"],
        },
        "matched_skills": matched,
        "missing_skills": missing,
        "resume_sections": {cat: cat in evidence["section_hits"] for cat in ("project", "internship", "work")},
        "job_skills": list(jd_result.get("all_skills", [])),
        "suggestions": suggestions,
        "algorithm_version": load_rules().get("algorithm_version", "rule-v1"),
        "evidence_detail": evidence,
        "evidence_items": _evidence_items(resume_text, jd_text, matched, missing, evidence),
        "confirmed_skills": sorted(effective_skills),
        "warnings": [],
    }


def score_match_texts(resume_text: str, jd_text: str) -> dict:
    """便捷入口：简历文本 + JD 文本 -> 匹配结果（内部先走 C2 的 parse_jd）。"""
    return score_match(resume_text, parse_jd(jd_text), jd_text=jd_text)


if __name__ == "__main__":
    _demo_resume = (
        "岗位：Python 后端开发工程师\n\n"
        "工作经历\n"
        "负责核心业务系统开发，使用 Python 编写高质量代码，基于 FastAPI 搭建 RESTful API。\n"
        "参与 SQL 查询优化，接口响应时间降低 40%。\n\n"
        "项目经历\n"
        "主导订单系统重构，支撑日均 10 万请求，可用性提升至 99.9%。\n"
    )
    _demo_jd = (
        "岗位：Python 后端开发工程师\n"
        "1. 负责服务端开发，使用 Python 编写高质量代码；\n"
        "2. 基于 FastAPI 搭建 RESTful API；\n"
        "3. 熟悉 SQL，了解 Redis 缓存者加分。\n"
    )
    _result = score_match_texts(_demo_resume, _demo_jd)
    print(json.dumps(_result, ensure_ascii=False, indent=2))
