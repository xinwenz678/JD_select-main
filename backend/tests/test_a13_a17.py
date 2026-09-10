from fastapi.testclient import TestClient
from app.core.config import Settings
from app.main import create_app

def make_client(tmp_path):
    config = Settings(_env_file=None, database_url=f"sqlite:///{(tmp_path / 'a13.db').as_posix()}")
    return TestClient(create_app(config))

def test_confirmed_skills_replace_raw_skill_extraction(tmp_path):
    with make_client(tmp_path) as client:
        response = client.post("/api/matches", json={
            "resume_text": "\u6280\u80fd\uff1aPython", "confirmed_skills": ["SQL"],
            "jd_text": "\u4efb\u804c\u8981\u6c42\n\u5fc5\u987b\u638c\u63e1 Python\n\u719f\u7ec3\u4f7f\u7528 SQL", "job_title": "\u6570\u636e\u5206\u6790",
        })
        assert response.status_code == 200
        result = response.json()
        assert result["confirmed_skills"] == ["SQL"]
        assert result["matched_skills"] == ["SQL"]
        assert "Python" in result["missing_skills"]
        sql = next(item for item in result["evidence_items"] if item["label"] == "SQL")
        assert sql["source"] == "confirmed_resume" and sql["line"] is None

def test_star_rule_fallback_is_safe_and_deterministic(tmp_path):
    with make_client(tmp_path) as client:
        payload = {"experience": "\u8d1f\u8d23\u6570\u636e\u6e05\u6d17", "jd_text": "\u4efb\u804c\u8981\u6c42\n\u5fc5\u987b\u638c\u63e1 Python\n\u719f\u7ec3\u4f7f\u7528 SQL"}
        first = client.post("/api/suggestions/star", json=payload)
        second = client.post("/api/suggestions/star", json=payload)
        assert first.status_code == 200 and first.json() == second.json()
        assert first.json()["source"] == "rule-fallback"
        assert "\u4e0d\u8981\u7f16\u9020" in first.json()["star"]["result"]
        assert first.json()["original"] == payload["experience"]