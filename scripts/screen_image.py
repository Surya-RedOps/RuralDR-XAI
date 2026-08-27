import sys
import argparse
from pathlib import Path

# Add project root to sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

import cv2
import torch

from src.core.config import RESULTS_DIR
from src.engine.orchestrator import ScreeningOrchestrator
from src.reporting.pdf_generator import generate_clinical_pdf_report
from src.reporting.report import export_screening_json, format_screening_markdown


def main():
    parser = argparse.ArgumentParser(description="RuralDR-XAI: Clinical Fundus Screening CLI")
    parser.add_argument("--input", type=str, required=True, help="Path to input fundus image (JPG/PNG/TIFF)")
    parser.add_argument("--output", type=str, default="results/cli_screening", help="Output directory")
    parser.add_argument("--checkpoint", type=str, default=None, help="Path to trained model weights (.pth)")
    parser.add_argument("--device", type=str, default="cuda" if torch.cuda.is_available() else "cpu", help="cuda or cpu")
    args = parser.parse_args()

    input_path = Path(args.input)
    output_dir = Path(args.output)
    output_dir.mkdir(parents=True, exist_ok=True)

    print(f"[*] Initializing RuralDR-XAI on device: {args.device}")
    device = torch.device(args.device)
    orchestrator = ScreeningOrchestrator(device=device)

    print(f"[*] Processing image: {input_path}")
    result, visual_layers = orchestrator.process_image(input_path)

    # Export JSON and Markdown
    json_path = output_dir / f"{result.case_id}_result.json"
    export_screening_json(result, json_path)

    md_report = format_screening_markdown(result)
    with open(output_dir / f"{result.case_id}_report.md", "w", encoding="utf-8") as f:
        f.write(md_report)

    # Save visual layers
    for name, img_arr in visual_layers.items():
        if img_arr.ndim == 2:
            cv2.imwrite(str(output_dir / f"{result.case_id}_{name}.png"), img_arr)
        elif img_arr.ndim == 3:
            bgr = cv2.cvtColor(img_arr, cv2.COLOR_RGB2BGR)
            cv2.imwrite(str(output_dir / f"{result.case_id}_{name}.jpg"), bgr)

    # Generate Clinical PDF
    composite_np = visual_layers.get("composite_annotated", visual_layers.get("original"))
    pdf_path = output_dir / f"{result.case_id}_clinical_report.pdf"
    generate_clinical_pdf_report(result, composite_np, pdf_path)

    print("\n" + "=" * 60)
    print(f"  SCREENING RESULT: {result.case_id}")
    print("=" * 60)
    print(f"• Image Quality:        {result.quality.status.value} (Score: {result.quality.quality_score:.2f})")
    if result.prediction:
        print(f"• Predicted Severity:   {result.prediction.grade_name}")
        print(f"• Referable DR:         {'YES (Level 2+)' if result.prediction.is_referable else 'NO (Level 0/1)'}")
        print(f"• Calibrated Conf:      {result.prediction.calibrated_confidence * 100:.1f}%")
    print(f"• Triage Action:        {result.triage_decision}")
    print(f"• Review Priority:      {result.review_priority.value}")
    print(f"• Lesion Inventory:     {result.lesions.microaneurysms_count} MAs, {result.lesions.hard_exudates_area_pct:.2f}% Exudates, {result.lesions.hemorrhages_count} HEs")
    print(f"• PDF Report:           {pdf_path}")
    print("=" * 60)


if __name__ == "__main__":
    main()
