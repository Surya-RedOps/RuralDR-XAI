# RuralDR-XAI: Explainable AI for Diabetic Retinopathy Screening & Rural Referral Platform
### Smart India Hackathon (SIH26038) — Sponsoring Organization: MathWorks

---

## 1. Executive Summary

**RuralDR-XAI** is an evidence-grounded, explainable retinal screening and tele-ophthalmology referral platform engineered for rural Primary Health Centers (PHCs) and Community Health Centers (CHCs) in India.

The platform transforms raw fundus camera inputs into verifiable, multi-gate clinical decisions backed by relational persistence, cloud-native medical storage, and an authoritative AI safety interlock:

$$\text{Fundus Image} \longrightarrow \text{Gate 1: Modality Guard} \longrightarrow \text{Gate 2: FIQA Quality} \longrightarrow \text{ICDR DR Classification} \longrightarrow \text{Grad-CAM Saliency} \longrightarrow \text{Biomarker Lesion Detection} \longrightarrow \text{Referral Triage & Doctor Decision}$$

---

## 2. Production Architecture

RuralDR-XAI is packaged as a complete, containerized multi-tier system with persistent state:

```
                                  +---------------------------------------+
                                  |     RuralDR-XAI Web Application       |
                                  |  (React 18 + Vite + Nginx Container)  |
                                  +-------------------+-------------------+
                                                      |
                                      REST API (JWT Auth + RBAC)
                                                      |
                                                      v
                                  +---------------------------------------+
                                  |     Backend Application Server        |
                                  |    (FastAPI + Python 3.11 + PyTorch)  |
                                  +---------+-------------------+---------+
                                            |                   |
                 +--------------------------+                   +--------------------------+
                 |                                                                         |
                 v                                                                         v
+---------------------------------------+                                 +---------------------------------------+
|          MySQL 8.0 Database           |                                 |         Image Storage Layer           |
|      18 Relational Tables (Alembic)   |                                 |    AWS S3 (Signed URLs) / Local       |
+---------------------------------------+                                 +---------------------------------------+
                 ^
                 |
                 +--- Alembic Migrations (`alembic upgrade head`)
```

### Core Technologies
- **Frontend**: React 18, Vite, Tailwind CSS, Heroicons, Syne Typography, Canvas API.
- **Backend**: FastAPI, Pydantic v2, SQLAlchemy 2.0, Alembic, ReportLab.
- **Database**: MySQL 8.0 with InnoDB engine and utf8mb4 collation (SQLite fallback for local testing).
- **Storage**: AWS S3 with signed private URL access (local filesystem storage fallback).
- **AI / Computer Vision**: PyTorch (ResNet18 classifier), OpenCV, NumPy, SciPy (Frangi filtering).

---

## 3. Relational Database Topology (18 Tables)

RuralDR-XAI enforces strict relational data integrity with Alembic migrations:

1. **`users`**: Base credentials (email, mobile, bcrypt `password_hash`, role enum).
2. **`healthcare_workers`**: Worker registration details and NHM verification status.
3. **`doctors`**: Ophthalmologist medical registration numbers and council verification status.
4. **`locations`**: Administrative hierarchy (State, District, State Code).
5. **`healthcare_centres`**: Primary Health Centres (PHCs) tied to locations.
6. **`hospitals`**: Verified referral eye care facilities with specialties and contact details.
7. **`patients`**: Rural patient demographic records.
8. **`screening_cases`**: Screening lifecycle records (`DRAFT`, `SCREENED`, `REFERRED`, `COMPLETED`).
9. **`screening_images`**: S3 keys, image metadata, resolution, and hashes.
10. **`image_validations`**: Gate 1 fundus modality verification results.
11. **`image_quality_assessments`**: Gate 2 FIQA optical quality scores.
12. **`ai_predictions`**: Deep DR severity classifications, calibrated probabilities, and Grad-CAM URLs.
13. **`lesion_findings`**: Microaneurysms, hemorrhages, and exudate region counts and areas.
14. **`referrals`**: Tele-ophthalmology referral cases routed to hospitals.
15. **`doctor_reviews`**: Doctor case examination logs.
16. **`clinical_decisions`**: Final digitally signed doctor diagnosis and treatment plans.
17. **`reports`**: Generated ReportLab PDF clinical documentation.
18. **`audit_logs`**: Immutable security and clinical audit trail.

---

## 4. AI Safety Pipeline: The Porsche Bug Root Cause & Resolution

### Root Cause Analysis
In naive image processing pipelines, red-channel dominance ($R > G > B$) is used as a fundus heuristic. However, non-retinal rectangular images—such as a **red Porsche car wallpaper**, human faces, or colorful documents—easily satisfied basic color checks, resulting in false positive DR predictions and fabricated lesions.

