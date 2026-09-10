"""简历规则诊断器（任务 B4）。

确定性规则引擎，不依赖外部 LLM。输入简历原文，输出按类别归组的诊断结论：
- quantified  ：经历/项目正文命中量化指标（如「修复线上缺陷 12 个」「延迟降低 30%」），
                提示保留并准备口径说明（正向亮点）；
- action_verb ：经历/项目正文不以动作动词开头（负责/搭建/开发/优化…），建议改写；
- suggestion  ：结构性缺失建议，如教育经历无年份、技能词过少、缺少经历区块。

实现从 B1/B2 解析结果（`parse_resume_text`）出发做二次扫描：
1. 先按原文行号把每一非空行归属到它所在的区块（借助 Section.line_start/line_end）；
2. 仅对 experience/projects 区块的「正文行」做量化与动作动词检查：
   正文行需以动作动词开头，或含量化指标，或含成果宾语词（系统/接口/app/pipeline…），
   三者皆无的行多半是岗位头衔或项目名（时间开头的条目头、过短标签同样跳过）；
3. education / skills 的缺失建议按区块整体判断。

本模块不联网、不猜模型输出；规则有改动时同步更新本文件 docstring 与测试。
"""
from __future__ import annotations

import re

from app.schemas.resume import (
    DiagnoseItem,
    DiagnoseSummary,
    ParsedResume,
    ResumeDiagnoseResponse,
    Section,
)
from app.services.resume_parser import parse_resume_text

# 正文行判断 ---------------------------------------------------------------------
# 行首时间（如 2024.06-2024.09 / 2024/06 / June 2024）：多为条目头，跳过诊断
_TIME_START_RE = re.compile(
    r"^(?:\d{2,4}年?\s*[-—]?\s*\d{0,2}月?|20\d{2}[-/.]\d{1,2}|"
    r"20\d{2}\s*[-—~]\s*|(\d{1,2})[-/.](\d{1,2})|"
    r"(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\.?\s+\d{4}|\d{4})",
    re.IGNORECASE,
)
# 岗位/头衔/项目名行不进入行级诊断：判断交给 _has_object_word / 动词 / 量化。
# 中文成果宾语词
_ZH_OBJECT_WORDS = (
    "项目", "系统", "模块", "平台", "功能", "数据", "流程", "方案", "脚本",
    "服务", "架构", "页面", "组件", "接口", "报表", "工具", "应用", "产品",
    "需求", "用例", "文档", "算法", "模型", "框架", "环境", "任务", "指标",
    "代码", "日志", "链路", "画像", "策略", "实验",
)
# 英文成果宾语词（做整词匹配，避免 app 误伤单词内部）
_EN_OBJECT_WORDS = (
    "app", "application", "api", "pipeline", "dashboard", "platform", "system",
    "module", "service", "database", "model", "report", "framework", "feature",
    "website", "library", "component", "ui", "tool", "interface", "workflow",
    "script", "query",
)
_EN_OBJECT_RE = re.compile(
    r"\b(?:" + "|".join(_EN_OBJECT_WORDS) + r"s?)\b", re.IGNORECASE
)


def _has_object_word(text: str) -> bool:
    """正文成果宾语词：中文直接包含，英文按单词边界。"""
    if any(w in text for w in _ZH_OBJECT_WORDS):
        return True
    return bool(_EN_OBJECT_RE.search(text))

# 行首可允许的修饰性前缀（后接动词），避免把「独立完成…」判成无动词
_ZH_SOFT_START = ("独立", "独自", "全程", "全权", "快速", "高效", "持续", "深入", "协助负责", "共同")
_EN_SOFT_WORDS = {
    "independently", "jointly", "collaboratively", "actively", "successfully",
    "rapidly", "proactively", "together",
}

