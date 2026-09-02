# 👁️ RuralDR-XAI: Complete Deployment & Operation Guide

> **Problem Statement ID**: SIH26038  
> **Platform**: AI-Powered Tele-Ophthalmology Early Detection & Referral System for Rural Healthcare  
> **Repository**: [https://github.com/Surya-RedOps/RuralDR-XAI.git](https://github.com/Surya-RedOps/RuralDR-XAI.git)  
> **Target Branch**: `Branch---1--Sai`  

---

## 📋 Table of Contents
1. [System Requirements](#-system-requirements)
2. [Environment Configuration (`.env`)](#-environment-configuration-env)
3. [Step-by-Step Execution Instructions](#-step-by-step-execution-instructions)
4. [Services & Port Mapping](#-services--port-mapping)
5. [Role-Based Access Credentials](#-role-based-access-credentials)
6. [Complete 6-Step Clinical Screening Workflow](#-complete-6-step-clinical-screening-workflow)
7. [AI Pipeline Architecture & Safety Gates](#-ai-pipeline-architecture--safety-gates)
8. [Troubleshooting & Verification](#-troubleshooting--verification)

---

## 🛠️ System Requirements

| Tool | Version Requirement | Verification Command |
| :--- | :--- | :--- |
| **Python** | Python 3.10 – 3.14 | `py -3.14 --version` |
| **Node.js** | Node 18.x or 20.x | `node --version` |
| **npm** | 9.x or higher | `npm --version` |
| **Docker Desktop** | 4.x or higher | `docker --version` |
| **Git** | 2.x | `git --version` |

---

## ⚙️ Environment Configuration (`.env`)

Create a local `.env` file in the project root (`d:\SIH\.env`):

```env
# Server & Security
SECRET_KEY=ruraldr-xai-super-secret-key-2026-production-sih26038
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=1440

# MySQL Database Connection (Port 3307 mapped container)
DATABASE_URL=mysql+pymysql://root:rootpassword@localhost:3307/ruraldr_db

# Local Storage Directory for Retinal Images
STORAGE_TYPE=local
LOCAL_STORAGE_DIR=data/uploads

# Model Weight Checkpoint Paths
DR_CLASSIFIER_PATH=models/dr_classifier/best_model.pth
MODALITY_GATE_PATH=models/modality_gate/fundus_modality_v1.pth
```

---

## 🚀 Step-by-Step Execution Instructions

### Step 1: Start MySQL 8.0 Container
Launch the Docker MySQL database container mapping internal port `3306` to host port `3307`:

```powershell
docker-compose up -d
```

Verify container health:
```powershell
docker ps --filter "name=ruraldr_mysql"
```

### Step 2: Initialize Database Schema & Seed Clinical Data
Execute the Python database seeder to create all database tables and seed verified health centers, eye hospitals, users, and cases:

```powershell
py -3.14 -m src.db.init_db
```

### Step 3: Launch FastAPI Backend Server
Start the Uvicorn REST API server on port `8000`:

```powershell
py -3.14 -m uvicorn src.api.server:app --host 0.0.0.0 --port 8000 --reload
```

### Step 4: Launch Vite Frontend Application
In a separate terminal window, start the React Vite development server:

```powershell
npm --prefix frontend run dev
```

---

## 🌐 Services & Port Mapping

| Service | Protocol | Access URL / Connection String |
| :--- | :--- | :--- |
| **Vite Frontend Web App** | HTTP | [`http://localhost:5173`](http://localhost:5173) |
| **FastAPI REST API Server** | HTTP | [`http://localhost:8000`](http://localhost:8000) |
| **Swagger Interactive Docs** | HTTP | [`http://localhost:8000/docs`](http://localhost:8000/docs) |
| **MySQL 8.0 Container** | Database | `localhost:3307` (`root:rootpassword`) |

---

## 🔐 Role-Based Access Credentials

### 1. Healthcare Worker (ANM Portal)
- **Portal URL**: [`http://localhost:5173/login/worker`](http://localhost:5173/login/worker)
- **Email / Mobile**: `worker@ruraldrxai.demo` *(or mobile `+919840212345`)*
- **Password**: `password123`
- **Feature**: 1-Click `⚡ Auto-Fill` button available on login page.

### 2. Vitreoretinal Specialist (Doctor Portal)
- **Portal URL**: [`http://localhost:5173/login/doctor`](http://localhost:5173/login/doctor)
- **Reg. Number**: `MCI-TN-2018-84729`
- **Email / Mobile**: `doctor@ruraldrxai.demo`
- **Password**: `password123`
- **Feature**: 1-Click `⚡ Auto-Fill` button available on login page.

---

## 🔄 Complete 6-Step Clinical Screening Workflow

```
[01. Patient Info] ➔ [02. Location Selection] ➔ [03. Fundus Image Upload]
                                                           │
                                                           ▼
[06. Doctor Referral] ◄── [05. Diagnostic Result] ◄── [04. AI Safety Gates]
```

1. **Step 01: Patient Case Details**:
   - Clean, interactive form fields (Patient ID, Age, Gender, Screening Date, Clinical Notes) for direct user entry without pre-filled sample text.

2. **Step 02: Location & Health Center Selection**:
   - Cascading State ➔ District ➔ Health Center selection.
   - Displays active operational status (`🟢 Active & Available`) with equipped retinal cameras and ANM care nodes.

3. **Step 03: Fundus Image Acquisition**:
   - Real prototype drag-and-drop / file browser for standard retinal fundus photographs (`.jpg`, `.png`, `.tiff`, `.bmp`).

4. **Step 04: Multi-Stage AI Safety Evaluation**:
   - **Gate 1 (Modality Verification)**: Rejects non-retinal photographs (e.g., cars, faces, screenshots) to eliminate false positives.
   - **Gate 2 (FIQA Quality Scoring)**: Checks illumination, focus blur, and vessel visibility.
   - **Stage 3 (ResNet18 DR Classification)**: Grades Diabetic Retinopathy from Level 0 (No DR) to Level 4 (Proliferative DR).
   - **Stage 4 (Explainability & Biomarkers)**: Generates Grad-CAM visual heatmaps and highlights microaneurysms, hemorrhages, and exudates.

5. **Step 05: AI Screening Result & Official Report**:
   - Interactive `MedicalRetinaViewer` with toggleable Grad-CAM layers.
   - Direct link to official printable screening report (`/report/{case_id}`).

6. **Step 06: Specialist Referral Routing**:
   - Auto-routes positive cases (Level 1–4) to nearby verified referral eye hospitals (e.g., Aravind Eye Hospital, Regional Eye Centre).
   - Enters the doctor review queue for clinical sign-off.

---

## 🧪 AI Pipeline Metrics (IDRiD Dataset)

Our ResNet-18 model fine-tuned on clinical images from the IDRiD dataset achieved:

- **Validation Quadratic Weighted Kappa (QWK)**: **`0.7397`** (73.97%)
- **Test ROC-AUC Score**: **`0.9360`** (93.60% Area Under ROC Curve on held-out test split)
- **Primary Model Weight File**: [`models/dr_classifier/best_model.pth`](file:///d:/SIH/models/dr_classifier/best_model.pth)

---

## 🔍 Troubleshooting & Verification

### Test Backend Health Endpoint:
```powershell
py -3.14 -c "import urllib.request; print(urllib.request.urlopen('http://localhost:8000/health').read().decode())"
```

### Test File Serving & Fallback Endpoint:
```powershell
py -3.14 -c "import urllib.request; print(urllib.request.urlopen('http://localhost:8000/api/v1/files/sample_fundus.jpg').status)"
```
*(Should return HTTP 200 OK)*

### Git Branch Sync:
```powershell
git checkout Branch---1--Sai
git pull origin Branch---1--Sai
```

---
*RuralDR-XAI Tele-Ophthalmology Platform · SIH26038 · Verified & Ready for Clinical Demonstration*
