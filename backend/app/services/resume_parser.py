"""简历文本结构化解析器（任务 B1/B2）。

规则引擎，不依赖外部 LLM：
1. 按行扫描，通过区块标题（中英文关键词）把正文切分为
   education / experience / projects / skills 等区块；
2. 从技能区块中拆分技能词（分隔符拆分 + 简单噪音过滤）；
3. 从文首区域尽力识别姓名/邮箱/电话（均允许缺失）；
4. 无法识别时输出 warnings，不猜测。

技能同义词归一化由成员 C 的技能词典负责（任务 C1），本模块不做词典匹配。
"""
from __future__ import annotations

import re

from app.schemas.resume import (
    BasicInfo,
    ContactInfo,
    ParsedResume,
    ResumeParseResponse,
    Section,
)

# 区块标题关键词，同一类内先放更长、更具体的词，匹配时取最长命中。
_HEADINGS: dict[str, tuple[str, ...]] = {
    "education": (
        "教育背景",
        "教育经历",
        "学历教育",
        "教育",
        "Education",
        "Academic Background",
        "education",
    ),
    "experience": (
        "实习经历",
        "实习经验",
        "工作经历",
        "工作经验",
        "职业经历",
        "项目实习",
        "经历",
        "Work Experience",
        "Internship Experience",
        "experience",
    ),
    "projects": (
        "项目经历",
        "项目经验",
        "项目实践",
        "主要项目",
        "项目",
        "Project Experience",
        "Projects",
        "Project",
        "projects",
        "project",
    ),
    "skills": (
        "专业技能",
        "技能清单",
        "技能特长",
        "掌握技能",
        "技术栈",
        "个人技能",
        "技能",
        "Technical Skills",
        "Skills",
        "Skill",
        "skills",
        "skill",
    ),
}

# 行首可能出现的装饰符号 / 编号（仅用于标题识别前的清理）
_PREFIX_RE = re.compile(r"^[\s•·■●★▪▶►○◎\-—–_、.【】\[\]()（）*#]+")
# 技能词拆分的分隔符
_SKILL_SPLIT_RE = re.compile(r"[、，,;；/|·•\\\n]+")
# 从括号/注释中剥离技能注释
_PAREN_RE = re.compile(r"[（(][^）)]*[)）]")

_EMAIL_RE = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")
_PHONE_RE = re.compile(r"(?<!\d)(?:\+?86[\s-]?)?1[3-9]\d{9}(?!\d)")
_TIME_HEAD_RE = re.compile(
    r"^(?:\d{2,4}年?|20\d{2}[-/.]\d{1,2}|(\d{1,2})[-/.](\d{1,2})|20\d{2}\s*[-—]\s*|至今|现在|Now|Present)",
    re.IGNORECASE,
)
_NAME_PREFIX_RE = re.compile(r"^(姓名|name)[:：]\s*", re.IGNORECASE)


def _clean_prefix(text: str) -> str:
    return _PREFIX_RE.sub("", text).strip()


def _split_heading(stripped: str) -> tuple[str | None, str | None, str | None]:
    """识别行首区块标题，返回 (kind, heading, 标题后剩余内容)。

    标题关键词须位于清理符号后的行首；命中多个关键词时取最长。
    两字通用词（教育/项目/技能/经历）若后接的是明显长正文，则放弃识别，
    避免把正文当标题。
    """
    text = _clean_prefix(stripped)
    if not text:
        return None, None, None
    low = text.lower()

    hits: list[tuple[int, str, str]] = []
    for kind, keywords in _HEADINGS.items():
        for kw in keywords:
            # 关键词含首字母大写变体（如 "Internship Experience"），统一小写后比较，
            # 否则全大写标题（TECHNICAL SKILLS）永远无法命中
            if low.startswith(kw.lower()):
                hits.append((len(kw), kind, kw))
    if not hits:
        return None, None, None

    length, kind, kw = max(hits, key=lambda h: h[0])
    rest = text[length:].strip(" :：、\t")

    if len(kw) <= 2 and rest:
        # 短关键词 + 长正文：多半是正文而非标题
        if _looks_like_body(rest):
            return None, None, None
    return kind, text[:length], rest or None


def _looks_like_body(rest: str) -> bool:
    """判断标题关键词之后的文本更像正文（长且不以时间/冒号开头）。"""
    if len(rest) <= 30:
        return False
    if rest.startswith(("：", ":", "（", "(", "【")):
        return False
    if _TIME_HEAD_RE.match(rest):
        return False
    return True


