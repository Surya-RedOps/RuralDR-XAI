import React, { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { useAuth } from '@/context/AuthContext';
import { SEVERE_NPDR_FUNDUS_SVG } from '@/services/sampleAssets';

const DoctorLoginPage: React.FC = () => {
  const navigate = useNavigate();
  const { loginDoctor, registerDoctor } = useAuth();

  const [activeTab, setActiveTab] = useState<'signin' | 'register'>('signin');

  // Sign In state
  const [identifier, setIdentifier] = useState('');
  const [password, setPassword] = useState('');

  // Register state
  const [regFullName, setRegFullName] = useState('');
  const [regMedicalNumber, setRegMedicalNumber] = useState('');
  const [regMobile, setRegMobile] = useState('');
  const [regEmail, setRegEmail] = useState('');
  const [regHospitalName, setRegHospitalName] = useState('Coimbatore Eye Care & Medical College Hospital');
  const [regSpeciality, setRegSpeciality] = useState('Vitreoretinal & Comprehensive Ophthalmology');
  const [regPassword, setRegPassword] = useState('');
  const [regConfirmPassword, setRegConfirmPassword] = useState('');

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSignIn = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setLoading(true);

    try {
      await loginDoctor(identifier.trim(), identifier.trim(), password.trim());
      navigate('/doctor/dashboard');
    } catch (err: any) {
      setError(err.response?.data?.detail || err.message || 'Clinical authentication failed. Please verify credentials.');
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
      await registerDoctor({
        full_name: regFullName.trim(),
        medical_reg_number: regMedicalNumber.trim(),
        mobile: regMobile.trim(),
        email: regEmail.trim(),
        hospital_name: regHospitalName.trim(),
        speciality: regSpeciality.trim(),
        password: regPassword.trim(),
      });
      navigate('/doctor/dashboard');
    } catch (err: any) {
      setError(err.response?.data?.detail || err.message || 'Medical registration failed. Please verify details.');
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

            <div className="relative z-10 mt-8 p-4 rounded-2xl bg-black/60 border border-emerald-500/20 backdrop-blur-md">
              <div className="flex items-center gap-3 mb-2">
                <div className="w-7 h-7 rounded-full bg-emerald-500/20 border border-emerald-500/40 flex items-center justify-center text-emerald-400 text-xs font-bold">
                  ✓
                </div>
                <div>
                  <p className="text-xs font-semibold text-white">Medical Registry Verification</p>
                  <p className="text-[10px] font-mono text-emerald-400">NMC / State Council Integration</p>
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
              {/* Tabs */}
              <div className="flex rounded-xl bg-white/5 p-1 mb-6 border border-white/10">
                <button
                  type="button"
                  onClick={() => { setActiveTab('signin'); setError(null); }}
                  className={`flex-1 py-2 text-xs font-semibold rounded-lg transition-all ${
                    activeTab === 'signin' ? 'bg-white text-black shadow-md' : 'text-neutral-400 hover:text-white'
                  }`}
                >
                  Doctor Sign In
                </button>
                <button
                  type="button"
                  onClick={() => { setActiveTab('register'); setError(null); }}
                  className={`flex-1 py-2 text-xs font-semibold rounded-lg transition-all ${
                    activeTab === 'register' ? 'bg-white text-black shadow-md' : 'text-neutral-400 hover:text-white'
                  }`}
                >
                  Doctor Registration
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
                      Medical Registration Number, Mobile, or Email
                    </label>
                    <input
                      type="text"
                      required
                      placeholder="e.g. MCI-TN-2018-84729 or doctor@hospital.org"
                      value={identifier}
                      onChange={(e) => setIdentifier(e.target.value)}
                      className="w-full px-4 py-3 rounded-xl bg-black/50 border border-white/10 text-white placeholder-neutral-600 text-xs focus:outline-none focus:border-emerald-500 transition-colors font-mono"
                    />
                  </div>

                  <div>
                    <div className="flex items-center justify-between mb-1.5">
                      <label className="text-xs font-medium text-neutral-300">Password</label>
                    </div>
                    <input
                      type="password"
                      required
                      placeholder="Enter clinical account password"
                      value={password}
                      onChange={(e) => setPassword(e.target.value)}
                      className="w-full px-4 py-3 rounded-xl bg-black/50 border border-white/10 text-white placeholder-neutral-600 text-xs focus:outline-none focus:border-emerald-500 transition-colors"
                    />
                  </div>

                  <div className="pt-2">
                    <button
                      type="submit"
                      disabled={loading}
                      className="w-full py-3.5 px-4 rounded-xl bg-emerald-500 hover:bg-emerald-400 text-black font-semibold text-xs transition-all shadow-lg flex items-center justify-center gap-2 disabled:opacity-50"
                    >
                      {loading ? (
                        <>
                          <span className="w-4 h-4 border-2 border-black border-t-transparent rounded-full animate-spin" />
                          <span>Verifying Medical Credentials...</span>
                        </>
                      ) : (
                        <>
                          <span>Access Diagnostic Queue</span>
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
                    <label className="block text-xs font-medium text-neutral-300 mb-1">Doctor's Full Name</label>
                    <input
                      type="text"
                      required
                      placeholder="e.g. Dr. S. K. Aravind, MS (Ophthalmology)"
                      value={regFullName}
                      onChange={(e) => setRegFullName(e.target.value)}
                      className="w-full px-3.5 py-2.5 rounded-xl bg-black/50 border border-white/10 text-white placeholder-neutral-600 text-xs focus:outline-none focus:border-emerald-500"
                    />
                  </div>

                  <div className="grid grid-cols-2 gap-3">
                    <div>
                      <label className="block text-xs font-medium text-neutral-300 mb-1">Medical Reg. Number</label>
                      <input
                        type="text"
                        required
                        placeholder="e.g. MCI-TN-2018-84729"
                        value={regMedicalNumber}
                        onChange={(e) => setRegMedicalNumber(e.target.value)}
                        className="w-full px-3.5 py-2.5 rounded-xl bg-black/50 border border-white/10 text-white placeholder-neutral-600 text-xs focus:outline-none focus:border-emerald-500 font-mono"
                      />
                    </div>
                    <div>
                      <label className="block text-xs font-medium text-neutral-300 mb-1">Mobile (+91)</label>
                      <input
                        type="tel"
                        required
                        placeholder="e.g. 9443156789"
                        value={regMobile}
                        onChange={(e) => setRegMobile(e.target.value)}
                        className="w-full px-3.5 py-2.5 rounded-xl bg-black/50 border border-white/10 text-white placeholder-neutral-600 text-xs focus:outline-none focus:border-emerald-500"
                      />
                    </div>
                  </div>

                  <div>
                    <label className="block text-xs font-medium text-neutral-300 mb-1">Official Clinical Email</label>
                    <input
                      type="email"
                      required
                      placeholder="e.g. dr.aravind@eyecentre.org"
                      value={regEmail}
                      onChange={(e) => setRegEmail(e.target.value)}
                      className="w-full px-3.5 py-2.5 rounded-xl bg-black/50 border border-white/10 text-white placeholder-neutral-600 text-xs focus:outline-none focus:border-emerald-500"
                    />
                  </div>

                  <div>
                    <label className="block text-xs font-medium text-neutral-300 mb-1">Hospital / Medical Centre</label>
                    <input
                      type="text"
                      required
                      placeholder="e.g. Regional Eye Centre, Coimbatore"
                      value={regHospitalName}
                      onChange={(e) => setRegHospitalName(e.target.value)}
                      className="w-full px-3.5 py-2.5 rounded-xl bg-black/50 border border-white/10 text-white placeholder-neutral-600 text-xs focus:outline-none focus:border-emerald-500"
                    />
                  </div>

                  <div>
                    <label className="block text-xs font-medium text-neutral-300 mb-1">Speciality</label>
                    <input
                      type="text"
                      required
                      value={regSpeciality}
                      onChange={(e) => setRegSpeciality(e.target.value)}
                      className="w-full px-3.5 py-2.5 rounded-xl bg-black/50 border border-white/10 text-white placeholder-neutral-600 text-xs focus:outline-none focus:border-emerald-500"
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
                        className="w-full px-3.5 py-2.5 rounded-xl bg-black/50 border border-white/10 text-white placeholder-neutral-600 text-xs focus:outline-none focus:border-emerald-500"
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
                        className="w-full px-3.5 py-2.5 rounded-xl bg-black/50 border border-white/10 text-white placeholder-neutral-600 text-xs focus:outline-none focus:border-emerald-500"
                      />
                    </div>
                  </div>

                  <div className="pt-2">
                    <button
                      type="submit"
                      disabled={loading}
                      className="w-full py-3 px-4 rounded-xl bg-emerald-500 hover:bg-emerald-400 text-black font-semibold text-xs transition-all shadow-lg flex items-center justify-center gap-2 disabled:opacity-50"
                    >
                      {loading ? (
                        <>
                          <span className="w-4 h-4 border-2 border-black border-t-transparent rounded-full animate-spin" />
                          <span>Registering Medical Account...</span>
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
        RuralDR-XAI · Vitreoretinal Diagnostic Network · SIH26038 Compliance
      </footer>
    </div>
  );
};

export default DoctorLoginPage;
