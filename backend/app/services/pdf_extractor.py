"""从文本型 PDF 提取简历原文，不进行 OCR。"""
from __future__ import annotations

from io import BytesIO

from pypdf import PdfReader
from pypdf.errors import PdfReadError

MAX_PDF_BYTES = 10 * 1024 * 1024
MAX_PDF_PAGES = 30
MAX_RESUME_TEXT_LENGTH = 50_000


def extract_pdf_text(content: bytes) -> tuple[str, int]:
    """校验 PDF 并返回整理后的文本和页数。"""
    if not content:
        raise ValueError("PDF 文件不能为空")
    if len(content) > MAX_PDF_BYTES:
        raise ValueError("PDF 文件不能超过 10 MB")
    if not content.lstrip().startswith(b"%PDF-"):
        raise ValueError("文件内容不是有效的 PDF")

    try:
        reader = PdfReader(BytesIO(content), strict=False)
        if reader.is_encrypted and reader.decrypt("") == 0:
            raise ValueError("暂不支持受密码保护的 PDF")
        page_count = len(reader.pages)
        if page_count == 0:
            raise ValueError("PDF 中没有页面")
        if page_count > MAX_PDF_PAGES:
            raise ValueError(f"PDF 页数不能超过 {MAX_PDF_PAGES} 页")
        pages = [(page.extract_text() or "").strip() for page in reader.pages]
    except ValueError:
        raise
    except (PdfReadError, OSError, TypeError, KeyError) as exc:
        raise ValueError("PDF 文件损坏或无法读取") from exc

    text = "\n\n".join(page for page in pages if page).strip()
    if not text:
        raise ValueError("未能从 PDF 提取文字，请上传文本型 PDF（暂不支持扫描件 OCR）")
    if len(text) > MAX_RESUME_TEXT_LENGTH:
        raise ValueError("PDF 提取后的简历文本不能超过 50000 字")
    return text, page_count