def _iter_nonblank_lines(text: str):
    for lineno, raw in enumerate(text.splitlines(), start=1):
        stripped = raw.strip()
        if stripped:
            yield lineno, stripped


def _extract_basic(preamble: list[str]) -> BasicInfo:
    """从文首区域尽力识别姓名/邮箱/电话，全部允许缺失。"""
    contact = ContactInfo()
    name: str | None = None

    joined = "\n".join(preamble[:12])
    m = _EMAIL_RE.search(joined)
    if m:
        contact.email = m.group(0)
    m = _PHONE_RE.search(joined)
    if m:
        contact.phone = m.group(0)

    for line in preamble:
        text = _clean_prefix(line)
        name_match = _NAME_PREFIX_RE.match(text)
        candidate = _NAME_PREFIX_RE.sub("", text).strip() if name_match else text
        if _looks_like_name(candidate):
            name = candidate.split()[0]
            break

    return BasicInfo(name=name, contact=contact)


def _looks_like_name(candidate: str) -> bool:
    candidate = candidate.strip()
    if not candidate:
        return False
    first = candidate.split()[0]
    if _EMAIL_RE.search(first) or _PHONE_RE.search(first):
        return False
    if any(ch.isdigit() for ch in first):
        return False
    if "：" in first or ":" in first:
        return False
    return 2 <= len(first) <= 12


def _clean_skill_token(token: str) -> str:
    token = _PAREN_RE.sub("", token)
    token = token.strip(" ：: \t.-–—·•*#/、,，;；|")
    return token


def _looks_noise(token: str) -> bool:
    if not token:
        return True
    if re.fullmatch(r"[\W_]+", token):
        return True
    if len(token) == 1:
        # 单个字符仅保留大写字母（如 C、R），去掉数字/标点/单个汉字
        return not (token.isalpha() and token.isupper())
    if len(re.sub(r"\s", "", token)) > 24:
        return True
    return False


def _split_skills(skill_lines: list[str]) -> list[str]:
    """把技能区块的行拆成技能词列表，去重保序。"""
    result: list[str] = []
    seen: set[str] = set()
    for line in skill_lines:
        # 去掉“编程语言：”这类行首标签，只保留技能词
        line = re.sub(r"^\s*[^:：,，;；/|·•]{1,12}[:：]\s*", "", line)
        for part in _SKILL_SPLIT_RE.split(line):
            token = _clean_skill_token(part)
            if _looks_noise(token):
                continue
            key = token.lower()
            if key in seen:
                continue
            seen.add(key)
            result.append(token)
    return result


def parse_resume_text(text: str) -> ParsedResume:
    sections: list[Section] = []
    current: Section | None = None
    preamble: list[str] = []
    skill_lines: list[str] = []
    current_start = 0

    def close_section(end: int) -> None:
        nonlocal current
        if current is not None:
            current.line_end = end
            sections.append(current)
            current = None

    for lineno, stripped in _iter_nonblank_lines(text):
        kind, heading, rest = _split_heading(stripped)
        if kind is not None:
            close_section(lineno - 1)
            current = Section(
                kind=kind,
                heading=heading or "",
                line_start=lineno,
                line_end=lineno,
            )
            current_start = lineno
            content = rest or ""
            if content:
                current.lines.append(content)
                if kind == "skills":
                    skill_lines.append(content)
            continue

        if current is None:
            preamble.append(stripped)
        else:
            current.lines.append(stripped)
            current.line_end = lineno
            if current.kind == "skills":
                skill_lines.append(stripped)

    close_section(len(text.splitlines()))

    basic = _extract_basic(preamble)
    skills = _split_skills(skill_lines)

    warnings: list[str] = []
    if not any(s.kind == "education" for s in sections):
        warnings.append("未识别到“教育背景”区块，解析结果可能不完整")
    if not skills:
        warnings.append("未识别到技能词，请确认是否有“技能/专业技能”区块")
    if basic.name is None:
        warnings.append("未识别到姓名（可选信息，不影响匹配）")

    return ParsedResume(
        basic=basic,
        sections=sections,
        skills=skills,
        warnings=warnings,
    )


def parse_resume(text: str) -> ResumeParseResponse:
    return ResumeParseResponse(resume=parse_resume_text(text))
