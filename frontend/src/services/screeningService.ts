/**
 * Explainable AI Screening Engine & Validation Pipeline for RuralDR-XAI
 * Modular service simulating multi-stage image validation, FIQA quality scoring,
 * DR grading, Grad-CAM heatmap generation, and lesion segmentation.
 */

import {
  ScreeningResult,
  SampleImageOption,
  ClassificationResult,
  GradCAMResult,
  SegmentationResult,
  AISafetyCheck,
  ImageValidationResult,
  QualityResult,
  ProcessingTimes,
} from '@/types/api';
import {
  NORMAL_FUNDUS_SVG,
  MILD_NPDR_FUNDUS_SVG,
  MODERATE_NPDR_FUNDUS_SVG,
  SEVERE_NPDR_FUNDUS_SVG,
  PDR_FUNDUS_SVG,
  INVALID_CAR_SVG,
  POOR_QUALITY_FUNDUS_SVG,
  getGradCamOverlaySvg,
  getLesionMaskOverlaySvg,
} from './sampleAssets';

export const SAMPLE_IMAGE_OPTIONS: SampleImageOption[] = [
  {
    id: 'sample-moderate-npdr',
    label: 'Sample 1: Moderate NPDR (Level 2)',
    subtitle: 'Classic microaneurysms, blot hemorrhages & hard exudates',
    category: 'moderate',
    imageUrl: MODERATE_NPDR_FUNDUS_SVG,
    expectedGrade: 2,
    expectedStatus: 'VALID',
  },
  {
    id: 'sample-normal',
    label: 'Sample 2: Normal Retina (Level 0)',
    subtitle: 'Healthy fundus, sharp optic disc, clear macula, no lesions',
    category: 'normal',
    imageUrl: NORMAL_FUNDUS_SVG,
    expectedGrade: 0,
    expectedStatus: 'VALID',
  },
  {
    id: 'sample-mild-npdr',
    label: 'Sample 3: Mild NPDR (Level 1)',
    subtitle: 'Early microaneurysms, isolated vascular changes',
    category: 'mild',
    imageUrl: MILD_NPDR_FUNDUS_SVG,
    expectedGrade: 1,
    expectedStatus: 'VALID',
  },
  {
    id: 'sample-severe-npdr',
    label: 'Sample 4: Severe NPDR (Level 3)',
    subtitle: 'Extensive 4-quadrant hemorrhages & cotton wool spots',
    category: 'severe',
    imageUrl: SEVERE_NPDR_FUNDUS_SVG,
    expectedGrade: 3,
    expectedStatus: 'VALID',
  },
  {
    id: 'sample-pdr',
    label: 'Sample 5: Proliferative DR (Level 4)',
    subtitle: 'Neovascularization at disc (NVD) & preretinal hemorrhage',
    category: 'pdr',
    imageUrl: PDR_FUNDUS_SVG,
    expectedGrade: 4,
    expectedStatus: 'VALID',
  },
  {
    id: 'sample-invalid-car',
    label: 'Sample 6: Invalid Image (Car / Vehicle)',
    subtitle: 'Non-fundus test image — triggers automated rejection',
    category: 'invalid',
    imageUrl: INVALID_CAR_SVG,
    expectedStatus: 'INVALID',
  },
  {
    id: 'sample-poor-quality',
    label: 'Sample 7: Poor Quality (Blurry / Dark)',
    subtitle: 'Severe optical blur & artifact — triggers FIQA warning',
    category: 'poor_quality',
    imageUrl: POOR_QUALITY_FUNDUS_SVG,
    expectedStatus: 'POOR_QUALITY',
  },
];

const STAGE_NAMES = [
  'No Diabetic Retinopathy',
  'Mild Non-Proliferative Diabetic Retinopathy',
  'Moderate Non-Proliferative Diabetic Retinopathy',
  'Severe Non-Proliferative Diabetic Retinopathy',
  'Proliferative Diabetic Retinopathy',
];

