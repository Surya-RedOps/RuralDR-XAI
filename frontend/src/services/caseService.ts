/**
 * Case Registry & Clinical State Management Service
 * Manages screening cases, persistence, status transitions, doctor queues, and referral states.
 */

import { ScreeningCase, DoctorReviewDecision } from '@/types/api';
import {
  MODERATE_NPDR_FUNDUS_SVG,
  NORMAL_FUNDUS_SVG,
  SEVERE_NPDR_FUNDUS_SVG,
  PDR_FUNDUS_SVG,
} from './sampleAssets';

const CASES_STORAGE_KEY = 'ruraldr_cases_store_v1';

// Initial pre-seeded cases for realistic prototype demonstrations
const SEEDED_CASES: ScreeningCase[] = [
  {
    id: 'RDX-1048',
    createdAt: new Date(Date.now() - 8 * 60 * 1000).toISOString(), // 8 mins ago
    updatedAt: new Date(Date.now() - 8 * 60 * 1000).toISOString(),
    status: 'REFERRED',
    priority: 'HIGH',
    patient: {
      patientId: 'PID-9082',
      age: 58,
      gender: 'Male',
      screeningDate: new Date().toISOString().split('T')[0],
      hba1c: '9.4%',
      diabetesDuration: '11 years',
      notes: 'Complains of mild blurred vision in right eye. Irregular glycemic control.',
    },
    location: {
      state: 'Tamil Nadu',
      district: 'Coimbatore',
      centerName: 'Community Health Centre — Pollachi',
    },
    workerId: 'HW-TN-4091',
    workerName: 'Lakshmi Narayanan, ANM',
    originalImageUrl: SEVERE_NPDR_FUNDUS_SVG,
    imageMeta: {
      filename: 'fundus_scan_9082.png',
      resolution: '2048x2048',
      sizeKb: 2840,
    },
    screeningResult: {
      case_id: 'RDX-1048',
      image_url: SEVERE_NPDR_FUNDUS_SVG,
      validation: {
        isValidFundus: true,
        qualityScore: 92,
        fieldVisibilityPct: 95,
        blurLevel: 'Low',
        illumination: 'Uniform',
      },
      quality: {
        status: 'GRADEABLE',
        score: 92,
        message: 'High clarity. Disc & macula fully evaluable.',
      },
      classification: {
        dr_grade: 3,
        severity: 'Severe Non-Proliferative Diabetic Retinopathy',
        confidence: 0.91,
        class_probabilities: [0.01, 0.03, 0.05, 0.91, 0.0],
        is_referable: true,
      },
      gradcam: {
        is_valid: true,
        target_class: 3,
        target_class_name: 'Severe NPDR',
        activation_coverage: 0.34,
        peak_intensity: 0.94,
        quality_flags: ['High diagnostic concordance'],
        overlay_url: '',
      },
      segmentation: {
        lesions: [
          {
            type: 'Microaneurysms',
            detected: true,
            num_regions: 24,
            area_pct: 2.4,
            confidence: 0.92,
            mask_url: '',
            color: '#ff1744',
          },
          {
            type: 'Hemorrhages',
            detected: true,
            num_regions: 18,
            area_pct: 4.8,
            confidence: 0.91,
            mask_url: '',
            color: '#dc2626',
          },
          {
            type: 'Cotton Wool Spots',
            detected: true,
            num_regions: 5,
            area_pct: 1.6,
            confidence: 0.88,
            mask_url: '',
            color: '#38bdf8',
          },
        ],
        input_resolution: '1024x1024',
      },
      safety: {
        fundusVerified: true,
        qualityAcceptable: true,
        confidenceAcceptable: true,
        explanationGenerated: true,
        highUncertaintyWarning: false,
      },
      processing_times: {
        quality_gate_ms: 220,
        classification_ms: 360,
        gradcam_ms: 290,
        segmentation_ms: 410,
        total_ms: 1280,
      },
      evidence_report: {
        primaryEvidence: 'Extensive 4-quadrant flame hemorrhages and soft cotton wool infarctions.',
        recommendedFollowup: 'Urgent referral for fluorescein angiography and panretinal photocoagulation assessment.',
      },
    },
    referral: {
      required: true,
      referredAt: new Date(Date.now() - 8 * 60 * 1000).toISOString(),
      reason: 'Automated AI referral for Level 3 Severe NPDR',
      hospital: {
        id: 'HOSP-CBE-01',
        name: 'Government Hospital & Medical College, Coimbatore',
        district: 'Coimbatore',
        state: 'Tamil Nadu',
        distanceKm: 28.4,
        ophthalmologistOnDuty: 'Dr. R. Meenakshi (Retina Specialist)',
        bedAvailability: '14 Ophthalmology Beds Available',
        specialization: 'Tertiary Eye Care & Laser Photocoagulation Unit',
        contactNumber: '+91 422 2301300',
        isVerified: true,
      },
    },
  },
  {
    id: 'RDX-1046',
    createdAt: new Date(Date.now() - 32 * 60 * 1000).toISOString(), // 32 mins ago
    updatedAt: new Date(Date.now() - 32 * 60 * 1000).toISOString(),
    status: 'REFERRED',
    priority: 'MEDIUM',
    patient: {
      patientId: 'PID-8841',
      age: 52,
      gender: 'Female',
      screeningDate: new Date().toISOString().split('T')[0],
      hba1c: '8.1%',
      diabetesDuration: '6 years',
      notes: 'Routine rural screening camp. Asymptomatic visual acuity 6/9.',
    },
    location: {
      state: 'Tamil Nadu',
      district: 'Coimbatore',
      centerName: 'Rural Primary Health Centre — Valparai',
    },
    workerId: 'HW-TN-4091',
    workerName: 'Lakshmi Narayanan, ANM',
    originalImageUrl: MODERATE_NPDR_FUNDUS_SVG,
    imageMeta: {
      filename: 'valparai_scan_8841.jpg',
      resolution: '1536x1536',
      sizeKb: 1980,
    },
    screeningResult: {
      case_id: 'RDX-1046',
      image_url: MODERATE_NPDR_FUNDUS_SVG,
      validation: {
        isValidFundus: true,
        qualityScore: 94,
        fieldVisibilityPct: 96,
        blurLevel: 'Low',
        illumination: 'Uniform',
      },
      quality: {
        status: 'GRADEABLE',
        score: 94,
        message: 'Excellent quality fundus photograph.',
      },
      classification: {
        dr_grade: 2,
        severity: 'Moderate Non-Proliferative Diabetic Retinopathy',
        confidence: 0.87,
        class_probabilities: [0.03, 0.08, 0.87, 0.02, 0.0],
        is_referable: true,
      },
      gradcam: {
        is_valid: true,
        target_class: 2,
        target_class_name: 'Moderate NPDR',
        activation_coverage: 0.28,
        peak_intensity: 0.91,
        quality_flags: ['High diagnostic concordance'],
        overlay_url: '',
      },
      segmentation: {
        lesions: [
          {
            type: 'Microaneurysms',
            detected: true,
            num_regions: 14,
            area_pct: 1.2,
            confidence: 0.9,
            mask_url: '',
            color: '#ff1744',
          },
          {
            type: 'Hemorrhages',
            detected: true,
            num_regions: 6,
            area_pct: 1.9,
            confidence: 0.87,
            mask_url: '',
            color: '#dc2626',
          },
          {
            type: 'Hard Exudates',
            detected: true,
            num_regions: 8,
            area_pct: 1.1,
            confidence: 0.86,
            mask_url: '',
            color: '#fbc02d',
          },
        ],
        input_resolution: '1024x1024',
      },
      safety: {
        fundusVerified: true,
        qualityAcceptable: true,
        confidenceAcceptable: true,
        explanationGenerated: true,
        highUncertaintyWarning: false,
      },
      processing_times: {
        quality_gate_ms: 210,
        classification_ms: 340,
        gradcam_ms: 280,
        segmentation_ms: 390,
        total_ms: 1220,
      },
      evidence_report: {
        primaryEvidence: 'Blot hemorrhages and circinate lipid exudates in superior temporal arcade.',
        recommendedFollowup: 'Ophthalmologist consultation within 1 month.',
      },
    },
    referral: {
      required: true,
      referredAt: new Date(Date.now() - 32 * 60 * 1000).toISOString(),
      reason: 'AI Level 2 Moderate NPDR Detection',
      hospital: {
        id: 'HOSP-CBE-02',
        name: 'District Eye Hospital, Pollachi Sub-Division',
        district: 'Coimbatore',
        state: 'Tamil Nadu',
        distanceKm: 14.2,
        ophthalmologistOnDuty: 'Dr. V. Sundaram (Vitreoretinal Consultant)',
        bedAvailability: '8 Beds Available',
        specialization: 'Diabetic Retinopathy Screening & Anti-VEGF Clinic',
        contactNumber: '+91 4259 223400',
        isVerified: true,
      },
    },
  },
  {
    id: 'RDX-1044',
    createdAt: new Date(Date.now() - 24 * 3600 * 1000).toISOString(), // Yesterday
    updatedAt: new Date(Date.now() - 24 * 3600 * 1000).toISOString(),
    status: 'DOCTOR_REVIEW',
    priority: 'CRITICAL',
    patient: {
      patientId: 'PID-7301',
      age: 64,
      gender: 'Male',
      screeningDate: '2026-09-01',
      hba1c: '10.2%',
      diabetesDuration: '18 years',
      notes: 'Severe vision loss reported in left eye over past 2 weeks.',
    },
    location: {
      state: 'Tamil Nadu',
      district: 'Salem',
      centerName: 'Rural Health Centre — Omalur',
    },
    workerId: 'HW-TN-4091',
    workerName: 'Lakshmi Narayanan, ANM',
    originalImageUrl: PDR_FUNDUS_SVG,
    screeningResult: {
      case_id: 'RDX-1044',
      image_url: PDR_FUNDUS_SVG,
      validation: {
        isValidFundus: true,
        qualityScore: 90,
        fieldVisibilityPct: 94,
        blurLevel: 'Low',
        illumination: 'Uniform',
      },
      quality: {
        status: 'GRADEABLE',
        score: 90,
        message: 'High resolution fundus field.',
      },
      classification: {
        dr_grade: 4,
        severity: 'Proliferative Diabetic Retinopathy',
        confidence: 0.95,
        class_probabilities: [0.0, 0.01, 0.02, 0.02, 0.95],
        is_referable: true,
      },
      gradcam: {
        is_valid: true,
        target_class: 4,
        target_class_name: 'PDR',
        activation_coverage: 0.42,
        peak_intensity: 0.97,
        quality_flags: ['Critical risk flag'],
        overlay_url: '',
      },
      segmentation: {
        lesions: [
          {
            type: 'Neovascularization',
            detected: true,
            num_regions: 8,
            area_pct: 3.8,
            confidence: 0.94,
            mask_url: '',
            color: '#ef4444',
          },
          {
            type: 'Preretinal Hemorrhage',
            detected: true,
            num_regions: 2,
            area_pct: 7.2,
            confidence: 0.96,
            mask_url: '',
            color: '#991b1b',
          },
        ],
        input_resolution: '1024x1024',
      },
      safety: {
        fundusVerified: true,
        qualityAcceptable: true,
        confidenceAcceptable: true,
        explanationGenerated: true,
        highUncertaintyWarning: false,
      },
      processing_times: {
        quality_gate_ms: 240,
        classification_ms: 390,
        gradcam_ms: 310,
        segmentation_ms: 430,
        total_ms: 1370,
      },
      evidence_report: {
        primaryEvidence: 'Fragile neovascular vessels at disc with superior preretinal hemorrhage.',
        recommendedFollowup: 'Urgent vitreoretinal surgical review and anti-VEGF injection.',
      },
    },
    referral: {
      required: true,
      referredAt: new Date(Date.now() - 24 * 3600 * 1000).toISOString(),
      hospital: {
        id: 'HOSP-SLM-01',
        name: 'Government Mohan Kumaramangalam Medical College Hospital, Salem',
        district: 'Salem',
        state: 'Tamil Nadu',
        distanceKm: 18.6,
        ophthalmologistOnDuty: 'Dr. A. Balamurugan (Senior Retina Specialist)',
        bedAvailability: '12 Beds Available',
        specialization: 'Diabetic Retinopathy Management & Laser Photocoagulation',
        contactNumber: '+91 427 2447190',
        isVerified: true,
      },
    },
  },
  {
    id: 'RDX-1042',
    createdAt: new Date(Date.now() - 2 * 3600 * 1000).toISOString(),
    updatedAt: new Date(Date.now() - 2 * 3600 * 1000).toISOString(),
    status: 'COMPLETED',
    priority: 'LOW',
    patient: {
      patientId: 'PID-5120',
      age: 46,
      gender: 'Female',
      screeningDate: new Date().toISOString().split('T')[0],
      hba1c: '6.4%',
      diabetesDuration: '2 years',
      notes: 'Annual routine diabetic screening. Good glycemic control.',
    },
    location: {
      state: 'Tamil Nadu',
      district: 'Coimbatore',
      centerName: 'Upgraded Primary Health Centre — Sulur',
    },
    workerId: 'HW-TN-4091',
    workerName: 'Lakshmi Narayanan, ANM',
    originalImageUrl: NORMAL_FUNDUS_SVG,
    screeningResult: {
      case_id: 'RDX-1042',
      image_url: NORMAL_FUNDUS_SVG,
      validation: {
        isValidFundus: true,
        qualityScore: 98,
        fieldVisibilityPct: 99,
        blurLevel: 'Low',
        illumination: 'Uniform',
      },
      quality: {
        status: 'GRADEABLE',
        score: 98,
        message: 'Crystal clear fundus view.',
      },
      classification: {
        dr_grade: 0,
        severity: 'No Diabetic Retinopathy',
        confidence: 0.96,
        class_probabilities: [0.96, 0.02, 0.01, 0.01, 0.0],
        is_referable: false,
      },
      gradcam: {
        is_valid: true,
        target_class: 0,
        target_class_name: 'No DR',
        activation_coverage: 0.05,
        peak_intensity: 0.3,
        quality_flags: ['Normal baseline'],
        overlay_url: '',
      },
      segmentation: {
        lesions: [],
        input_resolution: '1024x1024',
      },
      safety: {
        fundusVerified: true,
        qualityAcceptable: true,
        confidenceAcceptable: true,
        explanationGenerated: true,
        highUncertaintyWarning: false,
      },
      processing_times: {
        quality_gate_ms: 190,
        classification_ms: 320,
        gradcam_ms: 250,
        segmentation_ms: 340,
        total_ms: 1100,
      },
      evidence_report: {
        primaryEvidence: 'Healthy retinal vasculature. No microaneurysms, exudates, or hemorrhages.',
        recommendedFollowup: 'Routine annual retinal checkup after 12 months.',
      },
    },
    referral: {
      required: false,
    },
  },
];

