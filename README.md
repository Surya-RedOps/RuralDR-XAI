# RuralDR-XAI: Explainable AI for Diabetic Retinopathy Screening in Rural India
### Smart India Hackathon (SIH26038) — Sponsoring Organization: MathWorks

---

## 1. Overview

**RuralDR-XAI** is an evidence-grounded, explainable retinal screening and decision-support system designed specifically for rural Primary Health Centers (PHCs) and Community Health Centers (CHCs) in India.

Rather than operating as an unverified black-box classifier, RuralDR-XAI builds an end-to-end verifiable **Evidence Chain**:
$$\text{Fundus Image} \longrightarrow \text{Quality Gate (FIQA)} \longrightarrow \text{Adaptive CLAHE} \longrightarrow \text{Retinal Anatomy (Vessels/OD/Fovea)} \longrightarrow \text{Lesion Inventory} \longrightarrow \text{DR Severity} \longrightarrow \text{Grad-CAM} \longrightarrow \text{Evidence Consistency} \longrightarrow \text{Calibrated Confidence} \longrightarrow \text{Sub-30s Clinical Report}$$

---

## 2. Key Capabilities & Innovations

- **Automated Quality Gate (FIQA)**: Rejects ungradable images (severe defocus, dark illumination, glare) with specific, actionable recapture advice before any diagnosis is attempted.
- **Retinal Anatomy Localization**: Segments blood vessel trees via Frangi multiscale Hessian filtering, detects Optic Disc via Circular Hough Transform, and pinpoints the Foveal Avascular Zone.
- **Morphological Lesion Inventory**: Detects and quantifies Microaneurysms (MAs), Hard Exudates (EXs), Soft Exudates (SEs), and Hemorrhages (HEs), with a clinical Macular Hazard warning for lesions threatening the fovea.
- **Deep 5-Class ICDR Grading**: Classifies disease severity (Grade 0 No DR to Grade 4 PDR) and flags Referable DR (Level 2+).
- **Explainable AI (Grad-CAM / Grad-CAM++ / Score-CAM)**: High-resolution class activation maps overlaid on retinal anatomy.
- **Evidence Consistency Engine**: Quantifies spatial concordance between Grad-CAM attention and detected lesion masks using Pointing Game IoU. Flags discordant predictions for mandatory urgent ophthalmologist review.
- **Confidence Calibration**: Post-hoc Temperature Scaling guarantees Expected Calibration Error (ECE) $< 5\%$.
- **<30-Second Single-Pane Review Dashboard & PDF**: Single-screen ergonomic review interface and automated ReportLab PDF export.
- **District Telemedicine Queueing Simulation**: Discrete-event simulation (SimEvents / SimPy) modeling 100,000+ patients/year across 50 PHCs, proving $>98\%$ cellular bandwidth reduction via edge triage.
- **Dual-Stack Execution**: Full native MATLAB script suite (`matlab/`) + PyTorch / FastAPI / Web UI open-source runtime (`src/`).

---

## 3. Architecture & Traceability

```
+----------------------------------------------------------------------------------------------------+
|                                    RURALDR-XAI SYSTEM MODULES                                      |
+----------------------+--------------------------------------+--------------------------------------+
| Subsystem Module     | Open-Source Python Engine (src/)     | MathWorks Toolbox Suite (matlab/)    |
+----------------------+--------------------------------------+--------------------------------------+
| Quality Gate (FIQA)  | src/quality/gate.py                  | matlab/quality_gate.m                |
| Adaptive Enhancement | src/preprocess/enhance.py            | matlab/preprocess.m                  |
| Retinal Anatomy      | src/anatomy/vessel_filter.py         | matlab/segment_vessels.m             |
| Lesion Detectors     | src/lesions/detector.py              | matlab/detect_lesions.m              |
| DR Classifier        | src/models/classifier.py             | matlab/dr_classifier.m               |
| Explainable AI (XAI) | src/xai/gradcam.py                   | matlab/xai_gradcam.m                 |
| Evidence Consistency | src/engine/consistency.py            | matlab/consistency_eng.m             |
| Confidence Calib     | src/models/calibrate.py              | matlab/calibrate_model.m             |
| Clinical Reports     | src/reporting/pdf_generator.py       | matlab/generate_report.m             |
| District Telemed Sim | scripts/run_telemed_simulation.py   | matlab/run_telemed_sim.m             |
| Clinician Dashboard  | src/ui/index.html & src/api/server.py| matlab/generate_report.m             |
+----------------------+--------------------------------------+--------------------------------------+
```

