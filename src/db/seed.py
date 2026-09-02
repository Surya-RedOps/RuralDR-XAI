"""
RuralDR-XAI: Initial Database Seeder
Seeds verified users, medical facilities, locations, and sample cases into MySQL.
"""

from datetime import datetime, timedelta
import json
from sqlalchemy.orm import Session
from .models import User, Location, Hospital, ScreeningCase, ScreeningImage, AIPrediction, Referral, DoctorReview, AuditLog
from ..core.security import hash_password


def seed_initial_data(db: Session):
    """Populates clean demo data if the database is uninitialized."""
    # Check if already seeded
    if db.query(Location).first() is not None or db.query(User).first() is not None:
        return

    print("[*] Seeding database with verified locations, hospitals, and users...")

    # 1. Seed Locations
    locations_data = [
        # Tamil Nadu
        {"state": "Tamil Nadu", "district": "Coimbatore", "healthcare_centre": "Primary Health Centre — Valparai", "code": "TN-CBE-01"},
        {"state": "Tamil Nadu", "district": "Coimbatore", "healthcare_centre": "Community Health Centre — Pollachi", "code": "TN-CBE-02"},
        {"state": "Tamil Nadu", "district": "Coimbatore", "healthcare_centre": "Upgraded Primary Health Centre — Sulur", "code": "TN-CBE-03"},
        {"state": "Tamil Nadu", "district": "Coimbatore", "healthcare_centre": "Rural Health Sub-Center — Anaimalai", "code": "TN-CBE-04"},
        {"state": "Tamil Nadu", "district": "Coimbatore", "healthcare_centre": "Government Primary Health Centre — Kinathukadavu", "code": "TN-CBE-05"},
        
        {"state": "Tamil Nadu", "district": "Madurai", "healthcare_centre": "Primary Health Centre — Usilampatti", "code": "TN-MDU-01"},
        {"state": "Tamil Nadu", "district": "Madurai", "healthcare_centre": "Community Health Centre — Melur", "code": "TN-MDU-02"},
        {"state": "Tamil Nadu", "district": "Madurai", "healthcare_centre": "Rural Health Center — Thirumangalam", "code": "TN-MDU-03"},
        
        {"state": "Tamil Nadu", "district": "Salem", "healthcare_centre": "Rural Health Centre — Omalur", "code": "TN-SLM-01"},
        {"state": "Tamil Nadu", "district": "Salem", "healthcare_centre": "Primary Health Centre — Attur", "code": "TN-SLM-02"},
        {"state": "Tamil Nadu", "district": "Salem", "healthcare_centre": "Community Health Centre — Mettur", "code": "TN-SLM-03"},

        {"state": "Tamil Nadu", "district": "Tiruchirappalli", "healthcare_centre": "Primary Health Centre — Musiri", "code": "TN-TRY-01"},
        {"state": "Tamil Nadu", "district": "Tiruchirappalli", "healthcare_centre": "Community Health Centre — Manapparai", "code": "TN-TRY-02"},

        # Karnataka
        {"state": "Karnataka", "district": "Mysuru", "healthcare_centre": "Rural Primary Health Centre — Hunsur", "code": "KA-MYS-01"},
        {"state": "Karnataka", "district": "Mysuru", "healthcare_centre": "Community Health Centre — Nanjangud", "code": "KA-MYS-02"},
    ]

    location_objs = []
    for loc in locations_data:
        obj = Location(**loc)
        db.add(obj)
        location_objs.append(obj)
    db.commit()

    # Map for easy lookup by district
    loc_by_district = {}
    for obj in location_objs:
        loc_by_district.setdefault(obj.district, []).append(obj)

    # 2. Seed Verified Hospitals
    hospitals_data = [
        {
            "name": "Coimbatore Medical College Hospital — Regional Eye Centre",
            "district": "Coimbatore",
            "address": "Trichy Road, Coimbatore, Tamil Nadu 641018",
            "contact": "+91 422 230 1393",
            "speciality": "Tertiary Vitreoretinal & Laser Surgery Unit",
            "availability": "24/7 Emergency Eye Care",
            "is_verified": True,
        },
        {
            "name": "Aravind Eye Hospital — Coimbatore",
            "district": "Coimbatore",
            "address": "Avinashi Road, Civil Aerodrome Post, Coimbatore 641014",
            "contact": "+91 422 436 0400",
            "speciality": "Diabetic Retinopathy Speciality Clinic",
            "availability": "Mon-Sat 8:00 AM – 6:00 PM",
            "is_verified": True,
        },
        {
            "name": "Lotus Eye Hospital & Institute — Coimbatore",
            "district": "Coimbatore",
            "address": "Civil Aerodrome Post, Peelamedu, Coimbatore 641014",
            "contact": "+91 422 422 9900",
            "speciality": "Retina & Vitreous Subspeciality Center",
            "availability": "Mon-Sat 9:00 AM – 7:00 PM",
            "is_verified": True,
        },
        {
            "name": "Government Rajaji Hospital — Department of Ophthalmology",
            "district": "Madurai",
            "address": "Panagal Road, Shenoy Nagar, Madurai, Tamil Nadu 625020",
            "contact": "+91 452 253 2535",
            "speciality": "Government Tertiary Retina Care",
            "availability": "24/7 Emergency Care",
            "is_verified": True,
        },
        {
            "name": "Aravind Eye Hospital — Madurai",
            "district": "Madurai",
            "address": "1, Anna Nagar, Madurai, Tamil Nadu 625020",
            "contact": "+91 452 435 6100",
            "speciality": "Retina-Vitreous & Uvea Services",
            "availability": "Mon-Sat 7:30 AM – 6:00 PM",
            "is_verified": True,
        },
        {
            "name": "Government Mohan Kumaramangalam Medical College Hospital",
            "district": "Salem",
            "address": "Steel Plant Road, Salem, Tamil Nadu 636030",
            "contact": "+91 427 228 1500",
            "speciality": "Comprehensive Medical Retina Clinic",
            "availability": "24/7 Emergency Care",
            "is_verified": True,
        },
        {
            "name": "Mahatma Gandhi Memorial Government Hospital — Eye Dept",
            "district": "Tiruchirappalli",
            "address": "Collector Office Road, Tiruchirappalli, Tamil Nadu 620017",
            "contact": "+91 431 241 5450",
            "speciality": "Vitreoretinal Diagnostics & Laser Care",
            "availability": "24/7 Emergency Care",
            "is_verified": True,
        },
        {
            "name": "KR Hospital & Mysore Medical College — Dept of Ophthalmology",
            "district": "Mysuru",
            "address": "Irwin Road, Mysuru, Karnataka 570001",
            "contact": "+91 821 252 0512",
            "speciality": "Government Tertiary Eye Hospital",
            "availability": "24/7 Emergency Care",
            "is_verified": True,
        },
    ]

    for hosp in hospitals_data:
        dist_locs = loc_by_district.get(hosp["district"], location_objs)
        target_loc = dist_locs[0] if dist_locs else location_objs[0]
        obj = Hospital(
            name=hosp["name"],
            location_id=target_loc.id,
            address=hosp["address"],
            contact=hosp["contact"],
            speciality=hosp["speciality"],
            availability=hosp["availability"],
            is_verified=hosp["is_verified"],
        )
        db.add(obj)
    db.commit()

    # 3. Seed Verified Users (Healthcare Worker & Doctor)
    cbe_loc = location_objs[0]  # Valparai PHC

    # Healthcare Worker
    worker = User(
        role="HEALTHCARE_WORKER",
        email="worker@ruraldrxai.demo",
        mobile="+919840212345",
        password_hash=hash_password("password123"),
        full_name="Lakshmi Narayanan, ANM",
        reg_number="HW-TN-4091",
        facility_name="Primary Health Centre — Valparai, Coimbatore",
        location_id=cbe_loc.id,
        verification_status="VERIFIED",
    )
    db.add(worker)

    # Doctor
    doctor = User(
        role="DOCTOR",
        email="doctor@ruraldrxai.demo",
        mobile="+919443156789",
        password_hash=hash_password("password123"),
        full_name="Dr. S. K. Aravind, MS (Ophthalmology)",
        reg_number="MCI-TN-2018-84729",
        facility_name="Regional Eye Centre, Coimbatore Medical College Hospital",
        location_id=cbe_loc.id,
        verification_status="VERIFIED",
    )
    db.add(doctor)
    db.commit()

    # 4. Seed 2 realistic referral cases in database for immediate demonstration
    hosp_cbe = db.query(Hospital).filter(Hospital.name.like("%Coimbatore Medical College%")).first()

    # Case 1: Referred Moderate NPDR
    case1 = ScreeningCase(
        case_id="RDX-1048",
        patient_id="PID-9082",
        age=58,
        gender="Male",
        notes="Complains of blurred vision in right eye. 11-year history of Type 2 Diabetes.",
        location_id=location_objs[1].id,  # Pollachi CHC
        worker_id=worker.id,
        status="REFERRED",
        referral_required=True,
        created_at=datetime.utcnow() - timedelta(minutes=45),
        updated_at=datetime.utcnow() - timedelta(minutes=45),
    )
    db.add(case1)
    db.commit()

    # Image metadata
    img1 = ScreeningImage(
        case_id="RDX-1048",
        storage_key="cases/RDX-1048/original.jpg",
        storage_type="local",
        filename="fundus_patient_9082.jpg",
        mime_type="image/jpeg",
        width=1024,
        height=1024,
        file_size=324000,
    )
    db.add(img1)

    # AIPrediction
    pred1 = AIPrediction(
        case_id="RDX-1048",
        is_fundus=True,
        modality_confidence=0.98,
        quality_status="GRADEABLE",
        quality_score=0.92,
        dr_stage=3,
        severity_name="Severe Non-Proliferative Diabetic Retinopathy",
        confidence=0.91,
        class_probabilities_json=json.dumps({"0": 0.01, "1": 0.03, "2": 0.05, "3": 0.91, "4": 0.0}),
        gradcam_url="",
        lesion_data_json=json.dumps([
            {"type": "Microaneurysms", "detected": True, "count": 24, "area_pct": 2.4, "confidence": 0.92},
            {"type": "Hemorrhages", "detected": True, "count": 18, "area_pct": 4.8, "confidence": 0.91},
            {"type": "Cotton Wool Spots", "detected": True, "count": 5, "area_pct": 1.8, "confidence": 0.88},
        ]),
        triage_decision="HIGH PRIORITY: Severe NPDR detected. Urgent referral recommended.",
        priority="HIGH",
    )
    db.add(pred1)

    # Referral
    ref1 = Referral(
        case_id="RDX-1048",
        hospital_id=hosp_cbe.id if hosp_cbe else 1,
        doctor_id=doctor.id,
        priority="HIGH",
        status="PENDING",
        notes="High risk of progression to PDR. Fast-track evaluation requested.",
        created_at=datetime.utcnow() - timedelta(minutes=40),
    )
    db.add(ref1)

    # Audit log
    audit1 = AuditLog(
        user_id=worker.id,
        action="REFERRAL_CREATED",
        case_id="RDX-1048",
        metadata_json=json.dumps({"hospital_id": hosp_cbe.id if hosp_cbe else 1, "priority": "HIGH"}),
    )
    db.add(audit1)

    db.commit()
    print("[*] Database successfully initialized and seeded with demo records.")
