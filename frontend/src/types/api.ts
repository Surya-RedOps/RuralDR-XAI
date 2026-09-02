/**
 * API Response and Data Types for RuralDR-XAI
 * Includes full clinical screening, XAI, referral, doctor review & report types.
 */

export type UserRole = 'worker' | 'doctor';

export interface UserProfile {
  id: string;
  role: UserRole;
  name: string;
  email: string;
  mobile?: string;
  regNumber?: string;
  centerName?: string;
  isVerified: boolean;
  avatarUrl?: string;
}

export type CaseStatus =
  | 'DRAFT'
  | 'UPLOADED'
  | 'VALIDATING'
  | 'INVALID_IMAGE'
  | 'POOR_QUALITY'
  | 'SCREENING'
  | 'SCREENED'
  | 'NO_REFERRAL'
  | 'REFERRAL_RECOMMENDED'
  | 'REFERRED'
  | 'DOCTOR_REVIEW'
  | 'CLINICAL_DECISION'
  | 'COMPLETED';

export type PriorityLevel = 'CRITICAL' | 'HIGH' | 'MEDIUM' | 'REVIEW' | 'LOW';

export interface PatientInfo {
  patientId: string;
  age: number;
  gender: 'Male' | 'Female' | 'Other';
  screeningDate: string;
  notes?: string;
  hba1c?: string;
  diabetesDuration?: string;
}

export interface ScreeningLocation {
  state: string;
  district: string;
  centerName: string;
}

export interface HospitalFacility {
  id: string;
  name: string;
  district: string;
  state: string;
  distanceKm: number;
  ophthalmologistOnDuty: string;
  bedAvailability: string;
  specialization: string;
  contactNumber: string;
  isVerified: boolean;
}

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
  score: number; // 0-100
  message: string;
  artifactsDetected?: string[];
}

export interface ClassificationResult {
  dr_grade: number; // 0-4
  severity: string;
  confidence: number; // 0-1
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
  type: 'Microaneurysms' | 'Hemorrhages' | 'Hard Exudates' | 'Cotton Wool Spots' | string;
  detected: boolean;
  num_regions: number;
  area_pct: number;
  confidence: number;
  mask_url: string;
  color?: string;
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

export interface AISafetyCheck {
  fundusVerified: boolean;
  qualityAcceptable: boolean;
  confidenceAcceptable: boolean;
  explanationGenerated: boolean;
  highUncertaintyWarning: boolean;
}

export interface ImageValidationResult {
  isValidFundus: boolean;
  validationError?: 'NOT_A_FUNDUS' | 'POOR_QUALITY' | null;
  rejectionReason?: string;
  qualityScore: number;
  fieldVisibilityPct: number;
  blurLevel: 'Low' | 'Moderate' | 'High';
  illumination: 'Uniform' | 'Uneven' | 'Dark';
}

export interface ScreeningResult {
  case_id: string;
  image_url: string;
  thumbnail_url?: string;
  validation: ImageValidationResult;
  quality: QualityResult;
  classification: ClassificationResult;
  gradcam: GradCAMResult | null;
  segmentation: SegmentationResult | null;
  safety: AISafetyCheck;
  processing_times: ProcessingTimes;
  evidence_report: Record<string, any>;
}

export type DoctorDecisionType =
  | 'CONFIRM_AI'
  | 'MODIFY_ASSESSMENT'
  | 'REQUEST_NEW_IMAGE'
  | 'INSUFFICIENT_EVIDENCE';

export interface DoctorReviewDecision {
  decision: DoctorDecisionType;
  confirmedGrade: number;
  confirmedSeverity: string;
  doctorNotes: string;
  recommendedTreatment?: string;
  followUpTimeline: string;
  reviewedBy: string;
  regNumber: string;
  reviewedAt: string;
  signatureStamp?: string;
}

export interface ScreeningCase {
  id: string; // e.g. RDX-1048
  createdAt: string;
  updatedAt: string;
  status: CaseStatus;
  priority: PriorityLevel;
  patient: PatientInfo;
  location: ScreeningLocation;
  workerId: string;
  workerName: string;
  originalImageUrl: string;
  imageMeta?: {
    filename: string;
    resolution: string;
    sizeKb: number;
  };
  screeningResult?: ScreeningResult;
  referral?: {
    required: boolean;
    hospital?: HospitalFacility;
    referredAt?: string;
    reason?: string;
  };
  doctorReview?: DoctorReviewDecision;
}

export interface ApiError {
  error: string;
  message: string;
  details: Record<string, any>;
}

export interface SampleImageOption {
  id: string;
  label: string;
  subtitle: string;
  category: 'normal' | 'mild' | 'moderate' | 'severe' | 'pdr' | 'invalid' | 'poor_quality';
  imageUrl: string;
  expectedGrade?: number;
  expectedStatus: 'VALID' | 'INVALID' | 'POOR_QUALITY';
}
