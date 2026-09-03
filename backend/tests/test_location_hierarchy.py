"""
Test script using Python stdlib (urllib) to verify:
1. Location cascading hierarchy endpoints
2. Hierarchy tamper-proof validation
3. Role-specific registration (Healthcare Worker & Doctor)
4. Verification gating on login
5. Account verification flow
"""

import urllib.request
import urllib.error
import json

BASE_URL = "http://localhost:8000"


def http_req(method, url, data=None):
    headers = {"Content-Type": "application/json"}
    body = json.dumps(data).encode("utf-8") if data is not None else None
    req = urllib.request.Request(url, data=body, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req) as resp:
            status = resp.status
            content = resp.read().decode("utf-8")
            return status, json.loads(content) if content else {}
    except urllib.error.HTTPError as e:
        content = e.read().decode("utf-8")
        try:
            return e.code, json.loads(content)
        except Exception:
            return e.code, {"detail": content}


def run_tests():
    print("[*] Testing Cascading Location Hierarchy APIs...")
    # 1. States
    status, states = http_req("GET", f"{BASE_URL}/api/v1/locations/states")
    assert status == 200, f"States failed: {states}"
    assert len(states) >= 28, f"Expected at least 28 states, got {len(states)}"
    print(f"  [+] Retrieved {len(states)} states successfully.")

    tn = next((s for s in states if s["name"] == "Tamil Nadu"), None)
    assert tn is not None, "Tamil Nadu not found"
    tn_id = tn["id"]

    # 2. Districts
    status, districts = http_req("GET", f"{BASE_URL}/api/v1/locations/states/{tn_id}/districts")
    assert status == 200, f"Districts failed: {districts}"
    assert len(districts) >= 30, f"Expected at least 30 TN districts, got {len(districts)}"
    print(f"  [+] Retrieved {len(districts)} districts for Tamil Nadu.")

    cbe = next((d for d in districts if d["name"] == "Coimbatore"), None)
    assert cbe is not None, "Coimbatore not found"
    cbe_id = cbe["id"]

    # 3. Healthcare Centers
    status, phcs = http_req("GET", f"{BASE_URL}/api/v1/locations/districts/{cbe_id}/healthcare-centers")
    assert status == 200, f"PHCs failed: {phcs}"
    assert len(phcs) >= 3, f"Expected at least 3 PHCs in Coimbatore, got {len(phcs)}"
    phc_names = [p["name"] for p in phcs]
    print(f"  [+] Retrieved {len(phcs)} PHCs for Coimbatore: {phc_names}")

    # 4. Hospitals
    status, hosps = http_req("GET", f"{BASE_URL}/api/v1/locations/districts/{cbe_id}/hospitals")
    assert status == 200, f"Hospitals failed: {hosps}"
    assert len(hosps) >= 2, f"Expected at least 2 hospitals in Coimbatore, got {len(hosps)}"
    hosp_names = [h["name"] for h in hosps]
    print(f"  [+] Retrieved {len(hosps)} Hospitals for Coimbatore: {hosp_names}")

    # 5. Tamper Validation Test (District from KA with State TN)
    ka = next((s for s in states if s["name"] == "Karnataka"), None)
    status, ka_dists = http_req("GET", f"{BASE_URL}/api/v1/locations/states/{ka['id']}/districts")
    ka_dist = ka_dists[0]

    print("[*] Testing Hierarchical Relationship Integrity Validation...")
    worker_tamper = {
        "full_name": "Tamper Worker",
        "professional_id": "HW-TAMPER-001",
        "mobile": "9876543210",
        "email": "tamper.worker@test.org",
        "state_id": tn_id,
        "district_id": ka_dist["id"],  # Mismatch!
        "healthcare_centre_id": phcs[0]["id"],
        "password": "Password@123",
    }
    status, res = http_req("POST", f"{BASE_URL}/api/v1/auth/register/worker", worker_tamper)
    assert status == 400, f"Expected 400 for tampered district-state mismatch, got {status}: {res}"
    print(f"  [+] Tampered district rejected correctly: {res['detail']}")

    # 6. Real Worker Registration -> PENDING_VERIFICATION
    import time
    ts = int(time.time())
    worker_email = f"selvi.meenakshi.{ts}@tn.health.gov.in"
    worker_prof_id = f"ANM-CBE-{ts}"
    worker_mobile = f"984{ts % 10000000:07d}"

    valparai_phc = next((p for p in phcs if "Valparai" in p["name"]), phcs[0])
    worker_reg = {
        "full_name": "Selvi Meenakshi",
        "professional_id": worker_prof_id,
        "mobile": worker_mobile,
        "official_email": worker_email,
        "state_id": tn_id,
        "district_id": cbe_id,
        "healthcare_center_id": valparai_phc["id"],
        "password": "SecurePassword@123",
    }
    status, worker_res = http_req("POST", f"{BASE_URL}/api/v1/auth/register/worker", worker_reg)
    assert status == 201, f"Worker registration failed: {status} {worker_res}"
    assert worker_res["status"] == "PENDING_VERIFICATION", f"Expected PENDING_VERIFICATION, got {worker_res['status']}"
    print(f"  [+] Worker registered: status={worker_res['status']}")

    # 7. Worker Login Rejection while PENDING_VERIFICATION
    print("[*] Testing Verification Gated Login for Worker...")
    login_attempt = {
        "identifier": worker_email,
        "password": "SecurePassword@123",
    }
    status, res = http_req("POST", f"{BASE_URL}/api/v1/auth/login", login_attempt)
    assert status == 403, f"Expected 403 Forbidden for pending verification, got {status}: {res}"
    assert "pending verification" in res["detail"].lower(), f"Expected pending verification message, got {res}"
    print(f"  [+] Login correctly denied for unverified account: {res['detail']}")

    # 8. Real Doctor Registration -> PENDING_VERIFICATION
    doc_email = f"dr.rajesh.{ts}@retina.org"
    doc_med_reg = f"TNMC-{ts}"
    doc_mobile = f"944{ts % 10000000:07d}"

    aravind_hosp = next((h for h in hosps if "Aravind" in h["name"]), hosps[0])
    doc_reg = {
        "full_name": "Dr. Rajesh K. Sundaram",
        "medical_registration_id": doc_med_reg,
        "mobile": doc_mobile,
        "official_email": doc_email,
        "state_id": tn_id,
        "district_id": cbe_id,
        "hospital_id": aravind_hosp["id"],
        "speciality": "Vitreoretinal Specialist",
        "password": "DoctorSecure@123",
    }
    status, doc_res = http_req("POST", f"{BASE_URL}/api/v1/auth/register/doctor", doc_reg)
    assert status == 201, f"Doctor registration failed: {status} {doc_res}"
    assert doc_res["status"] == "PENDING_VERIFICATION", f"Expected PENDING_VERIFICATION, got {doc_res['status']}"
    print(f"  [+] Doctor registered: status={doc_res['status']}")

    # 9. Doctor Login Rejection while PENDING_VERIFICATION
    print("[*] Testing Verification Gated Login for Doctor...")
    login_attempt_doc = {
        "identifier": doc_email,
        "password": "DoctorSecure@123",
    }
    status, res = http_req("POST", f"{BASE_URL}/api/v1/auth/login", login_attempt_doc)
    assert status == 403, f"Expected 403 Forbidden for unverified doctor, got {status}: {res}"
    print(f"  [+] Login correctly denied for unverified doctor: {res['detail']}")

    # 10. Authoritative Verification via API
    print("[*] Verifying accounts via authoritative verification workflow...")
    status, res = http_req("POST", f"{BASE_URL}/api/v1/auth/verify-account", {
        "identifier": doc_email,
        "status": "VERIFIED",
        "notes": "Verified against Tamil Nadu Medical Council practitioner roster.",
    })
    assert status == 200, f"Verify doctor failed: {res}"
    assert res["is_verified"] is True

    status, res = http_req("POST", f"{BASE_URL}/api/v1/auth/verify-account", {
        "identifier": worker_email,
        "status": "VERIFIED",
        "notes": "Verified against NHM District Field Healthcare register.",
    })
    assert status == 200, f"Verify worker failed: {res}"
    assert res["is_verified"] is True
    print("  [+] Both accounts transitioned to VERIFIED status.")

    # 11. Login after verification
    print("[*] Testing Login for Verified Doctor...")
    status, doc_token = http_req("POST", f"{BASE_URL}/api/v1/auth/login", login_attempt_doc)
    assert status == 200, f"Doctor login after verification failed: {doc_token}"
    assert doc_token["access_token"] is not None
    assert doc_token["user"]["is_verified"] is True
    assert doc_token["user"]["facility_name"] == aravind_hosp["name"]
    print(f"  [+] Verified doctor logged in successfully! Facility: {doc_token['user']['facility_name']}")

    print("[*] Testing Login for Verified Healthcare Worker...")
    status, worker_token = http_req("POST", f"{BASE_URL}/api/v1/auth/login", login_attempt)
    assert status == 200, f"Worker login after verification failed: {worker_token}"
    assert worker_token["access_token"] is not None
    assert worker_token["user"]["is_verified"] is True
    assert worker_token["user"]["facility_name"] == valparai_phc["name"]
    print(f"  [+] Verified worker logged in successfully! Facility: {worker_token['user']['facility_name']}")

    print("\n=======================================================")
    print("ALL BACKEND VERIFICATION & LOCATION HIERARCHY TESTS PASSED!")
    print("=======================================================")

if __name__ == "__main__":
    run_tests()
