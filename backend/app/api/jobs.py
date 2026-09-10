"""POST /api/jobs/parse —— 解析 JD 文本，返回岗位名 + 必需/加分/否定技能（带证据）。

契约：{ jd_text: str } -> { job_title, required_skills[], bonus_skills[],
                             negated_skills[], all_skills[], warnings[] }
实现：完全复用 C2 的 jd_parser.parse_jd（无重复逻辑）；空文本返回 422 可读错误。
"""
from __future__ import annotations

from fastapi import APIRouter, HTTPException

from app.schemas.job import JobParseRequest, JobParseResponse, SkillInfo
from app.services.jd_parser import parse_jd

router = APIRouter(tags=["jobs"])


@router.post("/api/jobs/parse", response_model=JobParseResponse)
def parse_job(request: JobParseRequest) -> JobParseResponse:
    jd_text = request.jd_text.strip()
    if not jd_text:
        raise HTTPException(status_code=422, detail="JD 文本不能为空")

    result = parse_jd(jd_text)
    return JobParseResponse(
        job_title=result["job_title"],
        required_skills=[SkillInfo(**item) for item in result["required_skills"]],
        bonus_skills=[SkillInfo(**item) for item in result["bonus_skills"]],
        negated_skills=[SkillInfo(**item) for item in result["negated_skills"]],
        all_skills=result["all_skills"],
        warnings=result.get("warnings", []),
    )
