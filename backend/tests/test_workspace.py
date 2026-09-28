import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from app.main import app
from app.core.database import Base, get_db

@pytest.fixture
def client():
    engine = create_engine('sqlite://', connect_args={'check_same_thread': False}, poolclass=StaticPool)
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    def override():
        with Session() as db:
            try:
                yield db
                db.commit()
            except Exception:
                db.rollback()
                raise
    previous = app.dependency_overrides.get(get_db)
    app.dependency_overrides[get_db] = override
    with TestClient(app) as client:
        yield client
    if previous:
        app.dependency_overrides[get_db] = previous
    else:
        app.dependency_overrides.pop(get_db, None)
    engine.dispose()

def payload(**changes):
    data = dict(full_name='Anika Verma', dob='1990-01-01', address='10 Garden Street, Delhi', id_number='123456789012', occupation='Engineer', annual_income=800000, country='India', identity=dict(name_on_id='Anika Verma', dob_on_id='1990-01-01', address_on_id='10 Garden Street, Delhi'))
    data.update(changes)
    return data

def create(client, **changes):
    response = client.post('/api/workspace/applications', json=payload(**changes))
    assert response.status_code == 201, response.text
    return response.json()

def test_discrepancies_never_inflate_watchlist_risk(client):
    data = create(client, identity=dict(name_on_id='Anika Wrong', dob_on_id='1991-02-02', address_on_id='99 Different Road'))
    assert data['discrepancy_count'] == 3
    assert data['risk_level'] == 'LOW'
    assert data['watchlist_matches'] == 0
    assert data['status'] == 'IN_REVIEW'

def test_watchlist_risk_independent_of_clean_identity(client):
    client.post('/api/workspace/watchlist', json=dict(name='Anika Verma', country='India', reason='Synthetic sanctions entry'))
    data = create(client)
    assert data['risk_level'] == 'HIGH'
    assert data['discrepancy_count'] == 0
    assert data['highest_match'] == 100

def test_missing_identity_and_invalid_format(client):
    data = create(client, identity=None, id_number='123')
    assert data['discrepancy_count'] == 2
    assert data['risk_level'] == 'LOW'
    assert {c['status'] for c in data['checks']} == {'MISSING', 'FORMAT_INVALID'}

def test_unsupported_country_is_unverified_not_validated(client):
    data = create(client, country='Singapore')
    assert data['unverified_count'] == 1
    assert data['discrepancy_count'] == 0
    assert not data['passed']

def test_shared_street_word_does_not_hide_address_mismatch(client):
    data = create(client, identity=dict(name_on_id='Anika Verma', dob_on_id='1990-01-01', address_on_id='99 Garden Street, Mumbai'))
    assert next(c for c in data['checks'] if c['field'] == 'address')['status'] == 'MISMATCH'

def test_repeated_screening_does_not_duplicate_alerts(client):
    client.post('/api/workspace/watchlist', json=dict(name='Anika Verma', country='India', reason='Synthetic watchlist entry'))
    data = create(client)
    for _ in range(3):
        client.post(f"/api/workspace/applications/{data['application_id']}/screen")
    detail = client.get(f"/api/workspace/applications/{data['application_id']}").json()
    assert len(detail['matches']) == 1
    assert len(client.get('/api/alerts').json()) == 1

def test_approved_customer_reopens_on_new_watchlist_evidence(client):
    data = create(client)
    response = client.post(f"/api/workspace/applications/{data['application_id']}/decision", json=dict(decision='APPROVED', reviewed_by='Test Officer', reason='Checked identity and screening evidence'))
    assert response.status_code == 200
    result = client.post('/api/workspace/watchlist', json=dict(name='Anika Verma', country='India', reason='New synthetic sanctions entry'))
    assert result.json()['alerts_generated'] == 1
    detail = client.get(f"/api/workspace/applications/{data['application_id']}").json()
    assert detail['status'] == 'IN_REVIEW'
    assert detail['risk_level'] == 'HIGH'
    logs = client.get('/api/audit-logs').json()
    assert any(l['action'] == 'APPLICATION_APPROVED' and l['performed_by'] == 'Test Officer' for l in logs)

def test_dismissed_false_positive_stays_dismissed(client):
    client.post('/api/workspace/watchlist', json=dict(name='Anika Verma', country='India', reason='Synthetic watchlist entry'))
    data = create(client)
    match = data['matches'][0]
    response = client.post(f"/api/workspace/matches/{match['screening_id']}/dismiss", json=dict(reviewed_by='Test Officer', reason='Different person after identity review'))
    assert response.json()['risk_level'] == 'LOW'
    again = client.post(f"/api/workspace/applications/{data['application_id']}/screen", json={}).json()
    assert again['risk_level'] == 'LOW'
    assert again['matches'][0]['review_status'] == 'FALSE_POSITIVE'

def test_decision_requires_reviewer_and_explanation(client):
    data = create(client)
    url = f"/api/workspace/applications/{data['application_id']}/decision"
    assert client.post(url, json=dict(decision='APPROVED', reviewed_by=' ', reason=' ')).status_code == 422
    decision = dict(decision='APPROVED', reviewed_by='Officer Test', reason='Identity and screening checked')
    assert client.post(url, json=decision).status_code == 200
    assert client.post(url, json=decision).status_code == 409

@pytest.mark.parametrize('changes', [dict(dob='2999-01-01'), dict(full_name=' '), dict(annual_income=-1), dict(dob='2000-02-30')])
def test_invalid_application_is_not_saved(client, changes):
    assert client.post('/api/workspace/applications', json=payload(**changes)).status_code == 422
    assert client.get('/api/workspace/applications').json() == []
