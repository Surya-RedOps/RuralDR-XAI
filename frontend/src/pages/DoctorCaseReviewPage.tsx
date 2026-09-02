import React, { useState, useEffect } from 'react';
import { useParams, useNavigate, Link } from 'react-router-dom';
import { useAuth } from '@/context/AuthContext';
import { AppHeader } from '@/components/layout/AppHeader';
import { MedicalRetinaViewer } from '@/components/viewer/MedicalRetinaViewer';
import RetinaScene from '@/components/3d/RetinaScene';
import { caseService } from '@/services/caseService';
import { DoctorDecisionType, DoctorReviewDecision } from '@/types/api';

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

  const [caseData, setCaseData] = useState<any | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [show3dView, setShow3dView] = useState<boolean>(false);
  const [decisionType, setDecisionType] = useState<DoctorDecisionType>('CONFIRM_AI');
  const [modifiedGrade, setModifiedGrade] = useState<number>(2);
  const [doctorNotes, setDoctorNotes] = useState<string>('');
  const [followUpTimeline, setFollowUpTimeline] = useState<string>('3-4 Weeks for vitreoretinal evaluation');
  const [treatmentPlan, setTreatmentPlan] = useState<string>('Fundus fluorescein angiography (FFA) + Glycemic control consultation');
  const [submitting, setSubmitting] = useState<boolean>(false);

  useEffect(() => {
    if (caseId) {
      setLoading(true);
      caseService
        .getDoctorCaseDetail(caseId)
        .then((data) => {
          setCaseData(data);
          if (data.aiPrediction) {
            setModifiedGrade(data.aiPrediction.dr_grade);
          }
          if (data.doctorReview) {
            setDecisionType(data.doctorReview.decision as DoctorDecisionType);
            setModifiedGrade(data.doctorReview.confirmedGrade);
            setDoctorNotes(data.doctorReview.doctorNotes || '');
            setFollowUpTimeline(data.doctorReview.followUpTimeline || '');
            setTreatmentPlan(data.doctorReview.recommendedTreatment || '');
          }
        })
        .catch((err) => {
          console.error('Failed to load case detail:', err);
        })
        .finally(() => {
          setLoading(false);
        });
    }
  }, [caseId]);

  if (loading) {
    return (
      <div className="min-h-screen bg-[#070709] text-white flex flex-col">
        <AppHeader />
        <div className="flex-1 flex items-center justify-center p-8 text-center">
          <div>
            <div className="w-10 h-10 border-2 border-emerald-500 border-t-transparent rounded-full animate-spin mx-auto mb-4" />
            <p className="text-xs text-neutral-400 font-mono">Loading case data from clinical server...</p>
          </div>
        </div>
      </div>
    );
  }

  if (!caseData) {
    return (
      <div className="min-h-screen bg-[#070709] text-white flex flex-col">
        <AppHeader />
        <div className="flex-1 flex items-center justify-center p-8 text-center">
          <div>
            <h2 className="text-xl font-bold font-['Syne'] text-white mb-2">Case Not Found</h2>
            <p className="text-xs text-neutral-400 mb-6">The requested screening case ID {caseId} does not exist in the database.</p>
            <Link to="/doctor/dashboard" className="px-5 py-2.5 rounded-xl bg-white text-black font-semibold text-xs">
              Return to Clinical Queue
            </Link>
          </div>
        </div>
      </div>
    );
  }

  const aiPred = caseData.aiPrediction;
  const aiGrade = aiPred ? aiPred.dr_grade : 0;

  const handleSubmitDecision = async (e: React.FormEvent) => {
    e.preventDefault();
    setSubmitting(true);

    const confirmedGrade = decisionType === 'CONFIRM_AI' ? aiGrade : modifiedGrade;

    const review: DoctorReviewDecision = {
      decision: decisionType,
      confirmedGrade,
      confirmedSeverity: STAGE_NAMES[confirmedGrade],
      doctorNotes: doctorNotes.trim() || 'Clinical evaluation confirmed AI biomarker grading. Protocol dispatched.',
      recommendedTreatment: treatmentPlan,
      followUpTimeline,
      reviewedBy: user?.name || 'Dr. S. K. Aravind, MS',
      regNumber: user?.regNumber || 'MCI-TN-2018-84729',
      reviewedAt: new Date().toISOString(),
    };

    try {
      await caseService.submitDoctorDecision(caseData.id, review);
      navigate(`/report/${caseData.id}`);
    } catch (err) {
      console.error('Failed to submit decision:', err);
      alert('Failed to submit decision. Please try again.');
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="min-h-screen bg-[#060608] text-white flex flex-col">
      <AppHeader />

      <main className="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-6">
        {/* Breadcrumbs & Header */}
        <div className="mb-6 flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div className="flex items-center gap-3">
            <Link
              to="/doctor/dashboard"
              className="px-3 py-1.5 rounded-xl bg-white/5 hover:bg-white/10 text-neutral-400 hover:text-white text-xs transition-colors flex items-center gap-1.5"
            >
              <span>←</span>
              <span>Queue</span>
            </Link>
            <div>
              <div className="flex items-center gap-2">
                <h1 className="text-xl sm:text-2xl font-bold font-['Syne'] text-white">
                  Case Review: {caseData.id}
                </h1>
                <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-emerald-500/10 border border-emerald-500/30 text-emerald-400">
                  {caseData.status}
                </span>
              </div>
              <p className="text-xs text-neutral-400 mt-0.5">
                Patient: <span className="text-white font-mono">{caseData.patientId}</span> ({caseData.age} yrs · {caseData.gender}) · {caseData.location.district}
              </p>
            </div>
          </div>

          <div className="flex items-center gap-3">
            <button
              onClick={() => setShow3dView(!show3dView)}
              className={`px-3 py-2 rounded-xl text-xs font-medium border transition-colors flex items-center gap-2 ${
                show3dView
                  ? 'bg-teal-500/20 text-teal-300 border-teal-500/40'
                  : 'bg-white/5 text-neutral-300 hover:text-white border-white/10'
              }`}
            >
              <span>🌐</span>
              <span>{show3dView ? 'Hide 3D Experience' : 'Auxiliary 3D View'}</span>
            </button>
          </div>
        </div>

        {/* Main 2-Column Clinical Layout */}
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
          {/* Left Column: Medical Retina Viewer & AI Findings (7 cols) */}
          <div className="lg:col-span-7 space-y-6">
            {/* Interactive Retinal Viewer */}
            <div className="rounded-3xl bg-[#0a0a0e] border border-white/[0.08] p-4 sm:p-6 overflow-hidden">
              <div className="flex items-center justify-between mb-4">
                <h2 className="text-sm font-semibold text-white font-['Syne']">Interactive Retinal Viewer</h2>
                <span className="text-[10px] font-mono text-neutral-400">Resolution: {caseData.imageMeta?.resolution || '1024x1024'}</span>
              </div>

              <MedicalRetinaViewer
                imageUrl={caseData.originalImageUrl}
                gradCamUrl={aiPred?.gradcam_url}
                grade={aiGrade}
                className="w-full"
              />
            </div>

            {/* Auxiliary 3D Retinal Visualization */}
            {show3dView && (
              <div className="rounded-3xl bg-[#0a0a0e] border border-teal-500/20 p-6 overflow-hidden">
                <div className="flex items-center justify-between mb-3">
                  <div>
                    <h3 className="text-sm font-semibold text-teal-300 font-['Syne']">3D Retinal Experience (Anatomical View)</h3>
                    <p className="text-[11px] text-neutral-400">Auxiliary spherical mapping of fundus curvature and vascular branching</p>
                  </div>
                  <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-teal-500/10 text-teal-400">Three.js WebGL</span>
                </div>
                <div className="h-64 w-full rounded-2xl bg-black border border-white/5 overflow-hidden">
                  <RetinaScene />
                </div>
              </div>
            )}

            {/* AI Explanation & Evidence Breakdown */}
            <div className="rounded-3xl bg-[#0a0a0e] border border-white/[0.08] p-6">
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-sm font-semibold text-white font-['Syne']">AI Diagnostic Evidence</h3>
                <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-white/5 border border-white/10 text-teal-400">
                  Confidence: {Math.round((aiPred?.confidence || 0.9) * 100)}%
                </span>
              </div>

              <div className="p-4 rounded-2xl bg-white/[0.02] border border-white/5 mb-4">
                <p className="text-xs text-neutral-300 leading-relaxed">
                  <span className="font-semibold text-white">Triage Assessment: </span>
                  {aiPred?.triage_decision || 'Clinical screening completed.'}
                </p>
              </div>

              {/* Detected Lesions */}
              <div className="space-y-2 mb-4">
                <p className="text-[11px] font-mono text-neutral-400 uppercase">Biomarker Findings</p>
                {aiPred?.lesions && aiPred.lesions.length > 0 ? (
                  <div className="grid grid-cols-2 gap-2">
                    {aiPred.lesions.map((l: any, idx: number) => (
                      <div key={idx} className="p-2.5 rounded-xl bg-black/40 border border-white/5 flex items-center justify-between text-xs">
                        <span className="text-neutral-300">{l.type}</span>
                        <span className="font-mono text-teal-400 font-semibold">{l.count || 'Detected'}</span>
                      </div>
                    ))}
                  </div>
                ) : (
                  <p className="text-xs text-neutral-500 italic">No microaneurysms, hemorrhages, or exudates detected.</p>
                )}
              </div>

              <p className="text-[10px] text-neutral-500 italic">
                ⚠️ AI-generated evidence is intended solely to assist clinical triage. Final clinical diagnosis is established by the reviewing ophthalmologist.
              </p>
            </div>
          </div>

          {/* Right Column: Case Summary & Doctor Decision Form (5 cols) */}
          <div className="lg:col-span-5 space-y-6">
            {/* AI Prediction Summary Card */}
            <div className="rounded-3xl bg-[#0a0a0e] border border-white/[0.08] p-6">
              <p className="text-[11px] font-mono text-neutral-400 uppercase mb-2">AI Initial Assessment</p>
              <div className="p-4 rounded-2xl bg-gradient-to-br from-teal-950/30 via-black to-black border border-teal-500/20 mb-4">
                <p className="text-xs text-teal-400 font-mono mb-1">GRADE {aiGrade}</p>
                <h3 className="text-lg font-bold font-['Syne'] text-white">{aiPred?.severity || 'No DR'}</h3>
                <div className="mt-3 flex items-center gap-4 text-xs font-mono text-neutral-400">
                  <span>AI Confidence: <strong className="text-teal-300">{Math.round((aiPred?.confidence || 0.9) * 100)}%</strong></span>
                  <span>FIQA Quality: <strong className="text-white">{aiPred?.quality_score || 92}%</strong></span>
                </div>
              </div>

              <div className="space-y-2 text-xs text-neutral-400 border-t border-white/5 pt-4">
                <div className="flex justify-between">
                  <span>Referring PHC:</span>
                  <span className="text-neutral-200">{caseData.location.centerName}</span>
                </div>
                <div className="flex justify-between">
                  <span>Health Worker:</span>
                  <span className="text-neutral-200">{caseData.workerName}</span>
                </div>
                <div className="flex justify-between">
                  <span>Clinical Notes:</span>
                  <span className="text-neutral-200 text-right max-w-[200px] truncate">{caseData.notes || 'Routine screening'}</span>
                </div>
              </div>
            </div>

            {/* Doctor Decision Form */}
            <form onSubmit={handleSubmitDecision} className="rounded-3xl bg-[#0a0a0e] border border-white/[0.08] p-6 space-y-5">
              <div>
                <h3 className="text-base font-bold font-['Syne'] text-white mb-1">Clinical Decision & Action</h3>
                <p className="text-xs text-neutral-400">Confirm or adjust the AI grading and provide management advice.</p>
              </div>

              {/* Decision Type Radio Options */}
              <div className="space-y-2">
                <label className="text-[11px] font-mono text-neutral-400 uppercase">Review Action</label>
                <div className="grid grid-cols-1 gap-2">
                  {[
                    { id: 'CONFIRM_AI', label: 'Confirm AI Assessment' },
                    { id: 'MODIFY_ASSESSMENT', label: 'Modify Assessment Grade' },
                    { id: 'REQUEST_NEW_IMAGE', label: 'Request New Image / Recapture' },
                    { id: 'INSUFFICIENT_EVIDENCE', label: 'Insufficient Evidence' },
                  ].map((opt) => (
                    <label
                      key={opt.id}
                      className={`flex items-center gap-3 p-3 rounded-xl border text-xs cursor-pointer transition-all ${
                        decisionType === opt.id
                          ? 'bg-emerald-500/10 border-emerald-500/40 text-white font-semibold'
                          : 'bg-black/30 border-white/5 text-neutral-400 hover:text-white'
                      }`}
                    >
                      <input
                        type="radio"
                        name="decisionType"
                        value={opt.id}
                        checked={decisionType === opt.id}
                        onChange={() => setDecisionType(opt.id as DoctorDecisionType)}
                        className="accent-emerald-500"
                      />
                      <span>{opt.label}</span>
                    </label>
                  ))}
                </div>
              </div>

              {/* Modified Grade Selector (if modifying) */}
              {decisionType === 'MODIFY_ASSESSMENT' && (
                <div className="space-y-2 p-3 rounded-2xl bg-black/40 border border-white/10">
                  <label className="text-[11px] font-mono text-neutral-300">Select Confirmed DR Grade</label>
                  <select
                    value={modifiedGrade}
                    onChange={(e) => setModifiedGrade(parseInt(e.target.value))}
                    className="w-full bg-[#111116] border border-white/10 rounded-xl px-3 py-2 text-xs text-white focus:outline-none focus:border-emerald-500"
                  >
                    {STAGE_NAMES.map((name, idx) => (
                      <option key={idx} value={idx}>
                        Grade {idx} — {name}
                      </option>
                    ))}
                  </select>
                </div>
              )}

              {/* Doctor Clinical Notes */}
              <div className="space-y-2">
                <label className="text-[11px] font-mono text-neutral-400 uppercase">Ophthalmologist Notes</label>
                <textarea
                  rows={3}
                  value={doctorNotes}
                  onChange={(e) => setDoctorNotes(e.target.value)}
                  placeholder="Enter clinical observations, macular edema threat, or specific instructions for PHC..."
                  className="w-full bg-[#111116] border border-white/10 rounded-xl p-3 text-xs text-white placeholder-neutral-500 focus:outline-none focus:border-emerald-500"
                />
              </div>

              {/* Treatment / Management Plan */}
              <div className="space-y-2">
                <label className="text-[11px] font-mono text-neutral-400 uppercase">Recommended Management</label>
                <input
                  type="text"
                  value={treatmentPlan}
                  onChange={(e) => setTreatmentPlan(e.target.value)}
                  placeholder="e.g. FFA + Panretinal Photocoagulation assessment"
                  className="w-full bg-[#111116] border border-white/10 rounded-xl px-3 py-2 text-xs text-white placeholder-neutral-500 focus:outline-none focus:border-emerald-500"
                />
              </div>

              {/* Follow-up Timeline */}
              <div className="space-y-2">
                <label className="text-[11px] font-mono text-neutral-400 uppercase">Follow-up Timeline</label>
                <input
                  type="text"
                  value={followUpTimeline}
                  onChange={(e) => setFollowUpTimeline(e.target.value)}
                  placeholder="e.g. 3-4 Weeks / Immediate / 6 Months"
                  className="w-full bg-[#111116] border border-white/10 rounded-xl px-3 py-2 text-xs text-white placeholder-neutral-500 focus:outline-none focus:border-emerald-500"
                />
              </div>

              <button
                type="submit"
                disabled={submitting}
                className="w-full py-3.5 rounded-2xl bg-emerald-500 hover:bg-emerald-400 text-black font-bold text-xs transition-all shadow-lg hover:shadow-emerald-950/40 disabled:opacity-50"
              >
                {submitting ? 'Submitting Decision...' : '✓ Submit Clinical Decision & Generate Report'}
              </button>
            </form>
          </div>
        </div>
      </main>
    </div>
  );
};

export default DoctorCaseReviewPage;
