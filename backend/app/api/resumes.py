"""简历解析、PDF 上传与诊断接口。"""
from fastapi import APIRouter, HTTPException, Request

from app.schemas.resume import (
    ResumeDiagnoseResponse,
    ResumePdfUploadResponse,
    ResumeParseRequest,
    ResumeParseResponse,
)
from app.services.pdf_extractor import MAX_PDF_BYTES, extract_pdf_text
from app.services.resume_diagnose import diagnose_resume
from app.services.resume_parser import parse_resume

router = APIRouter(prefix="/api/resumes", tags=["resumes"])


@router.post("/parse", response_model=ResumeParseResponse)
def parse_resume_endpoint(payload: ResumeParseRequest) -> ResumeParseResponse:
    return parse_resume(payload.text)


@router.post("/upload-pdf", response_model=ResumePdfUploadResponse)
async def upload_pdf_endpoint(request: Request) -> ResumePdfUploadResponse:
    content_type = request.headers.get("content-type", "").split(";", 1)[0].strip().lower()
    if content_type != "application/pdf":
        raise HTTPException(status_code=415, detail="仅支持 PDF 文件")

    content_length = request.headers.get("content-length")
    if content_length:
        try:
            if int(content_length) > MAX_PDF_BYTES:
                raise HTTPException(status_code=413, detail="PDF 文件不能超过 10 MB")
        except ValueError:
            pass

    content = await request.body()
    try:
        text, pages = extract_pdf_text(content)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

    parsed = parse_resume(text)
    return ResumePdfUploadResponse(
        text=text,
        pages=pages,
        schema_version=parsed.schema_version,
        algorithm_version=parsed.algorithm_version,
        resume=parsed.resume,
    )


@router.post("/diagnose", response_model=ResumeDiagnoseResponse)
def diagnose_resume_endpoint(payload: ResumeParseRequest) -> ResumeDiagnoseResponse:
    return diagnose_resume(payload.text)
