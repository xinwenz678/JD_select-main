"""POST /api/matches —— 计算并保存简历 × JD 匹配结果（契约见 schemas/match.py）。

契约：{ resume_text, jd_text, job_title(可选) } -> MatchResponse
实现链路（全部复用，无重复逻辑）：
    1. 空文本 -> 422 可读错误（Pydantic 已拦空串，这里再拦纯空白）；
    2. C2 parse_jd 解析 JD -> C3 score_match 计算匹配分；
    3. analysis_store.save_record 持久化（C4 占位实现，A3 合入后自动替换）；
    4. 按契约返回响应。
"""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_session
from app.schemas.analysis_record import MatchResult, RecordCreate
from app.schemas.match import MatchRequest, MatchResponse, ScoreBreakdown
from app.services import analysis_records
from app.services.jd_parser import parse_jd
from app.services.scoring import score_match
from app.services.skill_dict import canonicalize_skills

router = APIRouter(tags=["matches"])


@router.post("/api/matches", response_model=MatchResponse)
def create_match(request: MatchRequest, session: Session = Depends(get_session)) -> MatchResponse:
    resume_text = request.resume_text.strip()
    jd_text = request.jd_text.strip()
    if not resume_text:
        raise HTTPException(status_code=422, detail="简历文本不能为空")
    if not jd_text:
        raise HTTPException(status_code=422, detail="JD 文本不能为空")

    jd_result = parse_jd(jd_text)
    if not jd_result.get("required_skills") and not jd_result.get("bonus_skills"):
        raise HTTPException(status_code=422, detail="未从 JD 中识别到可匹配的技能，请补充明确的岗位技能要求")
    if request.job_title.strip():
        jd_result["job_title"] = request.job_title.strip()

    confirmed_skills = None if request.confirmed_skills is None else canonicalize_skills(request.confirmed_skills)
    confirmed_name = request.confirmed_name or None
    result = score_match(resume_text, jd_result, jd_text=jd_text, resume_skills=confirmed_skills)

    stored_result = MatchResult(
        score=result["score"],
        score_breakdown=result["score_breakdown"],
        matched_skills=result["matched_skills"],
        missing_skills=result["missing_skills"],
        resume_sections=result["resume_sections"],
        job_skills=result["job_skills"],
        suggestions=result["suggestions"],
        evidence_items=result["evidence_items"],
        confirmed_skills=result["confirmed_skills"],
        confirmed_name=confirmed_name,
        algorithm_version=result["algorithm_version"],
    )
    record = analysis_records.create_record(
        session,
        RecordCreate(
            job_title=jd_result["job_title"] or None,
            resume_text=resume_text,
            jd_text=jd_text,
            result=stored_result,
        ),
    )
    record_id = str(record.id)
    session.commit()
    return MatchResponse(
        id=record_id,
        job_title=jd_result["job_title"] or None,
        score=result["score"],
        score_breakdown=ScoreBreakdown(**result["score_breakdown"]),
        matched_skills=result["matched_skills"],
        missing_skills=result["missing_skills"],
        resume_sections=result["resume_sections"],
        job_skills=result["job_skills"],
        suggestions=result["suggestions"],
        evidence_items=result["evidence_items"],
        confirmed_skills=result["confirmed_skills"],
        confirmed_name=confirmed_name,
        algorithm_version=result["algorithm_version"],
    )
