# RuralDR-XAI: Real-Time Clinical Screening Workflow & <30s Review Architecture

---

## 1. Real-Time Clinical Workflow Overview

The RuralDR-XAI operational lifecycle is designed specifically for resource-constrained rural Primary Health Centers (PHCs) and Community Health Centers (CHCs) in India. It links health workers on the ground with remote ophthalmologists at district base hospitals via an evidence-grounded decision support loop.

```
+----------------------------------------------------------------------------------------------------+
|                                    REAL-TIME CLINICAL LIFECYCLE                                    |
+----------------------------------------------------------------------------------------------------+

   [ Step 1: Patient Arrival & Anon ID ] (ASHA / Multipurpose Health Worker at PHC)
                      │
                      ▼
   [ Step 2: Non-Mydriatic Fundus Capture ] (Portable 45°/50° Fundus Camera)
                      │
                      ▼
   [ Step 3: Edge Quality Gate (< 1 sec) ]
          ├──► Status = UNGRADABLE ──► [ Instant Recapture Advice displayed on screen ]
          │                            (e.g., "Blurry: Re-focus on macula", "Flash too low")
          │                            ──► Immediate Re-capture (Patient still in chair)
          │
          └──► Status = GRADEABLE
                      │
                      ▼
   [ Step 4: Local Edge AI Processing (1–2 sec) ]
          ├── Adaptive Enhancement (CLAHE + Illumination homogenization)
          ├── Retinal Anatomy Mapping (Vessel tree, Optic Disc, Foveal center)
          ├── Lesion Evidence Extraction (MAs, Exudates, Hemorrhages)
          ├── ICDR Severity Classification (Grade 0 to 4)
          ├── Explainability Mapping (Grad-CAM & Attention Saliency)
          ├── Evidence Consistency Engine (Concordance verification)
          └── Confidence Calibration (ECE < 5%)
                      │
                      ▼
   [ Step 5: Instant Primary Triage (< 5 sec) ]
          ├── GRADE 0 / GRADE 1 (High Consistency):
          │   └── Non-Referable ──► Automated Discharge Leaflet (Annual re-screening advised)
          │
          └── GRADE 2+ / DISCORDANT / BORDERLINE:
              └── Referable / Review Needed ──► Asynchronous Sync to District Tele-Review Queue
                      │
                      ▼
   [ Step 6: Tele-Ophthalmologist Verification (< 30 sec) ]
          ├── Specialist logs into District Web Portal
          ├── Inspects Single-Pane Evidence Dashboard (Original vs Overlays vs Grad-CAM)
          ├── Reviews Lesion Inventory & Foveal Involvement Threat
          └── Performs 1-Click Verification / Override / Referral Routing
                      │
                      ▼
   [ Step 7: Final Signed Clinical Report & Patient Care Pathway ]
          ├── SMS / WhatsApp notification to patient
          └── Formal referral appointment booked at District Base Hospital if required
```

---

## 2. The <30-Second Ophthalmologist Review Design

Ophthalmologist burnout and severe specialist shortages in rural India demand that clinical verification must not take minutes. RuralDR-XAI optimizes visual ergonomics to achieve comprehensive clinical review in under 30 seconds:

```
+----------------------------------------------------------------------------------------------------+
|                         SINGLE-PANE OPHTHALMOLOGIST REVIEW DASHBOARD                               |
+----------------------------------------------------------------------------------------------------+
|  HEADER: Case #RDR-2026-9841  |  Eye: Left (OS)  |  Quality: GRADEABLE (0.94)  |  Mode: CLINICAL   |
+---------------------------------------------------+------------------------------------------------+
|  LEFT PANE: DYNAMIC RETINAL VIEWER                |  RIGHT PANE: CLINICAL EVIDENCE & TRIAGE        |
|  ┌──────────────────────────────────────────────┐ │                                                |
|  │                                              │ │  AI PREDICTION:                                |
|  │  [ High-Resolution Fundus Image Display ]    │ │  ► Grade 2: Moderate NPDR (Referable)         |
|  │                                              │ │  ► Calibrated Confidence: 92.4%                |
|  │  Interactive Layer Toggles:                  │ │                                                |
|  │  [x] Original RGB      [x] CLAHE Enhanced    │ │  EVIDENCE CONSISTENCY:                         |
|  │  [x] Optic Disc & Fovea[ ] Vessel Tree       │ │  Status: SUPPORTED (Concordance Index: 0.88)   |
|  │  [x] Lesions (MA/EX/HE)[x] Grad-CAM Heatmap  │ │                                                |
|  │                                              │ │  LESION INVENTORY:                             |
|  │  Visual Highlights:                          │ │  - Microaneurysms: 14 detected (Temporal/Inf)  |
|  │  - Red Dots: Microaneurysms                  │ │  - Hard Exudates: 6 clusters (Area: 0.42%)     |
|  │  - Yellow Contours: Exudates                 │ │  - Hemorrhages: 3 dot/blot (Nasal/Inferior)    |
|  │  - Blue Cross: Fovea Center (No exudates <1DD│ │  - Foveal Threat: SAFE (> 1 Disc Diameter)    |
|  │                                              │ │                                                |
|  └──────────────────────────────────────────────┘ │  RECOMMENDED CLINICAL ACTION:                  |
|                                                   │  [ Routine Referral to District Eye Clinic ]   |
+---------------------------------------------------+------------------------------------------------+
|  BOTTOM BAR: RAPID OPHTHALMOLOGIST DECISION ACTION                                                 |
|  [ ✓ AGREE & SIGN (Grade 2) ]  [ OVERRIDE GRADE ▼ ]  [ REQUEST RECAPTURE ]  [ EXPORT PDF REPORT ]  |
+----------------------------------------------------------------------------------------------------+
```

### Cognitive Budget Breakdown for <30-Second Review:
1. **0–5 seconds**: Eye fixates on predicted DR Grade, calibrated confidence, and referral status badge.
2. **5–15 seconds**: Visual inspection of fundus with lesion overlays and Grad-CAM heatmap to verify if flagged lesions correspond to true clinical pathology.
3. **15–22 seconds**: Review foveal macular hazard status (verifying whether hard exudates threaten central visual acuity).
4. **22–30 seconds**: 1-click electronic confirmation (`AGREE & SIGN`) or rapid dropdown grade override.
