import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { useAuth } from '@/context/AuthContext';
import { AppHeader } from '@/components/layout/AppHeader';
import { caseService } from '@/services/caseService';
import { ScreeningCase } from '@/types/api';

const WorkerDashboardPage: React.FC = () => {
  const { user } = useAuth();

  const [cases, setCases] = useState<ScreeningCase[]>([]);
  const [loading, setLoading] = useState(true);
  const [metrics, setMetrics] = useState({
    todayScreenings: 0,
    pendingReview: 0,
    referredCases: 0,
    completedCases: 0,
  });
  const [searchQuery, setSearchQuery] = useState('');

  const loadData = async () => {
    setLoading(true);
    try {
      const loadedCases = await caseService.getCases();
      setCases(loadedCases);
      const stats = await caseService.getWorkerStats();
      setMetrics({
        todayScreenings: stats.todayCount,
        pendingReview: stats.pendingCount,
        referredCases: stats.referredCount,
        completedCases: stats.completedCount,
      });
    } catch (err) {
      console.error('Failed to load worker dashboard:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
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
      case 'SCREENED':
        return <span className="px-2 py-0.5 rounded text-[10px] font-mono uppercase bg-blue-500/10 text-blue-300 border border-blue-500/20">Screened</span>;
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
              <span>New Screening</span>
            </Link>
          </div>
        </div>

        {/* Dynamic Metric Cards */}
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
          {[
            {
              label: "Today's Screenings",
              value: metrics.todayScreenings,
              color: 'text-white',
              border: 'border-white/10',
              bg: 'bg-[#0e0e12]',
            },
            {
              label: 'Pending Cases',
              value: metrics.pendingReview,
              color: 'text-amber-400',
              border: 'border-amber-500/20',
              bg: 'bg-[#12100a]',
            },
            {
              label: 'Referred to Doctor',
              value: metrics.referredCases,
              color: 'text-orange-400',
              border: 'border-orange-500/20',
              bg: 'bg-[#140e08]',
            },
            {
              label: 'Completed Cases',
              value: metrics.completedCases,
              color: 'text-emerald-400',
              border: 'border-emerald-500/20',
              bg: 'bg-[#08140f]',
            },
          ].map((m, idx) => (
            <div key={idx} className={`p-5 rounded-2xl ${m.bg} border ${m.border} flex flex-col justify-between`}>
              <p className="text-xs text-neutral-400 font-medium mb-3">{m.label}</p>
              <p className={`text-3xl sm:text-4xl font-bold font-['Syne'] ${m.color}`}>
                {loading ? '...' : m.value}
              </p>
            </div>
          ))}
        </div>

        {/* Cases Section Header & Search */}
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 mb-6">
          <div>
            <h2 className="text-lg font-bold font-['Syne'] text-white">Submitted Screening Cases</h2>
            <p className="text-xs text-neutral-400">All cases captured from this healthcare facility</p>
          </div>

          <div className="relative max-w-xs w-full">
            <input
              type="text"
              placeholder="Search by Case ID or Patient ID..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full bg-[#111116] border border-white/10 rounded-xl px-4 py-2.5 text-xs text-white placeholder-neutral-500 focus:outline-none focus:border-teal-500"
            />
          </div>
        </div>

        {/* Cases Table */}
        <div className="rounded-2xl bg-[#0a0a0d] border border-white/[0.08] overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead className="bg-[#121217] text-neutral-400 font-mono text-[11px] border-b border-white/5">
                <tr>
                  <th className="py-3.5 px-4 font-normal">Case ID</th>
                  <th className="py-3.5 px-4 font-normal">Patient</th>
                  <th className="py-3.5 px-4 font-normal">Location</th>
                  <th className="py-3.5 px-4 font-normal">AI DR Severity</th>
                  <th className="py-3.5 px-4 font-normal">Screening Date</th>
                  <th className="py-3.5 px-4 font-normal">Status</th>
                  <th className="py-3.5 px-4 font-normal text-right">Action</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-white/5 text-neutral-300">
                {filteredCases.length === 0 ? (
                  <tr>
                    <td colSpan={7} className="py-12 text-center text-neutral-500">
                      {loading ? 'Loading cases from database...' : 'No screening cases found.'}
                    </td>
                  </tr>
                ) : (
                  filteredCases.map((c) => (
                    <tr key={c.id} className="hover:bg-white/[0.02] transition-colors">
                      <td className="py-4 px-4 font-mono font-semibold text-white">
                        {c.id}
                      </td>
                      <td className="py-4 px-4">
                        <p className="font-semibold text-white">{c.patient.patientId}</p>
                        <p className="text-[11px] text-neutral-400">{c.patient.age} yrs · {c.patient.gender}</p>
                      </td>
                      <td className="py-4 px-4 text-neutral-300">
                        <p className="truncate max-w-[180px]">{c.location.centerName}</p>
                        <p className="text-[11px] text-neutral-400">{c.location.district}</p>
                      </td>
                      <td className="py-4 px-4">
                        {getSeverityBadge(c.screeningResult?.classification.dr_grade)}
                      </td>
                      <td className="py-4 px-4 font-mono text-neutral-400">
                        {c.patient.screeningDate}
                      </td>
                      <td className="py-4 px-4">
                        {getStatusBadge(c.status)}
                      </td>
                      <td className="py-4 px-4 text-right">
                        <Link
                          to={`/report/${c.id}`}
                          className="inline-flex items-center px-3 py-1.5 rounded-lg bg-white/5 hover:bg-white/10 text-white text-[11px] font-medium border border-white/10 transition-colors"
                        >
                          View Report
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

export default WorkerDashboardPage;
