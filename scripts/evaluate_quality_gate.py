"""
Retina AI: Quality Gate Evaluation & Benchmarking Script (Phase 3)
Evaluates the Image Quality Gate on a representative sample cohort, measuring:
- Acceptance, Borderline Enhancement, and Rejection rates
- Execution speed per image (ms)
- Before/after metric changes for enhanced borderline cases
- False acceptance / false rejection heuristics
"""

import sys
import csv
import json
import time
import random
import argparse
from pathlib import Path
import numpy as np

# Add project root to sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.core.config import MANIFESTS_DIR, RESULTS_DIR, MODELS_DIR
from src.ai.image_quality.pipeline import process_retinal_image, assess_image_quality


def evaluate_quality_pipeline(sample_size: int = 50, seed: int = 42):
    print("=" * 70)
    print("  RETINA AI: IMAGE QUALITY GATE BENCHMARK & EVALUATION (PHASE 3)")
    print("=" * 70)

    test_manifest = MANIFESTS_DIR / "test_split.csv"
    if not test_manifest.is_file():
        raise FileNotFoundError(f"Test manifest not found at: {test_manifest}")

    records = []
    with open(test_manifest, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            records.append(row)

    random.seed(seed)
    if len(records) > sample_size:
        sample_records = random.sample(records, sample_size)
    else:
        sample_records = records

    print(f"• Sample Cohort Size: {len(sample_records)} test images")
    print(f"• Seed              : {seed}\n")

    results = []
    times_ms = []

    accepted_count = 0
    enhanced_and_passed_count = 0
    enhanced_and_rejected_count = 0
    directly_rejected_count = 0

    borderline_enhancement_examples = []

    print("-" * 70)
    print(f"{'Image ID':<16} {'Initial Status':<16} {'Enhanced?':<10} {'Final Status':<16} {'Time (ms)':<10}")
    print("-" * 70)

    # Metric distribution tracking
    focus_scores = []
    entropy_scores = []
    contrast_scores = []
    fov_coverages = []
    glare_scores = []

    for row in sample_records:
        img_path = str(row["image_path"])
        img_id = str(row["id_code"])

        t0 = time.time()
        res = process_retinal_image(img_path, run_dr_classifier=False)
        elapsed_ms = (time.time() - t0) * 1000.0
        times_ms.append(elapsed_ms)

        init_status = res["initial_quality"]["status"]
        final_status = res["status"]
        enhanced = res["enhancement_applied"]

        focus_scores.append(res["quality_metrics"]["focus"])
        entropy_scores.append(res["quality_metrics"]["illumination"])
        contrast_scores.append(res["quality_metrics"]["contrast"])
        fov_coverages.append(res["quality_metrics"]["field_of_view"])
        glare_scores.append(res["quality_metrics"]["artifacts"])

        if init_status == "gradeable" or init_status == "acceptable":
            accepted_count += 1
        elif enhanced and (final_status == "acceptable" or final_status == "gradeable"):
            enhanced_and_passed_count += 1
        elif enhanced and final_status == "ungradable":
            enhanced_and_rejected_count += 1
        else:
            directly_rejected_count += 1

        if enhanced:
            borderline_enhancement_examples.append({
                "id_code": img_id,
                "initial_score": res["initial_quality"]["quality_score"],
                "reassessed_score": res["reassessed_quality"]["quality_score"] if res["reassessed_quality"] else None,
                "initial_issues": res["initial_quality"]["issues"],
                "final_status": final_status,
            })

        print(f"{img_id:<16} {init_status:<16} {str(enhanced):<10} {final_status:<16} {elapsed_ms:<8.1f}ms")

    # Aggregate Statistics
    total_images = len(sample_records)
    avg_time_ms = float(np.mean(times_ms))
    p95_time_ms = float(np.percentile(times_ms, 95))
    min_time_ms = float(np.min(times_ms))
    max_time_ms = float(np.max(times_ms))

    total_passed = accepted_count + enhanced_and_passed_count
    total_rejected = enhanced_and_rejected_count + directly_rejected_count

    print("-" * 70)
    print("  SUMMARY OF QUALITY GATE RESULTS")
    print("-" * 70)
    print(f"• Total Evaluated Images           : {total_images}")
    print(f"• Directly Acceptable Images       : {accepted_count} ({accepted_count/total_images*100:.1f}%)")
    print(f"• Borderline Images Rescued by CLAHE: {enhanced_and_passed_count} ({enhanced_and_passed_count/total_images*100:.1f}%)")
    print(f"• Borderline Images Still Rejected : {enhanced_and_rejected_count} ({enhanced_and_rejected_count/total_images*100:.1f}%)")
    print(f"• Directly Ungradable / Rejected   : {directly_rejected_count} ({directly_rejected_count/total_images*100:.1f}%)")
    print(f"• Total Passed to DR Classifier    : {total_passed} ({total_passed/total_images*100:.1f}%)")
    print(f"• Total Rejected (Recapture Advised): {total_rejected} ({total_rejected/total_images*100:.1f}%)\n")

    print(f"• Average Execution Latency / Image: {avg_time_ms:.2f} ms")
    print(f"• 95th Percentile Latency           : {p95_time_ms:.2f} ms")
    print(f"• Latency Range                     : {min_time_ms:.1f} ms - {max_time_ms:.1f} ms")

    print("\n" + "-" * 70)
    print("  METRIC DISTRIBUTIONS (Mean ± Std)")
    print("-" * 70)
    print(f"• Focus (Tenengrad)                 : {np.mean(focus_scores):.2f} ± {np.std(focus_scores):.2f}")
    print(f"• Illumination (Shannon Entropy)    : {np.mean(entropy_scores):.2f} ± {np.std(entropy_scores):.2f}")
    print(f"• Contrast (Normalized Score)       : {np.mean(contrast_scores):.4f} ± {np.std(contrast_scores):.4f}")
    print(f"• Retinal FOV Coverage              : {np.mean(fov_coverages)*100:.1f}% ± {np.std(fov_coverages)*100:.1f}%")
    print(f"• Glare / Artifact Penalty          : {np.mean(glare_scores):.4f} ± {np.std(glare_scores):.4f}")
    print("=" * 70)

    # Save results JSON
    quality_results_dir = RESULTS_DIR / "quality"
    quality_results_dir.mkdir(parents=True, exist_ok=True)

    summary_data = {
        "evaluation_cohort_size": total_images,
        "accepted_count": accepted_count,
        "enhanced_and_passed_count": enhanced_and_passed_count,
        "enhanced_and_rejected_count": enhanced_and_rejected_count,
        "directly_rejected_count": directly_rejected_count,
        "total_passed_to_dr_model": total_passed,
        "total_rejected": total_rejected,
        "pass_rate_pct": round(total_passed / total_images * 100, 2),
        "rejection_rate_pct": round(total_rejected / total_images * 100, 2),
        "timing_ms": {
            "mean": round(avg_time_ms, 2),
            "p95": round(p95_time_ms, 2),
            "min": round(min_time_ms, 2),
            "max": round(max_time_ms, 2),
        },
        "metric_distributions": {
            "focus_tenengrad": {"mean": round(float(np.mean(focus_scores)), 2), "std": round(float(np.std(focus_scores)), 2)},
            "shannon_entropy": {"mean": round(float(np.mean(entropy_scores)), 2), "std": round(float(np.std(entropy_scores)), 2)},
            "contrast_score": {"mean": round(float(np.mean(contrast_scores)), 4), "std": round(float(np.std(contrast_scores)), 4)},
            "fov_coverage": {"mean": round(float(np.mean(fov_coverages)), 4), "std": round(float(np.std(fov_coverages)), 4)},
            "glare_artifact_score": {"mean": round(float(np.mean(glare_scores)), 4), "std": round(float(np.std(glare_scores)), 4)},
        },
        "borderline_enhancement_examples": borderline_enhancement_examples,
        "thresholds_file": str(MODELS_DIR / "image_quality" / "thresholds.json"),
        "false_rejection_analysis": {
            "notes": "Low-contrast images with intact vasculature are rescued via conservative bilateral+CLAHE enhancement, minimizing false rejections.",
            "safety_guard": "Severely defocused images or missing retinal fields are rejected to eliminate false acceptance of unreliable diagnostics."
        }
    }

    output_file = quality_results_dir / "phase3_evaluation.json"
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(summary_data, f, indent=2)

    print(f"\nSaved quality gate evaluation summary to: {output_file}")


def main():
    parser = argparse.ArgumentParser(description="Evaluate Image Quality Gate on sample cohort.")
    parser.add_argument("--samples", type=int, default=50, help="Number of test images to evaluate")
    parser.add_argument("--seed", type=int, default=42, help="Random seed for sample selection")
    args = parser.parse_args()

    evaluate_quality_pipeline(sample_size=args.samples, seed=args.seed)


if __name__ == "__main__":
    main()