# 动作动词（中文：行首连续汉字命中即可；英文：取首词做小写匹配）
_ZH_VERBS = (
    "负责", "参与", "主导", "搭建", "开发", "设计", "实现", "优化", "推动", "完成",
    "修复", "编写", "撰写", "部署", "维护", "整理", "分析", "构建", "制定", "组织",
    "协调", "跟进", "输出", "交付", "研发", "重构", "迁移", "落地", "上线", "规划",
    "统筹", "支持", "协助", "梳理", "排查", "定位", "解决", "改进", "提升", "降低",
    "减少", "增加", "扩展", "接入", "集成", "验证", "测试", "采集", "清洗", "抽取",
    "建模", "训练", "调优", "封装", "运营", "推广", "对接", "打通", "沉淀", "探索",
)
_EN_VERBS = {
    "built", "developed", "designed", "led", "implemented", "optimized", "improved",
    "reduced", "created", "engineered", "architected", "refactored", "automated",
    "managed", "maintained", "migrated", "deployed", "integrated", "delivered",
    "shipped", "wrote", "analyzed", "launched", "coordinated", "initiated", "owned",
    "drove", "spearheaded", "established", "revamped", "streamlined", "scaled",
    "built", "programmed", "configured", "accelerated", "enhanced", "boosted",
}

# 量化指标：数字 + 单位/百分比（多字符单位放在前面优先匹配）
_QUANT_RE = re.compile(
    r"\d[\d,]*(?:\.\d+)?\s*(?:"
    r"用户|请求|小时|分钟|人天|人月|QPS|GB|MB|TB|ms|"
    r"个|人|万|亿|倍|天|月|年|次|项|条|份|篇|元|单|行|张|类|位|件|封|笔|名|家|台|%"
    r")"
)

_EDU_YEAR_RE = re.compile(r"(?:19|20)\d{2}")
# 行首装饰符号，仅用于检查动词前的前导清理
_BULLET_RE = re.compile(r"^[\s•·■●★▪▶►○◎\-–—–—~*]+")


# ---------- 行级判定 ----------


def _line_section(parsed: ParsedResume, lineno: int) -> Section | None:
    """返回该行所属区块：标题行为 line_start，归属下仍在该区块内的正文行。

    约定：正文行满足 section.line_start < 行号 <= section.line_end。
    """
    for sec in parsed.sections:
        if sec.line_start < lineno <= sec.line_end:
            return sec
    return None


def _strip_bullet(line: str) -> str:
    return _BULLET_RE.sub("", line).lstrip()


def _is_time_start(line: str) -> bool:
    return bool(_TIME_START_RE.match(line))


def _leading_action(line: str) -> bool:
    """判断行是否以动作动词开头（允许少量修饰词前缀）。"""
    text = _strip_bullet(line)
    if not text:
        return False

    for soft in _ZH_SOFT_START:
        if text.startswith(soft):
            text = text[len(soft):].lstrip()
            break

    for verb in _ZH_VERBS:
        if text.startswith(verb):
            return True

    first = text.split()[0].lower().rstrip(".,;:，。；：!?")
    if first in _EN_VERBS:
        return True
    if first in _EN_SOFT_WORDS and len(text.split()) > 1:
        second = text.split()[1].lower().rstrip(".,;:，。；：!?")
        return second in _EN_VERBS
    return False


def _is_body_line(line: str) -> bool:
    """experience/projects 区块中是否值得做动词/量化诊断的正文行。

    是正文的充分条件：以动作动词开头 / 含量化指标 / 含成果宾语词
    （系统、接口、app、pipeline…）。三者都没有的行多半是岗位头衔或项目名
    （如“后端开发实习生 @ XX 公司”“Resume Matcher (course project)”），跳过。
    时间开头的条目头、过短标签（<10 字符）也跳过。
    """
    text = _strip_bullet(line)
    if len(text) < 10:
        return False
    if _is_time_start(text):
        return False
    return bool(
        _leading_action(text)
        or _find_quantified(text)
        or _has_object_word(text)
    )


def _find_quantified(line: str) -> re.Match | None:
    return _QUANT_RE.search(line)


# ---------- 诊断文案 ----------


def _item(category: str, message: str, suggestion: str = "", line: int | None = None, section: str | None = None) -> DiagnoseItem:
    return DiagnoseItem(
        category=category,  # type: ignore[arg-type]
        message=message,
        suggestion=suggestion,
        line=line,
        section=section,
    )


# ---------- 主入口 ----------


