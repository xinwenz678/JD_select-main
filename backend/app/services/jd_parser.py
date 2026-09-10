"""JD 解析与必需/加分技能识别（C2 交付）。

职责：给定 JD 文本 ->
    job_title + required_skills + bonus_skills + negated_skills（均带原文证据）

设计约定：
1. 技能提取完全复用 C1 的 skill_dict（normalize + 同义词 + 词典 + 词边界），
   证据定位复用其编译好的匹配模式（_compile_patterns，只读引用），保证
   “提取到的技能”和“能找到原文位置的技能”永远一致；
2. 分类用“句级信号词法”：把正文按 ；。！？换行 切成句子（保留逗号），
   信号词只在本句内匹配。这样“上一句的加分/优先”不会漏进本句，
   “掌握 HTML5、CSS3”这类并列必需也不会被下一句的“者加分”误伤；
3. 句内分类优先级：否定 > 加分 > 必需 > 默认；
4. “X 或 Y”并列结构：同一句内，某技能与另一技能分别落在同一个“或”字
   两侧（±15 字符，含紧贴“X或Y”情形），判定为“并列可选项”，归入加分
   （典型如“掌握 MySQL 或 PostgreSQL”）；
5. 无任何信号词的技能按“必需·默认”处理（JD 中写出的技能即岗位要求），
   并显式标注 signal=默认，便于审计和讲解；
6. 同一技能在多句出现时取最强信号：否定 > 加分 > 必需 > 默认。

已知边界（写入 C6 算法文档）：
- “了解 X 者加分/优先/更佳” => 加分（加分词压过“了解”这类必需词）；
- “会使用 X 者优先” => 加分；
- “对 X 无要求 / 无需 X / 不要求 X” => 否定，不计入必需也不计入加分；
- 同一逗号句内同时出现“无需 X，掌握 Y”时，句内否定词会使 Y 也判为否定
  （此类表述极少见，MVP 接受该边界）；
- 证据片段基于原文展示（句内归一化偏移映射回原文坐标）。
"""
from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Dict, List, Tuple

# 允许本文件被 scripts/ 下的脚本以绝对路径直接运行
if __package__ in (None, ""):
    import sys
    _BACKEND_DIR = Path(__file__).resolve().parents[2]  # services -> app -> backend
    if str(_BACKEND_DIR) not in sys.path:
        sys.path.insert(0, str(_BACKEND_DIR))

from app.services.skill_dict import _compile_patterns, extract_skills, normalize  # noqa: E402

DATA_DIR = Path(__file__).resolve().parents[1] / "data"
SIGNAL_WORDS_FILE = DATA_DIR / "jd_signal_words.json"

# “或”并列结构判定距离（字符数，归一化句子上）
OR_WINDOW = 15

_signal_cache: dict = {}


def load_signal_words() -> dict[str, list[str]]:
    """加载并归一化信号词表（条目先 normalize 再去重排序，长词优先匹配）。"""
    if not _signal_cache:
        with SIGNAL_WORDS_FILE.open(encoding="utf-8") as f:
            raw = json.load(f)
        cleaned: dict[str, list[str]] = {}
        for key in ("required", "bonus", "negation"):
            words = sorted({normalize(w) for w in raw.get(key, [])}, key=len, reverse=True)
            cleaned[key] = words
        _signal_cache.update(cleaned)
    return _signal_cache


# 信号强度：数值越大越强（用于多处出现时取最强）
_STRENGTH = {"negated": 4, "bonus": 3, "required": 2, "default": 1}


def extract_job_title(text: str) -> str:
    """提取岗位名：优先 YAML job_title 字段，其次首个 # 标题行，再次首个非空行。"""
    lines = [ln.strip() for ln in text.splitlines()]
    for ln in lines:
        if ln.startswith("job_title:"):
            return ln.split(":", 1)[1].strip().strip('"')
    for ln in lines:
        if ln.startswith("#"):
            return ln.lstrip("#").strip()
    for ln in lines:
        if ln and not ln.startswith("---"):
            return ln[:40]
    return ""


def strip_front_matter(text: str) -> str:
    """剥离文件开头的 YAML 标注块（--- 到闭合 --- 之间），只保留 JD 正文。

    样例 JD 的 required_skills/bonus_skills 是验收标注，不是 JD 内容，
    若不过滤会污染技能分类；真实粘贴的 JD 文本没有 YAML 头，原样返回。
    """
    lines = text.splitlines(keepends=True)
    if not lines or lines[0].strip() != "---":
        return text
    for i in range(1, len(lines)):
        if lines[i].strip() == "---":
            return "".join(lines[i + 1:])
    # 没有闭合 ---（极少见）：跳过首个空行之前的全部行
    for i in range(1, len(lines)):
        if lines[i].strip() == "":
            return "".join(lines[i + 1:])
    return text


def _split_clauses(text: str) -> List[Tuple[str, int]]:
    """按句子结束符切句（；。！？换行 与 逗号），返回 [(句子原文, 起始偏移)]。

    - 逗号也切：避免“熟悉 CI/CD 流程，有 Jenkins 经验者加分”里“加分”误伤 CI/CD；
    - 顿号“、”不切：保证“了解 Redis 缓存、Kafka 消息队列者加分”整体判定为加分。
    """
    return [(m.group(0), m.start()) for m in re.finditer(r"[^；;\n。！？!?，,]+", text)]


def _normalize_with_map(text: str) -> Tuple[str, List[int]]:
    """与 skill_dict.normalize 等价的逐字符版本，额外返回 归一化索引 -> 原文索引 映射。"""
    low = text.lower()
    skip = re.compile(r"[\s\-_/·.、，。；：！？（）()【】\[\]{}]")
    out: list[str] = []
    mapping: list[int] = []
    for i, ch in enumerate(low):
        if skip.match(ch):
            continue
        out.append(ch)
        mapping.append(i)
    return "".join(out), mapping


