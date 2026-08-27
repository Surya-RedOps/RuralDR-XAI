# RuralDR-XAI: Complete Windows 11 Runbook & Execution Guide
## Reproducible Setup, Training, Inference, Simulation, and Testing

---

## 1. System Requirements & Hardware Specifications

### 1.1 Hardware Specifications
- **Operating System**: Windows 10 / 11 64-bit (Tested on Windows 11 Build 22631+).
- **CPU**: Intel Core i5/i7/i9 or AMD Ryzen 5/7/9 (4+ cores recommended).
- **GPU**: NVIDIA GPU with CUDA Compute Capability $\ge 6.0$ (e.g., RTX 4050 / RTX 3060 or higher with $\ge 4$ GB VRAM recommended).
- **RAM**: Minimum 8 GB (16 GB recommended).
- **Disk Space**: At least 30 GB free space for datasets, virtual environments, checkpoints, and logs.

### 1.2 Required Software Runtimes
- **Git for Windows**: $\ge 2.40.0$
- **Python Runtime**: Python 3.11.x (managed via `uv` or standard Python installer)
- **Node.js** (Optional, for web frontend development): $\ge 18.x$
- **MATLAB & Simulink** (For MathWorks SIH evaluation): R2023b / R2024a / R2024b with:
  - Image Processing Toolbox
  - Computer Vision Toolbox
  - Deep Learning Toolbox
  - Medical Imaging Toolbox
  - Statistics and Machine Learning Toolbox
  - Simulink & SimEvents

---

## 2. Environment Setup on Windows 11

### Step 2.1: Clone and Navigate to Repository
Open PowerShell (Admin or standard user):
```powershell
cd c:\Users\miste\OneDrive\Documents\Projects\RuralDR-XAI
```

### Step 2.2: Setup Python Virtual Environment using `uv`
The machine has `uv` available at `C:\Users\miste\AppData\Local\hermes\bin\uv.exe` and Python 3.11:
```powershell
# Create dedicated virtual environment using Python 3.11
& "C:\Users\miste\AppData\Local\hermes\bin\uv.exe" venv .venv --python 3.11

# Activate virtual environment
.\.venv\Scripts\Activate.ps1
```

### Step 2.3: Install PyTorch with CUDA 12.x Acceleration
```powershell
# Install PyTorch with CUDA 12.1 support for RTX 4050 GPU
& "C:\Users\miste\AppData\Local\hermes\bin\uv.exe" pip install torch torchvision --index-url https://download.pytorch.org/whl/cu121
```

### Step 2.4: Install Python Dependencies
```powershell
& "C:\Users\miste\AppData\Local\hermes\bin\uv.exe" pip install -r requirements.txt
```

*(If `requirements.txt` is being generated, the essential packages are: `numpy`, `scipy`, `scikit-image`, `scikit-learn`, `opencv-python-headless`, `timm`, `matplotlib`, `pandas`, `fastapi`, `uvicorn`, `pydantic`, `reportlab`, `pytest`, `simpy`)*

---

## 3. Dataset Setup and Placement

### Step 3.1: Download Required Datasets
Follow the explicit download guide in `data/README.md`:
- **IDRiD**: Download and unzip to `data/raw/IDRiD/`
- **EyeQ**: Download and unzip to `data/raw/EyeQ/`
- **APTOS 2019**: Download and unzip to `data/raw/APTOS2019/`
- **DRIVE**: Download and unzip to `data/raw/DRIVE/`
- **MESSIDOR-2**: Download and unzip to `data/raw/MESSIDOR2/`

### Step 3.2: Verify Dataset Integrity
Execute the dataset integrity validation script:
```powershell
python scripts/validate_datasets.py --data_dir data/raw
```

### Step 3.3: Generate Split Manifests
Generate reproducible, patient-stratified train/val/test split manifests:
```powershell
python scripts/prepare_splits.py --seed 42
```

---

## 4. Training and Calibration Workflow

### Step 4.1: Train Retinal Vessel & Anatomy Model (Baseline)
```powershell
python scripts/train_anatomy.py --dataset DRIVE --epochs 30 --batch_size 4 --lr 1e-4 --device cuda
```

