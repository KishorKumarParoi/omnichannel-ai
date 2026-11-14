"""
🏥 Automated End-to-End Test Suite for Hospital Doctor Focused Appointment Booking
and Clinical Patient Medical History Tracking with Previous History & Triage.
"""

import pytest
from fastapi.testclient import TestClient
from backend.app import app
from backend.database import init_db

@pytest.fixture(scope="module")
def client():
    init_db(force=True)
    return TestClient(app)


def test_hospital_overview(client):
    """Verifies hospital metadata, accreditation, and department analytics."""
    res = client.get("/api/v1/hospital/overview")
    assert res.status_code == 200
    data = res.json()
    assert "Apex Care" in data["hospital_name"]
    assert "JCI Accredited" in data["accreditation"]
    assert data["stats"]["total_active_doctors"] >= 6
    assert data["stats"]["registered_patients"] >= 2


def test_list_doctors_and_filtering(client):
    """Verifies listing of doctors and filtering by medical department."""
    res = client.get("/api/v1/hospital/doctors")
    assert res.status_code == 200
    doctors = res.json()
    assert len(doctors) >= 6
    names = [d["name"] for d in doctors]
    assert "Dr. Marcus Vance" in names
    assert "Dr. Elena Rostova" in names
    assert "Dr. Viktor Thorne" in names

    # Filter by department
    cardio_res = client.get("/api/v1/hospital/doctors?department=Cardiology")
    assert cardio_res.status_code == 200
    cardio_docs = cardio_res.json()
    assert any(d["name"] == "Dr. Marcus Vance" for d in cardio_docs)


def test_doctor_slots_availability(client):
    """Verifies computing available slots for Dr. Marcus Vance."""
    res = client.get("/api/v1/hospital/doctors/doc_marcus_vance/slots?target_date=2026-11-18")
    assert res.status_code == 200
    data = res.json()
    assert data["doctor_name"] == "Dr. Marcus Vance"
    assert data["chamber_no"] == "Cardiology Suite 301-A"
    assert len(data["available_slots"]) > 0


def test_lookup_patient_by_phone_and_previous_history(client):
    """Verifies looking up returning patient Kishor Kumar Paroi with MRN and past Cardiology history."""
    res = client.get("/api/v1/hospital/patients/lookup?identifier=%2B16172718180")
    assert res.status_code == 200
    patient = res.json()
    assert patient["full_name"] == "Kishor Kumar Paroi"
    assert patient["mrn"] == "MRN-2026-94821"
    assert patient["blood_group"] == "O+"
    assert "Sulfa drugs" in patient["allergies"]
    assert "Essential Hypertension" in patient["chronic_conditions"]
    assert len(patient["medical_history"]) >= 1

    # Verify that patient history contains recorded consultations
    doc_names = [e["doctor_name"] for e in patient["medical_history"]]
    assert any("Dr. Marcus Vance" in d or "Dr. Elena Rostova" in d for d in doc_names)


def test_register_new_patient_generates_mrn(client):
    """Verifies creating a new patient automatically issues unique MRN."""
    payload = {
        "full_name": "Alexander Hayes",
        "phone": "+16175559812",
        "email": "alexander.hayes@example.com",
        "date_of_birth": "1990-07-12",
        "gender": "Male",
        "blood_group": "B+",
        "allergies": ["Latex"],
        "chronic_conditions": ["Mild Asthma"],
        "active_medications": ["Fluticasone inhaler"]
    }
    res = client.post("/api/v1/hospital/patients", json=payload)
    assert res.status_code == 200
    patient = res.json()
    assert patient["full_name"] == "Alexander Hayes"
    assert patient["mrn"].startswith("MRN-2026-")
    assert "Latex" in patient["allergies"]


def test_book_doctor_appointment(client):
    """Verifies booking a consultation with Dr. Elena Rostova in Neurology."""
    payload = {
        "patient_name": "Alexander Hayes",
        "patient_phone": "+16175559812",
        "patient_email": "alexander.hayes@example.com",
        "doctor_name": "Dr. Elena Rostova",
        "department": "Neurology",
        "appointment_datetime": "2026-11-20T14:30:00",
        "appointment_type": "Initial Consultation",
        "symptoms": "Recurrent vestibular migraines and aura",
        "is_followup": False
    }
    res = client.post("/api/v1/hospital/appointments/book", json=payload)
    assert res.status_code == 200
    booking = res.json()
    assert booking["doctor_name"] == "Dr. Elena Rostova"
    assert booking["department"] == "Neurology"
    assert booking["chamber_no"] == "Neurology Tower 402-B"
    assert booking["token_no"] >= 1
    assert booking["mrn"].startswith("MRN-2026-")
    assert booking["status"] == "CONFIRMED"


