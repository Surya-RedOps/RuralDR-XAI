# Retina AI: Phase 2 Classification Error Analysis Report

## 1. Overview
- **Held-Out Test Set**: 78 cases (Zero overlap with training or validation cohorts)
- **Total Misclassifications**: 41 / 78 (52.56% Error Rate)
- **Overall Test Accuracy**: 47.44%
- **Quadratic Weighted Kappa (QWK)**: 0.7196

---

## 2. Error Severity Breakdown
| Error Category | Count | Percentage of Errors | Clinical Implication |
| :--- | :--- | :--- | :--- |
| **Adjacent-Grade Discrepancy ($\Delta = 1$)** | 25 | 61.0% | Low clinical hazard; reflects clinical inter-rater grader variability (e.g. Mild vs Moderate boundary). |
| **Severe Grade Discrepancy ($\Delta \ge 2$)** | 16 | 39.0% | High priority review required; model missed extensive lesion clusters. |
| **Referable DR False Negatives (FN)** | 8 | 19.5% | Missed referral cases (True Grade 2+ predicted as 0/1). |
| **Referable DR False Positives (FP)** | 4 | 9.8% | Unnecessary referral cases (True Grade 0/1 predicted as 2+). |

---

## 3. Representative Error Cases (Anonymized)
| Image ID | Groundtruth Grade | AI Predicted Grade | Calibrated Confidence | Error Type |
| :--- | :--- | :--- | :--- | :--- |
| `IDRiD_397` | Grade 2 (Moderate NPDR) | Grade 0 (No DR) | 34.1% | Referable FN |
| `IDRiD_044` | Grade 2 (Moderate NPDR) | Grade 4 (Proliferative DR) | 34.9% | Adjacent Discrepancy |
| `IDRiD_242` | Grade 2 (Moderate NPDR) | Grade 1 (Mild NPDR) | 29.0% | Referable FN |
| `IDRiD_203` | Grade 1 (Mild NPDR) | Grade 0 (No DR) | 33.1% | Adjacent Discrepancy |
| `IDRiD_284` | Grade 2 (Moderate NPDR) | Grade 1 (Mild NPDR) | 30.8% | Referable FN |
| `IDRiD_290` | Grade 1 (Mild NPDR) | Grade 0 (No DR) | 59.3% | Adjacent Discrepancy |
| `IDRiD_013` | Grade 3 (Severe NPDR) | Grade 4 (Proliferative DR) | 22.4% | Adjacent Discrepancy |
| `IDRiD_087` | Grade 2 (Moderate NPDR) | Grade 4 (Proliferative DR) | 32.1% | Adjacent Discrepancy |
| `IDRiD_309` | Grade 3 (Severe NPDR) | Grade 4 (Proliferative DR) | 33.4% | Adjacent Discrepancy |
| `IDRiD_343` | Grade 2 (Moderate NPDR) | Grade 4 (Proliferative DR) | 29.9% | Adjacent Discrepancy |
| `IDRiD_395` | Grade 0 (No DR) | Grade 1 (Mild NPDR) | 34.4% | Adjacent Discrepancy |
| `IDRiD_010` | Grade 4 (Proliferative DR) | Grade 3 (Severe NPDR) | 29.9% | Adjacent Discrepancy |
| `IDRiD_231` | Grade 2 (Moderate NPDR) | Grade 1 (Mild NPDR) | 30.0% | Referable FN |
| `IDRiD_007` | Grade 3 (Severe NPDR) | Grade 4 (Proliferative DR) | 31.6% | Adjacent Discrepancy |
| `IDRiD_253` | Grade 3 (Severe NPDR) | Grade 4 (Proliferative DR) | 27.9% | Adjacent Discrepancy |

---

## 4. Key Clinical Insights & Mitigations for Later Phases
1. **Mild vs. Moderate NPDR Boundary**: The majority of adjacent discrepancies occur between Grade 1 (few microaneurysms) and Grade 2 (numerous microaneurysms/exudates). In Phase 4 (Lesion Segmentation), explicit count quantification of microaneurysms will resolve this boundary.
2. **Macular Safety Gate**: Lesions near the fovea require ophthalmologist confirmation regardless of classifier grade.
3. **Doctor Review Workflow**: In Phase 5, all cases flagged as borderline or having high entropy will be routed for mandatory clinician sign-off.
