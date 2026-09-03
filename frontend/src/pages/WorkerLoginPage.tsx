import React, { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { useAuth } from '@/context/AuthContext';
import { NORMAL_FUNDUS_SVG } from '@/services/sampleAssets';

const WorkerLoginPage: React.FC = () => {
  const navigate = useNavigate();
  const { loginWorker, registerWorker } = useAuth();

  const [activeTab, setActiveTab] = useState<'signin' | 'register'>('signin');

  // Sign In form state
  const [emailOrMobile, setEmailOrMobile] = useState('');
  const [password, setPassword] = useState('');

  // Register form state
  const [regFullName, setRegFullName] = useState('');
  const [regProfId, setRegProfId] = useState('');
  const [regMobile, setRegMobile] = useState('');
  const [regEmail, setRegEmail] = useState('');
  const [regCentreName, setRegCentreName] = useState('Primary Health Centre — Valparai');
  const [regPassword, setRegPassword] = useState('');
  const [regConfirmPassword, setRegConfirmPassword] = useState('');

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSignIn = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setLoading(true);

    try {
      await loginWorker(emailOrMobile.trim(), password.trim());
      navigate('/worker/dashboard');
    } catch (err: any) {
      setError(err.response?.data?.detail || err.message || 'Authentication failed. Please check credentials.');
    } finally {
      setLoading(false);
    }
  };

  const handleRegister = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);

    if (regPassword !== regConfirmPassword) {
      setError('Passwords do not match. Please re-enter.');
      return;
    }

    setLoading(true);

    try {
      await registerWorker({
        full_name: regFullName.trim(),
        professional_id: regProfId.trim(),
        mobile: regMobile.trim(),
        email: regEmail.trim(),
        healthcare_centre_name: regCentreName.trim(),
        password: regPassword.trim(),
      });
      navigate('/worker/dashboard');
    } catch (err: any) {
      setError(err.response?.data?.detail || err.message || 'Registration failed. Please check inputs.');
    } finally {
      setLoading(false);
    }
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
        <span className="text-xs font-mono text-neutral-500">RuralDR-XAI · HEALTHCARE WORKER PORTAL</span>
      </header>

      {/* Main Split Layout */}
      <main className="flex-1 flex items-center justify-center p-6">
        <div className="max-w-5xl w-full grid grid-cols-1 lg:grid-cols-12 rounded-3xl bg-[#0a0a0c] border border-white/[0.08] overflow-hidden shadow-2xl">
          {/* Left Visual Banner (5 cols) */}
          <div className="lg:col-span-5 relative p-8 lg:p-10 flex flex-col justify-between bg-gradient-to-br from-[#120703] via-[#0b0c10] to-[#040e0e] border-b lg:border-b-0 lg:border-r border-white/5 overflow-hidden">
            <div className="absolute inset-0 opacity-25 pointer-events-none flex items-center justify-center scale-125">
              <img src={NORMAL_FUNDUS_SVG} alt="Retinal Ambient" className="w-full h-full object-cover blur-sm" />
            </div>

            <div className="relative z-10">
              <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-teal-500/10 border border-teal-500/20 text-teal-400 text-xs font-mono mb-6">
                <span className="w-1.5 h-1.5 rounded-full bg-teal-400 animate-pulse" />
                Primary Health Centre Tier
              </div>
              <h2 className="text-2xl lg:text-3xl font-bold font-['Syne'] text-white mb-3 leading-tight">
                Healthcare Worker Portal
              </h2>
              <p className="text-neutral-400 text-xs sm:text-sm leading-relaxed">
                Connect rural screening cameras, run explainable AI evaluations with multi-gate safety verification, and route specialized doctor referrals.
              </p>
            </div>

            <div className="relative z-10 mt-8 p-4 rounded-2xl bg-black/60 border border-white/10 backdrop-blur-md">
              <div className="flex items-center gap-3 mb-2">
                <div className="w-6 h-6 rounded-full bg-teal-500/20 border border-teal-500/40 flex items-center justify-center text-teal-400 text-xs">
                  ✓
                </div>
                <div>
                  <p className="text-xs font-semibold text-white">Database-Backed Verification</p>
                  <p className="text-[10px] text-neutral-400">NHM Tele-Ophthalmology Network</p>
                </div>
              </div>
              <p className="text-[11px] text-neutral-400 leading-snug">
                Professional IDs are validated against official primary healthcare worker registries before referral privileges are granted.
              </p>
            </div>
          </div>

          {/* Right Authentication Panel (7 cols) */}
          <div className="lg:col-span-7 p-8 lg:p-12 flex flex-col justify-center bg-[#09090b]">
            <div className="max-w-md w-full mx-auto">
              {/* Tabs */}
              <div className="flex rounded-xl bg-white/5 p-1 mb-6 border border-white/10">
                <button
                  type="button"
                  onClick={() => { setActiveTab('signin'); setError(null); }}
                  className={`flex-1 py-2 text-xs font-semibold rounded-lg transition-all ${
                    activeTab === 'signin' ? 'bg-white text-black shadow-md' : 'text-neutral-400 hover:text-white'
                  }`}
                >
                  Sign In
                </button>
                <button
                  type="button"
                  onClick={() => { setActiveTab('register'); setError(null); }}
                  className={`flex-1 py-2 text-xs font-semibold rounded-lg transition-all ${
                    activeTab === 'register' ? 'bg-white text-black shadow-md' : 'text-neutral-400 hover:text-white'
                  }`}
                >
                  Register New Account
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

              {/* Sign In Form */}
              {activeTab === 'signin' && (
                <form onSubmit={handleSignIn} className="space-y-4">
                  <div>
                    <label className="block text-xs font-medium text-neutral-300 mb-1.5">
                      Registered Mobile, Email, or Professional ID
                    </label>
                    <input
                      type="text"
                      required
                      placeholder="e.g. worker@domain.org or +91 98402 12345 or HW-TN-4091"
                      value={emailOrMobile}
                      onChange={(e) => setEmailOrMobile(e.target.value)}
                      className="w-full px-4 py-3 rounded-xl bg-black/50 border border-white/10 text-white placeholder-neutral-600 text-xs focus:outline-none focus:border-teal-400 transition-colors"
                    />
                  </div>

                  <div>
                    <div className="flex items-center justify-between mb-1.5">
                      <label className="text-xs font-medium text-neutral-300">Password</label>
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

                  <div className="pt-2">
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
                  </div>
                </form>
              )}

              {/* Registration Form */}
              {activeTab === 'register' && (
                <form onSubmit={handleRegister} className="space-y-3">
                  <div>
                    <label className="block text-xs font-medium text-neutral-300 mb-1">Full Name</label>
                    <input
                      type="text"
                      required
                      placeholder="e.g. Lakshmi Narayanan, ANM"
                      value={regFullName}
                      onChange={(e) => setRegFullName(e.target.value)}
                      className="w-full px-3.5 py-2.5 rounded-xl bg-black/50 border border-white/10 text-white placeholder-neutral-600 text-xs focus:outline-none focus:border-teal-400"
                    />
                  </div>

                  <div className="grid grid-cols-2 gap-3">
                    <div>
                      <label className="block text-xs font-medium text-neutral-300 mb-1">Professional ID</label>
                      <input
                        type="text"
                        required
                        placeholder="e.g. HW-TN-4091"
                        value={regProfId}
                        onChange={(e) => setRegProfId(e.target.value)}
                        className="w-full px-3.5 py-2.5 rounded-xl bg-black/50 border border-white/10 text-white placeholder-neutral-600 text-xs focus:outline-none focus:border-teal-400 font-mono"
                      />
                    </div>
                    <div>
                      <label className="block text-xs font-medium text-neutral-300 mb-1">Mobile (+91)</label>
                      <input
                        type="tel"
                        required
                        placeholder="e.g. 9840212345"
                        value={regMobile}
                        onChange={(e) => setRegMobile(e.target.value)}
                        className="w-full px-3.5 py-2.5 rounded-xl bg-black/50 border border-white/10 text-white placeholder-neutral-600 text-xs focus:outline-none focus:border-teal-400"
                      />
                    </div>
                  </div>

                  <div>
                    <label className="block text-xs font-medium text-neutral-300 mb-1">Official Email Address</label>
                    <input
                      type="email"
                      required
                      placeholder="e.g. lakshmi.anm@health.tn.gov.in"
                      value={regEmail}
                      onChange={(e) => setRegEmail(e.target.value)}
                      className="w-full px-3.5 py-2.5 rounded-xl bg-black/50 border border-white/10 text-white placeholder-neutral-600 text-xs focus:outline-none focus:border-teal-400"
                    />
                  </div>

                  <div>
                    <label className="block text-xs font-medium text-neutral-300 mb-1">Primary Healthcare Centre</label>
                    <input
                      type="text"
                      required
                      placeholder="e.g. Primary Health Centre — Valparai"
                      value={regCentreName}
                      onChange={(e) => setRegCentreName(e.target.value)}
                      className="w-full px-3.5 py-2.5 rounded-xl bg-black/50 border border-white/10 text-white placeholder-neutral-600 text-xs focus:outline-none focus:border-teal-400"
                    />
                  </div>

                  <div className="grid grid-cols-2 gap-3">
                    <div>
                      <label className="block text-xs font-medium text-neutral-300 mb-1">Password</label>
                      <input
                        type="password"
                        required
                        minLength={6}
                        placeholder="Min 6 characters"
                        value={regPassword}
                        onChange={(e) => setRegPassword(e.target.value)}
                        className="w-full px-3.5 py-2.5 rounded-xl bg-black/50 border border-white/10 text-white placeholder-neutral-600 text-xs focus:outline-none focus:border-teal-400"
                      />
                    </div>
                    <div>
                      <label className="block text-xs font-medium text-neutral-300 mb-1">Confirm Password</label>
                      <input
                        type="password"
                        required
                        placeholder="Re-enter password"
                        value={regConfirmPassword}
                        onChange={(e) => setRegConfirmPassword(e.target.value)}
                        className="w-full px-3.5 py-2.5 rounded-xl bg-black/50 border border-white/10 text-white placeholder-neutral-600 text-xs focus:outline-none focus:border-teal-400"
                      />
                    </div>
                  </div>

                  <div className="pt-2">
                    <button
                      type="submit"
                      disabled={loading}
                      className="w-full py-3 px-4 rounded-xl bg-teal-400 hover:bg-teal-300 text-black font-semibold text-xs transition-all shadow-lg flex items-center justify-center gap-2 disabled:opacity-50"
                    >
                      {loading ? (
                        <>
                          <span className="w-4 h-4 border-2 border-black border-t-transparent rounded-full animate-spin" />
                          <span>Creating Healthcare Account...</span>
                        </>
                      ) : (
                        <span>Register & Sign In</span>
                      )}
                    </button>
                  </div>
                </form>
              )}
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