### Biometric Multi-Gate Interlock
RuralDR-XAI implements a deterministic, multi-feature biometric gate in [`src/quality/modality.py`](file:///e:/SIH/src/quality/modality.py):

1. **Dark Peripheral Aperture Check**: Authentic fundus images have an unilluminated dark border due to circular camera aperture optics. All four corner luminances must satisfy $I_{\text{corner}} < 45$. Full-frame rectangular images (cars, wallpapers, landscapes, screenshots) are immediately flagged and rejected.
2. **Circularity & Mask Symmetry**: The illuminated optical area must conform to a convex circular mask ($\text{circularity} \ge 0.60$).
3. **Retinal Reflectance Spectrum**: Genuine vascular beds absorb blue wavelengths ($B / (R+G+B) \le 0.22$) and exhibit high red saturation ($S_{\text{HSV}} \ge 0.25$).
4. **Curvature vs. Linear Geometry**: Non-fundus human-made scenes contain straight lines (detected via Hough lines), whereas retinal tissue contains branching curvilinear vessels.

### Fail-Safe Circuit Breaker
If `is_fundus == False`:
- Downstream DR classification is **strictly bypassed**.
- Grad-CAM heatmaps and lesion segmentation are **never executed**.
- The UI presents an immediate safety modal:
  > **Image Not Recognized**
  > *This image does not appear to be a retinal fundus photograph. DR classification and explainability analysis have been halted.*

---

## 5. Quickstart: One-Command Docker Environment

Launch the entire stack (Frontend + Backend + MySQL + Migrations + S3/Local storage) with a single command:

```bash
docker compose up --build
```

### Services Started:
| Service | URL / Port | Purpose |
| :--- | :--- | :--- |
| **Frontend** | `http://localhost:3000` | Production React SPA served via Nginx |
| **Backend API** | `http://localhost:8000` | FastAPI Server with OpenAPI documentation at `/docs` |
| **Healthcheck** | `http://localhost:8000/health` | System readiness and database connectivity probe |
| **MySQL DB** | `localhost:3306` | MySQL 8.0 relational persistence with volume `mysql_data` |

---

## 6. Environment Configuration

Copy `.env.example` to `.env` to configure database, S3 credentials, and security keys:

```bash
cp .env.example .env
```

Key environment variables:
```env
# Application Mode
ENV=production
DEBUG=false
SECRET_KEY=ruraldr-super-secret-key-change-in-production-2026

# Relational Database
DB_HOST=mysql
DB_PORT=3306
DB_NAME=ruraldr_db
DB_USER=ruraldr_user
DB_PASSWORD=ruraldr_secure_password

# AWS S3 Storage (Optional — defaults to local persistent storage if unconfigured)
AWS_ACCESS_KEY_ID=
AWS_SECRET_ACCESS_KEY=
AWS_REGION=ap-south-1
S3_BUCKET_NAME=ruraldr-fundus-storage

# AI & Verification
AUTO_VERIFY_DEMO_REGISTRATIONS=true
AI_MODEL_PATH=models/checkpoints/dr_classifier_best.pth
```

---

## 7. Automated Test Suite

Run the full automated testing suite verifying all 17 clinical and architectural requirements:

```bash
# Activate Python environment
.\.venv\Scripts\pytest.exe tests/test_production_e2e.py -v
```

### Verified Test Cases:
1. `test_valid_fundus_passes_validation`: Genuine fundus passes Gate 1 & FIQA Gate 2.
2. `test_non_fundus_car_fails_validation`: Porsche / vehicle images fail Gate 1.
3. `test_non_fundus_never_enters_dr_classification_or_gradcam`: Non-fundus images halt without fake predictions or saliency maps.
4. `test_user_registration_and_bcrypt_hashing`: Professional registration hashes passwords with bcrypt.
5. `test_role_based_access_isolation`: Healthcare workers cannot access doctor queues; doctors cannot create screening cases.
6. `test_database_contains_no_fake_clinical_cases`: Database contains zero mock patients or fake cases.
7. `test_storage_service_private_storage`: S3 / local storage enforces secure access.
8. `test_referral_and_doctor_clinical_decision`: Complete referral creation, doctor examination, and final clinical decision recording.

---

## 8. Clinical Roles & User Experience

RuralDR-XAI provides dedicated, isolated portals for two distinct clinical roles:

### 1. Healthcare Worker Portal (`/worker/login`)
- Patient registration with biometric demographic capture.
- Location-aware routing based on administrative districts and PHCs.
- Real-time multi-stage AI screening with Gate 1 & Gate 2 progress transparency.
- Automated referral generation for DR Grade 1–4; discharge report generation for DR Grade 0.
- Hospital routing: Displays verified eye hospitals or explicitly alerts *"No verified referral facilities available for this location."*

### 2. Doctor Portal (`/doctor/login`)
- Prioritized review queue sorted by clinical severity (Level 4 Critical $\to$ Level 1 Review).
- Interactive retinal viewer with adjustable opacity Grad-CAM overlays.
- Biomarker lesion region inventory (microaneurysms, hemorrhages, exudates).
- Digitally signed clinical decision submission (`CONFIRM_AI`, `MODIFY_GRADE`, `REJECT_INSUFFICIENT_QUALITY`).

---

## 9. License & Medical Disclaimer

Licensed under the Apache 2.0 License.

> **Investigational Use Disclaimer**: *RuralDR-XAI is an investigational clinical decision-support and screening triage platform for rural health initiatives. All AI-generated findings must be clinically validated by a registered ophthalmologist before any medical, laser, or surgical intervention is administered.*
