"""
Retina AI: Complete Explainability Pipeline Demo
Runs the full Quality Gate → DR → Grad-CAM → Segmentation pipeline on a test image.

Usage:
    python scripts/run_explainability_demo.py --input <image_path> --output <output_dir>
"""

import sys
import json
import argparse
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.core.config import RESULTS_DIR
from src.ai.explainability.pipeline import ExplainableScreeningPipeline
from src.ai.explainability.evidence import generate_evidence_report


def main():
    parser = argparse.ArgumentParser(description="Run Explainability Pipeline Demo")
    parser.add_argument("--input", type=str, required=True, help="Path to retinal fundus image")
    parser.add_argument("--output", type=str, default=None, help="Output directory")
    parser.add_argument("--no-segmentation", action="store_true",
                        help="Skip lesion segmentation")
    args = parser.parse_args()

    input_path = Path(args.input)
    if not input_path.is_file():
        print(f"ERROR: Image not found: {input_path}")
        sys.exit(1)

    output_dir = args.output or str(RESULTS_DIR / "explainability")
    Path(output_dir).mkdir(parents=True, exist_ok=True)

    print(f"{'='*60}")
    print(f"Retina AI — Explainability Pipeline Demo")
    print(f"{'='*60}")
    print(f"Input: {input_path}")
    print(f"Output: {output_dir}")
    print()

    # Initialize pipeline
    pipeline = ExplainableScreeningPipeline()

    # Run pipeline
    result = pipeline.process(
        image_input=str(input_path),
        output_dir=output_dir,
        run_segmentation=not args.no_segmentation,
    )

    # Display results
    print(f"\n{'─'*60}")
    print(f"RESULTS")
    print(f"{'─'*60}")
    print(f"Case ID: {result.case_id}")
    print(f"Quality: {result.quality_status} (score: {result.quality_score:.4f})")
    print(f"Gradeable: {result.is_gradeable}")

    if result.dr_grade is not None:
        print(f"\nDR Grade: {result.dr_grade} — {result.severity}")
        print(f"Confidence: {result.classification_confidence:.1%}")
        print(f"Referable: {result.is_referable}")

    if result.gradcam_result:
        gc = result.gradcam_result
        print(f"\nGrad-CAM:")
        print(f"  Valid: {gc.is_valid}")
        print(f"  Target: {gc.target_class_name}")
        print(f"  Coverage: {gc.activation_coverage:.1%}")
        print(f"  Peak: {gc.peak_intensity:.4f}")
        if gc.quality_flags:
            print(f"  Flags: {', '.join(gc.quality_flags)}")

    if result.segmentation_result:
        print(f"\nLesion Segmentation:")
        for lesion in result.segmentation_result.lesions:
            status = "✓ Detected" if lesion.detected else "✗ Not detected"
            print(f"  {lesion.lesion_type}: {status}")
            if lesion.detected:
                print(f"    Regions: {lesion.num_connected_components}")
                print(f"    Area: {lesion.relative_area_pct:.4f}%")
                print(f"    Confidence: {lesion.mean_confidence:.1%}")

    print(f"\n{'─'*60}")
    print(f"TIMING")
    print(f"{'─'*60}")
    print(f"Quality Gate: {result.quality_gate_time_ms:.1f} ms")
    print(f"Classification: {result.classification_time_ms:.1f} ms")
    print(f"Grad-CAM: {result.gradcam_time_ms:.1f} ms")
    print(f"Segmentation: {result.segmentation_time_ms:.1f} ms")
    print(f"Total Pipeline: {result.total_pipeline_time_ms:.1f} ms")

    print(f"\n{'─'*60}")
    print(f"EVIDENCE SUMMARY")
    print(f"{'─'*60}")
    for line in result.evidence_summary:
        print(f"  • {line}")

    # Generate evidence report
    if result.is_gradeable:
        report = generate_evidence_report(result)
        report_path = Path(output_dir) / f"{result.case_id}_evidence_report.json"
        with open(report_path, "w", encoding="utf-8") as f:
            json.dump(report, f, indent=2, default=str)
        print(f"\nEvidence report: {report_path}")

    print(f"\nAll outputs saved to: {output_dir}")
    print(f"\n{result.disclaimer}")


if __name__ == "__main__":
    main()