### Step 4.2: Train Lesion Detection Models (IDRiD / DDR)
```powershell
python scripts/train_lesions.py --dataset IDRiD --epochs 40 --batch_size 4 --lr 2e-4 --device cuda
```

### Step 4.3: Train DR Severity Classifier (ICDR 0 to 4)
```powershell
python scripts/train_classifier.py --arch efficientnet_b4 --dataset APTOS2019 --epochs 25 --batch_size 8 --lr 3e-4 --device cuda
```

### Step 4.4: Run Post-Hoc Confidence Calibration (Temperature Scaling)
```powershell
python scripts/calibrate_model.py --checkpoint models/checkpoints/best_classifier.pth --val_manifest data/manifests/val_split.csv
```

---

## 5. Running the Complete Screening Pipeline

### Step 5.1: Command-Line Single-Image Inference
Run end-to-end screening on any input fundus image (generates visual overlays, Grad-CAM, lesion inventory, and PDF report):
```powershell
python scripts/screen_image.py --input data/sample/fundus_test.jpg --output results/report_001/ --device cuda
```

### Step 5.2: Launch Local Screening API & Web UI
Start the local offline-capable backend server:
```powershell
python -m uvicorn src.api.server:app --host 127.0.0.1 --port 8000 --reload
```
Open a browser and navigate to:
```
http://127.0.0.1:8000/
```

---

## 6. MATLAB & Simulink Telemedicine Simulation

### Step 6.1: Check MATLAB Environment
Ensure MATLAB R2023b+ is installed with Image Processing, Deep Learning, and Simulink toolboxes.

### Step 6.2: Run MATLAB Screening Pipeline
In MATLAB Command Window or terminal:
```matlab
>> cd('matlab')
>> results = run_pipeline('../data/sample/fundus_test.jpg')
```

### Step 6.3: Run District Telemedicine Simulink Model
To simulate a 100,000 patient/year rural district network and evaluate queuing bottlenecks:
```matlab
>> cd('matlab')
>> sim_results = run_telemed_sim('NumPHCs', 50, 'ArrivalRatePerPHC', 8, 'BandwidthMbps', 2.0, 'NumDoctors', 2)
```

### Step 6.4: Run Open-Source Discrete-Event Simulation (SimPy Fallback)
For systems without a MATLAB/Simulink license:
```powershell
python scripts/run_telemed_simulation.py --num_phcs 50 --arrival_rate 8 --bandwidth_mbps 2.0 --num_doctors 2 --annual_target 100000
```

---

## 7. Automated Testing & Quality Assurance

Run the comprehensive unit and integration test suite:
```powershell
pytest tests/ -v
```

Run test suite categories individually:
```powershell
# Test Quality Gate & FIQA
pytest tests/test_quality.py -v

# Test Retinal Anatomy & Vessel Segmentation
pytest tests/test_anatomy.py -v

# Test Lesion Detectors
pytest tests/test_lesions.py -v

# Test DR Classifier & Calibration
pytest tests/test_classifier.py -v

# Test Explainable AI (Grad-CAM)
pytest tests/test_xai.py -v

# Test Evidence Consistency Engine
pytest tests/test_consistency.py -v

# Test End-to-End Screening Pipeline
pytest tests/test_pipeline_integration.py -v
```

---

## 8. Troubleshooting Guide

| Issue / Error | Likely Cause | Solution |
| :--- | :--- | :--- |
| `CUDA out of memory` | Batch size too large for 6GB RTX 4050 VRAM | Reduce `--batch_size` to 2 or 4, or enable gradient accumulation `--accum_steps 2`. |
| `Ungradable image error` | Input image failed focus, illumination, or FOV quality check | Inspect quality log in report; re-acquire image adhering to recapture advice. |
| `Model checkpoint not found` | Models not yet trained or weights missing | Download certified weights into `models/checkpoints/` or run training scripts. |
| `MATLAB not found` | MATLAB not added to Windows PATH | Use the Python/PyTorch dual-stack runtime or add MATLAB bin folder to system PATH. |
| `FastAPI port 8000 in use` | Another local process is listening on port 8000 | Specify a different port: `--port 8080`. |
