import React from 'react';
import { Link, useNavigate, useLocation } from 'react-router-dom';
import { useAuth } from '@/context/AuthContext';

export const AppHeader: React.FC = () => {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();

  const handleLogout = () => {
    logout();
    navigate('/');
  };

  const isWorker = user?.role === 'worker';
  const isDoctor = user?.role === 'doctor';

  return (
    <header className="sticky top-0 z-40 bg-[#070707]/90 backdrop-blur-md border-b border-white/[0.07]">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-16">
          {/* Brand Logo & Clinical Workspace Indicator */}
          <div className="flex items-center gap-4">
            <Link to={isWorker ? '/worker/dashboard' : '/doctor/dashboard'} className="flex items-center gap-3 group">
              <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-red-600/30 to-teal-500/20 border border-white/10 flex items-center justify-center group-hover:border-white/20 transition-all">
                <svg width="18" height="18" viewBox="0 0 24 24" fill="none">
                  <circle cx="12" cy="12" r="10" stroke="rgba(255,255,255,0.4)" strokeWidth="1.5" />
                  <circle cx="12" cy="12" r="5" stroke="#06b6d4" strokeWidth="1.5" />
                  <circle cx="12" cy="12" r="2" fill="#ef4444" />
                </svg>
              </div>
              <div>
                <div className="flex items-center gap-2">
                  <span className="font-bold text-white text-sm tracking-wider font-['Syne']">RuralDR-XAI</span>
                  <span className="text-[10px] font-mono px-1.5 py-0.5 rounded bg-white/5 border border-white/10 text-neutral-400">
                    SIH26038
                  </span>
                </div>
                <p className="text-[11px] text-neutral-400 font-medium">
                  {isWorker ? 'Rural Screening Workspace' : 'Clinical Diagnostic Queue'}
                </p>
              </div>
            </Link>

            {/* Dynamic Database Verification Status Badge */}
            <div className="hidden md:flex items-center gap-2 pl-4 border-l border-white/10">
              {isWorker && (
                user?.verificationStatus === 'VERIFIED' ? (
                  <div className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-teal-500/10 border border-teal-500/20 text-teal-400 text-xs font-medium">
                    <span className="w-1.5 h-1.5 rounded-full bg-teal-400 animate-pulse" />
                    <span>Healthcare Worker</span>
                    <span className="text-teal-300/80 font-mono text-[10px]">✓ Verified</span>
                  </div>
                ) : user?.verificationStatus === 'REJECTED' ? (
                  <div className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-red-500/10 border border-red-500/20 text-red-400 text-xs font-medium">
                    <span className="w-1.5 h-1.5 rounded-full bg-red-400" />
                    <span>Registration Rejected</span>
                  </div>
                ) : (
                  <div className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-amber-500/10 border border-amber-500/20 text-amber-300 text-xs font-medium" title="National Health Mission verification pending">
                    <span className="w-1.5 h-1.5 rounded-full bg-amber-400 animate-ping" />
                    <span>Verification Pending</span>
                  </div>
                )
              )}
              {isDoctor && (
                user?.verificationStatus === 'VERIFIED' ? (
                  <div className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-emerald-500/10 border border-emerald-500/20 text-emerald-400 text-xs font-medium">
                    <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse" />
                    <span>Medical Professional Verified</span>
                    {user?.regNumber && (
                      <span className="text-emerald-300/70 font-mono text-[10px] border-l border-emerald-500/20 pl-1.5">
                        {user.regNumber}
                      </span>
                    )}
                  </div>
                ) : user?.verificationStatus === 'REJECTED' ? (
                  <div className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-red-500/10 border border-red-500/20 text-red-400 text-xs font-medium">
                    <span className="w-1.5 h-1.5 rounded-full bg-red-400" />
                    <span>Council Registration Rejected</span>
                  </div>
                ) : (
                  <div className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-amber-500/10 border border-amber-500/20 text-amber-300 text-xs font-medium" title="Medical Council verification pending">
                    <span className="w-1.5 h-1.5 rounded-full bg-amber-400 animate-ping" />
                    <span>NMC Verification Pending</span>
                  </div>
                )
              )}
            </div>
          </div>

          {/* Navigation Links based on role */}
          <nav className="flex items-center gap-2 sm:gap-4">
            {isWorker && (
              <>
                <Link
                  to="/worker/dashboard"
                  className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-all ${
                    location.pathname === '/worker/dashboard'
                      ? 'bg-white/10 text-white'
                      : 'text-neutral-400 hover:text-white hover:bg-white/5'
                  }`}
                >
                  Dashboard
                </Link>
                <Link
                  to="/worker/new-screening"
                  className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-all flex items-center gap-1.5 ${
                    location.pathname === '/worker/new-screening'
                      ? 'bg-red-500/20 text-red-200 border border-red-500/30'
                      : 'bg-white text-black font-semibold hover:bg-neutral-200'
                  }`}
                >
                  <span className="text-sm leading-none">+</span>
                  <span>New Screening</span>
                </Link>
              </>
            )}

            {isDoctor && (
              <>
                <Link
                  to="/doctor/dashboard"
                  className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-all ${
                    location.pathname === '/doctor/dashboard'
                      ? 'bg-white/10 text-white'
                      : 'text-neutral-400 hover:text-white hover:bg-white/5'
                  }`}
                >
                  Review Queue
                </Link>
              </>
            )}

            {/* Notifications badge */}
            <button
              title="System Notifications"
              className="p-2 rounded-lg text-neutral-400 hover:text-white hover:bg-white/5 transition-colors relative"
            >
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <path d="M18 8A6 6 0 0 0 6 8c0 7-3 9-3 9h18s-3-2-3-9" />
                <path d="M13.73 21a2 2 0 0 1-3.46 0" />
              </svg>
              <span className="absolute top-1.5 right-1.5 w-2 h-2 rounded-full bg-teal-400 animate-ping" />
              <span className="absolute top-1.5 right-1.5 w-2 h-2 rounded-full bg-teal-400" />
            </button>

            {/* User Profile Pill & Logout */}
            <div className="flex items-center gap-2 pl-2 border-l border-white/10">
              <div className="hidden sm:block text-right">
                <p className="text-xs font-medium text-white truncate max-w-[130px]">{user?.name || 'User'}</p>
                <p className="text-[10px] text-neutral-400 truncate max-w-[130px]">
                  {isWorker ? user?.centerName || 'Health Centre' : user?.regNumber || 'Ophthalmologist'}
                </p>
              </div>

              <button
                onClick={handleLogout}
                className="px-2.5 py-1.5 rounded-lg text-xs font-medium text-neutral-400 hover:text-red-400 hover:bg-red-500/10 border border-transparent hover:border-red-500/20 transition-all flex items-center gap-1"
                title="Sign out of current workspace"
              >
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4" />
                  <polyline points="16 17 21 12 16 7" />
                  <line x1="21" y1="12" x2="9" y2="12" />
                </svg>
                <span className="hidden md:inline">Sign Out</span>
              </button>
            </div>
          </nav>
        </div>
      </div>
    </header>
  );
};