export const screeningService = {
  /**
   * Pre-scan validation check: Fundus vs Non-Fundus and Quality Gate
   */
  async validateImage(
    imageUrl: string,
    fileMeta?: { name: string; size: number }
  ): Promise<ImageValidationResult> {
    // Artificial scanning delay
    await new Promise((res) => setTimeout(res, 900));

    // Check if it's the known invalid non-fundus sample
    if (imageUrl === INVALID_CAR_SVG || fileMeta?.name.toLowerCase().includes('car') || fileMeta?.name.toLowerCase().includes('landscape')) {
      return {
        isValidFundus: false,
        validationError: 'NOT_A_FUNDUS',
        rejectionReason:
          'This image does not appear to be a retinal fundus photograph. Please upload a valid fundus image captured using a retinal camera.',
        qualityScore: 12,
        fieldVisibilityPct: 0,
        blurLevel: 'High',
        illumination: 'Dark',
      };
    }

    // Check if it's the known poor quality sample
    if (imageUrl === POOR_QUALITY_FUNDUS_SVG || fileMeta?.name.toLowerCase().includes('blurry') || fileMeta?.name.toLowerCase().includes('dark')) {
      return {
        isValidFundus: true,
        validationError: 'POOR_QUALITY',
        rejectionReason:
          'Image Quality Insufficient. Severe optical blur, low retinal visibility (< 60%), and lighting artifacts detected.',
        qualityScore: 42,
        fieldVisibilityPct: 48,
        blurLevel: 'High',
        illumination: 'Uneven',
      };
    }

    // Default valid fundus
    return {
      isValidFundus: true,
      validationError: null,
      qualityScore: 94,
      fieldVisibilityPct: 96,
      blurLevel: 'Low',
      illumination: 'Uniform',
    };
  },

  /**
   * Full AI Screening execution for validated fundus image
   */
  async screenImage(
    caseId: string,
    imageUrl: string,
    selectedGradeHint?: number
  ): Promise<ScreeningResult> {
    // Determine DR grade
    let grade = 2; // Default realistic Moderate NPDR for demos
    if (selectedGradeHint !== undefined && selectedGradeHint >= 0 && selectedGradeHint <= 4) {
      grade = selectedGradeHint;
    } else if (imageUrl === NORMAL_FUNDUS_SVG) {
      grade = 0;
    } else if (imageUrl === MILD_NPDR_FUNDUS_SVG) {
      grade = 1;
    } else if (imageUrl === MODERATE_NPDR_FUNDUS_SVG) {
      grade = 2;
    } else if (imageUrl === SEVERE_NPDR_FUNDUS_SVG) {
      grade = 3;
    } else if (imageUrl === PDR_FUNDUS_SVG) {
      grade = 4;
    }

    // Class probabilities simulation
    const probs = [0.03, 0.05, 0.05, 0.04, 0.03];
    const confidence = grade === 0 ? 0.96 : grade === 1 ? 0.89 : grade === 2 ? 0.87 : grade === 3 ? 0.92 : 0.95;
    probs[grade] = confidence;
    const sum = probs.reduce((a, b) => a + b, 0);
    const normalizedProbs = probs.map((p) => Number((p / sum).toFixed(3)));

    const classification: ClassificationResult = {
      dr_grade: grade,
      severity: STAGE_NAMES[grade],
      confidence: confidence,
      class_probabilities: normalizedProbs,
      is_referable: grade > 0,
    };

    const quality: QualityResult = {
      status: 'GRADEABLE',
      score: 94,
      message: 'Excellent fundus visibility. Macula and Optic Disc clearly demarcated.',
    };

    const gradcam: GradCAMResult = {
      is_valid: true,
      target_class: grade,
      target_class_name: STAGE_NAMES[grade],
      activation_coverage: grade === 0 ? 0.04 : 0.28,
      peak_intensity: 0.93,
      quality_flags: ['High gradient fidelity', 'Focused anatomical correlation'],
      overlay_url: getGradCamOverlaySvg(grade),
    };

    // Lesions based on grade
    const lesions = [
      {
        type: 'Microaneurysms',
        detected: grade >= 1,
        num_regions: grade === 0 ? 0 : grade === 1 ? 6 : grade === 2 ? 14 : 28,
        area_pct: grade === 0 ? 0 : grade === 1 ? 0.4 : grade === 2 ? 1.2 : 2.8,
        confidence: 0.91,
        mask_url: getLesionMaskOverlaySvg(grade),
        color: '#ff1744',
      },
      {
        type: 'Hemorrhages',
        detected: grade >= 2,
        num_regions: grade <= 1 ? 0 : grade === 2 ? 5 : grade === 3 ? 16 : 24,
        area_pct: grade <= 1 ? 0 : grade === 2 ? 1.8 : 4.6,
        confidence: 0.88,
        mask_url: getLesionMaskOverlaySvg(grade),
        color: '#dc2626',
      },
      {
        type: 'Hard Exudates',
        detected: grade >= 2,
        num_regions: grade <= 1 ? 0 : grade === 2 ? 8 : grade === 3 ? 12 : 20,
        area_pct: grade <= 1 ? 0 : grade === 2 ? 1.1 : 2.4,
        confidence: 0.86,
        mask_url: getLesionMaskOverlaySvg(grade),
        color: '#fbc02d',
      },
      {
        type: 'Cotton Wool Spots',
        detected: grade >= 3,
        num_regions: grade <= 2 ? 0 : grade === 3 ? 4 : 7,
        area_pct: grade <= 2 ? 0 : 2.1,
        confidence: 0.84,
        mask_url: getLesionMaskOverlaySvg(grade),
        color: '#38bdf8',
      },
    ];

    const segmentation: SegmentationResult = {
      lesions,
      input_resolution: '1024x1024',
    };

    const safety: AISafetyCheck = {
      fundusVerified: true,
      qualityAcceptable: true,
      confidenceAcceptable: confidence >= 0.75,
      explanationGenerated: true,
      highUncertaintyWarning: confidence < 0.75,
    };

    const processing_times: ProcessingTimes = {
      quality_gate_ms: 240,
      classification_ms: 380,
      gradcam_ms: 310,
      segmentation_ms: 420,
      total_ms: 1350,
    };

    return {
      case_id: caseId,
      image_url: imageUrl,
      thumbnail_url: imageUrl,
      validation: {
        isValidFundus: true,
        qualityScore: 94,
        fieldVisibilityPct: 96,
        blurLevel: 'Low',
        illumination: 'Uniform',
      },
      quality,
      classification,
      gradcam,
      segmentation,
      safety,
      processing_times,
      evidence_report: {
        primaryEvidence:
          grade === 0
            ? 'No pathological retinal vascular lesions detected.'
            : grade === 1
            ? 'Early punctate microaneurysms detected in macular perimeter.'
            : grade === 2
            ? 'Multiple blot hemorrhages and circinate hard exudates near superior arcade.'
            : grade === 3
            ? 'Extensive 4-quadrant hemorrhages, venous beading & cotton wool infarctions.'
            : 'Active neovascularization at optic disc (NVD) with vitreous hemorrhage risk.',
        recommendedFollowup:
          grade === 0
            ? '12 months routine annual screening'
            : grade === 1
            ? '6 months follow-up examination'
            : grade === 2
            ? 'Specialist ophthalmologist review within 3-4 weeks'
            : grade === 3
            ? 'Urgent hospital referral within 1-2 weeks'
            : 'Immediate emergency vitreoretinal intervention within 48 hours',
      },
    };
  },
};
