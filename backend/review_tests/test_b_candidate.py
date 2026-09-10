"""Independent B checks for A's delivered contract; synthetic data only."""
import pytest
from fastapi.testclient import TestClient
from app.core.config import Settings
from app.main import create_app
from app.services import star_suggestions
from app.services.skill_dict import extract_skills

PAYLOAD = {"resume_text": "合成学生\n技能\nPython", "jd_text": "必须掌握 Python。\n必须掌握 SQL。", "job_title": "合成验收岗位"}


@pytest.fixture
def client(tmp_path):
    with TestClient(create_app(Settings(_env_file=None, database_url=f"sqlite:///{(tmp_path / 'b.db').as_posix()}", llm_api_key="")), raise_server_exceptions=False) as value:
        yield value


@pytest.mark.parametrize('skills,matched,missing', [([], [], ['Python', 'SQL']), (['SQL'], ['SQL'], ['Python']), (['Python', 'SQL'], ['Python', 'SQL'], [])])
def test_confirmed_set_saved_with_honest_evidence(client, skills, matched, missing):
    result = client.post('/api/matches', json={**PAYLOAD, 'confirmed_skills': skills}).json()
    assert set(result['matched_skills']) == set(matched)
    assert set(result['missing_skills']) == set(missing)
    assert set(result['confirmed_skills']) == set(skills)
    for item in result['evidence_items']:
        if item['source'] == 'confirmed_resume':
            assert item['line'] is None and item['label'] in skills
        else:
            lines = PAYLOAD[f"{item['source']}_text"].splitlines()
            assert item['text'] == lines[item['line'] - 1]
    detail = client.get('/api/matches/' + result['id']).json()
    assert detail['confirmed_skills'] == result['confirmed_skills']
    assert detail['resume_text'] == PAYLOAD['resume_text']
    assert detail['evidence_items'] == result['evidence_items']


def test_confirmed_aliases_have_same_score(client):
    canonical = client.post('/api/matches', json={**PAYLOAD, 'confirmed_skills': ['Python', 'SQL']}).json()
    aliases = client.post('/api/matches', json={**PAYLOAD, 'confirmed_skills': ['python', 'sql']}).json()
    assert aliases['score'] == canonical['score']
    assert aliases['matched_skills'] == canonical['matched_skills']


def test_punctuation_delimited_aliases_are_extracted_as_canonical_skills():
    assert extract_skills('pytorch、JS') == ['JavaScript', 'PyTorch']
    assert extract_skills('PyTorch / JavaScript') == ['JavaScript', 'PyTorch']


def test_confirmed_name_is_returned_and_persisted(client):
    result = client.post('/api/matches', json={**PAYLOAD, 'confirmed_name': '  合成候选人  '}).json()
    assert result['job_title'] == PAYLOAD['job_title']
    assert result['confirmed_name'] == '合成候选人'
    detail = client.get('/api/matches/' + result['id']).json()
    assert detail['confirmed_name'] == '合成候选人'


@pytest.mark.parametrize('field,value', [('resume_text', '合' * 100001), ('jd_text', 'Python\n' + '合' * 100001), ('job_title', '岗' * 201)], ids=['long-resume', 'long-jd', 'long-title'])
def test_oversized_match_input_is_validation_error_without_save(client, field, value):
    response = client.post('/api/matches', json={**PAYLOAD, field: value})
    assert response.status_code == 422, f'{field}: expected validation error, got {response.status_code}'
    assert client.get('/api/matches').json()['total'] == 0


def test_star_contract_no_key_determinism_and_no_persistence(client):
    body = {'experience': '负责整理社团活动资料，核对报名名单并制作表格。', 'jd_text': PAYLOAD['jd_text']}
    first = client.post('/api/suggestions/star', json=body)
    assert first.status_code == 200
    result = first.json()
    assert result == client.post('/api/suggestions/star', json=body).json()
    assert result['source'] == 'rule-fallback'
    assert result['original'] == body['experience']
    assert set(result['star']) == {'situation', 'task', 'action', 'result'}
    assert all(result['star'].values()) and result['metric_prompts'] and result['notice']
    assert set(result['jd_keywords']) == {'Python', 'SQL'}
    assert not any(character.isdigit() for character in result['optimized_draft'])
    assert client.get('/api/matches').json()['total'] == 0


@pytest.mark.parametrize('field,value', [('experience', ''), ('experience', ' \n '), ('jd_text', ''), ('experience', '合' * 10001), ('jd_text', '合' * 50001)], ids=['empty-experience', 'blank-experience', 'empty-jd', 'long-experience', 'long-jd'])
def test_star_input_boundaries(client, field, value):
    response = client.post('/api/suggestions/star', json={'experience': '合成经历', 'jd_text': 'Python', field: value})
    assert response.status_code == 422
    assert response.json()['error']['message']


def test_star_uses_configured_compatible_model(monkeypatch, tmp_path):
    expected = {
        'original': '合成经历',
        'star': {'situation': '背景', 'task': '任务', 'action': '行动', 'result': '结果'},
        'optimized_draft': '背景 任务 行动 结果',
        'jd_keywords': ['Python'],
        'metric_prompts': ['核实处理规模'],
        'source': 'llm',
        'notice': star_suggestions.NOTICE,
    }
    monkeypatch.setattr(star_suggestions, '_request_llm', lambda experience, jd_text, settings: expected)
    config = Settings(
        _env_file=None,
        database_url=f"sqlite:///{(tmp_path / 'llm.db').as_posix()}",
        llm_api_key='synthetic-key',
        llm_base_url='https://example.invalid/v1',
        llm_model='synthetic-model',
    )
    with TestClient(create_app(config), raise_server_exceptions=False) as model_client:
        response = model_client.post('/api/suggestions/star', json={'experience': '合成经历', 'jd_text': 'Python'})
    assert response.status_code == 200
    assert response.json() == expected


def test_star_model_timeout_falls_back_without_error(monkeypatch, tmp_path):
    def timeout(*args, **kwargs):
        raise TimeoutError('synthetic timeout')

    monkeypatch.setattr(star_suggestions, '_request_llm', timeout)
    config = Settings(
        _env_file=None,
        database_url=f"sqlite:///{(tmp_path / 'timeout.db').as_posix()}",
        llm_api_key='synthetic-key',
        llm_base_url='https://example.invalid/v1',
        llm_model='synthetic-model',
    )
    with TestClient(create_app(config), raise_server_exceptions=False) as model_client:
        response = model_client.post('/api/suggestions/star', json={'experience': '合成经历', 'jd_text': 'Python'})
    assert response.status_code == 200
    assert response.json()['source'] == 'rule-fallback'
