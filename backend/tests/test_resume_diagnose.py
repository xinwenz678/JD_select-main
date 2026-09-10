"""简历规则诊断器单元测试（任务 B4）。

覆盖点：
- 三个类别：quantified（量化命中）/ action_verb（无动词开头）/ suggestion（结构性缺失）
- 行号与原文空行对齐；experience/projects 只诊断正文行
- 跳过时间开头、岗位头衔、过短标签行
- 教育无年份、技能词过少、缺区块建议
"""
from __future__ import annotations

from app.services.resume_diagnose import diagnose_resume_text


def catset(diags):
    """返回 {(category, line), ...} 无序集合，便于整体断言。"""
    return {(d.category, d.line) for d in diags}


# ---------- 样例文件：完整简历（正向为主） ----------

def test_resume_basic_sample(sample_dir):
    text = (sample_dir / "resume_basic.txt").read_text(encoding="utf-8")
    diags = diagnose_resume_text(text)

    # 完整简历只给"建议类"小提示，不给结构性缺失建议
    assert catset(diags) == {
        ("suggestion", 11),   # 有动作无量化
        ("quantified", 12),   # 命中 12 个/30%
        ("action_verb", 16),  # 不以动作动词开头
        ("suggestion", 17),   # 有动作无量化
    }
    for d in diags:
        assert d.message and d.suggestion


def test_resume_en_sample(sample_dir):
    text = (sample_dir / "resume_en.txt").read_text(encoding="utf-8")
    diags = diagnose_resume_text(text)

    # 英文简历不误报结构性缺失，且能识别出量化/动词问题
    assert any(d.line for d in diags)
    assert not any(d.line is None for d in diags)
    assert any(d.category == "quantified" for d in diags)


def test_resume_missing_sections_sample(sample_dir):
    text = (sample_dir / "resume_missing_sections.txt").read_text(encoding="utf-8")
    diags = diagnose_resume_text(text)

    # 缺教育区块 + 无技能词 → 两条全局建议（line=None）
    assert any(d.line is None and "教育背景" in d.message for d in diags)
    assert any(d.line is None and "技能词" in d.message for d in diags)
    assert any(d.category == "quantified" for d in diags)


# ---------- 样例文件：弱简历（四类问题齐全） ----------

def test_resume_weak_sample(sample_dir):
    text = (sample_dir / "resume_weak.txt").read_text(encoding="utf-8")
    diags = diagnose_resume_text(text)

    assert catset(diags) == {
        ("action_verb", 10),  # 名词化描述，无动词开头
        ("suggestion", 11),   # 有动作无量化
        ("suggestion", 6),    # 教育无年份
        ("suggestion", None), # 技能词仅 1 项
    }


# ---------- 量化识别 ----------

def test_quantified_percent_and_count():
    text = (
        "实习经历\n"
        "2024.06 - 2024.09  XX公司  数据分析实习生\n"
        "搭建覆盖核心业务场景的用户指标体系\n"   # 有动作无量化 → suggestion
        "输出 12 份经营分析报告，问题定位耗时下降 40%\n"  # → quantified
    )
    diags = diagnose_resume_text(text)
    by_line = {d.line: d for d in diags}

    assert by_line[3].category == "suggestion"
    assert by_line[4].category == "quantified"


def test_quantified_english_percent():
    text = (
        "Internship Experience\n"
        "2024 Backend Intern at XX\n"
        "Built a dashboard that cut latency by 40%\n"
    )
    diags = diagnose_resume_text(text)

    assert any(d.category == "quantified" and d.section == "experience" for d in diags)


# ---------- 动作动词 ----------

def test_action_verb_missing():
    text = (
        "项目经历\n"
        "2024.03 - 2024.05  数据可视化大屏\n"
        "数据平台接口开发与联调工作\n"   # 名词化，应提示
        "独立完成 SQLite 数据表设计\n"   # 修饰词+完成 → 不提示
    )
    diags = diagnose_resume_text(text)

    assert any(d.category == "action_verb" and d.line == 3 for d in diags)
    assert not any(d.category == "action_verb" and d.line == 4 for d in diags)


def test_action_verb_english_ok_and_missing():
    text = (
        "Projects\n"
        "Built a CI pipeline\n"                                  # Built 开头 → OK
        "Dashboard setup and maintenance for monitoring\n"       # 含宾语词但无动词 → 提示
    )
    diags = diagnose_resume_text(text)

    assert not any(d.category == "action_verb" and d.line == 2 for d in diags)
    assert any(d.category == "action_verb" and d.line == 3 for d in diags)


# ---------- 跳过不相关行 ----------

def test_skip_time_and_title_lines():
    text = (
        "教育背景\n2020.09 - 2024.06  XX大学  本科\n"
        "\n"
        "实习经历\n"
        "2024.06 - 2024.09  XX科技有限公司  后端开发实习生\n"  # 时间开头 → 跳过
        "后端开发实习生 @ XX 公司\n"                             # 头衔行 → 跳过
        "X\n"                                                     # 过短 → 跳过
        "\n"
        "专业技能\nPython、SQL、FastAPI\n"
    )
    diags = diagnose_resume_text(text)

    assert diags == []


# ---------- 结构性建议 ----------

def test_education_missing_year_suggests():
    text = (
        "教育背景\n"
        "XX大学  计算机  本科\n"          # 无年份
        "\n"
        "专业技能\n"
        "Python、SQL\n"
    )
    diags = diagnose_resume_text(text)

    assert any(
        d.category == "suggestion" and d.line == 2 and "年份" in d.message
        for d in diags
    )


def test_education_has_year_no_suggest():
    text = (
        "教育背景\n"
        "2021.09 - 2025.06  XX大学  计算机  本科\n"
    )
    diags = diagnose_resume_text(text)

    assert not any(d.section == "education" for d in diags)


def test_skills_few_and_none():
    diags_few = diagnose_resume_text(
        "教育背景\n2020-2024 XX大学 本科\n\n专业技能\nPython"
    )
    assert any("仅 1 项" in d.message for d in diags_few)

    diags_none = diagnose_resume_text("教育背景\n2020-2024 XX大学 本科")
    assert any("未识别到任何技能词" in d.message for d in diags_none)


def test_missing_experience_suggests():
    text = (
        "教育背景\n2021.09 - 2025.06 XX大学 本科\n"
        "专业技能\nPython、SQL、FastAPI、Git\n"
    )
    diags = diagnose_resume_text(text)

    assert any("实习经历/项目经历" in d.message for d in diags)


def test_preamble_only_gives_structure_suggestions():
    text = "张三\n邮箱：zhang@x.com\n"
    diags = diagnose_resume_text(text)

    assert any("教育背景" in d.message for d in diags)
    assert any("实习经历/项目经历" in d.message for d in diags)
    assert any("技能词" in d.message for d in diags)


# ---------- 行号与原文对齐 ----------

def test_line_numbers_align_with_blank_lines():
    text = (
        "实习经历\n"
        "2024.06 - 2024.09  XX公司  后端实习生\n"
        "\n"
        "负责订单模块接口开发与系统联调\n"   # 有动作无量化 → suggestion
    )
    diags = diagnose_resume_text(text)

    # 第 4 行是正文（含空行占位，行号仍为 4）
    assert any(d.line == 4 and d.category == "suggestion" for d in diags)
