from datetime import datetime, timezone
from uuid import uuid4

from sqlalchemy import JSON, CheckConstraint, DateTime, Index, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class AnalysisRecord(Base):
    __tablename__ = "analysis_records"
    __table_args__ = (
        CheckConstraint("score >= 0 AND score <= 100", name="ck_analysis_score"),
        Index("ix_analysis_created_id", "created_at", "id"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    job_title: Mapped[str | None] = mapped_column(String(200), nullable=True)
    resume_text: Mapped[str] = mapped_column(Text)
    jd_text: Mapped[str] = mapped_column(Text)
    score: Mapped[int] = mapped_column(Integer)
    result_json: Mapped[dict] = mapped_column(JSON)
    algorithm_version: Mapped[str] = mapped_column(String(64))
    # SQLite stores a naive UTC timestamp; response serialization restores UTC.
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc).replace(tzinfo=None)
    )