def diagnose_resume_text(text: str) -> list[DiagnoseItem]:
    """对简历原文做规则诊断，返回结论列表（行号按原文 1 起、含空行占位）。"""
    parsed = parse_resume_text(text)
    items: list[DiagnoseItem] = []

    kinds = {s.kind for s in parsed.sections}
    has_experience_like = bool(kinds & {"experience", "projects"})

    # ---- 1) 逐行扫描 experience/projects 正文 ----
    for lineno, raw in enumerate(text.splitlines(), start=1):
        stripped = raw.strip()
        if not stripped:
            continue
        sec = _line_section(parsed, lineno)
        if sec is None or sec.kind not in {"experience", "projects"}:
            continue
        if not _is_body_line(stripped):
            continue

        quant = _find_quantified(stripped)
        if quant:
            matched = quant.group(0).strip()
            items.append(_item(
                "quantified",
                message=f"命中量化指标「{matched}」：数据点越具体越可信",
                suggestion="面试/简历核对时准备好口径：统计范围、时间区间、对比基准（环比/同比）。",
                line=lineno,
                section=sec.kind,
            ))
            continue

        if not _leading_action(stripped):
            items.append(_item(
                "action_verb",
                message="该条经历建议以动作动词开头，突出“我做了什么”",
                suggestion="示例改写：主导/搭建/开发/优化 + 对象 + 结果。如“开发订单模块接口，"
                           "修复线上缺陷 12 个，响应时间下降 30%”。",
                line=lineno,
                section=sec.kind,
            ))
            continue

        # 以动词开头但无量化 → 提示补量化（仅当行足够长，像完整成果句）
        if len(_strip_bullet(stripped)) >= 14:
            items.append(_item(
                "suggestion",
                message="该条有动作但缺少量化结果，说服力可以更强",
                suggestion="尝试补上数字：规模/时长/性能提升等，例如“…，使响应时间下降 30%”。",
                line=lineno,
                section=sec.kind,
            ))

    # ---- 2) 教育区块：无年份提示（指向区块内第一条无年份内容行）----
    edu_sec = next((s for s in parsed.sections if s.kind == "education"), None)
    if edu_sec is not None:
        anchor: int | None = None   # 教育区块第一条内容行
        has_year = False
        for lineno, raw in enumerate(text.splitlines(), start=1):
            stripped = raw.strip()
            if not stripped:
                continue
            sec = _line_section(parsed, lineno)
            if sec is not edu_sec:
                continue
            if anchor is None:
                anchor = lineno
            if _EDU_YEAR_RE.search(stripped):
                has_year = True
        if anchor is not None and not has_year:
            items.append(_item(
                "suggestion",
                message="教育经历未识别到起止年份，时间线不完整",
                suggestion="建议补充年份，如「2021.09 - 2025.06  XX大学  计算机 本科」。",
                line=anchor,
                section="education",
            ))

    # ---- 3) 结构缺失建议 ----
    if "education" not in kinds:
        items.append(_item(
            "suggestion",
            message="未识别到“教育背景”区块，招聘方难以判断学历与时间线",
            suggestion="补充学校、专业、学历与起止时间；应届简历建议放第一板块。",
        ))
    if not has_experience_like:
        items.append(_item(
            "suggestion",
            message="未识别到“实习经历/项目经历”区块，实践能力展示不足",
            suggestion="补充至少 2-3 段经历（实习、课程项目、竞赛均可），每条按“动作动词 + 量化结果”描述。",
        ))
    skill_count = len(parsed.skills)
    if skill_count == 0:
        items.append(_item(
            "suggestion",
            message="未识别到任何技能词，技术关键词缺失影响筛选",
            suggestion="补充独立“专业技能”区块，列出与目标岗位相关的 3-6 项核心技能。",
        ))
    elif skill_count < 3:
        items.append(_item(
            "suggestion",
            message=f"技能词仅 {skill_count} 项，覆盖偏窄",
            suggestion="补充 3-6 项核心技能（语言/框架/工具），并与岗位 JD 关键词对齐。",
        ))

    return items


def diagnose_resume(text: str) -> ResumeDiagnoseResponse:
    items = diagnose_resume_text(text)
    summary = DiagnoseSummary(
        total=len(items),
        quantified=sum(1 for i in items if i.category == "quantified"),
        action_verb=sum(1 for i in items if i.category == "action_verb"),
        suggestion=sum(1 for i in items if i.category == "suggestion"),
    )
    return ResumeDiagnoseResponse(summary=summary, diagnoses=items)
