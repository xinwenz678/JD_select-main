"""B review: independent, synthetic expectations through real HTTP + temporary SQLite."""
import json
import logging
from pathlib import Path
from uuid import UUID, uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.exc import OperationalError

from app.core.config import Settings
from app.main import create_app
from app.services import analysis_records

DATA = json.loads((Path(__file__).resolve().parents[2] / "sample_data/acceptance/cases.json").read_text(encoding="utf-8"))
CASES = [(case, variant) for case in DATA["cases"] for variant in case["variants"]]


def payload(case, variant):
    return {"resume_text": variant["resume_text"], "jd_text": variant.get("jd_text", case["jd_text"]), "job_title": case["job_title"]}


@pytest.fixture
def acceptance_config(tmp_path):
    return Settings(_env_file=None, database_url=f"sqlite:///{(tmp_path / 'acceptance.db').as_posix()}")


@pytest.fixture
def acceptance_client(acceptance_config):
    with TestClient(create_app(acceptance_config), raise_server_exceptions=False) as client:
        yield client


def verify_result(case, body, result):
    assert case["score_range"][0] <= result["score"] <= case["score_range"][1]
    assert result["score"] == sum(result["score_breakdown"].values())
    assert result["algorithm_version"] == "rule-v1"
    assert set(result["matched_skills"]) == set(case["matched_skills"])
    assert set(result["missing_skills"]) == set(case["missing_skills"])
    assert len(result["matched_skills"]) == len(set(result["matched_skills"]))
    assert all(isinstance(item, str) and item for item in result["suggestions"])
    for item in result["evidence_items"]:
        lines = body[f"{item['source']}_text"].strip().splitlines()
        assert 1 <= item["line"] <= len(lines)
        assert item["text"] == lines[item["line"] - 1].strip()
    for expected in case["skill_evidence"]:
        for label in expected["labels"]:
            assert any(item["source"] == expected["source"] and item["line"] == expected["line"] and item["label"] == label for item in result["evidence_items"])


@pytest.mark.parametrize("case,variant", CASES, ids=[f"{c['id']}-{v['name']}" for c, v in CASES])
def test_five_scenarios_persist_and_repeat(acceptance_client, case, variant):
    client = acceptance_client
    body = payload(case, variant)
    response = client.post("/api/matches", json=body)
    assert response.status_code == case["expected_status"]
    if response.status_code != 200:
        assert response.json()["error"]["message"]
        assert client.get("/api/matches").json()["total"] == 0
        return
    result = response.json()
    UUID(result["id"])
    verify_result(case, body, result)
    detail = client.get(f"/api/matches/{result['id']}").json()
    for key in result:
        assert detail[key] == result[key]
    assert detail["resume_text"] == body["resume_text"].strip()
    assert detail["jd_text"] == body["jd_text"].strip()
    again = client.post("/api/matches", json=body).json()
    assert again["id"] != result["id"]
    assert {k: v for k, v in result.items() if k != "id"} == {k: v for k, v in again.items() if k != "id"}
    assert client.get("/api/matches").json()["total"] == 2


def test_synonyms_have_equal_scores(acceptance_client):
    case = DATA["cases"][4]
    results = [acceptance_client.post("/api/matches", json=payload(case, v)).json() for v in case["variants"]]
    assert len({r["score"] for r in results}) == 1
    assert all(r["score_breakdown"] == results[0]["score_breakdown"] for r in results)


def test_match_commit_failure_rolls_back_and_retry_recovers(acceptance_client, monkeypatch, caplog):
    client = acceptance_client
    body = payload(DATA["cases"][0], DATA["cases"][0]["variants"][0])
    existing_id = client.post("/api/matches", json=body).json()["id"]
    marker = "SYNTHETIC_PRIVATE_BODY"
    with monkeypatch.context() as patch:
        from sqlalchemy.orm import Session

        def fail_commit(self):
            raise OperationalError("INSERT INTO analysis_records", {"resume": marker}, Exception("synthetic db failure"))

        patch.setattr(Session, "commit", fail_commit)
        with caplog.at_level(logging.ERROR, logger="jd_select.errors"):
            response = client.post("/api/matches", json={**body, "resume_text": body["resume_text"] + marker})
    assert response.status_code == 503
    assert response.json()["error"]["code"] == "DATABASE_ERROR"
    assert client.get("/api/matches").json()["total"] == 1
    assert client.get(f"/api/matches/{existing_id}").status_code == 200
    assert marker not in response.text + caplog.text
    assert "INSERT INTO" not in response.text + caplog.text
    assert "Traceback" not in response.text + caplog.text
    assert client.post("/api/matches", json=body).status_code == 200
    assert client.get("/api/matches").json()["total"] == 2


def test_unexpected_failure_after_flush_does_not_persist(acceptance_client, monkeypatch, caplog):
    original = analysis_records.create_record
    def fail_after_flush(session, record):
        original(session, record)
        raise RuntimeError("SYNTHETIC_SECRET internal path and SQL")
    with monkeypatch.context() as patch:
        patch.setattr(analysis_records, "create_record", fail_after_flush)
        with caplog.at_level(logging.ERROR, logger="jd_select.errors"):
            response = acceptance_client.post("/api/matches", json=payload(DATA["cases"][0], DATA["cases"][0]["variants"][0]))
    assert response.status_code == 500
    assert "SYNTHETIC_SECRET" not in response.text + caplog.text
    assert acceptance_client.get("/api/matches").json()["total"] == 0


def test_recent_ten_and_restart_preserve_real_matches(acceptance_config):
    body = payload(DATA["cases"][1], DATA["cases"][1]["variants"][0])
    with TestClient(create_app(acceptance_config)) as client:
        ids = [client.post("/api/matches", json={**body, "job_title": f"合成岗位 {i}"}).json()["id"] for i in range(12)]
        summaries = client.get("/api/matches").json()
        assert summaries["total"] == 12 and len(summaries["items"]) == 10
        assert [row["id"] for row in summaries["items"]] == list(reversed(ids))[:10]
        assert all("resume_text" not in row and "jd_text" not in row for row in summaries["items"])
        details = {id_: client.get(f"/api/matches/{id_}").json() for id_ in ids}
    with TestClient(create_app(acceptance_config)) as restarted:
        for id_, detail in details.items():
            assert restarted.get(f"/api/matches/{id_}").json() == detail
        assert restarted.get(f"/api/matches/{uuid4()}").status_code == 404
        assert restarted.get("/api/matches/not-a-uuid").status_code == 422
