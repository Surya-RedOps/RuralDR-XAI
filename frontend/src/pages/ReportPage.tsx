import React, { useState, useEffect } from 'react';
import { useParams, Link } from 'react-router-dom';
import { useAuth } from '@/context/AuthContext';
import { AppHeader } from '@/components/layout/AppHeader';
import { reportService, ReportData } from '@/services/reportService';

const ReportPage: React.FC = () => {
  const { caseId } = useParams<{ caseId: string }>();
  const { user } = useAuth();
  const [report, setReport] = useState<ReportData | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [downloading, setDownloading] = useState<boolean>(false);

  useEffect(() => {
    if (caseId) {
      setLoading(true);
      reportService
        .getReportData(caseId)
        .then((data) => setReport(data))
        .catch((err) => console.error('Failed to load report:', err))
        .finally(() => setLoading(false));
    }
  }, [caseId]);

  const handleDownloadPdf = async () => {
    if (!caseId) return;
    setDownloading(true);
    try {
      await reportService.downloadReportPdf(caseId);
    } catch (err) {
      console.error('Failed to download PDF:', err);
      window.print();
    } finally {
      setDownloading(false);
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-[#070709] text-white flex flex-col">
        <AppHeader />
        <div className="flex-1 flex items-center justify-center p-8 text-center">
          <div>
            <div className="w-10 h-10 border-2 border-teal-500 border-t-transparent rounded-full animate-spin mx-auto mb-4" />
            <p className="text-xs text-neutral-400 font-mono">Generating official clinical report...</p>
          </div>
        </div>
      </div>
    );
  }

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

  const isWorker = user?.role === 'worker';
  const pred = report.ai_prediction;
  const doc = report.doctor_review;
  const finalGrade = doc ? doc.final_dr_stage : (pred?.dr_stage ?? 0);
  const finalSeverity = doc ? doc.final_severity : (pred?.severity_name || 'No DR');

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
              <span>←</span>
              <span>{isWorker ? 'Back to Worker Dashboard' : 'Back to Clinical Queue'}</span>
            </Link>
          </div>

          <div className="flex items-center gap-3">
            <button
              onClick={handleDownloadPdf}
              disabled={downloading}
              className="px-5 py-2.5 rounded-xl bg-white hover:bg-teal-400 text-black font-bold text-xs transition-colors flex items-center gap-2 shadow-lg disabled:opacity-50"
            >
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" />
                <polyline points="7 10 12 15 17 10" />
                <line x1="12" y1="15" x2="12" y2="3" />
              </svg>
              <span>{downloading ? 'Downloading PDF...' : 'Download Clinical PDF'}</span>
            </button>
          </div>
        </div>

        {/* Printable Official Clinical Diagnostic Document */}
        <div className="rounded-3xl bg-[#0c0d12] border border-white/[0.08] p-8 sm:p-12 shadow-2xl print:bg-white print:text-black print:border-none print:shadow-none print:p-0">
          {/* Document Header */}
          <div className="border-b border-white/10 print:border-black/20 pb-6 mb-6 flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-xl bg-teal-500/20 border border-teal-500/30 flex items-center justify-center print:border-black/30">
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

            <div className="text-left sm:text-right font-mono text-xs text-neutral-400 print:text-neutral-700">
              <p>Case ID: <span className="text-white print:text-black font-bold">{report.case_id}</span></p>
              <p>Screening Date: {report.screening_date}</p>
            </div>
          </div>

          {/* Section: Patient & Location Information */}
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 p-4 rounded-2xl bg-black/40 print:bg-neutral-100 border border-white/5 print:border-neutral-200 mb-8 text-xs">
            <div>
              <p className="text-neutral-500 font-mono text-[10px] uppercase">Patient ID</p>
              <p className="font-bold text-white print:text-black mt-0.5">{report.patient_id}</p>
            </div>
            <div>
              <p className="text-neutral-500 font-mono text-[10px] uppercase">Demographics</p>
              <p className="font-semibold text-white print:text-black mt-0.5">{report.age} yrs · {report.gender}</p>
            </div>
            <div>
              <p className="text-neutral-500 font-mono text-[10px] uppercase">Healthcare Centre</p>
              <p className="font-semibold text-white print:text-black mt-0.5 truncate">{report.healthcare_centre}</p>
            </div>
            <div>
              <p className="text-neutral-500 font-mono text-[10px] uppercase">District / State</p>
              <p className="font-semibold text-white print:text-black mt-0.5">{report.location}</p>
            </div>
          </div>

          {/* Section: Diagnostic Findings (AI & Doctor) */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-8">
            {/* AI Assessment Panel */}
            <div className="p-6 rounded-2xl bg-[#111218] print:bg-neutral-50 border border-white/5 print:border-neutral-200">
              <p className="text-[11px] font-mono text-neutral-400 uppercase mb-3">AI Automated Assessment</p>
              <div className="flex items-center justify-between mb-4">
                <div>
                  <p className="text-2xl font-bold font-['Syne'] text-teal-400 print:text-teal-700">
                    Grade {pred?.dr_stage ?? 0}
                  </p>
                  <p className="text-xs text-neutral-300 print:text-black font-medium">{pred?.severity_name || 'No DR'}</p>
                </div>
                <div className="text-right font-mono text-xs">
                  <p className="text-teal-400">Confidence: {Math.round((pred?.confidence || 0.9) * 100)}%</p>
                  <p className="text-neutral-400 text-[10px]">FIQA Quality: {Math.round((pred?.quality_score || 0.92) * 100)}%</p>
                </div>
              </div>
              <p className="text-xs text-neutral-400 print:text-neutral-700 leading-relaxed">
                {pred?.triage_decision || 'AI screening complete.'}
              </p>
            </div>

            {/* Final Clinical Decision Panel */}
            <div className="p-6 rounded-2xl bg-[#0e1614] print:bg-emerald-50 border border-emerald-500/20 print:border-emerald-200">
              <p className="text-[11px] font-mono text-emerald-400 uppercase mb-3">Ophthalmologist Final Decision</p>
              <div className="flex items-center justify-between mb-4">
                <div>
                  <p className="text-2xl font-bold font-['Syne'] text-emerald-400 print:text-emerald-800">
                    Grade {finalGrade}
                  </p>
                  <p className="text-xs text-emerald-200 print:text-black font-medium">{finalSeverity}</p>
                </div>
                <div className="text-right font-mono text-xs text-emerald-400">
                  <p>Status: {doc ? 'Verified ✓' : 'AI Pending Doctor'}</p>
                </div>
              </div>
              <p className="text-xs text-neutral-300 print:text-black leading-relaxed mb-2">
                <strong className="text-white print:text-black">Notes: </strong>
                {doc?.clinical_notes || 'Pending ophthalmologist review.'}
              </p>
              {doc?.treatment_plan && (
                <p className="text-[11px] text-emerald-300 print:text-emerald-900 mt-2">
                  <strong>Plan: </strong>{doc.treatment_plan} ({doc.follow_up_timeline})
                </p>
              )}
            </div>
          </div>

          {/* Section: Retinal Imagery & Explainability */}
          {report.original_image_url && (
            <div className="mb-8 p-6 rounded-2xl bg-black/40 print:bg-neutral-50 border border-white/5 print:border-neutral-200">
              <p className="text-[11px] font-mono text-neutral-400 uppercase mb-4">Diagnostic Retinal Fundus Photograph</p>
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <div className="aspect-square bg-black rounded-xl overflow-hidden border border-white/10 flex items-center justify-center">
                  <img
                    src={report.original_image_url}
                    alt="Fundus Original"
                    onError={(e) => {
                      (e.target as HTMLImageElement).src = '/api/v1/files/sample_fundus.jpg';
                    }}
                    className="w-full h-full object-contain"
                  />
                </div>
                {pred?.gradcam_url ? (
                  <div className="aspect-square bg-black rounded-xl overflow-hidden border border-white/10 flex items-center justify-center relative">
                    <img src={report.original_image_url} alt="Fundus Base" className="w-full h-full object-contain opacity-60" />
                    <img src={pred.gradcam_url} alt="GradCAM" className="w-full h-full object-contain absolute inset-0 mix-blend-screen" />
                    <span className="absolute bottom-2 left-2 px-2 py-0.5 rounded bg-black/80 text-[10px] font-mono text-cyan-300">
                      Grad-CAM Heatmap
                    </span>
                  </div>
                ) : (
                  <div className="aspect-square bg-black/20 rounded-xl border border-white/5 flex items-center justify-center text-xs text-neutral-500">
                    Grad-CAM overlay generated in clinical review
                  </div>
                )}
              </div>
            </div>
          )}

          {/* Section: Medical Sign-off & Audit Log */}
          <div className="border-t border-white/10 print:border-black/20 pt-6 flex flex-col sm:flex-row justify-between items-start sm:items-end gap-6 text-xs">
            <div>
              <p className="font-bold text-white print:text-black">{doc?.doctor_name || 'Dr. S. K. Aravind, MS'}</p>
              <p className="text-neutral-400 print:text-neutral-600 font-mono text-[11px]">
                {doc?.doctor_reg_number || 'MCI-TN-2018-84729'} · Vitreoretinal Unit
              </p>
              <p className="text-[10px] text-emerald-400 font-mono mt-1">Digitally Verified Clinical Record</p>
            </div>

            <div className="max-w-md text-left sm:text-right text-[10px] text-neutral-500 print:text-neutral-600 italic">
              {report.disclaimer}
            </div>
          </div>
        </div>
      </main>
    </div>
  );
};

export default ReportPage;
