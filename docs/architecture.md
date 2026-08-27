# RuralDR-XAI: System Architecture & Technical Specification
## Evidence-Consistent Adaptive Diabetic Retinopathy Screening for Rural India

---

## 1. System Overview & Architectural Principles

**RuralDR-XAI** is engineered around the core principle that a clinical decision-support AI must never function as an unverified black box. Instead, it must construct an end-to-end, measurable **Evidence Chain** that evaluates image quality, isolates anatomical landmarks, detects specific clinical lesions, generates class activation explanations, calculates evidence consistency, calibrates predictive uncertainty, and packages findings into a sub-30-second review dashboard.

```
+-------------------------------------------------------------------------------------------------+
|                                 RURALDR-XAI PIPELINE ARCHITECTURE                               |
+-------------------------------------------------------------------------------------------------+

                      [ Raw Retinal Fundus Image ]
                                   │
                                   ▼
                   ┌──────────────────────────────┐
                   │  STAGE 1: QUALITY GATE (FIQA) │
                   │  - Sharpness / Focus         │
                   │  - Illumination / Exposure   │
                   │  - Field of View (FOV)       │
                   │  - Glare / Artifact Index    │
                   └──────────────┬───────────────┘
                                  │
                  ┌───────────────┴───────────────┐
                  ▼                               ▼
          [ UNGRADABLE ]                   [ GRADEABLE ]
                  │                               │
                  ▼                               ▼
       ┌─────────────────────┐         ┌─────────────────────┐
       │  Recapture Feedback │         │ STAGE 2: ADAPTIVE   │
       │  - Flash intensity  │         │ ENHANCEMENT         │
       │  - Focus adjustment │         │ - CLAHE / Green ch  │
       │  - Patient fixation │         │ - Illum correction  │
       └─────────────────────┘         │ - Denoising (BM3D)  │
                                       └──────────┬──────────┘
                                                  │
                                                  ▼
                                       ┌─────────────────────┐
                                       │ STAGE 3: RETINAL    │
                                       │ ANATOMY LOCALIZATION│
                                       │ - Vessel Tree (U-Net│
                                       │   / Frangi Filter)  │
                                       │ - Optic Disc (CHT)  │
                                       │ - Fovea / Macula    │
                                       └──────────┬──────────┘
                                                  │
                                                  ▼
                                       ┌─────────────────────┐
                                       │ STAGE 4: LESION-    │
                                       │ LEVEL EVIDENCE      │
                                       │ - Microaneurysms(MA)│
                                       │ - Hard Exudates(EX) │
                                       │ - Soft Exudates(SE) │
                                       │ - Hemorrhages (HE)  │
                                       │ - Neovascularization│
                                       └──────────┬──────────┘
                                                  │
                                                  ▼
                                       ┌─────────────────────┐
                                       │ STAGE 5: DR SEVERITY│
                                       │ MODEL (ICDR 0 - 4)  │
                                       │ EfficientNet/ConvNeXt│
                                       │ + Referable DR Flag │
                                       └──────────┬──────────┘
                                                  │
                                                  ▼
                                       ┌─────────────────────┐
                                       │ STAGE 6: XAI ENGINE │
                                       │ - Grad-CAM / CAM++  │
                                       │ - Score-CAM Saliency│
                                       │ - Anatomical Masking│
                                       └──────────┬──────────┘
                                                  │
                                                  ▼
                                       ┌─────────────────────┐
                                       │ STAGE 7: EVIDENCE   │
                                       │ CONSISTENCY ENGINE  │
                                       │ - Prediction vs.    │
                                       │   Lesion Concordance│
                                       │ - Pointing Game IoU │
                                       │ - Discordance Metric│
                                       └──────────┬──────────┘
                                                  │
                                                  ▼
                                       ┌─────────────────────┐
                                       │ STAGE 8: CONFIDENCE │
                                       │ CALIBRATION         │
                                       │ - Temperature Scale │
                                       │ - Reliability Check │
                                       └──────────┬──────────┘
                                                  │
                                                  ▼
                                       ┌─────────────────────┐
                                       │ STAGE 9: DECISION & │
                                       │ TRIAGE ENGINE       │
                                       │ - Non-referable     │
                                       │ - Referable (Lvl 2+)│
                                       │ - High Review Pri   │
                                       └──────────┬──────────┘
                                                  │
                                                  ▼
                                       ┌─────────────────────┐
                                       │ STAGE 10: <30-SECOND│
                                       │ CLINICAL REPORT     │
                                       │ - Single-pane UI    │
                                       │ - Overlay toggle    │
                                       │ - PDF / Export      │
                                       └─────────────────────┘
```

