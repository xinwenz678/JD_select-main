"""简历解析器单元测试（任务 B5）。

覆盖点：
- 中文/英文区块标题识别（含行首装饰符号、长词优先、正文误判防护）
- 技能拆分与清洗（去重、括号注释、行首标签、单字符噪音）
- 姓名/邮箱/电话的识别与可缺失
- 缺区块时的 warnings
- 区块行号与原文空行对齐
"""
from __future__ import annotations

from app.services.resume_parser import parse_resume_text

EDU_WARN = "未识别到“教育背景”区块，解析结果可能不完整"
SKILL_WARN = "未识别到技能词，请确认是否有“技能/专业技能”区块"
NAME_WARN = "未识别到姓名（可选信息，不影响匹配）"


# ---------- 样例文件：中文完整简历 ----------

def test_full_chinese_resume(sample_dir):
    text = (sample_dir / "resume_basic.txt").read_text(encoding="utf-8")
    r = parse_resume_text(text)

    assert r.basic.name == "李明"
    assert r.basic.contact.email == "liming.dev@example.com"
    assert r.basic.contact.phone == "13800138000"

    assert [s.kind for s in r.sections] == ["education", "experience", "projects", "skills"]

    edu, exp, proj, skills_sec = r.sections
    # 行号与原文对齐（含空行占位），标题行为 5/9/14/19
    assert (edu.line_start, edu.line_end) == (5, 8)
    assert (exp.line_start, exp.line_end) == (9, 13)
    assert (proj.line_start, proj.line_end) == (14, 18)
    assert (skills_sec.line_start, skills_sec.line_end) == (19, 23)
    assert edu.lines[0].startswith("2021.09")

    assert r.skills == [
        "Python", "SQL", "JavaScript",
        "FastAPI", "Django",
        "SQLite", "MySQL",
        "Git", "Docker", "Linux",
    ]
    assert r.warnings == []


# ---------- 样例文件：英文简历 / 缺区块简历 ----------

def test_english_sample(sample_dir):
    text = (sample_dir / "resume_en.txt").read_text(encoding="utf-8")
    r = parse_resume_text(text)

    assert r.basic.name == "Jane"
    assert r.basic.contact.email == "jane.doe@example.com"
    assert r.basic.contact.phone == "+8613912345678"
    assert [s.kind for s in r.sections] == ["education", "experience", "projects", "skills"]
    assert r.skills == ["Python", "Java", "C++", "FastAPI", "Spring Boot", "Git", "Docker", "MySQL"]
    assert r.warnings == []


def test_missing_sections_sample(sample_dir):
    text = (sample_dir / "resume_missing_sections.txt").read_text(encoding="utf-8")
    r = parse_resume_text(text)

    assert r.basic.name == "王五"
    assert r.basic.contact.phone == "13912345678"
    # 无独立技能区块 → 技能词不会从经历正文里扫出（契约第 2 问的现状）
    assert r.skills == []
    assert [s.kind for s in r.sections] == ["experience"]
    assert r.warnings == [EDU_WARN, SKILL_WARN]


# ---------- 标题识别 ----------

def test_decorated_heading_and_longest_match():
    text = "• 教育经历：XX大学 硕士\n\n■ 专业技能\nPython"
    r = parse_resume_text(text)

    edu, skills_sec = r.sections
    assert edu.kind == "education"
    # 命中“教育经历”而不是更短的“教育”
    assert edu.heading == "教育经历"
    assert edu.lines == ["XX大学 硕士"]
    assert skills_sec.kind == "skills"
    assert r.skills == ["Python"]


def test_short_heading_word_does_not_split_long_body():
    text = (
        "实习经历\n"
        "教育实践项目覆盖了面向对象程序设计、数据结构与算法、数据库系统原理、"
        "计算机网络等课程的综合训练与团队协作开发全过程"
    )
    r = parse_resume_text(text)

    # 第二行虽然以“教育”开头，但后接长正文，不应被误切为“教育”区块
    assert [s.kind for s in r.sections] == ["experience"]
    assert len(r.sections[0].lines) == 1


def test_english_keywords_and_line_numbers():
    text = (
        "Jane Doe\n"
        "Email: jane@dev.com\n"
        "\n"
        "EDUCATION\n"
        "2019-2023 ABC University, BSc in CS\n"
        "\n"
        "PROJECTS\n"
        "Resume Matcher\n"
        "Built with React + FastAPI\n"
        "\n"
        "TECHNICAL SKILLS\n"
        "Python, SQL, JavaScript\n"
    )
    r = parse_resume_text(text)

    assert r.basic.name == "Jane"
    assert r.basic.contact.email == "jane@dev.com"
    assert [s.kind for s in r.sections] == ["education", "projects", "skills"]

    edu, proj, skills_sec = r.sections
    assert (edu.line_start, edu.line_end) == (4, 6)
    assert (proj.line_start, proj.line_end) == (7, 10)
    assert (skills_sec.line_start, skills_sec.line_end) == (11, 12)
    assert r.skills == ["Python", "SQL", "JavaScript"]
    assert r.warnings == []


# ---------- 技能拆分与清洗 ----------

def test_skill_dedup_and_paren_and_label():
    text = (
        "专业技能\n"
        "编程语言：Python、SQL、python\n"
        "框架：FastAPI（熟练）\n"
        "工具：Git / Docker\n"
        "C、R、3D建模"
    )
    r = parse_resume_text(text)

    # python 与 Python 按大小写去重；括号注释剥离；C/R 单字符大写保留
    assert r.skills == ["Python", "SQL", "FastAPI", "Git", "Docker", "C", "R", "3D建模"]


def test_skill_noise_filtered():
    text = "专业技能\nPython、x、——、C、java"
    r = parse_resume_text(text)

    # 单个小写字母与纯标点是噪音，丢弃
    assert r.skills == ["Python", "C", "java"]


# ---------- 基本信息可缺失 ----------

def test_personal_info_missing_warns():
    text = "教育背景\n2020-2024 XX大学 本科\n\n专业技能\nPython"
    r = parse_resume_text(text)

    assert r.basic.name is None
    assert r.basic.contact.email is None
    assert r.basic.contact.phone is None
    assert r.skills == ["Python"]
    assert r.warnings == [NAME_WARN]


def test_name_with_label_prefix():
    text = "姓名：赵四\n邮箱：zhao@x.com\n\n教育背景\n2020-2024 XX大学 本科"
    r = parse_resume_text(text)

    assert r.basic.name == "赵四"
    assert r.basic.contact.email == "zhao@x.com"


def test_no_contact_but_name_ok():
    text = "王五\n\n教育背景\n2020-2024 XX大学 本科\n\n专业技能\nGo"
    r = parse_resume_text(text)

    assert r.basic.name == "王五"
    assert r.basic.contact.email is None
    assert r.basic.contact.phone is None
    assert NAME_WARN not in r.warnings


# ---------- 缺区块 / 无标题简历 ----------

def test_missing_education_and_skills_warns():
    text = (
        "2024.06-2024.09  XX公司  数据分析实习生\n"
        "负责搭建用户指标体系，独立输出12份月度经营分析报告"
    )
    r = parse_resume_text(text)

    # 无任何标题行：全部落在 preamble，无区块、无技能
    assert r.sections == []
    assert r.skills == []
    assert r.warnings == [EDU_WARN, SKILL_WARN, NAME_WARN]
