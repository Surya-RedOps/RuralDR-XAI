# RuralDR-XAI: Data Directory & Download Guide

This directory holds the raw and processed retinal fundus datasets used for training, calibrating, and evaluating the RuralDR-XAI system.

---

## 1. Compliance Notice

- **Never commit raw medical images or ZIP archives into Git.**
- Only commit split manifest CSVs (containing anonymous IDs, relative file paths, and labels).
- All datasets must be obtained from their official sources as detailed below.

---

## 2. Directory Structure

Place downloaded datasets into the following directories:

```
data/
├── raw/
│   ├── IDRiD/              <- Indian Diabetic Retinopathy Image Dataset
│   │   ├── 1. Original Images/
│   │   ├── 2. Groundtruths/
│   │   └── 3. Localization/
│   ├── EyeQ/               <- Fundus Image Quality Assessment Dataset
│   ├── APTOS2019/          <- Kaggle APTOS Blindness Detection Dataset
│   ├── DRIVE/              <- Digital Retinal Images for Vessel Extraction
│   ├── DDR/                <- DDR Lesion Segmentation & Grading
│   └── MESSIDOR2/          <- MESSIDOR-2 External Benchmark Dataset
├── processed/              <- Standardized 512x512 preprocessed images
├── annotations/            <- Standardized JSON/COCO format lesion masks
├── manifests/              <- Deterministic train/val/test split manifests
└── README.md
```

---

## 3. Dataset Download Instructions

### 3.1 IDRiD Dataset (Priority for Lesion-Level Evidence & Indian Demographics)
1. **Source**: IEEE Dataport / Grand Challenge
2. **URL**: https://idrid.grand-challenge.org/ or https://ieee-dataport.org/open-access/indian-diabetic-retinopathy-image-dataset-idrid
3. **Procedure**:
   - Register a free academic account on IEEE Dataport.
   - Download `A. Segmentation.zip`, `B. Disease Grading.zip`, and `C. Localization.zip`.
   - Extract into `data/raw/IDRiD/`.
4. **Expected Size**: ~12 GB (516 images with TIFF masks).

### 3.2 EyeQ Dataset (Priority for Quality Gate / FIQA)
1. **Source**: GitHub / IEEE TMI 2021
2. **URL**: https://github.com/HzFu/EyeQ
3. **Procedure**:
   - Follow the official repository link to download the cropped 512x512 image dataset and label CSVs (`Label_EyeQ_Train.csv`, `Label_EyeQ_Test.csv`).
   - Extract into `data/raw/EyeQ/`.
4. **Expected Size**: ~2.5 GB (28,792 images).

### 3.3 APTOS 2019 Blindness Detection (Priority for DR Severity Grading)
1. **Source**: Kaggle / Aravind Eye Hospital
2. **URL**: https://www.kaggle.com/c/aptos2019-blindness-detection/data
3. **Procedure**:
   - Run the Kaggle CLI: `kaggle competitions download -c aptos2019-blindness-detection`
   - Unzip `aptos2019-blindness-detection.zip` into `data/raw/APTOS2019/`.
4. **Expected Size**: ~9.5 GB (3,662 train images + CSV).

### 3.4 DRIVE Retinal Vessel Dataset (Priority for Vessel Anatomy Baseline)
1. **Source**: Grand Challenge
2. **URL**: https://drive.grand-challenge.org/
3. **Procedure**:
   - Download the official `DRIVE.zip` package.
   - Extract into `data/raw/DRIVE/`.
4. **Expected Size**: ~150 MB (40 images + expert manual vessel segmentations).

### 3.5 MESSIDOR-2 (Priority for External Clinical Validation)
1. **Source**: ADCIS / Messidor Consortium / Univ. of Iowa
2. **URL**: https://www.adcis.net/en/third-party/messidor2/
3. **Procedure**:
   - Download images and adjudicate consensus grade CSV.
   - Extract into `data/raw/MESSIDOR2/`.
4. **Expected Size**: ~4.5 GB (1,748 images).

---

## 4. Dataset Validation Script

After downloading datasets, verify the directory structure and checksums using the automated validation command:

```powershell
python scripts/validate_datasets.py --data_dir data/raw
```
