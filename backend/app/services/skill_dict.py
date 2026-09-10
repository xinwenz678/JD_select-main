"""技能词典与同义词表：加载、归一化、技能提取（C1 交付，C2/C3 直接复用）。

设计约定：
1. skill_dictionary.json 只保存“规范名”，是项目内唯一的技能标识；
2. 所有花式写法（缩写/大小写/中英文）统一放在 synonyms.json，映射到规范名；
3. 匹配前先 normalize() 压平文本（小写、去空白/连字符/点号/全半角标点），
   再判断“规范名或同义词是否出现在文本中”；
4. 短英文词（Go、Java、SQL、LLM、js、node 等）必须用词边界模式，
   否则 JavaScript 会被误判为 Java、json 会被误判为 js。

已知边界（写入 C6 算法文档）：
- “只写 MySQL 不写 SQL”不会被算作命中 SQL（SQL 用词边界）；
- “GitHub”不会算作命中 Git（Git 用词边界）；
- “Python3”会命中 Python（python3 在 synonyms.json 中）。
"""
from __future__ import annotations

import json
import re
from pathlib import Path

DATA_DIR = Path(__file__).resolve().parents[1] / "data"
DICTIONARY_FILE = DATA_DIR / "skill_dictionary.json"
SYNONYMS_FILE = DATA_DIR / "synonyms.json"

_cache: dict = {"dictionary": None, "synonyms": None, "patterns": None, "match_patterns": None}


def load_dictionary() -> dict:
    if _cache["dictionary"] is None:
        with DICTIONARY_FILE.open(encoding="utf-8") as f:
            _cache["dictionary"] = json.load(f)
    return _cache["dictionary"]


def load_synonyms() -> dict[str, dict]:
    if _cache["synonyms"] is None:
        with SYNONYMS_FILE.open(encoding="utf-8") as f:
            _cache["synonyms"] = json.load(f)
    return _cache["synonyms"]


def normalize(text: str) -> str:
    """第 1 层归一化：小写 + 去掉空白、连字符、下划线、斜杠、点号、全半角标点。"""
    text = text.lower()
    text = re.sub(r"[\s\-_/·.、，。；：！？（）()【】\[\]{}]+", "", text)
    return text


def to_canonical(surface: str) -> str:
    """把规范名、大小写变体或同义词统一映射回词典中的规范名。"""
    value = surface.strip()
    key = normalize(value)
    spec = load_synonyms().get(key)
    if spec:
        return spec["canonical"]
    for skill in load_dictionary()["skills"]:
        if normalize(skill["canonical"]) == key:
            return skill["canonical"]
    # 允许用户确认词典外的真实技能，并保留用户输入而不是强制变为小写。
    return value


def canonicalize_skills(skills: list[str]) -> list[str]:
    """规范化用户确认的技能，去空、去重并保持稳定排序。"""
    canonical = {to_canonical(skill) for skill in skills if skill and skill.strip()}
    return sorted(skill for skill in canonical if skill)


def _skill_forms(skill: dict) -> list[tuple[str, str]]:
    """返回 [(表面写法, 匹配模式)] = 规范名 + 同义词表里指向它的全部写法。"""
    mode = skill.get("match_mode", "substring")
    canonical_form = skill["canonical"].lower() if mode == "word" else normalize(skill["canonical"])
    forms = [(canonical_form, mode)]
    for surface, spec in load_synonyms().items():
        if spec.get("canonical") == skill["canonical"]:
            forms.append((surface, spec.get("match", mode)))
    return forms


def _compile_patterns() -> list[tuple[str, re.Pattern]]:
    """兼容 JD 解析器的压平文本模式。"""
    if _cache["patterns"] is not None:
        return _cache["patterns"]
    patterns: list[tuple[str, re.Pattern]] = []
    for skill in load_dictionary()["skills"]:
        for form, mode in _skill_forms(skill):
            expr = re.escape(normalize(form))
            if mode == "word":
                # 词边界只看拉丁字母/数字，中文前后天然是边界，不受影响
                expr = rf"(?<![a-z0-9]){expr}(?![a-z0-9])"
            patterns.append((skill["canonical"], re.compile(expr)))
    _cache["patterns"] = patterns
    return patterns


