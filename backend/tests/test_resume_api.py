"""简历解析接口测试（任务 B5）：POST /api/resumes/parse。"""
from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_upload_pdf_extracts_and_parses(monkeypatch):
    extracted = "教育背景\n2020-2024 XX大学 本科\n\n专业技能\nPython"
    monkeypatch.setattr("app.api.resumes.extract_pdf_text", lambda content: (extracted, 2))
    resp = client.post("/api/resumes/upload-pdf", content=b"%PDF-test", headers={"Content-Type": "application/pdf"})
    assert resp.status_code == 200
    body = resp.json()
    assert body["text"] == extracted
    assert body["pages"] == 2
    assert body["resume"]["skills"] == ["Python"]


def test_upload_pdf_rejects_wrong_content_type():
    resp = client.post("/api/resumes/upload-pdf", content=b"not-a-pdf", headers={"Content-Type": "text/plain"})
    assert resp.status_code == 415
    assert resp.json()["error"]["message"] == "仅支持 PDF 文件"


def test_upload_pdf_rejects_invalid_pdf():
    resp = client.post("/api/resumes/upload-pdf", content=b"not-a-pdf", headers={"Content-Type": "application/pdf"})
    assert resp.status_code == 422
    assert resp.json()["error"]["message"] == "文件内容不是有效的 PDF"


def test_parse_returns_contract():
    resp = client.post(
        "/api/resumes/parse",
        json={"text": "教育背景\n2020-2024 XX大学 本科\n\n专业技能\nPython"},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["schema_version"] == "resume-v1"
    assert body["algorithm_version"] == "rule-v1"
    assert body["resume"]["skills"] == ["Python"]
    assert body["resume"]["sections"][0]["kind"] == "education"


@pytest.mark.parametrize("name", ["resume_basic.txt", "resume_en.txt", "resume_missing_sections.txt"])
def test_sample_files_parse(name, sample_dir):
    text = (sample_dir / name).read_text(encoding="utf-8")
    resp = client.post("/api/resumes/parse", json={"text": text})
    assert resp.status_code == 200
    body = resp.json()["resume"]
    assert body["sections"]
    assert body["basic"] is not None


@pytest.mark.parametrize("bad", ["", "   ", "\n\n\t", "\u3000\u3000"])
def test_blank_text_rejected(bad):
    resp = client.post("/api/resumes/parse", json={"text": bad})
    assert resp.status_code == 422


def test_too_long_text_rejected():
    resp = client.post("/api/resumes/parse", json={"text": "a" * 50001})
    assert resp.status_code == 422


def test_missing_text_field_rejected():
    resp = client.post("/api/resumes/parse", json={})
    assert resp.status_code == 422


def test_health():
    with TestClient(app) as lifecycle_client:
        resp = lifecycle_client.get("/api/health")
    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"


# ---------- B4: POST /api/resumes/diagnose ----------

def test_diagnose_returns_contract():
    resp = client.post(
        "/api/resumes/diagnose",
        json={"text": "教育背景\nXX大学 本科\n\n专业技能\nPython"},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["schema_version"] == "resume-v1"
    assert body["algorithm_version"] == "rule-v1"
    assert body["summary"]["total"] == len(body["diagnoses"]) > 0
    assert body["summary"]["total"] == (
        body["summary"]["quantified"]
        + body["summary"]["action_verb"]
        + body["summary"]["suggestion"]
    )
    # 无年份教育 → 至少一条 suggestion
    assert any(d["category"] == "suggestion" for d in body["diagnoses"])


def test_diagnose_weak_sample(sample_dir):
    text = (sample_dir / "resume_weak.txt").read_text(encoding="utf-8")
    resp = client.post("/api/resumes/diagnose", json={"text": text})
    assert resp.status_code == 200
    body = resp.json()["diagnoses"]
    assert any(d["category"] == "action_verb" for d in body)
    assert any(d["category"] == "quantified" for d in body) is False
    assert any(d["category"] == "suggestion" for d in body)


@pytest.mark.parametrize("bad", ["", "   ", "\n\n\t", "\u3000\u3000"])
def test_diagnose_blank_text_rejected(bad):
    resp = client.post("/api/resumes/diagnose", json={"text": bad})
    assert resp.status_code == 422


def test_diagnose_missing_text_field_rejected():
    resp = client.post("/api/resumes/diagnose", json={})
    assert resp.status_code == 422
