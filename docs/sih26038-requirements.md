# SIH26038 — Explainable AI for Diabetic Retinopathy Screening in Rural India
## Official Requirements Specification & Traceability Matrix

---

## 1. Problem Overview & Background

- **Problem ID**: SIH26038
- **Title**: Explainable AI for Diabetic Retinopathy Screening in Rural India
- **Organization / Sponsoring Body**: MathWorks
- **Theme**: Healthcare / Clean & Green Technology / Software
- **Clinical Context**:
  - India is home to over 77 million adults living with diabetes, representing the second largest diabetic population globally.
  - Diabetic Retinopathy (DR) affects approximately 18–20% of this population and remains a leading cause of preventable blindness.
  - India suffers from a severe geographic disparity in healthcare: rural India has approximately 1 ophthalmologist per 100,000 to 250,000 individuals, making universal manual fundus screening physically impossible.
  - Existing black-box deep learning classifiers fail in real-world rural deployment because:
    1. They fail when presented with poor-quality, variable-illumination, or blurry images acquired from portable/handheld fundus cameras in community health centers (CHCs) and primary health centers (PHCs).
    2. They output uncalibrated probabilities that hide clinical uncertainty.
    3. They do not correlate heatmaps with established ophthalmological lesion criteria (microaneurysms, hemorrhages, hard/soft exudates, neovascularization).
    4. They do not enable rapid (<30 second) clinician verification.
    5. They lack district-level operational modeling for throughput, network bandwidth, and referral queue management.

---

## 2. SIH26038 Requirements Breakdown

| Req ID | Domain | Requirement Statement | SIH Target / Criterion |
| :--- | :--- | :--- | :--- |
| **REQ-01** | Quality Gate | Automated Fundus Image Quality Assessment (FIQA) evaluating focus, sharpness, illumination, exposure, field of view (FOV), and artifacts. | Rejection of ungradable images + actionable recapture guidance. |
| **REQ-02** | Enhancement | Adaptive image preprocessing (contrast enhancement, CLAHE, illumination correction, denoising) preserving morphological features. | Contrast & visibility improvement without hallucinating retinal lesions. |
| **REQ-03** | Retinal Anatomy | Detection and localization of key retinal anatomical structures: Optic Disc (OD), Fovea / Macula center, and Retinal Vessel Tree. | Accurate OD center/radius, foveal coordinate, and vessel segmentation mask. |
| **REQ-04** | Lesion Evidence | Pixel/region-level detection of key DR hallmarks: Microaneurysms (MAs), Hard Exudates (EXs), Soft Exudates / Cotton Wool Spots (SEs), Hemorrhages (HEs), and Neovascularization (NV). | Extraction of lesion coordinates, counts, area percentages, and anatomical sector localization. |
| **REQ-05** | Severity Grading | 5-class International Clinical Diabetic Retinopathy (ICDR) scale classification: Grade 0 (No DR), Grade 1 (Mild NPDR), Grade 2 (Moderate NPDR), Grade 3 (Severe NPDR), Grade 4 (PDR). | Multi-class classification with Quadratic Weighted Kappa (QWK) and multi-class AUC evaluation. |
| **REQ-06** | Referable DR | Binary triage of Referable Diabetic Retinopathy (RDR, defined clinically as ICDR Grade 2+ Moderate, Severe, or PDR, or presence of DME). | **Sensitivity > 90%**, **Specificity > 85%** on independent test datasets. |
| **REQ-07** | Explainable AI | Visual and feature-level explainability via Class Activation Mapping (Grad-CAM, Grad-CAM++, Score-CAM) and lesion-attention overlay. | High-fidelity heatmaps highlighting pathological zones. |
| **REQ-08** | Evidence Consistency | Multi-modal consistency engine comparing DR severity prediction against anatomical landmarks, detected lesion counts/masks, and Grad-CAM activations. | Measurable Consistency Index: Supported, Partially Supported, or Review Required. |
| **REQ-09** | Calibration | Post-hoc confidence calibration (Temperature Scaling, Isotonic Regression) to align predicted probabilities with actual empirical accuracy. | Low Expected Calibration Error (ECE < 5%), verified on validation split. |
| **REQ-10** | Clinical Reporting | Automated generation of structured, clinical-style screening summary reports with annotated overlays, lesion metrics, and referral flags. | Enable complete ophthalmologist review and sign-off in **< 30 seconds**. |
| **REQ-11** | Simulink Telemedicine | Discrete-event & physical workflow simulation in Simulink modeling patient arrival, acquisition, edge processing, bandwidth, review queues, and referral load. | Resource optimization for district healthcare networks serving **100,000+ patients/year**. |
| **REQ-12** | Offline Edge Design | Offline-first local execution for rural primary health centers with intermittent or zero internet connectivity. | Zero continuous cloud dependency for local triage and quality gating. |
| **REQ-13** | MathWorks + OSS Stack | Native MATLAB toolbox integration (Image Processing, Computer Vision, Deep Learning, Medical Imaging, Stats & ML, Simulink) + Open-Source PyTorch runtime. | Complete dual-stack reproducibility with zero paid API costs. |
| **REQ-14** | Clinical Safety | Zero hallucination, strict research/clinical disclaimers, privacy preservation, and explicit separation between research and screening modes. | Full compliance with medical software safety practices and data protection standards. |

---

## 3. Requirements Traceability Matrix (RTM)

The following matrix maps every explicit SIH26038 requirement to its dedicated subsystem module, implementation script/class, automated verification test, and verifiable evidence artifact.

