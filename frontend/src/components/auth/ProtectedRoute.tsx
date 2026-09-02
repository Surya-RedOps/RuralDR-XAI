import React from 'react';
import { Navigate, useLocation } from 'react-router-dom';
import { useAuth } from '@/context/AuthContext';
import { UserRole } from '@/types/api';

interface ProtectedRouteProps {
  children: React.ReactNode;
  allowedRole?: UserRole;
}

export const ProtectedRoute: React.FC<ProtectedRouteProps> = ({ children, allowedRole }) => {
  const { user, isAuthenticated } = useAuth();
  const location = useLocation();

  if (!isAuthenticated || !user) {
    if (allowedRole === 'worker') {
      return <Navigate to="/login/worker" state={{ from: location }} replace />;
    }
    if (allowedRole === 'doctor') {
      return <Navigate to="/login/doctor" state={{ from: location }} replace />;
    }
    return <Navigate to="/select-role" replace />;
  }

  if (allowedRole && user.role !== allowedRole) {
    // Role crossover protection: redirect worker to worker dashboard, doctor to doctor dashboard
    return <Navigate to={user.role === 'worker' ? '/worker/dashboard' : '/doctor/dashboard'} replace />;
  }

  return <>{children}</>;
};
