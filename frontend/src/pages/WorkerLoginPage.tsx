import React, { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { useAuth } from '@/context/AuthContext';
import { MOCK_USERS } from '@/services/authService';
import { NORMAL_FUNDUS_SVG } from '@/services/sampleAssets';

const WorkerLoginPage: React.FC = () => {
  const navigate = useNavigate();
  const { loginWorker } = useAuth();

  const [emailOrMobile, setEmailOrMobile] = useState('');
  const [password, setPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setLoading(true);

    try {
      await loginWorker(emailOrMobile || MOCK_USERS.worker.email, password || 'password123');
      navigate('/worker/dashboard');
    } catch (err: any) {
      setError(err.message || 'Authentication failed. Please check credentials.');
    } finally {
      setLoading(false);
    }
  };

  const handleFillDemo = () => {
    setEmailOrMobile(MOCK_USERS.worker.email);
    setPassword('password123');
    setError(null);
  };

  return (
    <div className="min-h-screen bg-[#050505] text-white flex flex-col justify-between">
      {/* Top Bar */}
      <header className="px-6 py-4 border-b border-white/5 flex items-center justify-between">
        <Link to="/select-role" className="flex items-center gap-2 text-xs text-neutral-400 hover:text-white transition-colors">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <path d="M19 12H5M12 19l-7-7 7-7" />
          </svg>
          <span>Change Role</span>
        </Link>
        <span className="text-xs font-mono text-neutral-500">RuralDR-XAI · WORKER PORTAL</span>
      </header>

      {/* Main Split Layout */}
      <main className="flex-1 flex items-center justify-center p-6">
        <div className="max-w-5xl w-full grid grid-cols-1 lg:grid-cols-12 rounded-3xl bg-[#0a0a0c] border border-white/[0.08] overflow-hidden shadow-2xl">
          {/* Left Visual Banner (5 cols) */}
          <div className="lg:col-span-5 relative p-8 lg:p-10 flex flex-col justify-between bg-gradient-to-br from-[#120703] via-[#0b0c10] to-[#040e0e] border-b lg:border-b-0 lg:border-r border-white/5 overflow-hidden">
            {/* Background Retinal Ambient Image */}
            <div className="absolute inset-0 opacity-25 pointer-events-none flex items-center justify-center scale-125">
              <img src={NORMAL_FUNDUS_SVG} alt="Retinal Ambient" className="w-full h-full object-cover blur-sm" />
            </div>

            <div className="relative z-10">
              <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-teal-500/10 border border-teal-500/20 text-teal-400 text-xs font-mono mb-6">
                <span className="w-1.5 h-1.5 rounded-full bg-teal-400 animate-pulse" />
                Primary Health Centre Tier
              </div>
              <h2 className="text-2xl lg:text-3xl font-bold font-['Syne'] text-white mb-3 leading-tight">
                Healthcare Worker Access
              </h2>
              <p className="text-neutral-400 text-xs sm:text-sm leading-relaxed">
                Connect rural screening cameras, run explainable AI evaluations, and initiate specialized doctor referrals.
              </p>
            </div>

            {/* Verification Status Card */}
            <div className="relative z-10 mt-8 p-4 rounded-2xl bg-black/60 border border-white/10 backdrop-blur-md">
              <div className="flex items-center gap-3 mb-2">
                <div className="w-6 h-6 rounded-full bg-teal-500/20 border border-teal-500/40 flex items-center justify-center text-teal-400 text-xs">
                  ✓
                </div>
                <div>
                  <p className="text-xs font-semibold text-white">Verified Healthcare Professional</p>
                  <p className="text-[10px] text-neutral-400">NHM Tele-Ophthalmology Registered</p>
                </div>
              </div>
              <p className="text-[11px] text-neutral-400 leading-snug">
                Your screening access is restricted to verified healthcare professionals at certified field units.
              </p>
            </div>
          </div>

          {/* Right Authentication Panel (7 cols) */}
          <div className="lg:col-span-7 p-8 lg:p-12 flex flex-col justify-center bg-[#09090b]">
            <div className="max-w-md w-full mx-auto">
              <div className="mb-6">
                <h3 className="text-xl font-bold text-white mb-1 font-['Syne']">Sign In</h3>
                <p className="text-xs text-neutral-400">Sign in to begin or manage retinal screening cases.</p>
              </div>

              {/* Demo Helper Button */}
              <div className="mb-6 p-3 rounded-xl bg-teal-500/5 border border-teal-500/20 flex items-center justify-between">
                <div className="text-xs">
                  <span className="text-teal-300 font-medium">Demo Worker Account: </span>
                  <span className="font-mono text-neutral-300">{MOCK_USERS.worker.email}</span>
                </div>
                <button
                  type="button"
                  onClick={handleFillDemo}
                  className="px-2.5 py-1 text-[11px] font-semibold rounded bg-teal-500/20 hover:bg-teal-500/30 text-teal-300 border border-teal-500/30 transition-colors"
                >
                  Fill Demo
                </button>
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
                    Registered Mobile or Email
                  </label>
                  <input
                    type="text"
                    required
                    placeholder="e.g. worker@ruraldrxai.demo or 9840212345"
                    value={emailOrMobile}
                    onChange={(e) => setEmailOrMobile(e.target.value)}
                    className="w-full px-4 py-3 rounded-xl bg-black/50 border border-white/10 text-white placeholder-neutral-600 text-xs focus:outline-none focus:border-teal-400 transition-colors"
                  />
                </div>

                <div>
                  <div className="flex items-center justify-between mb-1.5">
                    <label className="text-xs font-medium text-neutral-300">Password</label>
                    <button type="button" className="text-[11px] text-teal-400 hover:underline">
                      Forgot password?
                    </button>
                  </div>
                  <input
                    type="password"
                    required
                    placeholder="Enter account password"
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    className="w-full px-4 py-3 rounded-xl bg-black/50 border border-white/10 text-white placeholder-neutral-600 text-xs focus:outline-none focus:border-teal-400 transition-colors"
                  />
                </div>

                <div className="pt-2 space-y-3">
                  <button
                    type="submit"
                    disabled={loading}
                    className="w-full py-3.5 px-4 rounded-xl bg-white hover:bg-teal-400 text-black font-semibold text-xs transition-all shadow-lg flex items-center justify-center gap-2 disabled:opacity-50"
                  >
                    {loading ? (
                      <>
                        <span className="w-4 h-4 border-2 border-black border-t-transparent rounded-full animate-spin" />
                        <span>Verifying Credentials...</span>
                      </>
                    ) : (
                      <>
                        <span>Sign In to Screening Portal</span>
                        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
                          <path d="M5 12h14" />
                          <path d="M12 5l7 7-7 7" />
                        </svg>
                      </>
                    )}
                  </button>

                  <button
                    type="button"
                    onClick={handleFillDemo}
                    className="w-full py-2.5 px-4 rounded-xl bg-transparent hover:bg-white/5 border border-white/10 text-neutral-300 text-xs transition-colors"
                  >
                    Verify Account Status
                  </button>
                </div>
              </form>
            </div>
          </div>
        </div>
      </main>

      {/* Footer */}
      <footer className="px-6 py-4 text-center text-[11px] text-neutral-600 border-t border-white/5">
        RuralDR-XAI · Encrypted Medical Tele-Screening · SIH26038 Compliance
      </footer>
    </div>
  );
};

export default WorkerLoginPage;