---

## 2. Subsystem Module Breakdown

### 2.1 Module 1: Quality Gate & FIQA (`src/quality/` & `matlab/quality_gate.m`)
- **Inputs**: Raw RGB Fundus image (JPEG, PNG, TIFF).
- **Processing**:
  - Focus estimation via Tenengrad gradient and Laplacian variance on the green channel.
  - Illumination uniformity and dynamic range via entropy and HSV saturation histograms.
  - Retinal mask circularity and FOV coverage (>80% of sensor area).
  - Media opacity / contrast index.
- **Outputs**:
  - `status`: `GRADEABLE`, `BORDERLINE`, or `UNGRADABLE`.
  - `quality_score`: Scalar $[0.0, 1.0]$.
  - `recapture_advice`: List of specific remediation steps if ungradable.

### 2.2 Module 2: Adaptive Enhancement (`src/preprocess/` & `matlab/preprocess.m`)
- **Inputs**: Gradeable or Borderline RGB image.
- **Processing**:
  - Circular retinal ROI extraction and black background border cropping.
  - Luminance homogenization via large-kernel Gaussian background subtraction.
  - Contrast-Limited Adaptive Histogram Equalization (CLAHE) applied selectively to the green channel.
  - Bilateral / Wavelet edge-preserving denoising.
- **Outputs**:
  - Enhanced RGB image array.
  - Transformation audit log recording exact applied hyperparameters.

### 2.3 Module 3: Retinal Anatomy Engine (`src/anatomy/` & `matlab/segment_vessels.m`)
- **Inputs**: Enhanced fundus image.
- **Processing**:
  - **Vessel Segmentation**: Multi-scale Hessian vesselness (Frangi filter) + U-Net segmentation.
  - **Optic Disc (OD) Localization**: Morphological Top-Hat, intensity clustering, and Circular Hough Transform (CHT) to determine center $(x_{\text{od}}, y_{\text{od}})$ and radius $r_{\text{od}}$.
  - **Fovea Localization**: Spatial search in macular zone $2.5 \times r_{\text{od}}$ temporal to OD center, detecting local intensity minimum and avascular zone.
- **Outputs**:
  - Binary vessel mask $M_{\text{vessel}}$.
  - Optic disc bounding box and centroid.
  - Fovea coordinate $(x_{\text{fovea}}, y_{\text{fovea}})$.

### 2.4 Module 4: Lesion Evidence Extraction (`src/lesions/` & `matlab/detect_lesions.m`)
- **Inputs**: Enhanced fundus image + anatomical masks.
- **Processing**:
  - **Microaneurysm (MA) Detector**: Candidate extraction via morphological bottom-hat filtering and green-channel profile matching; vessel mask subtraction to prevent false positives.
  - **Hard Exudate (EX) Segmentor**: High-intensity yellowish lesion clustering in $L^*a^*b^*$ color space, spatial connectivity analysis.
  - **Soft Exudate / Cotton Wool Spot Segmentor**: Indistinct border white/grey lesion detection.
  - **Hemorrhage (HE) Segmentor**: Low-intensity non-vessel intraretinal blot and flame hemorrhage segmentation.
  - **Neovascularization (NV) Indicator**: Tortuous, abnormal vessel density analysis within peripapillary and retinal sectors.
- **Outputs**:
  - Lesion coordinate lists, count per quadrant, total lesion surface area percentage, and overlay masks.

### 2.5 Module 5: Deep DR Severity Classifier (`src/models/` & `matlab/dr_classifier.m`)
- **Inputs**: Preprocessed fundus image ($512 \times 512 \times 3$).
- **Architecture**: EfficientNet-B4 / ConvNeXt-Small backbone pretrained on ImageNet and fine-tuned on multi-centric fundus cohorts (APTOS 2019, IDRiD, DDR).
- **Outputs**:
  - Uncalibrated logits for 5 ICDR classes: $[z_0, z_1, z_2, z_3, z_4]$.
  - Predicted DR Grade $\in \{0, 1, 2, 3, 4\}$.
  - Binary Referable DR classification ($\text{Grade} \ge 2$).

