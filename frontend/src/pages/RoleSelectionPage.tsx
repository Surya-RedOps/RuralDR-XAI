import React from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { RetinaBackground } from '@/components/ui/RetinaBackground';

const RoleSelectionPage: React.FC = () => {
  const navigate = useNavigate();

  return (
    <div className="min-h-screen bg-[#000000] text-white flex flex-col relative overflow-hidden">
      {/* Background Retinal Ambience */}
      <div className="fixed inset-0 pointer-events-none z-0">
        <RetinaBackground intensity="low" className="opacity-30" />
      </div>

      {/* Top Bar with Brand Link */}
      <nav className="relative z-10 w-full px-6 lg:px-14 py-6 border-b border-white/[0.06] backdrop-blur-md">
        <div className="max-w-7xl mx-auto flex items-center justify-between">
          <Link to="/" className="flex items-center gap-3 group">
            <svg width="24" height="24" viewBox="0 0 26 26" fill="none">
              <circle cx="13" cy="13" r="11" stroke="rgba(255,255,255,0.25)" strokeWidth="1" />
              <circle cx="13" cy="13" r="6" stroke="rgba(255,255,255,0.4)" strokeWidth="1" />
              <circle cx="13" cy="13" r="2.5" fill="rgba(255,255,255,0.8)" />
            </svg>
            <span className="text-xs font-bold tracking-widest text-neutral-200 font-mono group-hover:text-white transition-colors">
              RuralDR-XAI
            </span>
          </Link>
          <div className="flex items-center gap-3 text-xs text-neutral-400">
            <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse" />
            <span className="font-mono">SIH26038 PROTOCOL</span>
          </div>
        </div>
      </nav>

      {/* Main Role Selection Content */}
      <main className="relative z-10 flex-1 flex items-center justify-center px-6 py-16">
        <div className="max-w-4xl w-full mx-auto">
          {/* Header */}
          <div className="text-center mb-12">
            <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-white/5 border border-white/10 text-neutral-300 text-xs font-mono uppercase tracking-wider mb-4">
              Screening Workflow Access
            </div>
            <h1 className="text-3xl sm:text-4xl md:text-5xl font-bold font-['Syne'] tracking-tight text-white mb-4">
              Choose your workspace
            </h1>
            <p className="text-neutral-400 text-sm sm:text-base max-w-xl mx-auto leading-relaxed">
              Access RuralDR-XAI based on your role in the diabetic retinopathy screening workflow.
            </p>
          </div>

          {/* Dual Role Grid */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-8 items-stretch">
            {/* OPTION 1: Healthcare Worker */}
            <div
              onClick={() => navigate('/login/worker')}
              className="group relative flex flex-col justify-between p-8 rounded-2xl bg-[#09090b]/80 hover:bg-[#0f1015]/90 border border-white/[0.08] hover:border-teal-500/40 transition-all duration-300 hover:shadow-2xl hover:shadow-teal-950/30 cursor-pointer backdrop-blur-xl"
            >
              <div>
                {/* Top Role Header */}
                <div className="flex items-center justify-between mb-6">
                  <div className="w-14 h-14 rounded-xl bg-teal-500/10 border border-teal-500/20 flex items-center justify-center text-teal-400 group-hover:scale-105 transition-transform">
                    <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.75">
                      <path d="M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2" />
                      <circle cx="9" cy="7" r="4" />
                      <path d="M22 21v-2a4 4 0 0 0-3-3.87" />
                      <path d="M16 3.13a4 4 0 0 1 0 7.75" />
                    </svg>
                  </div>
                  <span className="text-[11px] font-mono px-2.5 py-1 rounded-full bg-teal-500/10 border border-teal-500/20 text-teal-300">
                    PHC / Field Screening
                  </span>
                </div>

                <h2 className="text-xl font-bold font-['Syne'] text-white mb-2 group-hover:text-teal-300 transition-colors">
                  Healthcare Worker
                </h2>
                <p className="text-neutral-400 text-xs sm:text-sm leading-relaxed mb-6">
                  Capture and submit retinal screenings from rural healthcare centers.
                </p>

                {/* Feature List */}
                <div className="space-y-2.5 mb-8">
                  {[
                    'Create screening cases',
                    'Upload fundus images',
                    'Review AI screening results',
                    'Refer abnormal cases',
                    'Track submitted cases',
                  ].map((feat, idx) => (
                    <div key={idx} className="flex items-center gap-2.5 text-xs text-neutral-300">
                      <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="#14b8a6" strokeWidth="2.5">
                        <polyline points="20 6 9 17 4 12" />
                      </svg>
                      <span>{feat}</span>
                    </div>
                  ))}
                </div>
              </div>

              {/* Action Button */}
              <button
                type="button"
                className="w-full py-3.5 px-5 rounded-xl bg-white text-black font-semibold text-xs sm:text-sm group-hover:bg-teal-400 transition-colors flex items-center justify-center gap-2 shadow-lg"
              >
                <span>Continue as Healthcare Worker</span>
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <path d="M5 12h14" />
                  <path d="M12 5l7 7-7 7" />
                </svg>
              </button>
            </div>

            {/* OPTION 2: Doctor */}
            <div
              onClick={() => navigate('/login/doctor')}
              className="group relative flex flex-col justify-between p-8 rounded-2xl bg-[#09090b]/80 hover:bg-[#0f1015]/90 border border-white/[0.08] hover:border-emerald-500/40 transition-all duration-300 hover:shadow-2xl hover:shadow-emerald-950/30 cursor-pointer backdrop-blur-xl"
            >
              <div>
                {/* Top Role Header */}
                <div className="flex items-center justify-between mb-6">
                  <div className="w-14 h-14 rounded-xl bg-emerald-500/10 border border-emerald-500/20 flex items-center justify-center text-emerald-400 group-hover:scale-105 transition-transform">
                    <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.75">
                      <path d="M22 12h-4l-3 9L9 3l-3 9H2" />
                    </svg>
                  </div>
                  <span className="text-[11px] font-mono px-2.5 py-1 rounded-full bg-emerald-500/10 border border-emerald-500/20 text-emerald-300">
                    Clinical Triage & Decision
                  </span>
                </div>

                <h2 className="text-xl font-bold font-['Syne'] text-white mb-2 group-hover:text-emerald-300 transition-colors">
                  Doctor
                </h2>
                <p className="text-neutral-400 text-xs sm:text-sm leading-relaxed mb-6">
                  Review AI-assisted retinal screenings and make clinical decisions.
                </p>

                {/* Feature List */}
                <div className="space-y-2.5 mb-8">
                  {[
                    'View referred cases',
                    'Review retinal images',
                    'Inspect AI explanations',
                    'Review severity',
                    'Provide clinical decision',
                  ].map((feat, idx) => (
                    <div key={idx} className="flex items-center gap-2.5 text-xs text-neutral-300">
                      <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="#10b981" strokeWidth="2.5">
                        <polyline points="20 6 9 17 4 12" />
                      </svg>
                      <span>{feat}</span>
                    </div>
                  ))}
                </div>
              </div>

              {/* Action Button */}
              <button
                type="button"
                className="w-full py-3.5 px-5 rounded-xl bg-white text-black font-semibold text-xs sm:text-sm group-hover:bg-emerald-400 transition-colors flex items-center justify-center gap-2 shadow-lg"
              >
                <span>Continue as Doctor</span>
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <path d="M5 12h14" />
                  <path d="M12 5l7 7-7 7" />
                </svg>
              </button>
            </div>
          </div>

          {/* Footer note */}
          <div className="mt-12 text-center text-xs text-neutral-500">
            RuralDR-XAI is calibrated for rural tele-ophthalmology screening under the National Health Mission guidelines.
          </div>
        </div>
      </main>
    </div>
  );
};

export default RoleSelectionPage;
