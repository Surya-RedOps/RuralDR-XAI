import React from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate, Link } from 'react-router-dom';
import { AuthProvider } from '@/context/AuthContext';
import { ProtectedRoute } from '@/components/auth/ProtectedRoute';

import LandingPage from './pages/LandingPage';
import RoleSelectionPage from './pages/RoleSelectionPage';
import WorkerLoginPage from './pages/WorkerLoginPage';
import DoctorLoginPage from './pages/DoctorLoginPage';
import WorkerDashboardPage from './pages/WorkerDashboardPage';
import NewScreeningPage from './pages/NewScreeningPage';
import DoctorDashboardPage from './pages/DoctorDashboardPage';
import DoctorCaseReviewPage from './pages/DoctorCaseReviewPage';
import ReportPage from './pages/ReportPage';
import '@/index.css';

const NotFound: React.FC = () => (
  <div className="min-h-screen bg-black flex items-center justify-center text-center p-6">
    <div className="max-w-md">
      <p className="text-xs font-mono text-neutral-500 mb-2">404 ERROR</p>
      <h1 className="text-2xl font-bold text-white font-['Syne'] mb-3">Page Not Found</h1>
      <p className="text-xs text-neutral-400 mb-6">
        The requested screening workspace or clinical route could not be found.
      </p>
      <Link
        to="/"
        className="inline-flex items-center px-5 py-2.5 rounded-xl bg-white text-black font-semibold text-xs"
      >
        Return to Landing Page
      </Link>
    </div>
  </div>
);

function App() {
  return (
    <AuthProvider>
      <Router>
        <Routes>
          {/* Public Landing & Role Selection */}
          <Route path="/" element={<LandingPage />} />
          <Route path="/select-role" element={<RoleSelectionPage />} />

          {/* Authentication Routes */}
          <Route path="/login/worker" element={<WorkerLoginPage />} />
          <Route path="/login/doctor" element={<DoctorLoginPage />} />

          {/* Healthcare Worker Workspace (Protected) */}
          <Route
            path="/worker/dashboard"
            element={
              <ProtectedRoute allowedRole="worker">
                <WorkerDashboardPage />
              </ProtectedRoute>
            }
          />
          <Route
            path="/worker/new-screening"
            element={
              <ProtectedRoute allowedRole="worker">
                <NewScreeningPage />
              </ProtectedRoute>
            }
          />

          {/* Doctor Workspace (Protected) */}
          <Route
            path="/doctor/dashboard"
            element={
              <ProtectedRoute allowedRole="doctor">
                <DoctorDashboardPage />
              </ProtectedRoute>
            }
          />
          <Route
            path="/doctor/cases/:caseId"
            element={
              <ProtectedRoute allowedRole="doctor">
                <DoctorCaseReviewPage />
              </ProtectedRoute>
            }
          />

          {/* Official Diagnostic Report */}
          <Route
            path="/report/:caseId"
            element={
              <ProtectedRoute>
                <ReportPage />
              </ProtectedRoute>
            }
          />

          {/* Backward compatibility redirects */}
          <Route path="/upload" element={<Navigate to="/select-role" replace />} />
          <Route path="/results/:caseId" element={<Navigate to="/report/:caseId" replace />} />

          {/* 404 Fallback */}
          <Route path="*" element={<NotFound />} />
        </Routes>
      </Router>
    </AuthProvider>
  );
}

export default App;
