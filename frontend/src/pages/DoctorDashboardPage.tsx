import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { useAuth } from '@/context/AuthContext';
import { AppHeader } from '@/components/layout/AppHeader';
import { caseService } from '@/services/caseService';

const DoctorDashboardPage: React.FC = () => {
  const { user } = useAuth();

  const [cases, setCases] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [metrics, setMetrics] = useState({
    totalCases: 0,
    newReferrals: 0,
    highPriority: 0,
    inReview: 0,
    completed: 0,
  });
  const [activeTab, setActiveTab] = useState<'ALL' | 'NEW' | 'HIGH_PRIORITY' | 'IN_REVIEW' | 'COMPLETED'>('ALL');
  const [searchQuery, setSearchQuery] = useState('');

  const loadData = async () => {
    setLoading(true);
    try {
      const data = await caseService.getDoctorCases();
      setCases(data.cases || []);
      setMetrics({
        totalCases: data.total_cases,
        newReferrals: data.new_referrals,
        highPriority: data.high_priority,
        inReview: data.in_review,
        completed: data.completed,
      });
    } catch (err) {
      console.error('Failed to load doctor cases:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  const filteredCases = cases.filter((c) => {
    if (activeTab === 'NEW' && c.status !== 'PENDING') return false;
    if (activeTab === 'HIGH_PRIORITY' && c.priority !== 'HIGH' && c.priority !== 'CRITICAL') return false;
    if (activeTab === 'IN_REVIEW' && c.status !== 'IN_REVIEW') return false;
    if (activeTab === 'COMPLETED' && c.status !== 'COMPLETED') return false;

    if (!searchQuery.trim()) return true;
    const q = searchQuery.toLowerCase();
    return (
      c.id.toLowerCase().includes(q) ||
      c.patientId.toLowerCase().includes(q) ||
      c.location.toLowerCase().includes(q) ||
      c.severity.toLowerCase().includes(q)
    );
  });

  const getPriorityBadge = (priority: string, grade: number) => {
    switch (priority) {
      case 'CRITICAL':
        return <span className="px-2.5 py-1 rounded-full text-[10px] font-mono font-bold bg-red-500/20 text-red-300 border border-red-500/40 animate-pulse">CRITICAL · LEVEL {grade}</span>;
      case 'HIGH':
        return <span className="px-2.5 py-1 rounded-full text-[10px] font-mono font-bold bg-orange-500/20 text-orange-300 border border-orange-500/40">HIGH · LEVEL {grade}</span>;
      case 'MEDIUM':
        return <span className="px-2.5 py-1 rounded-full text-[10px] font-mono font-bold bg-amber-500/20 text-amber-300 border border-amber-500/40">MEDIUM · LEVEL {grade}</span>;
      default:
        return <span className="px-2.5 py-1 rounded-full text-[10px] font-mono font-bold bg-lime-500/20 text-lime-300 border border-lime-500/40">REVIEW · LEVEL {grade}</span>;
    }
  };

  const getTimeAgo = (dateStr: string) => {
    try {
      const diffMs = Date.now() - new Date(dateStr).getTime();
      const diffMins = Math.floor(diffMs / 60000);
      if (diffMins < 1) return 'Just now';
      if (diffMins < 60) return `${diffMins} min ago`;
      const diffHours = Math.floor(diffMins / 60);
      if (diffHours < 24) return `${diffHours} hr ago`;
      return new Date(dateStr).toLocaleDateString('en-IN', { month: 'short', day: 'numeric' });
    } catch {
      return 'Recently';
    }
  };

  return (
    <div className="min-h-screen bg-[#060608] text-white flex flex-col">
      <AppHeader />

      <main className="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Doctor Workspace Header */}
        <div className="mb-8 flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div>
            <div className="inline-flex items-center gap-2 px-2.5 py-1 rounded-full bg-emerald-500/10 border border-emerald-500/20 text-emerald-400 text-xs font-mono mb-2">
              <span>{user?.regNumber || 'Medical Professional'} · {user?.centerName || 'Regional Eye Centre'}</span>
            </div>
            <h1 className="text-2xl sm:text-3xl font-bold font-['Syne'] text-white">
              Clinical Review Queue
            </h1>
            <p className="text-xs sm:text-sm text-neutral-400 mt-1">
              AI-assisted retinal screening cases requiring ophthalmologist evaluation and clinical decision.
            </p>
          </div>

          <div className="flex items-center gap-3">
            <span className="text-xs font-mono text-neutral-400">Clinical Priority: Level 4 Critical → Level 1 Review</span>
          </div>
        </div>

        {/* NMC Verification Status Banner if Pending or Rejected */}
        {user?.verificationStatus === 'PENDING' && (
          <div className="mb-6 p-4 rounded-2xl bg-amber-500/10 border border-amber-500/30 text-amber-200 flex items-start gap-3">
            <div className="p-1 rounded-full bg-amber-500/20 text-amber-400 mt-0.5">
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <circle cx="12" cy="12" r="10" />
                <line x1="12" y1="8" x2="12" y2="12" />
                <line x1="12" y1="16" x2="12.01" y2="16" />
              </svg>
            </div>
            <div>
              <h4 className="text-xs font-bold text-amber-300 uppercase tracking-wider font-mono">
                Medical Registry Verification Pending · National Medical Commission
              </h4>
              <p className="text-xs text-amber-200/80 mt-1 leading-relaxed">
                Your medical registration number ({user?.regNumber || 'Pending'}) is currently undergoing verification against the state/national medical council registry. You can inspect case images and AI activation maps; official diagnostic decision signatures will be unlocked upon registry confirmation.
              </p>
            </div>
          </div>
        )}

        {user?.verificationStatus === 'REJECTED' && (
          <div className="mb-6 p-4 rounded-2xl bg-red-500/10 border border-red-500/30 text-red-200 flex items-start gap-3">
            <div className="p-1 rounded-full bg-red-500/20 text-red-400 mt-0.5">
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <circle cx="12" cy="12" r="10" />
                <line x1="15" y1="9" x2="9" y2="15" />
                <line x1="9" y1="9" x2="15" y2="15" />
              </svg>
            </div>
            <div>
              <h4 className="text-xs font-bold text-red-300 uppercase tracking-wider font-mono">
                Medical Registration Rejected
              </h4>
              <p className="text-xs text-red-200/80 mt-1 leading-relaxed">
                Your medical registration number could not be validated with the Medical Council. Clinical review submission is prohibited.
              </p>
            </div>
          </div>
        )}

        {/* Quick Status Metrics */}
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
          <div
            onClick={() => setActiveTab('HIGH_PRIORITY')}
            className={`p-5 rounded-2xl bg-[#0b0c10] border cursor-pointer transition-all ${
              activeTab === 'HIGH_PRIORITY' ? 'border-red-500 ring-1 ring-red-500' : 'border-red-500/20 hover:border-red-500/40'
            }`}
          >
            <div className="flex items-center justify-between text-neutral-400 text-xs font-medium mb-3">
              <span>High Priority (PDR/Severe)</span>
              <span className="w-2 h-2 rounded-full bg-red-500 animate-ping" />
            </div>
            <p className="text-3xl font-bold font-['Syne'] text-red-400 tracking-tight">
              {loading ? '...' : metrics.highPriority}
            </p>
            <p className="text-[11px] text-neutral-500 mt-1">Requires fast-track review</p>
          </div>

          <div
            onClick={() => setActiveTab('NEW')}
            className={`p-5 rounded-2xl bg-[#0b0c10] border cursor-pointer transition-all ${
              activeTab === 'NEW' ? 'border-amber-500 ring-1 ring-amber-500' : 'border-amber-500/20 hover:border-amber-500/40'
            }`}
          >
            <div className="flex items-center justify-between text-neutral-400 text-xs font-medium mb-3">
              <span>New Referrals</span>
              <span className="w-2 h-2 rounded-full bg-amber-500" />
            </div>
            <p className="text-3xl font-bold font-['Syne'] text-amber-400 tracking-tight">
              {loading ? '...' : metrics.newReferrals}
            </p>
            <p className="text-[11px] text-neutral-500 mt-1">Awaiting initial inspection</p>
          </div>

          <div
            onClick={() => setActiveTab('IN_REVIEW')}
            className={`p-5 rounded-2xl bg-[#0b0c10] border cursor-pointer transition-all ${
              activeTab === 'IN_REVIEW' ? 'border-teal-500 ring-1 ring-teal-500' : 'border-teal-500/20 hover:border-teal-500/40'
            }`}
          >
            <div className="flex items-center justify-between text-neutral-400 text-xs font-medium mb-3">
              <span>Under Review</span>
              <span className="w-2 h-2 rounded-full bg-teal-400" />
            </div>
            <p className="text-3xl font-bold font-['Syne'] text-teal-300 tracking-tight">
              {loading ? '...' : metrics.inReview}
            </p>
            <p className="text-[11px] text-neutral-500 mt-1">In progress cases</p>
          </div>

          <div
            onClick={() => setActiveTab('COMPLETED')}
            className={`p-5 rounded-2xl bg-[#0b0c10] border cursor-pointer transition-all ${
              activeTab === 'COMPLETED' ? 'border-emerald-500 ring-1 ring-emerald-500' : 'border-emerald-500/20 hover:border-emerald-500/40'
            }`}
          >
            <div className="flex items-center justify-between text-neutral-400 text-xs font-medium mb-3">
              <span>Completed</span>
              <span className="w-2 h-2 rounded-full bg-emerald-500" />
            </div>
            <p className="text-3xl font-bold font-['Syne'] text-emerald-400 tracking-tight">
              {loading ? '...' : metrics.completed}
            </p>
            <p className="text-[11px] text-neutral-500 mt-1">Decisions submitted & reported</p>
          </div>
        </div>

        {/* Filter Tabs & Search Bar */}
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 mb-6">
          <div className="flex items-center gap-1.5 p-1 rounded-xl bg-[#0e0f14] border border-white/5 overflow-x-auto">
            {[
              { id: 'ALL', label: 'All Cases' },
              { id: 'NEW', label: 'New' },
              { id: 'HIGH_PRIORITY', label: 'High Priority' },
              { id: 'IN_REVIEW', label: 'In Review' },
              { id: 'COMPLETED', label: 'Completed' },
            ].map((tab) => (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id as any)}
                className={`px-3.5 py-1.5 rounded-lg text-xs font-medium transition-colors whitespace-nowrap ${
                  activeTab === tab.id
                    ? 'bg-white text-black font-semibold shadow-sm'
                    : 'text-neutral-400 hover:text-white hover:bg-white/5'
                }`}
              >
                {tab.label}
              </button>
            ))}
          </div>

          <div className="relative max-w-xs w-full">
            <input
              type="text"
              placeholder="Search case, patient ID, district..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full bg-[#111116] border border-white/10 rounded-xl px-4 py-2 text-xs text-white placeholder-neutral-500 focus:outline-none focus:border-emerald-500"
            />
          </div>
        </div>

        {/* Clinical Cases Queue Table */}
        <div className="rounded-2xl bg-[#090a0d] border border-white/[0.08] overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead className="bg-[#111218] text-neutral-400 font-mono text-[11px] border-b border-white/5">
                <tr>
                  <th className="py-3.5 px-4 font-normal">Priority</th>
                  <th className="py-3.5 px-4 font-normal">Case ID</th>
                  <th className="py-3.5 px-4 font-normal">Patient</th>
                  <th className="py-3.5 px-4 font-normal">Location</th>
                  <th className="py-3.5 px-4 font-normal">AI Assessment</th>
                  <th className="py-3.5 px-4 font-normal">AI Confidence</th>
                  <th className="py-3.5 px-4 font-normal">Received</th>
                  <th className="py-3.5 px-4 font-normal text-right">Action</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-white/5 text-neutral-300">
                {filteredCases.length === 0 ? (
                  <tr>
                    <td colSpan={8} className="py-12 text-center text-neutral-500">
                      {loading ? 'Loading review queue from database...' : 'No cases matching the selected filter.'}
                    </td>
                  </tr>
                ) : (
                  filteredCases.map((c) => (
                    <tr key={c.id} className="hover:bg-white/[0.02] transition-colors">
                      <td className="py-4 px-4">
                        {getPriorityBadge(c.priority, c.drGrade)}
                      </td>
                      <td className="py-4 px-4 font-mono font-semibold text-white">
                        {c.id}
                      </td>
                      <td className="py-4 px-4">
                        <p className="font-semibold text-white">{c.patientId}</p>
                        <p className="text-[11px] text-neutral-400">{c.age} yrs · {c.gender}</p>
                      </td>
                      <td className="py-4 px-4">
                        <p className="text-white">{c.location}</p>
                        <p className="text-[11px] text-neutral-400 truncate max-w-[150px]">{c.centerName}</p>
                      </td>
                      <td className="py-4 px-4">
                        <p className="font-semibold text-white">{c.severity}</p>
                        <p className="text-[10px] font-mono text-neutral-400">FIQA Quality: {c.qualityScore}%</p>
                      </td>
                      <td className="py-4 px-4 font-mono">
                        <span className="text-teal-400 font-semibold">{Math.round(c.confidence * 100)}%</span>
                      </td>
                      <td className="py-4 px-4 font-mono text-neutral-400">
                        {getTimeAgo(c.createdAt)}
                      </td>
                      <td className="py-4 px-4 text-right">
                        <Link
                          to={`/doctor/cases/${c.id}`}
                          className="inline-flex items-center px-3.5 py-1.5 rounded-lg bg-emerald-500/10 hover:bg-emerald-500 text-emerald-300 hover:text-black font-semibold text-xs border border-emerald-500/30 transition-all shadow-sm"
                        >
                          Review Case →
                        </Link>
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        </div>
      </main>
    </div>
  );
};

export default DoctorDashboardPage;
