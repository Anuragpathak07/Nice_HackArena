import os
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.main import app
from app.core.database import Base, get_db
from app.models import Applicant, IDRecord, Watchlist, ScreeningResult, Alert, AuditLog
from app.services.matching_service import MatchingService
from app.services.consistency_service import ConsistencyService

TEST_DATABASE_URL = "sqlite:///./test_kyc_aml.db"

engine = create_engine(TEST_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db

@pytest.fixture(autouse=True)
def setup_db():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)

client = TestClient(app)

# TEST 1: Applicant creation
def test_1_applicant_creation():
    payload = {
        "application_id": "APP_TEST_001",
        "full_name": "Test User",
        "dob": "1990-01-01",
        "address": "123 Main St, New York, NY",
        "id_number": "999-00-1111",
        "occupation": "Engineer",
        "annual_income": 75000.0,
        "country": "United States"
    }
    response = client.post("/api/applicants", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert data["application_id"] == "APP_TEST_001"
    assert data["full_name"] == "Test User"

# TEST 2: Applicant retrieval
def test_2_applicant_retrieval():
    test_1_applicant_creation()
    response = client.get("/api/applicants/APP_TEST_001")
    assert response.status_code == 200
    assert response.json()["application_id"] == "APP_TEST_001"

# TEST 3: Invalid input
def test_3_invalid_input():
    # Missing required field full_name & dob
    payload = {"country": "India"}
    response = client.post("/api/applicants", json=payload)
    assert response.status_code == 422 # Unprocessable Entity

# TEST 4: ID format validation
def test_4_id_format_validation():
    # Valid Indian Aadhaar (12 digits)
    res_valid = ConsistencyService.check_id_number_format("7755 5218 2488", "India")
    assert res_valid.status == "MATCH"

    # Invalid Indian Aadhaar format (only 5 digits)
    res_invalid = ConsistencyService.check_id_number_format("12345", "India")
    assert res_invalid.status == "FORMAT_INVALID"

# TEST 5: Matching names
def test_5_matching_names():
    score, match_type, _ = MatchingService.calculate_similarity("Rajesh Kumar", "Rajesh Kumar")
    assert score == 100.0
    assert match_type == "EXACT"

# TEST 6: Name mismatch
def test_6_name_mismatch():
    score, match_type, _ = MatchingService.calculate_similarity("Rajesh Kumar", "Alice Smith")
    assert score < 50.0
    assert match_type == "NO_MATCH"

# TEST 7: DOB mismatch
def test_7_dob_mismatch():
    app = Applicant(full_name="John Doe", dob="1990-01-01", address="Same St", id_number="123456", country="India")
    id_rec = IDRecord(name_on_id="John Doe", dob_on_id="1992-05-10", address_on_id="Same St")
    res = ConsistencyService.verify_consistency(app, id_rec)
    assert res.passed == False
    dob_check = next(c for c in res.checks if c.field == "dob")
    assert dob_check.status == "MISMATCH"

# TEST 8: Address mismatch
def test_8_address_mismatch():
    app = Applicant(full_name="John Doe", dob="1990-01-01", address="123 Street A", id_number="123456", country="India")
    id_rec = IDRecord(name_on_id="John Doe", dob_on_id="1990-01-01", address_on_id="999 Random Blvd")
    res = ConsistencyService.verify_consistency(app, id_rec)
    assert res.passed == False

# TEST 9: Exact watchlist match
def test_9_exact_watchlist_match():
    score, match_type, _ = MatchingService.calculate_similarity("Chen Wei", "Chen Wei")
    assert score == 100.0
    assert match_type == "EXACT"

# TEST 10: Near watchlist match
def test_10_near_watchlist_match():
    score, match_type, _ = MatchingService.calculate_similarity("Rajesh Kumar", "Rajesh Kumarr")
    assert score > 90.0
    assert match_type == "FUZZY_HIGH"

# TEST 11: No watchlist match
def test_11_no_watchlist_match():
    score, match_type, _ = MatchingService.calculate_similarity("Johnathan Vance", "Emeka Nwankwo")
    assert score < 60.0

# TEST 12: Multiple potential matches
def test_12_multiple_potential_matches():
    # Seed Watchlist
    client.post("/api/watchlist", json={"name": "Rajesh Kumar", "country": "India", "reason": "Fraud"})
    client.post("/api/watchlist", json={"name": "Rajesh Kumarr", "country": "India", "reason": "Tax Evasion"})

    # Post Applicant
    res = client.post("/api/applicants", json={
        "application_id": "APP_MULT",
        "full_name": "Rajesh Kumar",
        "dob": "1990-01-01",
        "address": "Delhi",
        "id_number": "7755 5218 2488",
        "country": "India"
    })
    
    screen_res = client.post("/api/applicants/APP_MULT/screen")
    assert len(screen_res.json()) >= 2

# TEST 13: Risk classification
def test_13_risk_classification():
    # High match + same country -> CRITICAL risk
    client.post("/api/watchlist", json={"name": "Ahmad Khan", "country": "Pakistan", "reason": "Terrorism"})
    client.post("/api/applicants", json={
        "application_id": "APP_RISK",
        "full_name": "Ahmad Khan",
        "dob": "1986-02-19",
        "address": "Islamabad",
        "id_number": "22948-6628360-1",
        "country": "Pakistan"
    })
    app_res = client.get("/api/applicants/APP_RISK")
    assert app_res.json()["risk_level"] in ["HIGH", "CRITICAL"]

# TEST 14: Compliance decision
def test_14_compliance_decision():
    test_13_risk_classification()
    alerts = client.get("/api/alerts").json()
    assert len(alerts) > 0
    alert_id = alerts[0]["alert_id"]

    review_res = client.post(f"/api/alerts/{alert_id}/review", json={
        "action": "REJECT_APPLICANT",
        "reviewed_by": "Compliance Officer Officer_007",
        "reason": "Confirmed match against sanctions watchlist record"
    })
    assert review_res.status_code == 200
    assert review_res.json()["new_status"] == "REJECTED"

# TEST 15: Audit log creation
def test_15_audit_log_creation():
    test_14_compliance_decision()
    audits = client.get("/api/audit-logs").json()
    assert len(audits) > 0
    assert any("COMPLIANCE_ALERT_REVIEWED_REJECT_APPLICANT" in a["action"] for a in audits)

# TEST 16: Watchlist addition
def test_16_watchlist_addition():
    res = client.post("/api/watchlist", json={
        "name": "New Sanction Target",
        "country": "Russia",
        "reason": "Sanctions List"
    })
    assert res.status_code == 201
    assert res.json()["name"] == "New Sanction Target"

# TEST 17: Existing-customer re-screening
def test_17_existing_customer_rescreening():
    # 1. Create applicant with clean record
    client.post("/api/applicants", json={
        "application_id": "APP_CLEAN",
        "full_name": "Sergey Volkov",
        "dob": "1980-01-01",
        "address": "Moscow",
        "id_number": "4864 887663",
        "country": "Russia"
    })
    
    # 2. Add new watchlist record matching existing customer
    res = client.post("/api/watchlist", json={
        "name": "Sergey Volkov",
        "country": "Russia",
        "reason": "Sanctions Update"
    })
    assert res.status_code == 201

    # 3. Check that alert was generated automatically for APP_CLEAN
    app_data = client.get("/api/applicants/APP_CLEAN").json()
    assert app_data["status"] == "IN_REVIEW"

# TEST 18: No-match re-screening
def test_18_no_match_rescreening():
    # Add unique non-matching target
    res = client.post("/api/watchlist", json={
        "name": "Unique Unknown Person 12345",
        "country": "Iceland",
        "reason": "Test"
    })
    assert res.status_code == 201

# TEST 19: Duplicate data
def test_19_duplicate_data():
    test_1_applicant_creation()
    # Try duplicate post with same ID
    res = client.post("/api/applicants", json={
        "application_id": "APP_TEST_001",
        "full_name": "Duplicate User",
        "dob": "1990-01-01",
        "address": "123 St",
        "id_number": "999-00-1111",
        "country": "United States"
    })
    assert res.status_code == 400

# TEST 20: Large screening workload
def test_20_large_screening_workload():
    # Create 50 applicants & screen synchronously
    for i in range(50):
        client.post("/api/applicants", json={
            "application_id": f"APP_BULK_{i}",
            "full_name": f"Bulk Test Person {i}",
            "dob": "1990-01-01",
            "address": "Bulk St",
            "id_number": f"1000{i}",
            "country": "India"
        })
    dashboard = client.get("/api/dashboard/summary").json()
    assert dashboard["total_applicants"] >= 50