### 2.6 Module 6: Explainable AI Engine (`src/xai/` & `matlab/xai_gradcam.m`)
- **Inputs**: Classifier logits, intermediate feature maps from the final convolutional stage.
- **Methods**:
  - Grad-CAM: Class-specific gradient-weighted activation mapping.
  - Grad-CAM++: Highlighting multiple co-occurring lesion clusters.
  - Saliency normalization and colormap blending (Turbo / Jet / Thermal).
- **Outputs**:
  - Spatial attention heatmap $H_{\text{cam}} \in [0, 1]^{H \times W}$.
  - High-activation binary mask $M_{\text{cam}} = (H_{\text{cam}} \ge \tau_{\text{cam}})$.

### 2.7 Module 7: Evidence Consistency Engine (`src/engine/consistency.py` & `matlab/consistency_eng.m`)
- **Inputs**: Predicted DR grade, lesion counts/masks ($M_{\text{MA}}, M_{\text{EX}}, M_{\text{HE}}$), Grad-CAM mask ($M_{\text{cam}}$), anatomical masks.
- **Methodology**:
  - *Clinical Rule Verification*: Checks whether predicted DR Grade aligns with detected morphological lesions (e.g., Grade 1 must have MAs but zero/negligible HEs/EXs; Grade 2+ must exhibit HEs or EXs; Grade 0 must have zero significant lesions).
  - *Pointing Game & Attribution IoU*: Computes spatial intersection between Grad-CAM high-attention zones and actual detected lesion locations:
    $$\text{Concordance Index} = \frac{\text{Area}(M_{\text{cam}} \cap M_{\text{lesions}})}{\text{Area}(M_{\text{lesions}}) + \epsilon}$$
  - *Discordance Flags*: Flags false-positive attention (e.g., model focusing on the optic disc or camera edge artifacts while predicting DR Grade 3).
- **Outputs**:
  - Evidence status: `SUPPORTED`, `PARTIALLY_SUPPORTED`, or `REVIEW_REQUIRED`.
  - Discordance explanation and review priority score.

### 2.8 Module 8: Confidence Calibration (`src/models/calibrate.py` & `matlab/calibrate_model.m`)
- **Inputs**: Model logits $\mathbf{z}$, temperature parameter $T$ (learned on validation set).
- **Processing**:
  $$\mathbf{p}_{\text{calibrated}} = \text{Softmax}\left(\frac{\mathbf{z}}{T}\right)$$
- **Outputs**: Calibrated posterior probabilities and Expected Calibration Error (ECE) certificate.

### 2.9 Module 9: Decision & Triage Engine (`src/models/triage.py`)
- **Inputs**: Calibrated confidence, evidence consistency status, patient age/history if supplied.
- **Triage Categories**:
  - `NON_REFERABLE`: Grade 0 or Grade 1 with high consistency $\rightarrow$ Routine annual re-screening.
  - `REFERABLE_ROUTINE`: Grade 2 Moderate NPDR $\rightarrow$ Clinic referral within 3 months.
  - `REFERABLE_URGENT`: Grade 3 Severe NPDR or Grade 4 PDR or Macular Exudate involvement $\rightarrow$ Specialist referral within 1–2 weeks.
  - `EXPEDITE_HUMAN_REVIEW`: Discordant evidence or Borderline quality $\rightarrow$ Immediate ophthalmologist queue review.

### 2.10 Module 10: Clinical Summary Report & <30s Reviewer UI (`src/reporting/`, `src/ui/`, `matlab/generate_report.m`)
- **Outputs**:
  - High-density single-pane interactive web dashboard and PDF report.
  - Fast toggle overlays: Original | Enhanced | Lesions | Grad-CAM | Anatomical sectors.
  - Structured summary: DR grade, calibrated confidence, lesion inventory (count/area), foveal threat assessment, recapture status, and electronic signature box.

---

