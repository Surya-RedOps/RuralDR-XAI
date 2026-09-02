import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { useAuth } from '@/context/AuthContext';
import { AppHeader } from '@/components/layout/AppHeader';
import { caseService } from '@/services/caseService';
import { ScreeningCase } from '@/types/api';

const DoctorDashboardPage: React.FC = () => {
  const { user } = useAuth();

  const [cases, setCases] = useState<ScreeningCase[]>([]);
  const [metrics, setMetrics] = useState({
    urgentCases: 0,
    newReferrals: 0,
    underReview: 0,
    completed: 0,
  });
  const [filterPriority, setFilterPriority] = useState<string>('ALL');
  const [searchQuery, setSearchQuery] = useState('');

  useEffect(() => {
    const loadedCases = caseService.getAllCases();
    setCases(loadedCases);
    setMetrics(caseService.getDoctorMetrics());
  }, []);

  const filteredCases = cases.filter((c) => {
    // Only show cases relevant to clinical review queue (referred or requiring doctor input)
    if (filterPriority !== 'ALL' && c.priority !== filterPriority) {
      return false;
    }

    if (!searchQuery.trim()) return true;
    const q = searchQuery.toLowerCase();
    return (
      c.id.toLowerCase().includes(q) ||
      c.patient.patientId.toLowerCase().includes(q) ||
      c.location.district.toLowerCase().includes(q) ||
      c.screeningResult?.classification.severity.toLowerCase().includes(q)
    );
  });

  const getPriorityBadge = (priority: string) => {
    switch (priority) {
      case 'CRITICAL':
        return <span className="px-2.5 py-1 rounded-full text-[10px] font-mono font-bold bg-red-500/20 text-red-300 border border-red-500/40 animate-pulse">CRITICAL · LEVEL 4</span>;
      case 'HIGH':
        return <span className="px-2.5 py-1 rounded-full text-[10px] font-mono font-bold bg-orange-500/20 text-orange-300 border border-orange-500/40">HIGH · LEVEL 3</span>;
      case 'MEDIUM':
        return <span className="px-2.5 py-1 rounded-full text-[10px] font-mono font-bold bg-amber-500/20 text-amber-300 border border-amber-500/40">MEDIUM · LEVEL 2</span>;
      case 'REVIEW':
        return <span className="px-2.5 py-1 rounded-full text-[10px] font-mono font-bold bg-lime-500/20 text-lime-300 border border-lime-500/40">REVIEW · LEVEL 1</span>;
      default:
        return <span className="px-2.5 py-1 rounded-full text-[10px] font-mono font-bold bg-white/10 text-neutral-400">ROUTINE</span>;
    }
  };

  const getTimeAgo = (dateStr: string) => {
    const diffMs = Date.now() - new Date(dateStr).getTime();
    const diffMins = Math.floor(diffMs / 60000);
    if (diffMins < 1) return 'Just now';
    if (diffMins < 60) return `${diffMins} min ago`;
    const diffHours = Math.floor(diffMins / 60);
    if (diffHours < 24) return `${diffHours} hr ago`;
    return new Date(dateStr).toLocaleDateString('en-IN', { month: 'short', day: 'numeric' });
  };

  return (
    <div className="min-h-screen bg-[#060608] text-white flex flex-col">
      <AppHeader />

      <main className="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Doctor Workspace Header */}
        <div className="mb-8 flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div>
            <div className="inline-flex items-center gap-2 px-2.5 py-1 rounded-full bg-emerald-500/10 border border-emerald-500/20 text-emerald-400 text-xs font-mono mb-2">
              <span>{user?.regNumber || 'Medical Council Verified'} · {user?.centerName || 'Regional Eye Centre'}</span>
            </div>
            <h1 className="text-2xl sm:text-3xl font-bold font-['Syne'] text-white">
              Clinical Review Queue
            </h1>
            <p className="text-xs sm:text-sm text-neutral-400 mt-1">
              AI-assisted retinal screening cases requiring ophthalmologist evaluation and clinical decision.
            </p>
          </div>

          <div className="flex items-center gap-3">
            <span className="text-xs font-mono text-neutral-400">Triage Priority: Level 4 → Level 1</span>
          </div>
        </div>

        {/* Quick Status Metrics (No Pie Charts) */}
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
          <div className="p-5 rounded-2xl bg-[#0b0c10] border border-red-500/20 hover:border-red-500/40 transition-colors">
            <div className="flex items-center justify-between text-neutral-400 text-xs font-medium mb-3">
              <span>Urgent Cases (PDR / Severe)</span>
              <span className="w-2 h-2 rounded-full bg-red-500 animate-ping" />
            </div>
            <p className="text-3xl font-bold font-['Syne'] text-red-400 tracking-tight">{metrics.urgentCases}</p>
            <p className="text-[11px] text-neutral-500 mt-1">Requires immediate review</p>
          </div>

          <div className="p-5 rounded-2xl bg-[#0b0c10] border border-white/[0.06] hover:border-white/10 transition-colors">
            <div className="flex items-center justify-between text-neutral-400 text-xs font-medium mb-3">
              <span>New Referrals</span>
              <span className="w-2 h-2 rounded-full bg-amber-400" />
            </div>
            <p className="text-3xl font-bold font-['Syne'] text-amber-400 tracking-tight">{metrics.newReferrals}</p>
            <p className="text-[11px] text-neutral-500 mt-1">Awaiting clinical review</p>
          </div>

          <div className="p-5 rounded-2xl bg-[#0b0c10] border border-white/[0.06] hover:border-white/10 transition-colors">
            <div className="flex items-center justify-between text-neutral-400 text-xs font-medium mb-3">
              <span>Under Review</span>
              <span className="w-2 h-2 rounded-full bg-cyan-400" />
            </div>
            <p className="text-3xl font-bold font-['Syne'] text-cyan-400 tracking-tight">{metrics.underReview}</p>
            <p className="text-[11px] text-neutral-500 mt-1">In examination progress</p>
          </div>

          <div className="p-5 rounded-2xl bg-[#0b0c10] border border-white/[0.06] hover:border-white/10 transition-colors">
            <div className="flex items-center justify-between text-neutral-400 text-xs font-medium mb-3">
              <span>Decisions Completed</span>
              <span className="w-2 h-2 rounded-full bg-emerald-400" />
            </div>
            <p className="text-3xl font-bold font-['Syne'] text-emerald-400 tracking-tight">{metrics.completed}</p>
            <p className="text-[11px] text-neutral-500 mt-1">Reports digitally signed</p>
          </div>
        </div>

        {/* Clinical Case Queue Table */}
        <div className="rounded-3xl bg-[#0b0c10] border border-white/[0.08] overflow-hidden">
          {/* Filters & Search Toolbar */}
          <div className="p-6 border-b border-white/[0.06] flex flex-col md:flex-row md:items-center justify-between gap-4">
            {/* Priority Tabs */}
            <div className="flex flex-wrap items-center gap-1 bg-black/40 p-1 rounded-xl border border-white/5">
              {[
                { key: 'ALL', label: 'All Cases' },
                { key: 'CRITICAL', label: 'Critical (PDR)' },
                { key: 'HIGH', label: 'High (Severe)' },
                { key: 'MEDIUM', label: 'Medium (Moderate)' },
              ].map((tab) => (
                <button
                  key={tab.key}
                  onClick={() => setFilterPriority(tab.key)}
                  className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-all ${
                    filterPriority === tab.key
                      ? 'bg-white text-black font-semibold shadow-sm'
                      : 'text-neutral-400 hover:text-white hover:bg-white/5'
                  }`}
                >
                  {tab.label}
                </button>
              ))}
            </div>

            {/* Search */}
            <div className="relative w-full md:w-64">
              <input
                type="text"
                placeholder="Search case, district..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="w-full pl-9 pr-4 py-2 rounded-xl bg-black/50 border border-white/10 text-xs text-white placeholder-neutral-500 focus:outline-none focus:border-emerald-400 transition-colors"
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

          {/* Queue List */}
          <div className="overflow-x-auto">
            <table className="w-full text-left border-collapse">
              <thead>
                <tr className="border-b border-white/[0.04] bg-white/[0.01] text-[11px] font-mono text-neutral-400 uppercase tracking-wider">
                  <th className="py-3.5 px-6">Priority</th>
                  <th className="py-3.5 px-4">Case ID</th>
                  <th className="py-3.5 px-4">Origin / District</th>
                  <th className="py-3.5 px-4">AI DR Classification</th>
                  <th className="py-3.5 px-4">AI Confidence</th>
                  <th className="py-3.5 px-4">Received</th>
                  <th className="py-3.5 px-4">Review Status</th>
                  <th className="py-3.5 px-6 text-right">Clinical Action</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-white/[0.03] text-xs">
                {filteredCases.map((c) => (
                  <tr key={c.id} className="hover:bg-white/[0.02] transition-colors group">
                    <td className="py-4 px-6">{getPriorityBadge(c.priority)}</td>
                    <td className="py-4 px-4 font-mono font-bold text-white">
                      {c.id}
                      <span className="block text-[10px] font-normal text-neutral-500">
                        {c.patient.patientId} · {c.patient.age}y {c.patient.gender}
                      </span>
                    </td>
                    <td className="py-4 px-4">
                      <span className="text-neutral-200 font-medium">{c.location.district}</span>
                      <span className="block text-[10px] text-neutral-500 truncate max-w-[140px]">
                        {c.location.centerName}
                      </span>
                    </td>
                    <td className="py-4 px-4">
                      <span className="font-semibold text-white">
                        {c.screeningResult?.classification.severity || 'Analysis Pending'}
                      </span>
                      <span className="block text-[10px] text-neutral-400">
                        Quality: {c.screeningResult?.quality.score}% · FIQA Passed
                      </span>
                    </td>
                    <td className="py-4 px-4 font-mono text-neutral-300">
                      {c.screeningResult
                        ? `${Math.round(c.screeningResult.classification.confidence * 100)}%`
                        : '—'}
                    </td>
                    <td className="py-4 px-4 text-neutral-400 font-mono text-[11px]">
                      {getTimeAgo(c.createdAt)}
                    </td>
                    <td className="py-4 px-4">
                      {c.doctorReview ? (
                        <span className="px-2 py-0.5 rounded text-[10px] font-mono uppercase bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
                          ✓ Decision Signed
                        </span>
                      ) : (
                        <span className="px-2 py-0.5 rounded text-[10px] font-mono uppercase bg-amber-500/10 text-amber-300 border border-amber-500/20">
                          Pending Review
                        </span>
                      )}
                    </td>
                    <td className="py-4 px-6 text-right">
                      <Link
                        to={`/doctor/cases/${c.id}`}
                        className="inline-flex items-center gap-1.5 px-3.5 py-2 rounded-xl bg-white hover:bg-emerald-400 text-black font-semibold text-xs transition-colors shadow-sm"
                      >
                        <span>{c.doctorReview ? 'View Review' : 'Open Case'}</span>
                        <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
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
                No matching referred cases in the queue.
              </div>
            )}
          </div>
        </div>
      </main>
    </div>
  );
};

export default DoctorDashboardPage;
