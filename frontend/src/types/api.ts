/**
 * API Response and Data Types
 * Mirrors the FastAPI backend response structure
 */

export interface UploadResponse {
  upload_id: string;
  filename: string;
  size_bytes: number;
  message: string;
}

export interface ProcessResponse {
  job_id: string;
  status: string;
  message: string;
}

export interface StatusResponse {
  job_id: string;
  status: 'processing' | 'completed' | 'failed';
  progress_pct: number;
  current_step: string;
  error?: string;
}

export interface QualityResult {
  status: 'GRADEABLE' | 'BORDERLINE' | 'UNGRADABLE';
  score: number;
  message: string;
}

export interface ClassificationResult {
  dr_grade: number; // 0-4
  severity: string;
  confidence: number;
  class_probabilities: number[];
  is_referable: boolean;
}

export interface GradCAMResult {
  is_valid: boolean;
  target_class: number;
  target_class_name: string;
  activation_coverage: number;
  peak_intensity: number;
  quality_flags: string[];
  overlay_url: string;
}

export interface LesionDetection {
  type: string;
  detected: boolean;
  num_regions: number;
  area_pct: number;
  confidence: number;
  mask_url: string;
}

export interface SegmentationResult {
  lesions: LesionDetection[];
  input_resolution: string;
}

export interface ProcessingTimes {
  quality_gate_ms: number;
  classification_ms: number;
  gradcam_ms: number;
  segmentation_ms: number;
  total_ms: number;
}

export interface ScreeningResult {
  case_id: string;
  quality: QualityResult;
  classification: ClassificationResult;
  gradcam: GradCAMResult | null;
  segmentation: SegmentationResult | null;
  processing_times: ProcessingTimes;
  evidence_report: Record<string, any>;
}

export interface ApiError {
  error: string;
  message: string;
  details: Record<string, any>;
}
