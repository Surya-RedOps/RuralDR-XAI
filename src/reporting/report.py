"""
Screening Report Serializer and Markdown Formatter
"""

import json
from pathlib import Path
from typing import Dict, Any

from ..core.contracts import ScreeningResult


def export_screening_json(result: ScreeningResult, output_path: Path) -> Path:
    """
    Exports structured JSON representation of ScreeningResult.
    """
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(result.model_dump_json(indent=2))
    return output_path


def format_screening_markdown(result: ScreeningResult) -> str:
    """
    Generates clean Markdown representation of screening findings.
    """
    pred_str = result.prediction.grade_name if result.prediction else "N/A"
    conf_str = f"{result.prediction.calibrated_confidence*100:.1f}%" if result.prediction else "N/A"
    rdr_str = "REFERABLE (Level 2+)" if (result.prediction and result.prediction.is_referable) else "NON-REFERABLE"

    md = f"""# Retinal Screening Summary — Case {result.case_id}
**Timestamp**: `{result.timestamp}`  
**Image Quality**: **{result.quality.status.value}** (Score: `{result.quality.quality_score:.2f}`)  
**Review Priority**: **{result.review_priority.value}**

---

### 1. Diagnosis & Triage
- **Predicted Severity**: {pred_str}
- **Referable Status**: **{rdr_str}**
- **Calibrated Confidence**: `{conf_str}`
- **Recommendation**: {result.triage_decision}

---

### 2. Anatomical & Lesion Inventory
- **Optic Disc**: {'Detected' if result.anatomy.optic_disc_center else 'Not Localized'}
- **Fovea Center**: {'Localized' if result.anatomy.fovea_center else 'Not Localized'}
- **Microaneurysms**: `{result.lesions.microaneurysms_count}` detected
- **Hard Exudates**: `{result.lesions.hard_exudates_area_pct:.2f}%` area coverage
- **Hemorrhages**: `{result.lesions.hemorrhages_count}` lesions
- **Foveal Threat Warning**: {'YES — EXUDATES WITHIN 1 DD OF FOVEA' if result.lesions.foveal_involvement_threat else 'SAFE'}

---

> *{result.disclaimer}*
"""
    return md
