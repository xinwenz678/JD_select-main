from copy import deepcopy
from datetime import datetime, timedelta
from uuid import UUID, uuid4

import pytest
from fastapi import Depends
from fastapi.testclient import TestClient
from sqlalchemy import select, text
from sqlalchemy.exc import OperationalError

from app.core.config import Settings
from app.core.database import build_engine, get_session
from app.main import create_app
from app.models.analysis_record import AnalysisRecord
from app.schemas.analysis_record import RecordCreate
from app.services.analysis_records import create_record


@pytest.fixture
def payload():
    return {
        "resume_text": "测试简历：Python、SQL 项目经验",
        "jd_text": "测试岗位：Python、SQL、Tableau",
        "job_title": "数据分析实习生",
        "result": {
            "score": 72,
            "score_breakdown": {"required_skills": 55, "preferred_skills": 12, "evidence_quality": 5},
            "matched_skills": ["Python", "SQL"],
            "missing_skills": ["Tableau"],
            "resume_sections": {"skills": ["Python", "SQL"]},
            "job_skills": [{"name": "Python", "required": True}],
            "suggestions": ["补充量化成果"],
            "algorithm_version": "rule-v1",
        },
    }


@pytest.fixture
def config(tmp_path):
    return Settings(_env_file=None, database_url=f"sqlite:///{(tmp_path / 'records.db').as_posix()}")


@pytest.fixture
def app(config):
    return create_app(config)


@pytest.fixture
def client(app):
    with TestClient(app) as test_client:
        yield test_client


def test_health_and_empty_history(client):
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "version": "0.1.0", "app": "JD Select", "database": "ok"}
    assert client.get("/api/matches").json() == {"items": [], "total": 0, "limit": 10, "offset": 0}


def test_create_detail_update_delete(client, payload):
    response = client.post("/api/analysis-records", json=payload)
    assert response.status_code == 201
    result = response.json()
    record_id = str(UUID(result["id"]))
    assert result["score"] == 72
    assert result["resume_sections"] == payload["result"]["resume_sections"]
    assert result["created_at"].endswith("Z")
    assert client.get(f"/api/matches/{record_id}").json() == result
    response = client.patch(f"/api/analysis-records/{record_id}", json={"job_title": "新标题"})
    assert response.status_code == 200
    assert response.json()["job_title"] == "新标题"
    assert response.json()["created_at"] == result["created_at"]
    assert response.json()["score_breakdown"] == result["score_breakdown"]
    assert client.patch(f"/api/analysis-records/{record_id}", json={"job_title": None}).json()["job_title"] is None
    response = client.delete(f"/api/analysis-records/{record_id}")
    assert response.status_code == 204
    assert response.content == b""
    assert client.get(f"/api/matches/{record_id}").status_code == 404
    assert client.get("/api/matches").json()["total"] == 0


def test_file_persistence_across_app_restart(config, payload):
    with TestClient(create_app(config)) as first:
        record = first.post("/api/analysis-records", json=payload).json()
    with TestClient(create_app(config)) as second:
        assert second.get(f"/api/matches/{record['id']}").json() == record
        assert second.get("/api/matches").json()["total"] == 1


def test_history_order_pagination_and_no_raw_text(client, app, payload):
    ids = []
    for i in range(12):
        item = deepcopy(payload)
        item["job_title"] = f"岗位{i}"
        ids.append(client.post("/api/analysis-records", json=item).json()["id"])
    # Fixed timestamps avoid assumptions about clock resolution.
    with app.state.session_factory.begin() as session:
        for i, record_id in enumerate(ids):
            session.get(AnalysisRecord, record_id).created_at = datetime(2026, 1, 1) + timedelta(seconds=i)
    page = client.get("/api/matches").json()
    assert page["total"] == 12 and len(page["items"]) == 10
    assert [item["id"] for item in page["items"]] == list(reversed(ids))[:10]
    assert "resume_text" not in page["items"][0] and "result_json" not in page["items"][0]
    assert [item["id"] for item in client.get("/api/matches?offset=10&limit=2").json()["items"]] == [ids[1], ids[0]]
    assert client.get("/api/matches?offset=99").json()["items"] == []


@pytest.mark.parametrize("query", ["limit=0", "limit=101", "offset=-1", "limit=abc"])
def test_invalid_pagination(client, query):
    response = client.get(f"/api/matches?{query}")
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "VALIDATION_ERROR"


@pytest.mark.parametrize("record_id,expected", [("not-a-uuid", 422), (str(uuid4()), 404)])
def test_bad_or_missing_id(client, record_id, expected):
    assert client.get(f"/api/matches/{record_id}").status_code == expected
    assert client.patch(f"/api/analysis-records/{record_id}", json={"job_title": "x"}).status_code == expected
    assert client.delete(f"/api/analysis-records/{record_id}").status_code == expected


