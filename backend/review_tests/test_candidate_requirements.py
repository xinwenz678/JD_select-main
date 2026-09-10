"""Release requirement regressions retained after B resolved the candidate defects."""
from fastapi.testclient import TestClient
from app.core.config import Settings
from app.main import create_app


def test_unknown_skill_jd_is_readable_validation_error(tmp_path):
    config = Settings(_env_file=None, database_url=f"sqlite:///{(tmp_path / 'candidate.db').as_posix()}")
    with TestClient(create_app(config), raise_server_exceptions=False) as client:
        response = client.post("/api/matches", json={"resume_text": "技能\nPython", "jd_text": "欢迎加入，本岗位要求认真细致。"})
        assert response.status_code in (400, 422), f"Unrecognized JD must not become a server error: HTTP {response.status_code}"
        assert client.get("/api/matches").json()["total"] == 0


def test_star_is_registered_before_level_two_release():
    paths = create_app(Settings(_env_file=None, database_url="sqlite:///:memory:")).openapi()["paths"]
    assert "post" in paths.get("/api/suggestions/star", {}), "A17: STAR endpoint/contract is not delivered"
