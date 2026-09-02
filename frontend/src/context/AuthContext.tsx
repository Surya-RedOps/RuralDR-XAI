import React, { createContext, useContext, useState, useEffect } from 'react';
import { UserProfile, UserRole } from '@/types/api';
import { authService, MOCK_USERS } from '@/services/authService';

interface AuthContextType {
  user: UserProfile | null;
  role: UserRole | null;
  isAuthenticated: boolean;
  loginWorker: (emailOrMobile: string, password: string) => Promise<UserProfile>;
  loginDoctor: (regNumber: string, emailOrMobile: string, password: string) => Promise<UserProfile>;
  quickLogin: (role: UserRole) => Promise<UserProfile>;
  logout: () => void;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [user, setUser] = useState<UserProfile | null>(() => authService.getCurrentUser());

  useEffect(() => {
    const current = authService.getCurrentUser();
    setUser(current);
  }, []);

  const loginWorker = async (emailOrMobile: string, password: string) => {
    const profile = await authService.loginWorker(emailOrMobile, password);
    setUser(profile);
    return profile;
  };

  const loginDoctor = async (regNumber: string, emailOrMobile: string, password: string) => {
    const profile = await authService.loginDoctor(regNumber, emailOrMobile, password);
    setUser(profile);
    return profile;
  };

  const quickLogin = async (role: UserRole) => {
    if (role === 'worker') {
      return loginWorker(MOCK_USERS.worker.email, 'password123');
    } else {
      return loginDoctor(MOCK_USERS.doctor.regNumber || 'MCI-TN-2018-84729', MOCK_USERS.doctor.email, 'password123');
    }
  };

  const logout = () => {
    authService.logout();
    setUser(null);
  };

  return (
    <AuthContext.Provider
      value={{
        user,
        role: user?.role ?? null,
        isAuthenticated: !!user,
        loginWorker,
        loginDoctor,
        quickLogin,
        logout,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};