function loadCasesFromStorage(): ScreeningCase[] {
  try {
    const raw = localStorage.getItem(CASES_STORAGE_KEY);
    if (raw) {
      const parsed = JSON.parse(raw);
      if (Array.isArray(parsed) && parsed.length > 0) {
        return parsed;
      }
    }
  } catch {
    // fallback
  }
  // Store seeds if empty
  localStorage.setItem(CASES_STORAGE_KEY, JSON.stringify(SEEDED_CASES));
  return SEEDED_CASES;
}

function saveCasesToStorage(cases: ScreeningCase[]) {
  try {
    localStorage.setItem(CASES_STORAGE_KEY, JSON.stringify(cases));
  } catch (err) {
    console.error('Failed to save cases to localStorage', err);
  }
}

export const caseService = {
  getAllCases(): ScreeningCase[] {
    return loadCasesFromStorage();
  },

  getCaseById(id: string): ScreeningCase | null {
    const cases = loadCasesFromStorage();
    return cases.find((c) => c.id === id) || null;
  },

  createCase(newCase: ScreeningCase): ScreeningCase {
    const cases = loadCasesFromStorage();
    const updated = [newCase, ...cases];
    saveCasesToStorage(updated);
    return newCase;
  },

  updateCase(id: string, updates: Partial<ScreeningCase>): ScreeningCase {
    const cases = loadCasesFromStorage();
    const idx = cases.findIndex((c) => c.id === id);
    if (idx === -1) {
      throw new Error(`Case ${id} not found`);
    }

    const updatedCase: ScreeningCase = {
      ...cases[idx],
      ...updates,
      updatedAt: new Date().toISOString(),
    };

    cases[idx] = updatedCase;
    saveCasesToStorage(cases);
    return updatedCase;
  },

  submitDoctorDecision(caseId: string, decision: DoctorReviewDecision): ScreeningCase {
    return this.updateCase(caseId, {
      status: 'CLINICAL_DECISION',
      doctorReview: decision,
    });
  },

  generateNextCaseId(): string {
    const cases = loadCasesFromStorage();
    const maxNum = cases.reduce((max, c) => {
      const match = c.id.match(/RDX-(\d+)/);
      if (match) {
        const n = parseInt(match[1], 10);
        return n > max ? n : max;
      }
      return max;
    }, 1048);

    return `RDX-${maxNum + 1}`;
  },

  getWorkerMetrics() {
    const cases = loadCasesFromStorage();
    const todayStr = new Date().toISOString().split('T')[0];
    const todayCases = cases.filter((c) => c.createdAt.startsWith(todayStr));

    return {
      todayScreenings: todayCases.length,
      pendingReview: cases.filter((c) => c.status === 'REFERRED' || c.status === 'DOCTOR_REVIEW').length,
      referredCases: cases.filter((c) => c.referral?.required === true).length,
      completedCases: cases.filter((c) => c.status === 'COMPLETED' || c.status === 'CLINICAL_DECISION' || c.status === 'NO_REFERRAL').length,
    };
  },

  getDoctorMetrics() {
    const cases = loadCasesFromStorage();
    return {
      urgentCases: cases.filter(
        (c) => (c.priority === 'CRITICAL' || c.priority === 'HIGH') && c.status !== 'COMPLETED' && c.status !== 'CLINICAL_DECISION'
      ).length,
      newReferrals: cases.filter((c) => c.status === 'REFERRED').length,
      underReview: cases.filter((c) => c.status === 'DOCTOR_REVIEW').length,
      completed: cases.filter((c) => c.status === 'COMPLETED' || c.status === 'CLINICAL_DECISION').length,
    };
  },
};
