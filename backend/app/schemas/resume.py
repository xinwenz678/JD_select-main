"""简历解析公共契约（任务 B1）。

结构冻结前请与成员 A（持久化）、C（匹配）和 D（结果页）共同确认，
变更会同时影响接口两端，见 docs/resume-contract.md。
"""
from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field, field_validator


class ContactInfo(BaseModel):
    """联系方式（可缺失）。"""

    email: str | None = None
    phone: str | None = None


class BasicInfo(BaseModel):
    """基本信息（可缺失）。"""

    name: str | None = None
    contact: ContactInfo = Field(default_factory=ContactInfo)


class Section(BaseModel):
    """简历中识别出的一个原文区块。

    kind 取值：education | experience | projects | skills | other
    line_start / line_end 为区块首尾非空行在原文中的行号（1 起），
    供诊断建议（B4）和结果页定位使用。
    """

    kind: str
    heading: str = ""
    line_start: int = Field(..., description="区块起始行号（1 起）")
    line_end: int = Field(..., description="区块结束行号（含）")
    lines: list[str] = Field(default_factory=list)


class ParsedResume(BaseModel):
    basic: BasicInfo = Field(default_factory=BasicInfo)
    sections: list[Section] = Field(default_factory=list)
    skills: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)


class ResumeParseRequest(BaseModel):
    text: str = Field(..., min_length=1, max_length=50_000, description="简历原文")

    @field_validator("text")
    @classmethod
    def text_not_blank(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("简历文本不能为空")
        return v


class ResumeParseResponse(BaseModel):
    schema_version: str = "resume-v1"
    algorithm_version: str = "rule-v1"
    resume: ParsedResume


class ResumePdfUploadResponse(ResumeParseResponse):
    """PDF 文本提取并解析后的结果。"""

    text: str
    pages: int = Field(..., ge=1)


# ---------- 任务 B4：简历规则诊断 ----------


class DiagnoseItem(BaseModel):
    """一条简历诊断结论。

    category 取值：
    - quantified   命中量化指标（数字 + 单位/百分比），正向亮点；
    - action_verb  经历/项目行不以动作动词开头，建议改写；
    - suggestion   结构性缺失建议（缺年份/技能过少/缺区块等）。

    line 为该结论定位到的原文非空行号（1 起），区块级/全局结论可为 null；
    section 为 line 所在区块 kind（education/experience/projects/skills），
    便于结果页按区块分组展示。
    """

    category: Literal["quantified", "action_verb", "suggestion"]
    message: str
    suggestion: str = ""
    line: int | None = None
    section: str | None = None


class DiagnoseSummary(BaseModel):
    """诊断统计，供结果页仪表盘直接使用。"""

    total: int
    quantified: int = 0
    action_verb: int = 0
    suggestion: int = 0


class ResumeDiagnoseResponse(BaseModel):
    schema_version: str = "resume-v1"
    algorithm_version: str = "rule-v1"
    summary: DiagnoseSummary
    diagnoses: list[DiagnoseItem] = Field(default_factory=list)