## 3. Dual-Stack Architecture: MATLAB/Simulink + Open-Source Engine

To meet MathWorks SIH26038 requirements while providing zero-cost open-source deployment, RuralDR-XAI implements a unified dual-stack architecture:

```
+----------------------------------------------------------------------------------------------------+
|                                    DUAL-STACK ARCHITECTURE                                         |
+----------------------------------------------------------------------------------------------------+
| Layer                | MATLAB / MathWorks Stack             | Open-Source Python Stack             |
+----------------------+--------------------------------------+--------------------------------------+
| Quality Assessment   | Image Processing Toolbox             | OpenCV, NumPy, SciPy                 |
| Enhancement          | Image Processing Toolbox (adapthisteq)| OpenCV CLAHE, Scikit-Image          |
| Anatomy (Vessels/OD) | Computer Vision / Med Imaging TB     | PyTorch U-Net, Morphological Filter  |
| Lesion Segmentation  | Medical Imaging / Deep Learning TB   | PyTorch Patch CNN / U-Net, SciPy     |
| DR Classifier        | Deep Learning Toolbox (dlnetwork)    | PyTorch (timm / torchvision)         |
| Explainability (XAI) | Deep Learning Toolbox (gradCAM)      | PyTorch Grad-CAM, Captum             |
| Confidence Calib     | Stats and Machine Learning Toolbox   | Scikit-Learn, PyTorch Temperature    |
| District Simulation  | Simulink & SimEvents (.slx)          | SimPy discrete-event fallback sim    |
| User Interface       | MATLAB App Designer (.mlapp)         | FastAPI + Modern Responsive Web UI   |
+----------------------+--------------------------------------+--------------------------------------+
```

---

## 4. Simulink Telemedicine Simulation Architecture

The district-scale telemedicine simulation models an entire rural health network serving 100,000+ diabetic citizens across a multi-tier hierarchy:

```
+-------------------------------------------------------------------------------+
|                       DISTRICT TELEMEDICINE QUEUEING MODEL                    |
+-------------------------------------------------------------------------------+

  [ 40-80 Rural PHCs ]                     [ Telemedicine Network ]
  ┌──────────────────┐
  │ Patient Arrival  │ ──► [ Portable Camera ] ──► [ Local Edge Quality Gate ]
  └──────────────────┘                                        │
                                              ┌───────────────┴───────────────┐
                                              ▼                               ▼
                                      [ UNGRADABLE ]                   [ GRADEABLE ]
                                       Immediate Recapture                    │
                                                                              ▼
                                                                  [ Edge AI Screening ]
                                                                              │
                                              ┌───────────────────────────────┴───────────────┐
                                              ▼                                               ▼
                                      [ Non-Referable ]                               [ Referable / Review ]
                                      Local Discharge                                         │
                                      (80% Volume)                                            ▼
                                                                              [ 3G/4G Bandwidth Queue ]
                                                                              (Low payload sync)
                                                                                      │
                                                                                      ▼
                                                                         [ District Tele-Ophth Queue ]
                                                                                      │
                                                                                      ▼
                                                                         [ Human Specialist Review ]
                                                                         (<30s verification)
                                                                                      │
                                                                                      ▼
                                                                         [ Hospital Referral / Rx ]
```

### Parametric Variables in Simulink Model:
- $N_{\text{PHC}}$: Number of active rural Primary Health Centers ($10 - 100$).
- $\lambda_{\text{arr}}$: Patient arrival rate per PHC ($\text{patients/day}$).
- $p_{\text{reject}}$: Camera quality gate rejection rate ($5\% - 30\%$).
- $t_{\text{capture}}$: Image acquisition duration ($2 - 5\text{ min}$).
- $t_{\text{edge}}$: Local Edge AI inference latency ($1 - 3\text{ sec/image}$).
- $B_{\text{net}}$: Cellular network bandwidth ($50\text{ kbps} - 10\text{ Mbps}$).
- $N_{\text{doc}}$: Number of district ophthalmologists on tele-review roster ($1 - 5$).
- $t_{\text{review}}$: Clinician review duration per referable case ($30\text{ sec} - 120\text{ sec}$).
- $\text{Cap}_{\text{annual}}$: Annual district screening capacity ($100,000+$).