@pytest.mark.parametrize("field,value", [("resume_text", ""), ("jd_text", "  "), ("resume_text", "x" * 100001)], ids=["empty-resume", "blank-jd", "oversize-resume"])
def test_invalid_input_not_saved(client, payload, field, value):
    payload[field] = value
    response = client.post("/api/analysis-records", json=payload)
    assert response.status_code == 422
    assert client.get("/api/matches").json()["total"] == 0
    for detail in response.json()["error"]["details"]:
        assert "input" not in detail and "ctx" not in detail


@pytest.mark.parametrize("score", [-1, 101, 71, True, "72"])
def test_invalid_or_inconsistent_score(client, payload, score):
    payload["result"]["score"] = score
    assert client.post("/api/analysis-records", json=payload).status_code == 422
    assert client.get("/api/matches").json()["total"] == 0


def test_invalid_json_and_immutable_snapshot(client, payload):
    response = client.post("/api/analysis-records", content="{bad", headers={"Content-Type": "application/json"})
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "VALIDATION_ERROR"
    record_id = client.post("/api/analysis-records", json=payload).json()["id"]
    assert client.patch(f"/api/analysis-records/{record_id}", json={}).status_code == 422
    assert client.patch(f"/api/analysis-records/{record_id}", json={"job_title": "x", "score": 99}).status_code == 422
    assert client.get(f"/api/matches/{record_id}").json()["score"] == 72


def test_http_errors(client):
    assert client.get("/api/unknown").json()["error"]["code"] == "NOT_FOUND"
    response = client.post("/api/health")
    assert response.status_code == 405
    assert response.json()["error"]["code"] == "METHOD_NOT_ALLOWED"
    assert "GET" in response.headers["allow"]


def test_cors_preflight_and_errors(client, app):
    origin = {"Origin": "http://localhost:5173"}
    response = client.options("/api/analysis-records", headers={
        **origin, "Access-Control-Request-Method": "POST", "Access-Control-Request-Headers": "content-type",
    })
    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == origin["Origin"]
    denied = client.options("/api/analysis-records", headers={
        "Origin": "https://other.example", "Access-Control-Request-Method": "POST",
    })
    assert denied.status_code == 400
    assert "access-control-allow-origin" not in denied.headers
    for path in ["/api/health", "/api/matches?limit=0", "/api/matches/nope", "/api/unknown"]:
        assert client.get(path, headers=origin).headers["access-control-allow-origin"] == origin["Origin"]


def test_unexpected_failure_is_safe_and_has_cors(client, app, caplog):
    @app.get("/test-error")
    def crash():
        raise RuntimeError("PRIVATE_RESUME_SENTINEL")

    response = client.get("/test-error", headers={"Origin": "http://localhost:5173"})
    assert response.status_code == 500
    assert response.json()["error"]["code"] == "INTERNAL_ERROR"
    assert response.headers["access-control-allow-origin"] == "http://localhost:5173"
    assert "PRIVATE_RESUME_SENTINEL" not in response.text + caplog.text


def test_database_failure_is_503(client, app, caplog):
    def unavailable():
        raise OperationalError("private query", {}, Exception("PRIVATE_DB_SENTINEL"))
    app.dependency_overrides[get_session] = unavailable
    try:
        response = client.get("/api/health", headers={"Origin": "http://localhost:5173"})
    finally:
        app.dependency_overrides.clear()
    assert response.status_code == 503
    assert response.json()["error"]["code"] == "DATABASE_ERROR"
    assert "PRIVATE_DB_SENTINEL" not in response.text + caplog.text
    assert response.headers["access-control-allow-origin"] == "http://localhost:5173"


def test_service_rollback_and_next_request(client, app, payload):
    @app.post("/test-rollback")
    def rollback_route(session=Depends(get_session)):
        create_record(session, RecordCreate.model_validate(payload))
        raise RuntimeError("abort transaction")

    assert client.post("/test-rollback").status_code == 500
    assert client.get("/api/matches").json()["total"] == 0
    assert client.post("/api/analysis-records", json=payload).status_code == 201


def test_stable_sqlite_path_when_cwd_changes(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    engine = build_engine("sqlite:///./jd_select.db")
    try:
        from app.core.database import BACKEND_DIR
        assert engine.url.database == str((BACKEND_DIR / "jd_select.db").resolve())
    finally:
        engine.dispose()


def test_tie_break_order(client, app, payload):
    ids = [client.post("/api/analysis-records", json=payload).json()["id"] for _ in range(3)]
    with app.state.session_factory.begin() as session:
        for record in session.scalars(select(AnalysisRecord)):
            record.created_at = datetime(2026, 1, 1)
    actual = [item["id"] for item in client.get("/api/matches").json()["items"]]
    assert actual == sorted(ids, reverse=True)
