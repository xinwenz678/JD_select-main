"""匹配接口的请求/响应模型（C4 交付，严格对齐冻结契约）。

对应契约：POST /api/matches
    - 请求: { resume_text: str, jd_text: str, job_title: str(可选) }
    - 响应: { id, score, score_breakdown, matched_skills, missing_skills,
              resume_sections, job_skills, suggestions, algorithm_version }

评分规则 v1：必需技能覆盖率 60 + 加分技能覆盖率 20 + 经历证据质量 20，
总分 0-100；算法版本固定为 rule-v1，保证同输入同输出。
"""
from __future__ import annotations

from typing import Annotated, List

from pydantic import BaseModel, Field, StringConstraints

NonEmptyMatchText = Annotated[str, StringConstraints(min_length=1, max_length=100_000)]
MatchJobTitle = Annotated[str, StringConstraints(max_length=200)]
ConfirmedName = Annotated[str, StringConstraints(strip_whitespace=True, max_length=200)]


class MatchRequest(BaseModel):
    """POST /api/matches 请求体。resume_text / jd_text 为空时由 Pydantic 直接返回 422。"""

    resume_text: NonEmptyMatchText = Field(..., description="简历文本")
    jd_text: NonEmptyMatchText = Field(..., description="JD 文本")
    job_title: MatchJobTitle = Field("", description="岗位名，可选；不传则从 JD 自动提取")
    confirmed_skills: List[str] | None = Field(None, description="用户确认后的技能集合；不传时从原文提取")
    confirmed_name: ConfirmedName | None = Field(None, description="用户确认后的姓名")


class ScoreBreakdown(BaseModel):
    """分项得分（契约字段名固定，前端结果页逐项展示）。"""

    required_skills: int = Field(..., description="必需技能覆盖率得分（满分 60）")
    preferred_skills: int = Field(..., description="加分技能覆盖率得分（满分 20）")
    evidence_quality: int = Field(..., description="经历证据质量得分（满分 20）")



class EvidenceItem(BaseModel):
    source: str
    category: str
    label: str
    line: int | None = Field(None, ge=1)
    text: str
class MatchResponse(BaseModel):
    """POST /api/matches 响应体（契约字段，一个不少）。"""

    id: str = Field(..., description="分析记录 id（uuid）")
    job_title: str | None = Field(None, description="岗位名称")
    score: int = Field(..., ge=0, le=100, description="总分 0-100")
    score_breakdown: ScoreBreakdown
    matched_skills: List[str] = Field(..., description="命中的 JD 技能")
    missing_skills: List[str] = Field(..., description="缺失的 JD 必需技能")
    resume_sections: dict = Field(..., description="简历区块检测（项目/实习/工作）")
    job_skills: List[str] = Field(..., description="JD 中识别到的全部技能")
    suggestions: List[str] = Field(..., description="规则化改进建议")
    evidence_items: List[EvidenceItem] = Field(default_factory=list, description="可定位到原文行的评分证据")
    confirmed_skills: List[str] = Field(default_factory=list, description="匹配时使用的用户确认技能集合")
    confirmed_name: str | None = Field(None, description="用户确认后的姓名")
    algorithm_version: str = Field(..., description="算法版本，固定 rule-v1")