def _compile_match_patterns() -> list[tuple[str, str, re.Pattern]]:
    """为最终提取编译模式：短英文词在保留分隔符的原文上检查边界。"""
    if _cache["match_patterns"] is not None:
        return _cache["match_patterns"]
    patterns: list[tuple[str, str, re.Pattern]] = []
    for skill in load_dictionary()["skills"]:
        for form, mode in _skill_forms(skill):
            expression = re.escape(form)
            if mode == "word":
                expression = rf"(?<![a-z0-9]){expression}(?![a-z0-9])"
            patterns.append((skill["canonical"], mode, re.compile(expression)))
    _cache["match_patterns"] = patterns
    return patterns


def extract_skills(text: str) -> list[str]:
    """从任意文本（JD 或简历）中提取命中的规范技能名，去重后按字典序返回。"""
    compact_text = normalize(text)
    raw_text = text.lower()
    hits: set[str] = set()
    word_spans: dict[str, list[tuple[int, int]]] = {}
    for canonical, mode, pattern in _compile_match_patterns():
        target = raw_text if mode == "word" else compact_text
        matches = list(pattern.finditer(target))
        if matches:
            hits.add(canonical)
            if mode == "word":
                word_spans.setdefault(canonical, []).extend(match.span() for match in matches)

    # “Spring Boot”不应同时制造一个“Spring”命中；若短词在别处独立出现则仍保留。
    separator = r"[\s\-_/·.]*"
    for short, spans in word_spans.items():
        short_key = normalize(short)
        covering: list[tuple[int, int]] = []
        for longer in hits:
            longer_key = normalize(longer)
            if longer == short or not longer_key.startswith(short_key) or len(longer_key) <= len(short_key):
                continue
            parts = [part for part in re.split(r"[\s\-_/·.]+", longer.lower()) if part]
            expression = separator.join(re.escape(part) for part in parts)
            covering.extend(match.span() for match in re.finditer(expression, raw_text))
        if covering and all(
            any(start >= outer_start and end <= outer_end for outer_start, outer_end in covering)
            for start, end in spans
        ):
            hits.discard(short)
    return sorted(hits)


def validate_dictionary() -> list[str]:
    """C1 自查：词数 >= 40、canonical 唯一、同义词指向存在且模式合法。"""
    problems: list[str] = []
    data = load_dictionary()
    skills = data.get("skills", [])
    canonicals = [s["canonical"] for s in skills]

    if len(canonicals) < 40:
        problems.append(f"技能词不足 40 个：当前 {len(canonicals)} 个")
    seen = set()
    for c in canonicals:
        if not c or not c.strip():
            problems.append("存在空的 canonical")
        elif c in seen:
            problems.append(f"存在重复 canonical：{c}")
        seen.add(c)

    known = set(canonicals)
    valid_modes = {"substring", "word"}
    for surface, spec in load_synonyms().items():
        if not surface:
            problems.append("同义词表存在空键")
        if spec.get("canonical") not in known:
            problems.append(f"同义词 {surface!r} 指向不存在的技能 {spec.get('canonical')}")
        if spec.get("match") not in valid_modes:
            problems.append(f"同义词 {surface!r} 的 match 模式非法：{spec.get('match')}")
    return problems


if __name__ == "__main__":
    data = load_dictionary()
    print(f"技能词总数: {len(data['skills'])}")
    print(f"同义词条数: {len(load_synonyms())}")
    print(f"词典版本: {data.get('algorithm_version')}")
    for p in validate_dictionary():
        print(f"[问题] {p}")