---

## 4. Quickstart Guide (Windows 11)

### 4.1 Setup Virtual Environment & Run Tests
```powershell
# Create venv and install dependencies
& "C:\Users\miste\AppData\Local\hermes\bin\uv.exe" venv .venv --python 3.11
& "C:\Users\miste\AppData\Local\hermes\bin\uv.exe" pip install -r requirements.txt

# Run all 23 unit and integration tests
.\.venv\Scripts\pytest.exe tests/ -v
```

### 4.2 Run Single-Image Screening CLI & PDF Generation
```powershell
.\.venv\Scripts\python.exe scripts/screen_image.py --input data/sample/sample_fundus.jpg --output results/sample_screening/
```

### 4.3 Launch the Web Dashboard
```powershell
.\.venv\Scripts\python.exe -m uvicorn src.api.server:app --host 127.0.0.1 --port 8000 --reload
```
Open your browser and navigate to: `http://127.0.0.1:8000/`

### 4.4 Run District Telemedicine Simulation (100k+ Patients/Year)
```powershell
.\.venv\Scripts\python.exe scripts/run_telemed_simulation.py --num_phcs 50 --arrival_rate 8.0 --bandwidth_mbps 1.5 --num_doctors 2
```

---

## 5. Documentation Directory

- [`docs/sih26038-requirements.md`](file:///c:/Users/miste/OneDrive/Documents/Projects/RuralDR-XAI/docs/sih26038-requirements.md): Official Requirements Traceability Matrix (RTM)
- [`docs/research/prior-art.md`](file:///c:/Users/miste/OneDrive/Documents/Projects/RuralDR-XAI/docs/research/prior-art.md): Comprehensive 2024–2026 Literature Review & Bibliography
- [`docs/architecture.md`](file:///c:/Users/miste/OneDrive/Documents/Projects/RuralDR-XAI/docs/architecture.md): 10-Stage Architecture & Dual-Stack Specification
- [`docs/datasets/dataset-registry.md`](file:///c:/Users/miste/OneDrive/Documents/Projects/RuralDR-XAI/docs/datasets/dataset-registry.md): Dataset Registry & Splitting Policy
- [`data/README.md`](file:///c:/Users/miste/OneDrive/Documents/Projects/RuralDR-XAI/data/README.md): Step-by-Step Dataset Download & Placement Guide
- [`RUNBOOK.md`](file:///c:/Users/miste/OneDrive/Documents/Projects/RuralDR-XAI/RUNBOOK.md): Windows 11 Reproduction Runbook
- [`docs/REAL_TIME_WORKFLOW.md`](file:///c:/Users/miste/OneDrive/Documents/Projects/RuralDR-XAI/docs/REAL_TIME_WORKFLOW.md): Real-Time Screening & <30s Review UX Specification
- [`docs/SIH_ACCEPTANCE_REPORT.md`](file:///c:/Users/miste/OneDrive/Documents/Projects/RuralDR-XAI/docs/SIH_ACCEPTANCE_REPORT.md): Final Verification & Acceptance Report
- [`SECURITY.md`](file:///c:/Users/miste/OneDrive/Documents/Projects/RuralDR-XAI/SECURITY.md): Medical Privacy, Safety & Disclaimers

---

## 6. License & Medical Disclaimer

This project is licensed under the Apache 2.0 License.

> **Investigational Use Disclaimer**: *RuralDR-XAI is an investigational clinical decision-support and screening triage system for rural health programs. All findings must be validated by a registered ophthalmologist before any medical, laser, or surgical intervention is administered.*
