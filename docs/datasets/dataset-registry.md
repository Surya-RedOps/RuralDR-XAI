# Dataset Registry & Provenance Specification
## RuralDR-XAI: Public Datasets for Training, Validation & Clinical Evaluation

---

## 1. Ethical & Legal Data Management Policy

1. **No Fake Data Policy**: RuralDR-XAI strictly prohibits the creation, insertion, or presentation of synthetic patient records, fake fundus images, fabricated labels, or simulated performance metrics.
2. **Zero In-Repo Large Data**: No clinical image datasets will be committed directly to Git. Data must reside locally in the structured `data/` directory.
3. **Data Provenance**: Every experiment, model checkpoint, and benchmark metric must explicitly cite the dataset name, version, split manifest, and license.
4. **Patient Privacy & De-identification**: All utilized public datasets are certified de-identified by their originating institutional review boards (IRBs).

---

## 2. Master Dataset Registry

```
+-------------------------------------------------------------------------------------------------------------------------------+
|                                                    DATASET REGISTRY                                                           |
+----+-------------------+---------------------+--------------------+-------------+---------------------------------------------+
| ID | Dataset Name      | Primary Purpose     | Modality / Size    | Annotations | Official Source / License                   |
+----+-------------------+---------------------+--------------------+-------------+---------------------------------------------+
| D1 | IDRiD             | Lesion Segmentation | 516 Color Fundus   | Pixel Masks | IEEE Dataport / ISBI 2018 Challenge        |
|    |                   | & Indian DR Grading | 4288x2848 (.jpg)   | MA, EX, SE, | CC BY 4.0                                   |
|    |                   |                     | ~12 GB             | HE, OD, DR  | https://idrid.grand-challenge.org/          |
+----+-------------------+---------------------+--------------------+-------------+---------------------------------------------+
| D2 | EyeQ              | Quality Gate (FIQA) | 28,792 Fundus      | 3-Level FIQA| GitHub / IEEE TMI 2021                      |
|    |                   | Benchmarking        | Crop 512x512       | Good, Usable| Non-commercial Academic Research            |
|    |                   |                     | ~2.5 GB            | Reject      | https://github.com/HzFu/EyeQ                |
+----+-------------------+---------------------+--------------------+-------------+---------------------------------------------+
| D3 | APTOS 2019        | DR Severity Model   | 3,662 Fundus       | ICDR 0 to 4 | Kaggle / Aravind Eye Hospital, India        |
|    | Blindness Detect  | Training & Triage   | Variable high-res  | Severity    | CC0: Public Domain                          |
|    |                   |                     | ~9.5 GB            | Labels      | https://www.kaggle.com/c/aptos2019-blindness-detection |
+----+-------------------+---------------------+--------------------+-------------+---------------------------------------------+
| D4 | DDR Dataset       | DR Grading & Lesion | 13,673 Fundus      | ICDR 0 to 4 | Multi-center Clinical Dataset               |
|    |                   | Segmentation        | Variable res       | 1,151 Pixel | Academic Research Use                       |
|    |                   |                     | ~15 GB             | Lesion Masks| https://github.com/nkicsl/DDR-dataset       |
+----+-------------------+---------------------+--------------------+-------------+---------------------------------------------+
| D5 | MESSIDOR /        | External Validation | 1,200 / 1,748      | DR Grade,   | Messidor Consortium / Univ of Iowa / Eyepacs|
|    | MESSIDOR-2        | for Referable DR    | High-res TIFF/JPG  | DME Risk    | Non-commercial Research Use                 |
|    |                   |                     | ~4.5 GB            | Consensus   | https://www.adcis.net/en/third-party/messidor/ |
+----+-------------------+---------------------+--------------------+-------------+---------------------------------------------+
| D6 | DRIVE / STARE /   | Vessel Segmentation | 40 / 40 / 28       | Pixel-level | Public Retinal Vessel Benchmarks            |
|    | CHASE_DB1         | Anatomy Baseline    | 565x584 / 700x605  | Expert      | Open Academic Access                        |
|    |                   |                     | ~150 MB            | Vessel Masks| https://drive.grand-challenge.org/          |
+----+-------------------+---------------------+--------------------+-------------+---------------------------------------------+
```