def test_add_medical_encounter_to_history(client):
    """Verifies adding a doctor consultation encounter and retrieving it."""
    encounter_payload = {
        "doctor_name": "Dr. Elena Rostova",
        "department": "Neurology",
        "chief_complaint": "Vestibular migraine assessment",
        "diagnosis": "Migraine with brainstem aura; Benign Paroxysmal Positional Vertigo",
        "vitals": {"bp": "118/76 mmHg", "heart_rate": 66, "spo2": 99},
        "prescriptions": ["Sumatriptan 50mg PRN", "Magnesium Glycinate 400mg QD"],
        "clinical_notes": "Cranial nerves II-XII intact. Epley maneuver performed with symptom resolution.",
        "followup_recommended": "Review in 6 weeks with headache diary."
    }
    res = client.post("/api/v1/hospital/patients/MRN-2026-94821/history", json=encounter_payload)
    assert res.status_code == 200
    data = res.json()
    assert data["mrn"] == "MRN-2026-94821"
    assert data["doctor_name"] == "Dr. Elena Rostova"

    # Verify retrieval
    history_res = client.get("/api/v1/hospital/patients/MRN-2026-94821/history")
    assert history_res.status_code == 200
    encs = history_res.json()["encounters"]
    assert len(encs) >= 2


def test_clinical_symptom_triage_engine(client):
    """Verifies emergency red-flag triage detection vs routine department routing."""
    # Emergency Chest Pain
    emerg_res = client.post("/api/v1/hospital/triage/assess", json={
        "symptoms": "Severe crushing chest pain radiating to left jaw with cold sweats",
        "severity_scale_1_to_10": 9
    })
    assert emerg_res.status_code == 200
    emerg_data = emerg_res.json()
    assert emerg_data["is_emergency"] is True
    assert emerg_data["priority"] == "EMERGENCY"
    assert "911" in emerg_data["escalation_instructions"]

    # Non-emergency Knee Joint Pain -> Orthopedics
    ortho_res = client.post("/api/v1/hospital/triage/assess", json={
        "symptoms": "Chronic right knee pain and clicking after marathon running",
        "severity_scale_1_to_10": 5
    })
    assert ortho_res.status_code == 200
    ortho_data = ortho_res.json()
    assert ortho_data["is_emergency"] is False
    assert ortho_data["recommended_department"] == "Orthopedics"
    assert "Arthur Pendleton" in ortho_data["recommended_doctor"]


def test_vapi_mid_call_hospital_tools(client):
    """Verifies Vapi tool webhook executing hospital doctor tools mid-call."""
    # 1. Lookup patient record tool
    lookup_payload = {
        "message": {
            "type": "tool-calls",
            "toolCalls": [
                {
                    "id": "call_lookup_001",
                    "type": "function",
                    "function": {
                        "name": "lookup_patient_record",
                        "arguments": {"mrn": "MRN-2026-94821"}
                    }
                }
            ],
            "call": {"customer": {"number": "+16172718180"}}
        }
    }
    lookup_res = client.post("/api/vapi-tools", json=lookup_payload)
    assert lookup_res.status_code == 200
    result_text = lookup_res.json()["results"][0]["result"]
    assert "Kishor Kumar Paroi" in result_text
    assert "MRN-2026-94821" in result_text
    assert ("Dr. Marcus Vance" in result_text or "Dr. Elena Rostova" in result_text)

    # 2. Check doctor availability tool
    slots_payload = {
        "message": {
            "type": "tool-calls",
            "toolCalls": [
                {
                    "id": "call_slots_002",
                    "type": "function",
                    "function": {
                        "name": "check_doctor_availability",
                        "arguments": {"doctor_name": "Dr. Marcus Vance", "target_date": "2026-11-22"}
                    }
                }
            ]
        }
    }
    slots_res = client.post("/api/vapi-tools", json=slots_payload)
    assert slots_res.status_code == 200
    slots_text = slots_res.json()["results"][0]["result"]
    assert "Dr. Marcus Vance" in slots_text
    assert "Cardiology Suite 301-A" in slots_text

    # 3. Clinical triage tool
    triage_payload = {
        "message": {
            "type": "tool-calls",
            "toolCalls": [
                {
                    "id": "call_triage_003",
                    "type": "function",
                    "function": {
                        "name": "triage_symptom_urgency",
                        "arguments": {"symptoms": "Crushing chest pain and nausea", "severity_scale_1_to_10": 10}
                    }
                }
            ]
        }
    }
    triage_res = client.post("/api/vapi-tools", json=triage_payload)
    assert triage_res.status_code == 200
    triage_text = triage_res.json()["results"][0]["result"]
    assert "CRITICAL MEDICAL ALERT" in triage_text
    assert "911" in triage_text
