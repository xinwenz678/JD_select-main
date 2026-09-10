"""JD 解析接口的请求/响应模型（C4 交付，对齐冻结契约）。

对应契约：POST /api/jobs/parse
    - 请求: { jd_text: str }
    - 响应: { job_title, required_skills[], bonus_skills[], negated_skills[],
              all_skills[], warnings[] }
其中 required/bonus/negated 的技能项结构为 { name, signal, evidence }，
evidence 为原文证据片段，供结果页展示"评分依据"。
"""
from __future__ import annotations

from typing import List

from pydantic import BaseModel, Field


class JobParseRequest(BaseModel):
    """POST /api/jobs/parse 请求体。jd_text 为空字符串时由 Pydantic 直接返回 422。"""

    jd_text: str = Field(..., min_length=1, description="JD 文本")


class SkillInfo(BaseModel):
    """单个技能及其分类依据。"""

    name: str = Field(..., description="规范技能名")
    signal: str = Field(..., description="分类依据（必需·默认 / 加分 / 否定）")
    evidence: str = Field("", description="JD 原文证据片段")


class JobParseResponse(BaseModel):
    """POST /api/jobs/parse 响应体。"""

    job_title: str = ""
    required_skills: List[SkillInfo] = []
    bonus_skills: List[SkillInfo] = []
    negated_skills: List[SkillInfo] = []
    all_skills: List[str] = []
    warnings: List[str] = []