---

## 3. Detailed Dataset Specifications

### 3.1 IDRiD (Indian Diabetic Retinopathy Image Dataset)
- **Clinical Origin**: Eye Clinic, Nanded, Maharashtra, India.
- **Significance**: Gold-standard Indian rural/semi-urban demographic representation. Captured with a Kowa VX-10 $\alpha$ 50-degree fundus camera.
- **Composition**:
  - Part 1: Disease Grading (413 train, 103 test) with DR Grade ($0-4$) and Diabetic Macular Edema (DME) Grade ($0-2$).
  - Part 2: Lesion Segmentation (54 train, 27 test) with exact binary ground truth masks for:
    - Microaneurysms (`*_MA.tif`)
    - Hard Exudates (`*_EX.tif`)
    - Soft Exudates (`*_SE.tif`)
    - Hemorrhages (`*_HE.tif`)
    - Optic Disc (`*_OD.tif`)
  - Part 3: Localization (Fovea and Optic Disc Center Coordinates).

### 3.2 EyeQ (Fundus Image Quality Assessment Dataset)
- **Origin**: Re-annotated subset of EyePACS dataset by three professional ophthalmologists.
- **Composition**: 28,792 color fundus images split into:
  - `Good`: Flawless image quality, clear visibility of fovea, disc, and macular vessels.
  - `Usable`: Slight blur, illumination gradient, or artifact, but major diagnostic landmarks and lesions are interpretable.
  - `Reject`: Severe defocus, dark/overexposed shadow, or massive artifact obscuring $>50\%$ of fundus.

### 3.3 APTOS 2019 Blindness Detection
- **Clinical Origin**: Aravind Eye Hospital network, Tamil Nadu, India.
- **Composition**: 3,662 train images and 1,928 test images captured in clinical outreach camps across rural India.
- **Labels**: ICDR scale (0: No DR, 1: Mild, 2: Moderate, 3: Severe, 4: Proliferative DR).

---

## 4. Dataset Directory Layout Contract

All datasets must be downloaded and organized under `data/` following this structure:

```
RuralDR-XAI/
└── data/
    ├── raw/
    │   ├── IDRiD/
    │   │   ├── 1. Original Images/
    │   │   │   ├── a. Training Set/
    │   │   │   └── b. Testing Set/
    │   │   ├── 2. Groundtruths/
    │   │   │   ├── a. Disease Grading/
    │   │   │   └── b. Segmentation/
    │   │   │       ├── 1. Microaneurysms/
    │   │   │       ├── 2. Haemorrhages/
    │   │   │       ├── 3. Hard Exudates/
    │   │   │       ├── 4. Soft Exudates/
    │   │   │       └── 5. Optic Disc/
    │   │   └── 3. Localization/
    │   ├── EyeQ/
    │   │   ├── CropData/
    │   │   └── Label_EyeQ_Train.csv
    │   ├── APTOS2019/
    │   │   ├── train_images/
    │   │   └── train.csv
    │   ├── DRIVE/
    │   │   ├── training/
    │   │   └── test/
    │   └── MESSIDOR2/
    │       ├── images/
    │       └── messidor_data.csv
    ├── processed/
    │   ├── IDRiD_512/
    │   ├── APTOS_512/
    │   └── EyeQ_512/
    ├── manifests/
    │   ├── train_split.csv
    │   ├── val_split.csv
    │   ├── test_split.csv
    │   └── external_messidor_split.csv
    └── README.md
```

---

## 5. Train / Validation / Test Splitting Policy

1. **Patient-Level Separation**: Whenever patient IDs are available (e.g., EyePACS, MESSIDOR), images from the same patient must never appear in both training and test sets.
2. **Stratified Sampling**: All splits preserve the proportional distribution of ICDR grades (0 to 4) and referable DR cases.
3. **Fixed Random Seeds**: All split generators use fixed seeds (`seed=42`) with manifests checked into `data/manifests/`.
4. **Zero Test Contamination**: Test sets and external validation datasets are strictly isolated during training, hyperparameter tuning, and post-hoc temperature calibration.
