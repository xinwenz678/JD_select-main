"""Persistence boundary for member C; no scoring or HTTP dependencies."""
from datetime import timezone
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.analysis_record import AnalysisRecord
from app.schemas.analysis_record import RecordCreate, RecordDetail, RecordPage, RecordSummary, RecordUpdate


def _timestamp(record: AnalysisRecord):
    value = record.created_at
    return value.replace(tzinfo=timezone.utc) if value.tzinfo is None else value


def as_detail(record: AnalysisRecord) -> RecordDetail:
    return RecordDetail(
        **record.result_json,
        id=record.id,
        job_title=record.job_title,
        resume_text=record.resume_text,
        jd_text=record.jd_text,
        created_at=_timestamp(record),
    )


def create_record(session: Session, payload: RecordCreate) -> AnalysisRecord:
    record = AnalysisRecord(
        job_title=payload.job_title,
        resume_text=payload.resume_text,
        jd_text=payload.jd_text,
        score=payload.result.score,
        algorithm_version=payload.result.algorithm_version,
        result_json=payload.result.model_dump(mode="json"),
    )
    session.add(record)
    # Caller controls commit/rollback so C can compose this within a transaction.
    session.flush()
    return record


def get_record(session: Session, record_id: UUID) -> AnalysisRecord | None:
    return session.get(AnalysisRecord, str(record_id))


def list_records(session: Session, limit: int = 10, offset: int = 0) -> RecordPage:
    if not 1 <= limit <= 100 or offset < 0:
        raise ValueError("limit must be 1..100 and offset must be >= 0")
    total = session.scalar(select(func.count()).select_from(AnalysisRecord)) or 0
    # Do not load full resume/JD/result blobs for the history list.
    rows = session.execute(
        select(
            AnalysisRecord.id, AnalysisRecord.job_title, AnalysisRecord.score,
            AnalysisRecord.algorithm_version, AnalysisRecord.created_at,
        )
        .order_by(AnalysisRecord.created_at.desc(), AnalysisRecord.id.desc())
        .offset(offset).limit(limit)
    ).all()
    items = [
        RecordSummary(
            id=row.id, job_title=row.job_title, score=row.score,
            algorithm_version=row.algorithm_version,
            created_at=row.created_at.replace(tzinfo=timezone.utc),
        )
        for row in rows
    ]
    return RecordPage(items=items, total=total, limit=limit, offset=offset)


def update_record(session: Session, record: AnalysisRecord, payload: RecordUpdate) -> AnalysisRecord:
    record.job_title = payload.job_title
    session.flush()
    return record


def delete_record(session: Session, record: AnalysisRecord) -> None:
    session.delete(record)
    session.flush()
