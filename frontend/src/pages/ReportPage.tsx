import React, { useState, useEffect } from 'react';
import { useParams, Link } from 'react-router-dom';
import { useAuth } from '@/context/AuthContext';
import { AppHeader } from '@/components/layout/AppHeader';
import { caseService } from '@/services/caseService';
import { reportService, ClinicalReportDocument } from '@/services/reportService';
import { getGradCamOverlaySvg, getLesionMaskOverlaySvg } from '@/services/sampleAssets';

const ReportPage: React.FC = () => {
  const { caseId } = useParams<{ caseId: string }>();
  const { user } = useAuth();
  const [report, setReport] = useState<ClinicalReportDocument | null>(null);

  useEffect(() => {
    if (caseId) {
      const found = caseService.getCaseById(caseId);
      if (found) {
        setReport(reportService.generateReport(found));
      }
    }
  }, [caseId]);

  if (!report) {
    return (
      <div className="min-h-screen bg-[#070709] text-white flex flex-col">
        <AppHeader />
        <div className="flex-1 flex items-center justify-center p-8 text-center">
          <div>
            <h2 className="text-xl font-bold font-['Syne'] text-white mb-2">Report Not Found</h2>
            <p className="text-xs text-neutral-400 mb-6">Could not locate screening records for Case {caseId}.</p>
            <Link to="/" className="px-5 py-2.5 rounded-xl bg-white text-black font-semibold text-xs">
              Return to Workspace
            </Link>
          </div>
        </div>
      </div>
    );
  }

  const c = report.caseData;
  const grade = c.doctorReview?.confirmedGrade ?? c.screeningResult?.classification.dr_grade ?? 0;
  const isWorker = user?.role === 'worker';

  return (
    <div className="min-h-screen bg-[#060608] text-white flex flex-col print:bg-white print:text-black">
      {/* App Header hidden on print */}
      <div className="print:hidden">
        <AppHeader />
      </div>

      <main className="flex-1 max-w-4xl w-full mx-auto px-4 sm:px-6 py-8">
        {/* Action Controls Bar (Hidden in Print) */}
        <div className="mb-6 flex flex-wrap items-center justify-between gap-4 print:hidden">
          <div className="flex items-center gap-2">
            <Link
              to={isWorker ? '/worker/dashboard' : '/doctor/dashboard'}
              className="px-4 py-2 rounded-xl bg-white/5 hover:bg-white/10 text-neutral-300 text-xs font-medium border border-white/10 transition-colors flex items-center gap-1.5"
            >
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <path d="M19 12H5M12 19l-7-7 7-7" />
              </svg>
              <span>{isWorker ? 'Back to Worker Dashboard' : 'Back to Clinical Queue'}</span>
            </Link>
          </div>

          <div className="flex items-center gap-3">
            <button
              onClick={() => reportService.printReport()}
              className="px-5 py-2.5 rounded-xl bg-white hover:bg-teal-400 text-black font-bold text-xs transition-colors flex items-center gap-2 shadow-lg"
            >
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <polyline points="6 9 6 2 18 2 18 9" />
                <path d="M6 18H4a2 2 0 0 1-2-2v-5a2 2 0 0 1 2-2h16a2 2 0 0 1 2 2v5a2 2 0 0 1-2 2h-2" />
                <rect x="6" y="14" width="12" height="8" />
              </svg>
              <span>Print / Export PDF</span>
            </button>
          </div>
        </div>

        {/* Printable Official Clinical Diagnostic Document */}
        <div className="rounded-3xl bg-[#0c0d12] border border-white/[0.08] p-8 sm:p-12 shadow-2xl print:bg-white print:text-black print:border-none print:shadow-none print:p-0">
          {/* Document Header */}
          <div className="border-b border-white/10 print:border-black/20 pb-6 mb-6 flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-xl bg-red-600/20 border border-red-500/30 flex items-center justify-center print:border-black/30">
                <svg width="22" height="22" viewBox="0 0 24 24" fill="none">
                  <circle cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="1.5" className="text-white print:text-black" />
                  <circle cx="12" cy="12" r="4" stroke="#06b6d4" strokeWidth="1.5" />
                </svg>
              </div>
              <div>
                <h1 className="text-xl font-bold font-['Syne'] text-white print:text-black tracking-wider">
                  RuralDR-XAI
                </h1>
                <p className="text-[11px] text-neutral-400 print:text-neutral-600 font-mono">
                  Explainable AI Tele-Ophthalmology Screening System · SIH26038
                </p>
              </div>
            </div>

            <div className="text-right sm:text-right">
              <span className="font-mono font-bold text-sm text-teal-400 print:text-black block">{c.id}</span>
              <span className="text-[10px] text-neutral-400 print:text-neutral-600">
                Generated: {report.generatedAt}
              </span>
            </div>
          </div>

          {/* Patient & Facility Grid */}
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 p-4 rounded-2xl bg-black/40 print:bg-neutral-100 border border-white/5 print:border-black/10 mb-6 text-xs">
            <div>
              <span className="text-neutral-500 print:text-neutral-600 text-[10px] uppercase font-mono block">Patient Token</span>
              <strong className="text-white print:text-black font-mono">{c.patient.patientId}</strong>
            </div>
            <div>
              <span className="text-neutral-500 print:text-neutral-600 text-[10px] uppercase font-mono block">Age / Gender</span>
              <strong className="text-white print:text-black">{c.patient.age} Yrs · {c.patient.gender}</strong>
            </div>
            <div>
              <span className="text-neutral-500 print:text-neutral-600 text-[10px] uppercase font-mono block">Screening Center</span>
              <strong className="text-white print:text-black truncate block max-w-[160px]">{c.location.centerName}</strong>
            </div>
            <div>
              <span className="text-neutral-500 print:text-neutral-600 text-[10px] uppercase font-mono block">District / State</span>
              <strong className="text-white print:text-black">{c.location.district}, {c.location.state}</strong>
            </div>
          </div>

          {/* Diagnostic Imagery Trio */}
          <div className="mb-6">
            <h3 className="text-xs font-mono font-bold text-neutral-400 print:text-neutral-700 uppercase tracking-wider mb-3">
              Retinal Imagery & AI Explainability Evidence
            </h3>
            <div className="grid grid-cols-3 gap-3">
              {/* Original Fundus */}
              <div className="rounded-xl overflow-hidden bg-black border border-white/10 print:border-black/20 p-2 text-center">
                <img src={c.originalImageUrl} alt="Original Retina" className="w-full aspect-square object-contain mx-auto mb-1" />
                <span className="text-[10px] font-mono text-neutral-400 print:text-neutral-700">01. Original Fundus</span>
              </div>

              {/* Grad-CAM Heatmap */}
              <div className="rounded-xl overflow-hidden bg-black border border-white/10 print:border-black/20 p-2 text-center relative">
                <div className="relative w-full aspect-square flex items-center justify-center mb-1">
                  <img src={c.originalImageUrl} alt="Original" className="w-full h-full object-contain" />
                  <img
                    src={getGradCamOverlaySvg(grade)}
                    alt="Grad-CAM"
                    className="absolute inset-0 w-full h-full object-contain mix-blend-screen opacity-85"
                  />
                </div>
                <span className="text-[10px] font-mono text-cyan-400 print:text-cyan-800">02. Grad-CAM Attention</span>
              </div>

              {/* Lesion Segmentation */}
              <div className="rounded-xl overflow-hidden bg-black border border-white/10 print:border-black/20 p-2 text-center relative">
                <div className="relative w-full aspect-square flex items-center justify-center mb-1">
                  <img src={c.originalImageUrl} alt="Original" className="w-full h-full object-contain" />
                  <img
                    src={getLesionMaskOverlaySvg(grade)}
                    alt="Lesions"
                    className="absolute inset-0 w-full h-full object-contain opacity-90"
                  />
                </div>
                <span className="text-[10px] font-mono text-red-400 print:text-red-800">03. Lesion Segmentation</span>
              </div>
            </div>
          </div>

          {/* AI Assessment vs Doctor Decision Summary */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-6">
            {/* AI Screening Box */}
            <div className="p-4 rounded-2xl bg-black/40 print:bg-neutral-50 border border-white/5 print:border-black/10 text-xs space-y-2">
              <span className="text-[10px] font-mono text-teal-400 print:text-teal-800 uppercase block">
                Automated AI Inference
              </span>
              <p className="text-base font-bold text-white print:text-black font-['Syne']">
                {c.screeningResult?.classification.severity || 'Normal Retina'}
              </p>
              <div className="flex justify-between text-neutral-400 print:text-neutral-700 text-[11px] pt-1">
                <span>Model Confidence: {Math.round((c.screeningResult?.classification.confidence || 0) * 100)}%</span>
                <span>Image FIQA: {c.screeningResult?.quality.score}%</span>
              </div>
            </div>

            {/* Doctor's Confirmed Assessment Box */}
            <div className="p-4 rounded-2xl bg-emerald-950/20 print:bg-emerald-50 border border-emerald-500/20 print:border-emerald-300 text-xs space-y-2">
              <span className="text-[10px] font-mono text-emerald-400 print:text-emerald-800 uppercase block">
                Doctor Confirmed Clinical Diagnosis
              </span>
              <p className="text-base font-bold text-white print:text-black font-['Syne']">
                {c.doctorReview?.confirmedSeverity || c.screeningResult?.classification.severity || 'Diagnosis Confirmed'}
              </p>
              <div className="text-neutral-300 print:text-neutral-800 text-[11px] pt-1">
                <span>Evaluator: <strong>{c.doctorReview?.reviewedBy || 'Pending Doctor Signoff'}</strong></span>
              </div>
            </div>
          </div>

          {/* Doctor Clinical Notes */}
          {c.doctorReview && (
            <div className="p-4 rounded-2xl bg-black/40 print:bg-neutral-50 border border-white/5 print:border-black/10 text-xs space-y-2 mb-6">
              <span className="text-[10px] font-mono text-neutral-400 print:text-neutral-700 uppercase block">
                Doctor's Clinical Notes & Follow-up Prescription
              </span>
              <p className="text-neutral-200 print:text-neutral-900 leading-relaxed font-medium">
                {c.doctorReview.doctorNotes}
              </p>
              <div className="pt-2 border-t border-white/5 print:border-black/10 flex justify-between text-[11px] text-neutral-400 print:text-neutral-600">
                <span>Follow-up: {c.doctorReview.followUpTimeline}</span>
                <span>Reg No: {c.doctorReview.regNumber}</span>
              </div>
            </div>
          )}

          {/* Digital Signature & Verification Seal */}
          <div className="border-t border-white/10 print:border-black/20 pt-6 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 text-xs">
            <div className="space-y-1">
              <p className="font-mono text-[10px] text-neutral-400 print:text-neutral-600">
                Digital Verification Hash: <span className="text-neutral-300 print:text-black">SHA256-RDX-2026-SIH26038</span>
              </p>
              <p className="text-[10px] text-emerald-400 print:text-emerald-800 font-semibold">
                ✓ Medical Professional Verified · RuralDR-XAI Tele-Triage
              </p>
            </div>

            <div className="text-left sm:text-right border-l sm:border-l-0 sm:border-t-0 pl-3 sm:pl-0 border-white/10">
              <p className="font-semibold text-white print:text-black">Dr. S. K. Aravind, MS (Ophth)</p>
              <p className="text-[10px] text-neutral-400 print:text-neutral-600 font-mono">
                Reg: MCI-TN-2018-84729
              </p>
            </div>
          </div>

          {/* Medical Disclaimer */}
          <div className="mt-8 pt-4 border-t border-dashed border-white/10 print:border-black/20 text-[10px] text-neutral-500 print:text-neutral-600 leading-relaxed text-center">
            {report.disclaimer}
          </div>
        </div>
      </main>
    </div>
  );
};

export default ReportPage;