```
+----------------------------------------------------------------------------------------------------+
|                                  REQUIREMENTS TRACEABILITY MATRIX                                  |
+--------+--------------------------+----------------------------+-----------------+-----------------+
| Req ID | Subsystem Module         | Implementation Artifact    | Test Suite      | Evidence Output |
+--------+--------------------------+----------------------------+-----------------+-----------------+
| REQ-01 | Quality Gate (FIQA)      | src/quality/gate.py        | tests/test_     | Rejection Log & |
|        |                          | matlab/quality_gate.m      | quality.py      | Recapture Advice|
+--------+--------------------------+----------------------------+-----------------+-----------------+
| REQ-02 | Adaptive Enhancement     | src/preprocess/enhance.py  | tests/test_     | Before/After    |
|        |                          | matlab/preprocess.m        | preprocess.py   | PSNR/SSIM Metric|
+--------+--------------------------+----------------------------+-----------------+-----------------+
| REQ-03 | Retinal Anatomy Engine   | src/anatomy/vessel_od.py   | tests/test_     | Dice/IoU Mask & |
|        |                          | matlab/segment_vessels.m   | anatomy.py      | OD Distance Err |
+--------+--------------------------+----------------------------+-----------------+-----------------+
| REQ-04 | Lesion Evidence Detector | src/lesions/detector.py    | tests/test_     | Lesion Mask &   |
|        |                          | matlab/detect_lesions.m    | lesions.py      | Precision-Recall|
+--------+--------------------------+----------------------------+-----------------+-----------------+
| REQ-05 | DR Severity Classifier   | src/models/classifier.py   | tests/test_     | Confusion Matrix|
|        |                          | matlab/dr_classifier.m     | classifier.py   | & QWK Score     |
+--------+--------------------------+----------------------------+-----------------+-----------------+
| REQ-06 | Referable DR Triage      | src/models/triage.py       | tests/test_     | ROC-AUC Curve,  |
|        |                          | matlab/evaluate_rdr.m      | triage.py       | Sens/Spec Table |
+--------+--------------------------+----------------------------+-----------------+-----------------+
| REQ-07 | Explainable AI Engine    | src/xai/gradcam.py         | tests/test_     | Grad-CAM /      |
|        |                          | matlab/xai_gradcam.m       | xai.py          | Score-CAM Maps  |
+--------+--------------------------+----------------------------+-----------------+-----------------+
| REQ-08 | Evidence Consistency Eng | src/engine/consistency.py  | tests/test_     | Consistency     |
|        |                          | matlab/consistency_eng.m   | consistency.py  | Score & Discord |
+--------+--------------------------+----------------------------+-----------------+-----------------+
| REQ-09 | Confidence Calibration   | src/models/calibrate.py    | tests/test_     | Reliability     |
|        |                          | matlab/calibrate_model.m   | calibrate.py    | Diagram & ECE   |
+--------+--------------------------+----------------------------+-----------------+-----------------+
| REQ-10 | Clinical-Style Report    | src/reporting/report.py    | tests/test_     | PDF/HTML Report |
|        |                          | matlab/generate_report.m   | reporting.py    | (<30s UX audit) |
+--------+--------------------------+----------------------------+-----------------+-----------------+
| REQ-11 | Simulink Telemedicine    | simulink/rural_telemed.slx | tests/test_     | Sim Throughput, |
|        | Workflow Model           | matlab/run_telemed_sim.m   | simulink_sim.m  | Queue & Cost Opt|
+--------+--------------------------+----------------------------+-----------------+-----------------+
| REQ-12 | Offline Edge Engine      | src/edge/offline_sync.py   | tests/test_     | Zero-Net Run &  |
|        |                          | src/api/server.py          | edge_offline.py | Batch Sync Log  |
+--------+--------------------------+----------------------------+-----------------+-----------------+
| REQ-13 | Dual-Stack MATLAB/Python | matlab/run_pipeline.m      | tests/test_     | Cross-Platform  |
|        | Integration              | scripts/run_pipeline.py    | dual_stack.py   | Verification Log|
+--------+--------------------------+----------------------------+-----------------+-----------------+
| REQ-14 | Safety, Audit & Privacy  | src/core/safety.py         | tests/test_     | Audit Log &     |
|        |                          | SECURITY.md                | security.py     | Anonymizer Check|
+--------+--------------------------+----------------------------+-----------------+-----------------+
```

---

## 4. Verification and Acceptance Criteria

1. **Image Quality Acceptance**:
   - Must successfully flag underexposed, overexposed, out-of-focus, or severely occluded images as `UNGRADABLE`.
   - Must output specific textual feedback (e.g., "Illumination low in peripheral retina; re-align flash intensity and ask patient to fixate on green target").
2. **Clinical Performance Acceptance**:
   - Referable DR: Sensitivity $\ge 90.0\%$ and Specificity $\ge 85.0\%$ evaluated on external validation sets (e.g., IDRiD / MESSIDOR-2 test sets).
   - Expected Calibration Error (ECE) $< 5.0\%$.
3. **Clinician Efficiency Acceptance**:
   - The clinical summary interface must assemble all diagnostic evidence (DR level, calibrated confidence, detected lesions with coordinates, Grad-CAM heatmap, foveal involvement) onto a single unified pane viewable and signable in $< 30$ seconds.
4. **Simulink Simulation Acceptance**:
   - Must simulate realistic 100,000+ patient/year district workflows with parametric inputs (number of PHCs, camera count, fiber/cellular bandwidth, ophthalmologist roster size, local vs. cloud inference).
   - Must compute waiting times, doctor queue backlogs, network bandwidth saturation, and total cost per screened patient.
