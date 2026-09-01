# Retina AI: Dataset Registry & Operational Configuration

This document outlines the clinical and research datasets connected to the **Retina AI** system, their storage locations, dynamic environment configuration, and task mappings for future AI training and evaluation phases.

---

## 1. Public Research Datasets Summary

| Dataset | Primary Purpose | Classes / Scope | Verified Location |
| :--- | :--- | :--- | :--- |
| **APTOS 2019 Blindness Detection** | DR Severity Classification | 5 ICDR Grades (0 = No DR, 1 = Mild, 2 = Moderate, 3 = Severe, 4 = Proliferative DR) | `../Data_set/aptos2019-blindness-detection` (3,662 train images, 1,928 test images) |
| **IDRiD Disease Grading** | Multi-class DR & Macular Edema Validation | Grade 0–4 Severity + Macular Edema Risk | `../IDRiD/B. Disease Grading/B. Disease Grading/` (413 train, 103 test images) |
| **IDRiD Lesion Segmentation** | Morphological Lesion Localization & XAI Groundtruth | Microaneurysms, Haemorrhages, Hard Exudates, Soft Exudates, Optic Disc | `../IDRiD/A. Segmentation/A. Segmentation/` (80 TIFF annotated masks per lesion) |
| **IDRiD Landmark Localization** | Anatomical Reference (Optic Disc & Fovea) | Optic Disc Center $(x, y)$ and Fovea Center $(x, y)$ markups | `../IDRiD/C. Localization/C. Localization/` (515 annotated fundus images) |

---

## 2. Dynamic Environment Configuration

The application resolves dataset directories centrally via `src/core/config.py` using environment variables with local workspace fallbacks:

```python
# Set custom dataset paths if datasets are located on an external drive or cluster:
export APTOS_DATASET_DIR="/path/to/aptos2019-blindness-detection"
export IDRID_DATASET_DIR="/path/to/IDRiD"
```

### Windows PowerShell Example:
```powershell
$env:APTOS_DATASET_DIR = "E:\SIH\Data_set\aptos2019-blindness-detection"
$env:IDRID_DATASET_DIR = "E:\SIH\IDRiD"
```

---

## 3. Dataset Task Mapping

### 3.1 APTOS 2019 (Classification Engine)
- **Files**: `train.csv`, `test.csv`, `train_images/`, `test_images/`.
- **Target Column**: `diagnosis` $\in \{0, 1, 2, 3, 4\}$.
- **ID Column**: `id_code` (mapped to `<id_code>.png`).
- **Class Breakdown**:
  - `0 (No DR)`: 1,805 images (49.29%)
  - `1 (Mild NPDR)`: 370 images (10.10%)
  - `2 (Moderate NPDR)`: 999 images (27.28%)
  - `3 (Severe NPDR)`: 193 images (5.27%)
  - `4 (Proliferative DR)`: 295 images (8.06%)

### 3.2 IDRiD Disease Grading (Validation Engine)
- **Files**: `a. IDRiD_Disease Grading_Training Labels.csv`, `b. IDRiD_Disease Grading_Testing Labels.csv`.
- **Columns**: `Image name`, `Retinopathy grade`, `Risk of macular edema `.

### 3.3 IDRiD Lesion Segmentation (Explainability & Groundtruth Engine)
- **Subdirectories**:
  - `1. Microaneurysms`: 54 masks
  - `2. Haemorrhages`: 53 masks
  - `3. Hard Exudates`: 54 masks
  - `4. Soft Exudates`: 26 masks
  - `5. Optic Disc`: 54 masks

### 3.4 IDRiD Landmark Localization (Anatomical Grid Engine)
- **Optic Disc Center**: `a. IDRiD_OD_Center_Training Set_Markups.csv`
- **Fovea Center**: `IDRiD_Fovea_Center_Training Set_Markups.csv`

---

## 4. Operational Commands

### 4.1 Inspect and Audit Datasets
```powershell
.venv\Scripts\python.exe scripts/summarize_datasets.py
```

### 4.2 Validate Dataset Provenance & Presence
```powershell
.venv\Scripts\python.exe scripts/validate_datasets.py
```

### 4.3 Run Single-Image Screening CLI
```powershell
.venv\Scripts\python.exe scripts/screen_image.py --input data/sample/sample_fundus.jpg --output results/sample_screening/
```

### 4.4 Run Full Phase 1 Verification Suite
```powershell
.venv\Scripts\python.exe scripts/verify_phase1.py
```

---

## 5. Medical Safety & Compliance

> **Investigational Screening Prototype**: *Predictions produced by models evaluated on these datasets constitute AI-assisted screening findings and do not replace definitive clinical examinations. All diagnoses must be confirmed by a licensed ophthalmologist.*
