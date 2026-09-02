import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { useAuth } from '@/context/AuthContext';
import { AppHeader } from '@/components/layout/AppHeader';
import { caseService } from '@/services/caseService';
import { ScreeningCase } from '@/types/api';

const WorkerDashboardPage: React.FC = () => {
  const { user } = useAuth();

  const [cases, setCases] = useState<ScreeningCase[]>([]);
  const [metrics, setMetrics] = useState({
    todayScreenings: 0,
    pendingReview: 0,
    referredCases: 0,
    completedCases: 0,
  });
  const [searchQuery, setSearchQuery] = useState('');

  useEffect(() => {
    const loadedCases = caseService.getAllCases();
    setCases(loadedCases);
    setMetrics(caseService.getWorkerMetrics());
  }, []);

  const filteredCases = cases.filter((c) => {
    if (!searchQuery.trim()) return true;
    const q = searchQuery.toLowerCase();
    return (
      c.id.toLowerCase().includes(q) ||
      c.patient.patientId.toLowerCase().includes(q) ||
      c.location.district.toLowerCase().includes(q) ||
      c.screeningResult?.classification.severity.toLowerCase().includes(q)
    );
  });

  const getGreeting = () => {
    const hour = new Date().getHours();
    if (hour < 12) return 'Good morning';
    if (hour < 17) return 'Good afternoon';
    return 'Good evening';
  };

  const getSeverityBadge = (grade?: number) => {
    switch (grade) {
      case 0:
        return <span className="px-2 py-0.5 rounded text-[11px] font-semibold bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">Grade 0 · No DR</span>;
      case 1:
        return <span className="px-2 py-0.5 rounded text-[11px] font-semibold bg-lime-500/10 text-lime-400 border border-lime-500/20">Grade 1 · Mild NPDR</span>;
      case 2:
        return <span className="px-2 py-0.5 rounded text-[11px] font-semibold bg-amber-500/10 text-amber-400 border border-amber-500/20">Grade 2 · Moderate NPDR</span>;
      case 3:
        return <span className="px-2 py-0.5 rounded text-[11px] font-semibold bg-orange-500/10 text-orange-400 border border-orange-500/20">Grade 3 · Severe NPDR</span>;
      case 4:
        return <span className="px-2 py-0.5 rounded text-[11px] font-semibold bg-red-500/10 text-red-400 border border-red-500/20">Grade 4 · PDR</span>;
      default:
        return <span className="px-2 py-0.5 rounded text-[11px] font-semibold bg-white/5 text-neutral-400 border border-white/10">Under Analysis</span>;
    }
  };

  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'COMPLETED':
      case 'CLINICAL_DECISION':
        return <span className="px-2 py-0.5 rounded text-[10px] font-mono uppercase bg-emerald-500/10 text-emerald-300 border border-emerald-500/20">Completed</span>;
      case 'REFERRED':
      case 'DOCTOR_REVIEW':
        return <span className="px-2 py-0.5 rounded text-[10px] font-mono uppercase bg-amber-500/10 text-amber-300 border border-amber-500/20">Sent to Doctor</span>;
      case 'NO_REFERRAL':
        return <span className="px-2 py-0.5 rounded text-[10px] font-mono uppercase bg-blue-500/10 text-blue-300 border border-blue-500/20">Routine Followup</span>;
      default:
        return <span className="px-2 py-0.5 rounded text-[10px] font-mono uppercase bg-white/10 text-neutral-300">Active</span>;
    }
  };

  return (
    <div className="min-h-screen bg-[#070709] text-white flex flex-col">
      <AppHeader />

      <main className="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Welcome Banner */}
        <div className="mb-8 p-6 sm:p-8 rounded-3xl bg-gradient-to-r from-[#121217] via-[#0d1417] to-[#0a1816] border border-white/[0.08] relative overflow-hidden flex flex-col md:flex-row md:items-center justify-between gap-6">
          <div className="relative z-10 max-w-xl">
            <div className="inline-flex items-center gap-2 px-2.5 py-1 rounded-full bg-teal-500/10 border border-teal-500/20 text-teal-400 text-xs font-mono mb-3">
              <span>{user?.centerName || 'Rural Primary Health Centre'}</span>
            </div>
            <h1 className="text-2xl sm:text-3xl font-bold font-['Syne'] text-white mb-2">
              {getGreeting()}, {user?.name || 'Healthcare Worker'}
            </h1>
            <p className="text-neutral-400 text-xs sm:text-sm">
              Ready to screen your next patient? Early detection protects rural patients from irreversible vision loss.
            </p>
          </div>

          <div className="relative z-10 flex-shrink-0">
            <Link
              to="/worker/new-screening"
              className="inline-flex items-center gap-2.5 px-6 py-4 rounded-2xl bg-white hover:bg-teal-400 text-black font-bold text-sm transition-all shadow-xl hover:shadow-teal-900/20 hover:scale-[1.02] active:scale-[0.98]"
            >
              <span className="text-lg leading-none">+</span>
              <span>New Retinal Screening</span>
            </Link>
          </div>

          {/* Decorative glow */}
          <div className="absolute right-0 top-0 w-80 h-80 bg-teal-500/10 rounded-full blur-3xl pointer-events-none" />
        </div>

        {/* Quick Status Metrics (No Pie Charts) */}
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
          <div className="p-5 rounded-2xl bg-[#0c0d12] border border-white/[0.06] hover:border-white/10 transition-colors">
            <div className="flex items-center justify-between text-neutral-400 text-xs font-medium mb-3">
              <span>Today's Screenings</span>
              <span className="w-2 h-2 rounded-full bg-teal-400" />
            </div>
            <p className="text-3xl font-bold font-['Syne'] text-white tracking-tight">{metrics.todayScreenings}</p>
            <p className="text-[11px] text-neutral-500 mt-1">Screened at current centre</p>
          </div>

          <div className="p-5 rounded-2xl bg-[#0c0d12] border border-white/[0.06] hover:border-white/10 transition-colors">
            <div className="flex items-center justify-between text-neutral-400 text-xs font-medium mb-3">
              <span>Pending Review</span>
              <span className="w-2 h-2 rounded-full bg-amber-400 animate-pulse" />
            </div>
            <p className="text-3xl font-bold font-['Syne'] text-amber-400 tracking-tight">{metrics.pendingReview}</p>
            <p className="text-[11px] text-neutral-500 mt-1">Awaiting doctor triage</p>
          </div>

          <div className="p-5 rounded-2xl bg-[#0c0d12] border border-white/[0.06] hover:border-white/10 transition-colors">
            <div className="flex items-center justify-between text-neutral-400 text-xs font-medium mb-3">
              <span>Referred Cases</span>
              <span className="w-2 h-2 rounded-full bg-orange-400" />
            </div>
            <p className="text-3xl font-bold font-['Syne'] text-orange-400 tracking-tight">{metrics.referredCases}</p>
            <p className="text-[11px] text-neutral-500 mt-1">Transferred to eye hospital</p>
          </div>

          <div className="p-5 rounded-2xl bg-[#0c0d12] border border-white/[0.06] hover:border-white/10 transition-colors">
            <div className="flex items-center justify-between text-neutral-400 text-xs font-medium mb-3">
              <span>Completed Cases</span>
              <span className="w-2 h-2 rounded-full bg-emerald-400" />
            </div>
            <p className="text-3xl font-bold font-['Syne'] text-emerald-400 tracking-tight">{metrics.completedCases}</p>
            <p className="text-[11px] text-neutral-500 mt-1">Closed / Normal reports</p>
          </div>
        </div>

        {/* Recent Cases Section */}
        <div className="rounded-3xl bg-[#0c0d12] border border-white/[0.06] overflow-hidden">
          {/* Header & Search */}
          <div className="p-6 border-b border-white/[0.06] flex flex-col sm:flex-row sm:items-center justify-between gap-4">
            <div>
              <h2 className="text-lg font-bold font-['Syne'] text-white">Recent Screening Cases</h2>
              <p className="text-xs text-neutral-400">All patient fundus captures submitted from this health centre</p>
            </div>

            <div className="flex items-center gap-3">
              <div className="relative w-full sm:w-64">
                <input
                  type="text"
                  placeholder="Search case, patient ID..."
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  className="w-full pl-9 pr-4 py-2 rounded-xl bg-black/50 border border-white/10 text-xs text-white placeholder-neutral-500 focus:outline-none focus:border-teal-400 transition-colors"
                />
                <svg
                  className="absolute left-3 top-2.5 text-neutral-500"
                  width="14"
                  height="14"
                  viewBox="0 0 24 24"
                  fill="none"
                  stroke="currentColor"
                  strokeWidth="2"
                >
                  <circle cx="11" cy="11" r="8" />
                  <line x1="21" y1="21" x2="16.65" y2="16.65" />
                </svg>
              </div>
            </div>
          </div>

          {/* Cases Table */}
          <div className="overflow-x-auto">
            <table className="w-full text-left border-collapse">
              <thead>
                <tr className="border-b border-white/[0.04] bg-white/[0.01] text-[11px] font-mono text-neutral-400 uppercase tracking-wider">
                  <th className="py-3.5 px-6">Case ID</th>
                  <th className="py-3.5 px-4">Patient</th>
                  <th className="py-3.5 px-4">Location</th>
                  <th className="py-3.5 px-4">AI Result</th>
                  <th className="py-3.5 px-4">Referral Status</th>
                  <th className="py-3.5 px-4">Status</th>
                  <th className="py-3.5 px-6 text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-white/[0.03] text-xs">
                {filteredCases.map((c) => (
                  <tr key={c.id} className="hover:bg-white/[0.02] transition-colors group">
                    <td className="py-4 px-6 font-mono font-semibold text-white">
                      {c.id}
                      <span className="block text-[10px] font-normal text-neutral-500">
                        {new Date(c.createdAt).toLocaleDateString('en-IN', { month: 'short', day: 'numeric' })}
                      </span>
                    </td>
                    <td className="py-4 px-4">
                      <span className="font-semibold text-neutral-200">{c.patient.patientId}</span>
                      <span className="block text-[11px] text-neutral-400">
                        {c.patient.age}y · {c.patient.gender}
                      </span>
                    </td>
                    <td className="py-4 px-4">
                      <span className="text-neutral-300">{c.location.district}</span>
                      <span className="block text-[10px] text-neutral-500 truncate max-w-[140px]">
                        {c.location.centerName}
                      </span>
                    </td>
                    <td className="py-4 px-4">{getSeverityBadge(c.screeningResult?.classification.dr_grade)}</td>
                    <td className="py-4 px-4">
                      {c.referral?.required ? (
                        <div>
                          <span className="text-amber-300 font-medium text-[11px] flex items-center gap-1">
                            <span>Referred</span>
                            <span className="text-[10px] text-neutral-400">→</span>
                          </span>
                          <span className="text-[10px] text-neutral-400 truncate max-w-[150px] block">
                            {c.referral.hospital?.name || 'Eye Hospital'}
                          </span>
                        </div>
                      ) : (
                        <span className="text-neutral-400 text-[11px]">No Referral Required</span>
                      )}
                    </td>
                    <td className="py-4 px-4">{getStatusBadge(c.status)}</td>
                    <td className="py-4 px-6 text-right">
                      <Link
                        to={`/report/${c.id}`}
                        className="inline-flex items-center gap-1 px-3 py-1.5 rounded-lg bg-white/5 hover:bg-white/10 border border-white/10 text-neutral-200 text-xs font-medium transition-colors"
                      >
                        <span>View Report</span>
                        <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                          <path d="M5 12h14" />
                          <path d="M12 5l7 7-7 7" />
                        </svg>
                      </Link>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>

            {filteredCases.length === 0 && (
              <div className="py-12 text-center text-neutral-500 text-xs">
                No matching screening cases found.
              </div>
            )}
          </div>
        </div>
      </main>
    </div>
  );
};

export default WorkerDashboardPage;
