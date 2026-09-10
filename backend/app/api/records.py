from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy.orm import Session

from app.core.database import get_session
from app.schemas.analysis_record import RecordCreate, RecordDetail, RecordPage, RecordUpdate
from app.services import analysis_records as storage

router = APIRouter(prefix="/api", tags=["analysis records"])
DBSession = Annotated[Session, Depends(get_session)]


def require_record(session: Session, record_id: UUID):
    record = storage.get_record(session, record_id)
    if record is None:
        raise HTTPException(404, "分析记录不存在")
    return record


@router.post("/analysis-records", response_model=RecordDetail, status_code=status.HTTP_201_CREATED)
def save_analysis(payload: RecordCreate, session: DBSession):
    """Save an already-computed result; this endpoint does not calculate a score."""
    record = storage.create_record(session, payload)
    result = storage.as_detail(record)
    session.commit()
    return result


@router.get("/matches", response_model=RecordPage)
def history(
    session: DBSession,
    limit: Annotated[int, Query(ge=1, le=100)] = 10,
    offset: Annotated[int, Query(ge=0)] = 0,
):
    return storage.list_records(session, limit, offset)


@router.get("/matches/{record_id}", response_model=RecordDetail)
def detail(record_id: UUID, session: DBSession):
    return storage.as_detail(require_record(session, record_id))


@router.patch("/analysis-records/{record_id}", response_model=RecordDetail)
def rename(record_id: UUID, payload: RecordUpdate, session: DBSession):
    record = storage.update_record(session, require_record(session, record_id), payload)
    result = storage.as_detail(record)
    session.commit()
    return result


@router.delete("/analysis-records/{record_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove(record_id: UUID, session: DBSession):
    storage.delete_record(session, require_record(session, record_id))
    session.commit()
    return Response(status_code=204)