def _skill_spans(norm_text: str) -> Dict[str, List[Tuple[int, int]]]:
    """返回 {规范技能名: [归一化文本上的命中区间, ...]}，复用 C1 编译好的模式。"""
    spans: Dict[str, List[Tuple[int, int]]] = {}
    for canonical, pat in _compile_patterns():
        for m in pat.finditer(norm_text):
            spans.setdefault(canonical, []).append(m.span())
    return spans


def _classify_clause(clause_norm: str) -> Tuple[str, str]:
    """对整句分类，返回 (类别, 命中的信号词/原因)。优先级：否定 > 加分 > 必需。"""
    signals = load_signal_words()
    for w in signals["negation"]:
        if w in clause_norm:
            return "negated", w
    for w in signals["bonus"]:
        if w in clause_norm:
            return "bonus", w
    for w in signals["required"]:
        if w in clause_norm:
            return "required", w
    return "default", "默认"


def _or_optional_skills(spans: Dict[str, List[Tuple[int, int]]], norm_text: str) -> set[str]:
    """“X 或 Y”并列结构检测（句内）：或字两侧 ±OR_WINDOW 内各至少有一个技能时，
    这些技能均为“并列可选项”（归入加分）。e <= pos 覆盖“X或Y”紧贴情形。"""
    optional: set[str] = set()
    for m in re.finditer("或", norm_text):
        pos = m.start()
        left = {
            skill
            for skill, sss in spans.items()
            for s, e in sss
            if pos - OR_WINDOW <= e <= pos
        }
        right = {
            skill
            for skill, sss in spans.items()
            for s, e in sss
            if pos < s <= pos + OR_WINDOW
        }
        if left and right:
            optional.update(left)
            optional.update(right)
    return optional


def classify_skills(text: str) -> Dict[str, str]:
    """对整段 JD 正文中的全部技能分类。返回 {规范名: 类别}，类别 ∈ {required, bonus, negated}。"""
    result: Dict[str, str] = {}
    for clause, _off in _split_clauses(text):
        norm = normalize(clause)
        if not norm:
            continue
        spans = _skill_spans(norm)
        # 短英文技能必须在保留顿号/空格的原句中判断边界；补回压平文本会漏掉的命中。
        for skill in extract_skills(clause):
            spans.setdefault(skill, [])
        if not spans:
            continue
        optional = _or_optional_skills(spans, norm)
        cls, _word = _classify_clause(norm)  # 整句即上下文
        for skill in spans:
            c = cls
            if skill in optional and c == "required":
                c = "bonus"  # 并列可选项
            # 首次出现直接记录；已存在则仅当信号更强时覆盖
            # （用 skill not in result 而非比较强度，避免 default(1)>default(1) 为假导致技能丢失）
            if skill not in result or _STRENGTH[c] > _STRENGTH[result[skill]]:
                result[skill] = c
    for skill, c in list(result.items()):
        if c == "default":
            result[skill] = "required"  # 无信号默认按必需
    return result


def _evidence(original: str, orig_s: int, orig_e: int) -> str:
    """截取原文 [orig_s, orig_e) 前后各 25 字符作为证据片段。"""
    start = max(0, orig_s - 25)
    end = min(len(original), orig_e + 25)
    snippet = original[start:end].replace("\n", " ")
    if start > 0:
        snippet = "…" + snippet
    if end < len(original):
        snippet += "…"
    return snippet


def parse_jd(text: str) -> dict:
    """C2 主入口：JD 文本 -> 结构化解析结果（C4 将包装为 /api/jobs/parse）。"""
    body = strip_front_matter(text)  # 剥离 YAML 验收标注，避免污染分类
    classes = classify_skills(body)

    # 每个技能取首个命中位置生成证据（句内归一化偏移映射回正文绝对坐标）
    first_evidence: Dict[str, str] = {}
    for clause, off in _split_clauses(body):
        norm, mapping = _normalize_with_map(clause)
        clause_spans = _skill_spans(norm)
        for skill in extract_skills(clause):
            clause_spans.setdefault(skill, [])
        for skill, sss in clause_spans.items():
            if skill in first_evidence:
                continue
            if not sss:
                first_evidence[skill] = clause.strip()
                continue
            s, e = sss[0]
            first_evidence[skill] = _evidence(body, off + mapping[s], off + mapping[e - 1] + 1)

    buckets = {"required": [], "bonus": [], "negated": []}
    for skill, cls in classes.items():
        signal = {"required": "必需·默认", "bonus": "加分", "negated": "否定"}[cls]
        buckets[cls].append({
            "name": skill,
            "signal": signal,
            "evidence": first_evidence.get(skill, ""),
        })

    for key in buckets:
        buckets[key].sort(key=lambda item: item["name"])

    return {
        "job_title": extract_job_title(text),
        "required_skills": buckets["required"],
        "bonus_skills": buckets["bonus"],
        "negated_skills": buckets["negated"],
        "all_skills": sorted(classes.keys()),
        "warnings": [],
    }


if __name__ == "__main__":
    demo = (
        "# Python 后端开发工程师\n"
        "岗位职责\n"
        "1. 负责服务端开发，使用 Python 编写高质量代码；\n"
        "2. 基于 FastAPI 搭建 RESTful API。\n"
        "任职要求\n"
        "1. 熟悉 Python，熟练使用 SQL；\n"
        "2. 了解 Redis 缓存者加分；\n"
        "3. 对 Kubernetes 无要求。\n"
    )
    import json as _json

    print(_json.dumps(parse_jd(demo), ensure_ascii=False, indent=2))
