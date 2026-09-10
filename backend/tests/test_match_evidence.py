from fastapi.testclient import TestClient

from app.core.config import Settings
from app.main import create_app


def test_match_returns_and_persists_line_addressable_evidence(tmp_path):
    config = Settings(_env_file=None, database_url=f"sqlite:///{(tmp_path / 'evidence.db').as_posix()}")
    resume = "\n".join([
        "项目经历",
        "负责使用 Python 开发数据接口",
        "优化接口响应时间 30%",
    ])
    jd = "\n".join([
        "Python 后端工程师",
        "必须掌握 Python、FastAPI、SQL",
    ])
    with TestClient(create_app(config)) as client:
        response = client.post(
            "/api/matches",
            json={"resume_text": resume, "jd_text": jd, "job_title": "Python 后端工程师"},
        )
        assert response.status_code == 200
        result = response.json()
        evidence = result["evidence_items"]
        assert {
            "source": "resume",
            "category": "matched_skill",
            "label": "Python",
            "line": 2,
            "text": "负责使用 Python 开发数据接口",
        } in evidence
        assert any(item["source"] == "resume" and item["category"] == "quantified_result" and item["line"] == 3 for item in evidence)
        assert any(item["source"] == "jd" and item["category"] == "required_skill" and item["label"] == "FastAPI" and item["line"] == 2 for item in evidence)

        record_id = result["id"]
        detail = client.get(f"/api/matches/{record_id}")
        assert detail.status_code == 200
        assert detail.json()["evidence_items"] == evidence