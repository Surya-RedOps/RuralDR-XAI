import React, { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { useAuth } from '@/context/AuthContext';
import { SEVERE_NPDR_FUNDUS_SVG } from '@/services/sampleAssets';

const DoctorLoginPage: React.FC = () => {
  const navigate = useNavigate();
  const { loginDoctor } = useAuth();

  const [regNumber, setRegNumber] = useState('');
  const [emailOrMobile, setEmailOrMobile] = useState('');
  const [password, setPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if ((!regNumber.trim() && !emailOrMobile.trim()) || !password.trim()) {
      setError('Please enter registration number or email/mobile and password.');
      return;
    }
    setError(null);
    setLoading(true);

    try {
      await loginDoctor(
        regNumber.trim(),
        emailOrMobile.trim(),
        password.trim()
      );
      navigate('/doctor/dashboard');
    } catch (err: any) {
      setError(err.response?.data?.detail || err.message || 'Clinical authentication failed.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-[#040405] text-white flex flex-col justify-between">
      {/* Top Bar */}
      <header className="px-6 py-4 border-b border-white/5 flex items-center justify-between">
        <Link to="/select-role" className="flex items-center gap-2 text-xs text-neutral-400 hover:text-white transition-colors">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <path d="M19 12H5M12 19l-7-7 7-7" />
          </svg>
          <span>Change Role</span>
        </Link>
        <div className="flex items-center gap-3 text-xs font-mono text-neutral-400">
          <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse" />
          <span>RuralDR-XAI · CLINICAL REVIEW GATEWAY</span>
        </div>
      </header>

      {/* Main Clinical Split Layout */}
      <main className="flex-1 flex items-center justify-center p-6">
        <div className="max-w-5xl w-full grid grid-cols-1 lg:grid-cols-12 rounded-3xl bg-[#090a0d] border border-white/[0.08] overflow-hidden shadow-2xl">
          {/* Left Clinical Information Banner (5 cols) */}
          <div className="lg:col-span-5 relative p-8 lg:p-10 flex flex-col justify-between bg-gradient-to-br from-[#0c1417] via-[#080d11] to-[#040608] border-b lg:border-b-0 lg:border-r border-white/5 overflow-hidden">
            {/* Background Retinal Ambient Image */}
            <div className="absolute inset-0 opacity-20 pointer-events-none flex items-center justify-center scale-125">
              <img src={SEVERE_NPDR_FUNDUS_SVG} alt="Clinical Ambient" className="w-full h-full object-cover blur-sm" />
            </div>

            <div className="relative z-10">
              <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-emerald-500/10 border border-emerald-500/20 text-emerald-400 text-xs font-mono mb-6">
                <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse" />
                Vitreoretinal Specialist Portal
              </div>
              <h2 className="text-2xl lg:text-3xl font-bold font-['Syne'] text-white mb-3 leading-tight">
                Doctor Access
              </h2>
              <p className="text-neutral-400 text-xs sm:text-sm leading-relaxed">
                Review referred retinal cases with integrated Grad-CAM class activation maps, biomarker segmentation, and structured diagnostic reporting.
              </p>
            </div>

            {/* Medical Verification Badge */}
            <div className="relative z-10 mt-8 p-4 rounded-2xl bg-black/60 border border-emerald-500/20 backdrop-blur-md">
              <div className="flex items-center gap-3 mb-2">
                <div className="w-7 h-7 rounded-full bg-emerald-500/20 border border-emerald-500/40 flex items-center justify-center text-emerald-400 text-xs font-bold">
                  ✓
                </div>
                <div>
                  <p className="text-xs font-semibold text-white">Medical Professional Verified</p>
                  <p className="text-[10px] font-mono text-emerald-400">Registration Verified · NMC / State Council</p>
                </div>
              </div>
              <p className="text-[11px] text-neutral-400 leading-snug">
                Clinical triage and decision confirmation are digitally signed and recorded in compliance with medical imaging standards.
              </p>
            </div>
          </div>

          {/* Right Authentication Panel (7 cols) */}
          <div className="lg:col-span-7 p-8 lg:p-12 flex flex-col justify-center bg-[#09090c]">
            <div className="max-w-md w-full mx-auto">
              <div className="mb-6">
                <h3 className="text-xl font-bold text-white mb-1 font-['Syne']">Doctor Authentication</h3>
                <p className="text-xs text-neutral-400">Review AI-assisted retinal screening cases requiring clinical attention.</p>
              </div>

              {error && (
                <div className="mb-4 p-3 rounded-xl bg-red-500/10 border border-red-500/20 text-red-300 text-xs flex items-center gap-2">
                  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                    <circle cx="12" cy="12" r="10" />
                    <line x1="12" y1="8" x2="12" y2="12" />
                    <line x1="12" y1="16" x2="12.01" y2="16" />
                  </svg>
                  <span>{error}</span>
                </div>
              )}

              <form onSubmit={handleSubmit} className="space-y-4">
                <div>
                  <label className="block text-xs font-medium text-neutral-300 mb-1.5">
                    Medical Council Registration Number
                  </label>
                  <input
                    type="text"
                    required
                    placeholder="e.g. MCI-TN-2018-84729"
                    value={regNumber}
                    onChange={(e) => setRegNumber(e.target.value)}
                    className="w-full px-4 py-3 rounded-xl bg-black/50 border border-white/10 text-white placeholder-neutral-600 text-xs font-mono uppercase focus:outline-none focus:border-emerald-400 transition-colors"
                  />
                </div>

                <div>
                  <label className="block text-xs font-medium text-neutral-300 mb-1.5">
                    Registered Email or Mobile
                  </label>
                  <input
                    type="text"
                    required
                    placeholder="e.g. doctor@ruraldrxai.demo"
                    value={emailOrMobile}
                    onChange={(e) => setEmailOrMobile(e.target.value)}
                    className="w-full px-4 py-3 rounded-xl bg-black/50 border border-white/10 text-white placeholder-neutral-600 text-xs focus:outline-none focus:border-emerald-400 transition-colors"
                  />
                </div>

                <div>
                  <div className="flex items-center justify-between mb-1.5">
                    <label className="text-xs font-medium text-neutral-300">Password</label>
                    <button type="button" className="text-[11px] text-emerald-400 hover:underline">
                      Forgot password?
                    </button>
                  </div>
                  <input
                    type="password"
                    required
                    placeholder="Enter account password"
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    className="w-full px-4 py-3 rounded-xl bg-black/50 border border-white/10 text-white placeholder-neutral-600 text-xs focus:outline-none focus:border-emerald-400 transition-colors"
                  />
                </div>

                <div className="pt-2 space-y-3">
                  <button
                    type="submit"
                    disabled={loading}
                    className="w-full py-3.5 px-4 rounded-xl bg-white hover:bg-emerald-400 text-black font-semibold text-xs transition-all shadow-lg flex items-center justify-center gap-2 disabled:opacity-50"
                  >
                    {loading ? (
                      <>
                        <span className="w-4 h-4 border-2 border-black border-t-transparent rounded-full animate-spin" />
                        <span>Verifying Registration Record...</span>
                      </>
                    ) : (
                      <>
                        <span>Open Clinical Review Queue</span>
                        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
                          <path d="M5 12h14" />
                          <path d="M12 5l7 7-7 7" />
                        </svg>
                      </>
                    )}
                  </button>
                </div>
              </form>
            </div>
          </div>
        </div>
      </main>

      {/* Footer */}
      <footer className="px-6 py-4 text-center text-[11px] text-neutral-600 border-t border-white/5">
        RuralDR-XAI · Specialized Clinical Tele-Ophthalmology Module · SIH26038
      </footer>
    </div>
  );
};

export default DoctorLoginPage;
