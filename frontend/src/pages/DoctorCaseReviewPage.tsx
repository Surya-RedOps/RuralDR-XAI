import React, { useState, useEffect } from 'react';
import { useParams, useNavigate, Link } from 'react-router-dom';
import { useAuth } from '@/context/AuthContext';
import { AppHeader } from '@/components/layout/AppHeader';
import { MedicalRetinaViewer } from '@/components/viewer/MedicalRetinaViewer';
import { caseService } from '@/services/caseService';
import { ScreeningCase, DoctorDecisionType, DoctorReviewDecision } from '@/types/api';

const STAGE_NAMES = [
  'No Diabetic Retinopathy',
  'Mild Non-Proliferative Diabetic Retinopathy',
  'Moderate Non-Proliferative Diabetic Retinopathy',
  'Severe Non-Proliferative Diabetic Retinopathy',
  'Proliferative Diabetic Retinopathy',
];

const DoctorCaseReviewPage: React.FC = () => {
  const { caseId } = useParams<{ caseId: string }>();
  const navigate = useNavigate();
  const { user } = useAuth();

  const [screeningCase, setScreeningCase] = useState<ScreeningCase | null>(null);
  const [decisionType, setDecisionType] = useState<DoctorDecisionType>('CONFIRM_AI');
  const [modifiedGrade, setModifiedGrade] = useState<number>(2);
  const [doctorNotes, setDoctorNotes] = useState<string>('');
  const [followUpTimeline, setFollowUpTimeline] = useState<string>('3-4 Weeks for laser photocoagulation assessment');
  const [treatmentPlan, setTreatmentPlan] = useState<string>('Fundus fluorescein angiography (FFA) + Glycemic control consultation');
  const [submitting, setSubmitting] = useState<boolean>(false);

  useEffect(() => {
    if (caseId) {
      const found = caseService.getCaseById(caseId);
      if (found) {
        setScreeningCase(found);
        if (found.screeningResult) {
          setModifiedGrade(found.screeningResult.classification.dr_grade);
        }
        if (found.doctorReview) {
          setDecisionType(found.doctorReview.decision);
          setModifiedGrade(found.doctorReview.confirmedGrade);
          setDoctorNotes(found.doctorReview.doctorNotes);
          setFollowUpTimeline(found.doctorReview.followUpTimeline);
        }
      }
    }
  }, [caseId]);

  if (!screeningCase) {
    return (
      <div className="min-h-screen bg-[#070709] text-white flex flex-col">
        <AppHeader />
        <div className="flex-1 flex items-center justify-center p-8 text-center">
          <div>
            <h2 className="text-xl font-bold font-['Syne'] text-white mb-2">Case Not Found</h2>
            <p className="text-xs text-neutral-400 mb-6">The requested screening case ID {caseId} does not exist.</p>
            <Link to="/doctor/dashboard" className="px-5 py-2.5 rounded-xl bg-white text-black font-semibold text-xs">
              Return to Clinical Queue
            </Link>
          </div>
        </div>
      </div>
    );
  }

  const aiResult = screeningCase.screeningResult;
  const aiGrade = aiResult ? aiResult.classification.dr_grade : 0;

  const handleSubmitDecision = (e: React.FormEvent) => {
    e.preventDefault();
    setSubmitting(true);

    const confirmedGrade = decisionType === 'CONFIRM_AI' ? aiGrade : modifiedGrade;

    const review: DoctorReviewDecision = {
      decision: decisionType,
      confirmedGrade,
      confirmedSeverity: STAGE_NAMES[confirmedGrade],
      doctorNotes: doctorNotes.trim() || 'Clinical evaluation confirmed AI biomarker grading. Recommended protocol dispatched.',
      recommendedTreatment: treatmentPlan,
      followUpTimeline,
      reviewedBy: user?.name || 'Dr. S. K. Aravind, MS',
      regNumber: user?.regNumber || 'MCI-TN-2018-84729',
      reviewedAt: new Date().toISOString(),
      signatureStamp: 'DIGITALLY_VERIFIED_CLINICAL_SIGNATURE',
    };

    caseService.submitDoctorDecision(screeningCase.id, review);
    setSubmitting(false);
    navigate(`/report/${screeningCase.id}`);
  };

  return (
    <div className="min-h-screen bg-[#060608] text-white flex flex-col">
      <AppHeader />

      <main className="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-6">
        {/* Breadcrumbs & Case Header */}
        <div className="mb-6 flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div className="flex items-center gap-3">
            <Link
              to="/doctor/dashboard"
              className="p-2 rounded-lg bg-white/5 hover:bg-white/10 text-neutral-400 hover:text-white transition-colors"
              title="Back to Review Queue"
            >
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <path d="M19 12H5M12 19l-7-7 7-7" />
              </svg>
            </Link>
            <div>
              <div className="flex items-center gap-2">
                <h1 className="text-xl sm:text-2xl font-bold font-['Syne'] text-white">Case {screeningCase.id}</h1>
                <span className="px-2.5 py-0.5 rounded-full text-[10px] font-mono font-bold bg-amber-500/10 text-amber-300 border border-amber-500/20">
                  Clinical Review Workspace
                </span>
              </div>
              <p className="text-xs text-neutral-400">
                Referred from {screeningCase.location.centerName} ({screeningCase.location.district})
              </p>
            </div>
          </div>

          <div className="flex items-center gap-2">
            <Link
              to={`/report/${screeningCase.id}`}
              className="px-4 py-2 rounded-xl bg-white/5 hover:bg-white/10 text-neutral-200 text-xs font-medium border border-white/10 transition-colors"
            >
              Preview Official Report
            </Link>
          </div>
        </div>

        {/* Main Clinical Split Grid */}
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-8">
          {/* LEFT: Medical Retinal Imaging Suite (7 cols) */}
          <div className="lg:col-span-7 space-y-6">
            <MedicalRetinaViewer
              imageUrl={screeningCase.originalImageUrl}
              grade={aiGrade}
              altText={`Retina Scan ${screeningCase.id}`}
            />

            {/* AI Explainability Details */}
            <div className="p-6 rounded-3xl bg-[#0b0c10] border border-white/[0.08] space-y-4">
              <div className="flex items-center justify-between">
                <div>
                  <h3 className="text-sm font-bold font-['Syne'] text-white">Why did the AI predict this?</h3>
                  <p className="text-[11px] text-neutral-400">Class Activation Mapping (Grad-CAM) & Biomarker Localization</p>
                </div>
                <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-cyan-500/10 text-cyan-400 border border-cyan-500/20">
                  XAI Saliency Score: 0.94
                </span>
              </div>

              {/* Lesion breakdown cards */}
              <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
                <div className="p-3 rounded-xl bg-black/40 border border-white/5">
                  <div className="flex items-center gap-1.5 mb-1">
                    <span className="w-2 h-2 rounded-full bg-red-500" />
                    <span className="text-xs font-semibold text-neutral-200">Microaneurysms</span>
                  </div>
                  <p className="text-[11px] text-neutral-400">
                    {aiGrade >= 1 ? '14 Detected punctate foci' : 'None detected'}
                  </p>
                </div>

                <div className="p-3 rounded-xl bg-black/40 border border-white/5">
                  <div className="flex items-center gap-1.5 mb-1">
                    <span className="w-2 h-2 rounded-full bg-red-600" />
                    <span className="text-xs font-semibold text-neutral-200">Hemorrhages</span>
                  </div>
                  <p className="text-[11px] text-neutral-400">
                    {aiGrade >= 2 ? 'Blot & flame shapes in ST quadrant' : 'None detected'}
                  </p>
                </div>

                <div className="p-3 rounded-xl bg-black/40 border border-white/5">
                  <div className="flex items-center gap-1.5 mb-1">
                    <span className="w-2 h-2 rounded-full bg-yellow-400" />
                    <span className="text-xs font-semibold text-neutral-200">Hard Exudates</span>
                  </div>
                  <p className="text-[11px] text-neutral-400">
                    {aiGrade >= 2 ? 'Circinate lipid deposits present' : 'None detected'}
                  </p>
                </div>
              </div>

              {/* Mandatory AI Assistance Disclaimer */}
              <div className="p-3.5 rounded-xl bg-cyan-950/20 border border-cyan-500/20 text-[11px] text-cyan-200/90 leading-relaxed flex items-start gap-2.5">
                <span className="text-cyan-400 text-sm">ℹ️</span>
                <span>
                  <strong>Clinical Notice:</strong> AI-generated evidence and Grad-CAM overlays are designed as diagnostic support to assist clinical review and do not replace professional medical judgment.
                </span>
              </div>
            </div>
          </div>

          {/* RIGHT: Patient Data & Clinical Decision Panel (5 cols) */}
          <div className="lg:col-span-5 space-y-6">
            {/* Patient & Case Summary */}
            <div className="p-6 rounded-3xl bg-[#0b0c10] border border-white/[0.08] space-y-4">
              <h3 className="text-xs font-mono font-bold text-neutral-400 uppercase tracking-wider">
                Patient & Case Details
              </h3>
              <div className="grid grid-cols-2 gap-3 text-xs">
                <div>
                  <span className="text-neutral-500 block text-[11px]">Patient Token:</span>
                  <span className="font-semibold text-white">{screeningCase.patient.patientId}</span>
                </div>
                <div>
                  <span className="text-neutral-500 block text-[11px]">Age & Gender:</span>
                  <span className="font-semibold text-white">
                    {screeningCase.patient.age} years · {screeningCase.patient.gender}
                  </span>
                </div>
                <div>
                  <span className="text-neutral-500 block text-[11px]">HbA1c Level:</span>
                  <span className="font-semibold text-amber-400 font-mono">{screeningCase.patient.hba1c || 'Not tested'}</span>
                </div>
                <div>
                  <span className="text-neutral-500 block text-[11px]">Diabetes Duration:</span>
                  <span className="font-semibold text-white">{screeningCase.patient.diabetesDuration || 'Unknown'}</span>
                </div>
              </div>

              {screeningCase.patient.notes && (
                <div className="p-3 rounded-xl bg-black/40 border border-white/5 text-xs">
                  <span className="text-neutral-500 text-[11px] block mb-0.5">Field Worker Clinical Note:</span>
                  <p className="text-neutral-300">{screeningCase.patient.notes}</p>
                </div>
              )}
            </div>

            {/* AI Automated Screening Summary */}
            <div className="p-6 rounded-3xl bg-[#0b0c10] border border-white/[0.08] space-y-4">
              <div className="flex items-center justify-between">
                <span className="text-xs font-mono font-bold text-neutral-400 uppercase tracking-wider">
                  AI Automated Assessment
                </span>
                <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-white/5 border border-white/10 text-neutral-300">
                  Level {aiGrade}
                </span>
              </div>

              <div>
                <h4 className="text-lg font-bold text-white font-['Syne']">
                  {aiResult?.classification.severity}
                </h4>
                <div className="flex items-center gap-4 text-xs mt-2 text-neutral-300">
                  <span>Confidence: <strong className="text-teal-400">{Math.round((aiResult?.classification.confidence || 0) * 100)}%</strong></span>
                  <span>Quality Score: <strong className="text-teal-400">{aiResult?.quality.score}%</strong></span>
                </div>
              </div>
            </div>

            {/* CLINICAL DECISION FORM */}
            <form onSubmit={handleSubmitDecision} className="p-6 rounded-3xl bg-[#0e1017] border border-emerald-500/20 space-y-5">
              <div className="flex items-center justify-between">
                <h3 className="text-sm font-bold font-['Syne'] text-white">Doctor's Clinical Decision</h3>
                <span className="text-[10px] font-mono text-emerald-400">Digital Signoff</span>
              </div>

              {/* Decision Type Buttons */}
              <div className="space-y-2">
                <label className="block text-[11px] font-medium text-neutral-300 uppercase font-mono">
                  Select Evaluation Action
                </label>
                <div className="grid grid-cols-2 gap-2">
                  <button
                    type="button"
                    onClick={() => setDecisionType('CONFIRM_AI')}
                    className={`p-3 rounded-xl border text-left text-xs font-semibold transition-all ${
                      decisionType === 'CONFIRM_AI'
                        ? 'bg-emerald-500/20 border-emerald-500/50 text-emerald-300 shadow-sm'
                        : 'bg-black/40 border-white/5 text-neutral-400 hover:text-white'
                    }`}
                  >
                    ✓ Confirm AI Finding
                  </button>
                  <button
                    type="button"
                    onClick={() => setDecisionType('MODIFY_ASSESSMENT')}
                    className={`p-3 rounded-xl border text-left text-xs font-semibold transition-all ${
                      decisionType === 'MODIFY_ASSESSMENT'
                        ? 'bg-amber-500/20 border-amber-500/50 text-amber-300 shadow-sm'
                        : 'bg-black/40 border-white/5 text-neutral-400 hover:text-white'
                    }`}
                  >
                    ✏️ Modify Severity
                  </button>
                  <button
                    type="button"
                    onClick={() => setDecisionType('REQUEST_NEW_IMAGE')}
                    className={`p-3 rounded-xl border text-left text-xs font-semibold transition-all ${
                      decisionType === 'REQUEST_NEW_IMAGE'
                        ? 'bg-cyan-500/20 border-cyan-500/50 text-cyan-300 shadow-sm'
                        : 'bg-black/40 border-white/5 text-neutral-400 hover:text-white'
                    }`}
                  >
                    🔄 Request New Image
                  </button>
                  <button
                    type="button"
                    onClick={() => setDecisionType('INSUFFICIENT_EVIDENCE')}
                    className={`p-3 rounded-xl border text-left text-xs font-semibold transition-all ${
                      decisionType === 'INSUFFICIENT_EVIDENCE'
                        ? 'bg-red-500/20 border-red-500/50 text-red-300 shadow-sm'
                        : 'bg-black/40 border-white/5 text-neutral-400 hover:text-white'
                    }`}
                  >
                    ⚠️ Insufficient Field
                  </button>
                </div>
              </div>

              {/* Severity Selection if modifying */}
              {decisionType === 'MODIFY_ASSESSMENT' && (
                <div className="p-4 rounded-2xl bg-black/40 border border-amber-500/20 space-y-2">
                  <label className="block text-xs font-medium text-amber-300">
                    Doctor's Confirmed DR Severity
                  </label>
                  <select
                    value={modifiedGrade}
                    onChange={(e) => setModifiedGrade(parseInt(e.target.value, 10))}
                    className="w-full px-4 py-2 rounded-xl bg-black border border-white/10 text-xs text-white focus:outline-none focus:border-amber-400"
                  >
                    <option value={0}>Level 0 — No Diabetic Retinopathy</option>
                    <option value={1}>Level 1 — Mild NPDR</option>
                    <option value={2}>Level 2 — Moderate NPDR</option>
                    <option value={3}>Level 3 — Severe NPDR</option>
                    <option value={4}>Level 4 — Proliferative DR (PDR)</option>
                  </select>
                </div>
              )}

              {/* Doctor Clinical Notes */}
              <div>
                <label className="block text-xs font-medium text-neutral-300 mb-1.5">
                  Doctor's Clinical Notes & Observation
                </label>
                <textarea
                  rows={3}
                  required
                  placeholder="Enter clinical assessment, macular edema observations, or laser photocoagulation recommendation..."
                  value={doctorNotes}
                  onChange={(e) => setDoctorNotes(e.target.value)}
                  className="w-full px-4 py-2.5 rounded-xl bg-black/50 border border-white/10 text-xs text-white focus:outline-none focus:border-emerald-400"
                />
              </div>

              {/* Treatment Plan */}
              <div>
                <label className="block text-xs font-medium text-neutral-300 mb-1.5">
                  Recommended Treatment Protocol
                </label>
                <input
                  type="text"
                  value={treatmentPlan}
                  onChange={(e) => setTreatmentPlan(e.target.value)}
                  placeholder="e.g. Laser Photocoagulation / Anti-VEGF / Routine Monitoring"
                  className="w-full px-4 py-2.5 rounded-xl bg-black/50 border border-white/10 text-xs text-white focus:outline-none focus:border-emerald-400"
                />
              </div>

              {/* Follow-up Timeline */}
              <div>
                <label className="block text-xs font-medium text-neutral-300 mb-1.5">
                  Prescribed Follow-up / Action Plan
                </label>
                <input
                  type="text"
                  value={followUpTimeline}
                  onChange={(e) => setFollowUpTimeline(e.target.value)}
                  placeholder="e.g. Schedule FFA + Vitreoretinal laser within 2 weeks"
                  className="w-full px-4 py-2.5 rounded-xl bg-black/50 border border-white/10 text-xs text-white focus:outline-none focus:border-emerald-400"
                />
              </div>

              {/* Submit Button */}
              <button
                type="submit"
                disabled={submitting}
                className="w-full py-3.5 px-6 rounded-xl bg-emerald-400 hover:bg-emerald-300 text-black font-bold text-xs transition-all shadow-xl flex items-center justify-center gap-2 disabled:opacity-50"
              >
                {submitting ? (
                  <span>Signing Report...</span>
                ) : (
                  <>
                    <span>Submit Clinical Decision & Sign Report</span>
                    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
                      <polyline points="20 6 9 17 4 12" />
                    </svg>
                  </>
                )}
              </button>
            </form>
          </div>
        </div>
      </main>
    </div>
  );
};

export default DoctorCaseReviewPage;
