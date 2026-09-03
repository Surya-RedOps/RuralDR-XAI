import React, { useState, useEffect } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { useAuth } from '@/context/AuthContext';
import { locationService } from '@/services/locationService';
import { StateItem, DistrictItem, HealthcareCenterItem } from '@/types/api';
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

  // Cascading Location Dropdowns State
  const [states, setStates] = useState<StateItem[]>([]);
  const [selectedStateId, setSelectedStateId] = useState<number | ''>('');
  const [districts, setDistricts] = useState<DistrictItem[]>([]);
  const [selectedDistrictId, setSelectedDistrictId] = useState<number | ''>('');
  const [centres, setCentres] = useState<HealthcareCenterItem[]>([]);
  const [selectedCentreId, setSelectedCentreId] = useState<number | ''>('');

  const [loadingStates, setLoadingStates] = useState(false);
  const [loadingDistricts, setLoadingDistricts] = useState(false);
  const [loadingCentres, setLoadingCentres] = useState(false);

  const [regPassword, setRegPassword] = useState('');
  const [regConfirmPassword, setRegConfirmPassword] = useState('');

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Registration Pending Verification Modal
  const [registrationSuccess, setRegistrationSuccess] = useState<{
    email: string;
    name: string;
    status: string;
    message: string;
  } | null>(null);

  // Load States on mount
  useEffect(() => {
    let isMounted = true;
    const fetchStates = async () => {
      setLoadingStates(true);
      try {
        const data = await locationService.getStates();
        if (isMounted) {
          setStates(data);
        }
      } catch (err: any) {
        console.error('Failed to load states:', err);
      } finally {
        if (isMounted) setLoadingStates(false);
      }
    };
    fetchStates();
    return () => {
      isMounted = false;
    };
  }, []);

  // Handle State Change -> Cascading Districts
  const handleStateChange = async (e: React.ChangeEvent<HTMLSelectElement>) => {
    const val = e.target.value ? Number(e.target.value) : '';
    setSelectedStateId(val);
    setSelectedDistrictId('');
    setDistricts([]);
    setSelectedCentreId('');
    setCentres([]);

    if (val) {
      setLoadingDistricts(true);
      try {
        const data = await locationService.getDistricts(val);
        setDistricts(data);
      } catch (err) {
        console.error('Failed to load districts:', err);
      } finally {
        setLoadingDistricts(false);
      }
    }
  };

  // Handle District Change -> Cascading Healthcare Centres
  const handleDistrictChange = async (e: React.ChangeEvent<HTMLSelectElement>) => {
    const val = e.target.value ? Number(e.target.value) : '';
    setSelectedDistrictId(val);
    setSelectedCentreId('');
    setCentres([]);

    if (val) {
      setLoadingCentres(true);
      try {
        const data = await locationService.getHealthcareCenters(val);
        setCentres(data);
      } catch (err) {
        console.error('Failed to load healthcare centres:', err);
      } finally {
        setLoadingCentres(false);
      }
    }
  };

  const handleSignIn = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setLoading(true);

    try {
      await loginWorker(emailOrMobile.trim(), password.trim());
      navigate('/worker/dashboard');
    } catch (err: any) {
      const detail = err.response?.data?.detail;
      const msg = typeof detail === 'string' ? detail : err.message || 'Authentication failed. Please verify credentials.';
      setError(msg);
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

    if (!selectedStateId) {
      setError('Please select a state.');
      return;
    }
    if (!selectedDistrictId) {
      setError('Please select a district.');
      return;
    }
    if (!selectedCentreId) {
      setError('Please select a healthcare centre.');
      return;
    }

    setLoading(true);

    try {
      const res = await registerWorker({
        full_name: regFullName.trim(),
        professional_id: regProfId.trim(),
        mobile: regMobile.trim(),
        official_email: regEmail.trim(),
        email: regEmail.trim(),
        state_id: Number(selectedStateId),
        district_id: Number(selectedDistrictId),
        healthcare_center_id: Number(selectedCentreId),
        healthcare_centre_id: Number(selectedCentreId),
        password: regPassword.trim(),
      });

      // Show Verification Pending notification
      setRegistrationSuccess({
        email: regEmail.trim(),
        name: regFullName.trim(),
        status: res.status,
        message: res.message,
      });

      // Pre-fill email in signin
      setEmailOrMobile(regEmail.trim());
    } catch (err: any) {
      const detail = err.response?.data?.detail;
      let msg = 'Registration failed. Please check form fields.';
      if (typeof detail === 'string') {
        msg = detail;
      } else if (Array.isArray(detail) && detail.length > 0 && detail[0].msg) {
        msg = detail[0].msg;
      } else if (typeof detail === 'object' && detail !== null) {
        msg = detail.message || JSON.stringify(detail);
      } else if (err.message) {
        msg = err.message;
      }
      setError(msg);
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
                <div className="w-6 h-6 rounded-full bg-teal-500/20 border border-teal-500/40 flex items-center justify-center text-teal-400 text-xs font-bold">
                  ✓
                </div>
                <div>
                  <p className="text-xs font-semibold text-white">Hierarchical Facility Linkage</p>
                  <p className="text-[10px] text-neutral-400">State &rarr; District &rarr; Rural Primary Facility</p>
                </div>
              </div>
              <p className="text-[11px] text-neutral-400 leading-snug">
                Registrations require official district and facility verification before field screening authorization is granted.
              </p>
            </div>
          </div>

          {/* Right Authentication Panel (7 cols) */}
          <div className="lg:col-span-7 p-8 lg:p-12 flex flex-col justify-center bg-[#09090b]">
            <div className="max-w-xl w-full mx-auto">
              {/* Tabs */}
              <div className="flex rounded-xl bg-white/5 p-1 mb-6 border border-white/10">
                <button
                  type="button"
                  id="tab-worker-signin"
                  onClick={() => { setActiveTab('signin'); setError(null); }}
                  className={`flex-1 py-2 text-xs font-semibold rounded-lg transition-all ${
                    activeTab === 'signin' ? 'bg-white text-black shadow-md' : 'text-neutral-400 hover:text-white'
                  }`}
                >
                  Sign In
                </button>
                <button
                  type="button"
                  id="tab-worker-register"
                  onClick={() => { setActiveTab('register'); setError(null); }}
                  className={`flex-1 py-2 text-xs font-semibold rounded-lg transition-all ${
                    activeTab === 'register' ? 'bg-white text-black shadow-md' : 'text-neutral-400 hover:text-white'
                  }`}
                >
                  Register New Account
                </button>
              </div>

              {/* Error Banner */}
              {error && (
                <div className="mb-4 p-3.5 rounded-xl bg-red-500/10 border border-red-500/20 text-red-300 text-xs flex items-start gap-2.5">
                  <svg className="w-4 h-4 mt-0.5 flex-shrink-0 text-red-400" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                    <circle cx="12" cy="12" r="10" />
                    <line x1="12" y1="8" x2="12" y2="12" />
                    <line x1="12" y1="16" x2="12.01" y2="16" />
                  </svg>
                  <div>
                    <p className="font-medium">{error}</p>
                    {error.toLowerCase().includes('pending verification') && (
                      <p className="text-[11px] text-red-300/80 mt-1">
                        Your registration has been received and is awaiting administrative approval before sign-in is allowed.
                      </p>
                    )}
                  </div>
                </div>
              )}

              {/* Sign In Form */}
              {activeTab === 'signin' && (
                <form onSubmit={handleSignIn} className="space-y-4">
                  <div>
                    <label className="block text-xs font-medium text-neutral-300 mb-1">
                      Official Email or Mobile Number
                    </label>
                    <input
                      type="text"
                      id="worker-signin-identifier"
                      required
                      placeholder="e.g. selvi.meenakshi@tn.health.gov.in"
                      value={emailOrMobile}
                      onChange={(e) => setEmailOrMobile(e.target.value)}
                      className="w-full px-3.5 py-2.5 rounded-xl bg-black/50 border border-white/10 text-white placeholder-neutral-600 text-xs focus:outline-none focus:border-teal-400 transition-colors"
                    />
                  </div>

                  <div>
                    <label className="block text-xs font-medium text-neutral-300 mb-1">Password</label>
                    <input
                      type="password"
                      id="worker-signin-password"
                      required
                      placeholder="••••••••"
                      value={password}
                      onChange={(e) => setPassword(e.target.value)}
                      className="w-full px-3.5 py-2.5 rounded-xl bg-black/50 border border-white/10 text-white placeholder-neutral-600 text-xs focus:outline-none focus:border-teal-400 transition-colors"
                    />
                  </div>

                  <div className="pt-2">
                    <button
                      type="submit"
                      id="btn-worker-signin"
                      disabled={loading}
                      className="w-full py-3 px-4 rounded-xl bg-teal-400 hover:bg-teal-300 text-black font-semibold text-xs transition-all shadow-lg flex items-center justify-center gap-2 disabled:opacity-50"
                    >
                      {loading ? (
                        <>
                          <span className="w-4 h-4 border-2 border-black border-t-transparent rounded-full animate-spin" />
                          <span>Verifying Credentials...</span>
                        </>
                      ) : (
                        <span>Sign In as Healthcare Worker</span>
                      )}
                    </button>
                  </div>
                </form>
              )}

              {/* Registration Form with Cascading Location Hierarchy */}
              {activeTab === 'register' && (
                <form onSubmit={handleRegister} className="space-y-3">
                  <div>
                    <label className="block text-xs font-medium text-neutral-300 mb-1">Full Name</label>
                    <input
                      type="text"
                      id="worker-reg-fullname"
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
                        id="worker-reg-profid"
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
                        id="worker-reg-mobile"
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
                      id="worker-reg-email"
                      required
                      placeholder="e.g. lakshmi.anm@health.tn.gov.in"
                      value={regEmail}
                      onChange={(e) => setRegEmail(e.target.value)}
                      className="w-full px-3.5 py-2.5 rounded-xl bg-black/50 border border-white/10 text-white placeholder-neutral-600 text-xs focus:outline-none focus:border-teal-400"
                    />
                  </div>

                  {/* 3-TIER CASCADING LOCATION HIERARCHY: STATE -> DISTRICT -> CENTRE */}
                  <div className="p-4 rounded-2xl bg-white/[0.02] border border-white/10 space-y-3">
                    <div className="flex items-center gap-2">
                      <span className="w-1.5 h-1.5 rounded-full bg-teal-400" />
                      <span className="text-xs font-semibold text-neutral-200">
                        Primary Healthcare Centre
                      </span>
                    </div>

                    <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
                      {/* Step 1: State Dropdown */}
                      <div>
                        <label className="block text-[11px] font-medium text-neutral-300 mb-1">State</label>
                        <div className="relative">
                          <select
                            id="worker-reg-state"
                            required
                            value={selectedStateId}
                            onChange={handleStateChange}
                            className="w-full h-10 px-3 pr-8 rounded-xl bg-black/60 border border-white/10 text-white text-xs focus:outline-none focus:border-teal-400 hover:border-white/20 transition-all appearance-none cursor-pointer truncate"
                          >
                            <option value="">{loadingStates ? 'Loading states...' : 'Select State'}</option>
                            {states.map((s) => (
                              <option key={s.id} value={s.id} className="bg-[#121216] text-white">
                                {s.name}
                              </option>
                            ))}
                          </select>
                          <div className="pointer-events-none absolute inset-y-0 right-0 flex items-center px-2 text-neutral-400">
                            <svg className="w-3.5 h-3.5" viewBox="0 0 20 20" fill="currentColor">
                              <path fillRule="evenodd" d="M5.293 7.293a1 1 0 011.414 0L10 10.586l3.293-3.293a1 1 0 111.414 1.414l-4 4a1 1 0 01-1.414 0l-4-4a1 1 0 010-1.414z" clipRule="evenodd" />
                            </svg>
                          </div>
                        </div>
                      </div>

                      {/* Step 2: District Dropdown */}
                      <div>
                        <label className="block text-[11px] font-medium text-neutral-300 mb-1">District</label>
                        <div className="relative">
                          <select
                            id="worker-reg-district"
                            required
                            disabled={!selectedStateId || loadingDistricts}
                            value={selectedDistrictId}
                            onChange={handleDistrictChange}
                            className="w-full h-10 px-3 pr-8 rounded-xl bg-black/60 border border-white/10 text-white text-xs focus:outline-none focus:border-teal-400 hover:border-white/20 transition-all appearance-none cursor-pointer truncate disabled:opacity-40 disabled:cursor-not-allowed disabled:hover:border-white/10"
                          >
                            {!selectedStateId ? (
                              <option value="">Select State First</option>
                            ) : loadingDistricts ? (
                              <option value="">Loading districts...</option>
                            ) : districts.length === 0 ? (
                              <option value="">No districts found for this state</option>
                            ) : (
                              <>
                                <option value="">Select District</option>
                                {districts.map((d) => (
                                  <option key={d.id} value={d.id} className="bg-[#121216] text-white">
                                    {d.name}
                                  </option>
                                ))}
                              </>
                            )}
                          </select>
                          <div className="pointer-events-none absolute inset-y-0 right-0 flex items-center px-2 text-neutral-400">
                            <svg className="w-3.5 h-3.5" viewBox="0 0 20 20" fill="currentColor">
                              <path fillRule="evenodd" d="M5.293 7.293a1 1 0 011.414 0L10 10.586l3.293-3.293a1 1 0 111.414 1.414l-4 4a1 1 0 01-1.414 0l-4-4a1 1 0 010-1.414z" clipRule="evenodd" />
                            </svg>
                          </div>
                        </div>
                      </div>

                      {/* Step 3: Centre Dropdown */}
                      <div>
                        <label className="block text-[11px] font-medium text-neutral-300 mb-1">Centre</label>
                        <div className="relative">
                          <select
                            id="worker-reg-centre"
                            required
                            disabled={!selectedDistrictId || loadingCentres}
                            value={selectedCentreId}
                            onChange={(e) => setSelectedCentreId(e.target.value ? Number(e.target.value) : '')}
                            className="w-full h-10 px-3 pr-8 rounded-xl bg-black/60 border border-white/10 text-white text-xs focus:outline-none focus:border-teal-400 hover:border-white/20 transition-all appearance-none cursor-pointer truncate disabled:opacity-40 disabled:cursor-not-allowed disabled:hover:border-white/10"
                          >
                            {!selectedDistrictId ? (
                              <option value="">Select District First</option>
                            ) : loadingCentres ? (
                              <option value="">Loading healthcare centres...</option>
                            ) : centres.length === 0 ? (
                              <option value="">No healthcare centres available for this district.</option>
                            ) : (
                              <>
                                <option value="">Select Centre</option>
                                {centres.map((c) => (
                                  <option key={c.id} value={c.id} className="bg-[#121216] text-white">
                                    {c.name}
                                  </option>
                                ))}
                              </>
                            )}
                          </select>
                          <div className="pointer-events-none absolute inset-y-0 right-0 flex items-center px-2 text-neutral-400">
                            <svg className="w-3.5 h-3.5" viewBox="0 0 20 20" fill="currentColor">
                              <path fillRule="evenodd" d="M5.293 7.293a1 1 0 011.414 0L10 10.586l3.293-3.293a1 1 0 111.414 1.414l-4 4a1 1 0 01-1.414 0l-4-4a1 1 0 010-1.414z" clipRule="evenodd" />
                            </svg>
                          </div>
                        </div>
                      </div>
                    </div>
                  </div>

                  <div className="grid grid-cols-2 gap-3">
                    <div>
                      <label className="block text-xs font-medium text-neutral-300 mb-1">Password</label>
                      <input
                        type="password"
                        id="worker-reg-password"
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
                        id="worker-reg-confirmpassword"
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
                      id="btn-worker-register-submit"
                      disabled={loading}
                      className="w-full py-3 px-4 rounded-xl bg-teal-400 hover:bg-teal-300 text-black font-semibold text-xs transition-all shadow-lg flex items-center justify-center gap-2 disabled:opacity-50"
                    >
                      {loading ? (
                        <>
                          <span className="w-4 h-4 border-2 border-black border-t-transparent rounded-full animate-spin" />
                          <span>Submitting Registration...</span>
                        </>
                      ) : (
                        <span>Submit Registration for Verification</span>
                      )}
                    </button>
                  </div>
                </form>
              )}
            </div>
          </div>
        </div>
      </main>

      {/* Registration Pending Verification Modal */}
      {registrationSuccess && (
        <div className="fixed inset-0 z-50 bg-black/80 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="max-w-md w-full bg-[#0d0e12] border border-teal-500/30 rounded-3xl p-6 lg:p-8 shadow-2xl relative animate-in fade-in zoom-in duration-200">
            <div className="w-12 h-12 rounded-2xl bg-teal-500/10 border border-teal-500/30 flex items-center justify-center text-teal-400 mb-4 mx-auto">
              <svg className="w-6 h-6" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z" />
                <path d="M12 8v4" />
                <path d="M12 16h.01" />
              </svg>
            </div>

            <div className="text-center mb-6">
              <div className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-amber-500/10 border border-amber-500/20 text-amber-300 text-[11px] font-mono mb-2">
                STATUS: {registrationSuccess.status}
              </div>
              <h3 className="text-xl font-bold font-['Syne'] text-white mb-2">
                Registration Submitted Successfully
              </h3>
              <p className="text-xs text-neutral-300 leading-relaxed">
                Thank you, <span className="text-white font-semibold">{registrationSuccess.name}</span>. Your healthcare worker registration has been recorded in the database.
              </p>
            </div>

            <div className="p-3.5 rounded-xl bg-white/[0.03] border border-white/10 mb-6 text-xs text-neutral-400 space-y-2">
              <p className="flex items-center gap-2">
                <span className="text-amber-400 font-bold">ℹ</span>
                <span>Your account is currently <strong>pending administrative verification</strong>.</span>
              </p>
              <p className="text-[11px] text-neutral-400">
                In compliance with health mission policy, you cannot sign in until credentials are verified against the administrative registry.
              </p>
            </div>

            <button
              type="button"
              id="btn-worker-pending-dismiss"
              onClick={() => {
                setRegistrationSuccess(null);
                setActiveTab('signin');
              }}
              className="w-full py-3 px-4 rounded-xl bg-teal-400 hover:bg-teal-300 text-black font-semibold text-xs transition-all shadow-md"
            >
              Proceed to Sign In
            </button>
          </div>
        </div>
      )}

      {/* Footer */}
      <footer className="px-6 py-4 text-center text-[11px] text-neutral-600 border-t border-white/5">
        RuralDR-XAI · Encrypted Medical Tele-Screening · SIH26038 Compliance
      </footer>
    </div>
  );
};

export default WorkerLoginPage;
