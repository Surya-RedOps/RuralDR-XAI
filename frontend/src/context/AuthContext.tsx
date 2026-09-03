import React, { createContext, useContext, useState, useEffect } from 'react';
import { UserProfile, UserRole } from '@/types/api';
import { authService, RegisterWorkerData, RegisterDoctorData } from '@/services/authService';

interface AuthContextType {
  user: UserProfile | null;
  role: UserRole | null;
  isAuthenticated: boolean;
  loginWorker: (emailOrMobile: string, password: string) => Promise<UserProfile>;
  loginDoctor: (regNumber: string, emailOrMobile: string, password: string) => Promise<UserProfile>;
  registerWorker: (data: RegisterWorkerData) => Promise<UserProfile>;
  registerDoctor: (data: RegisterDoctorData) => Promise<UserProfile>;
  logout: () => void;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [user, setUser] = useState<UserProfile | null>(() => authService.getCurrentUser());

  useEffect(() => {
    // Re-verify session with backend on load
    authService.verifySession().then((verifiedUser) => {
      if (verifiedUser) {
        setUser(verifiedUser);
      }
    });
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

  const registerWorker = async (data: RegisterWorkerData) => {
    const profile = await authService.registerWorker(data);
    setUser(profile);
    return profile;
  };

  const registerDoctor = async (data: RegisterDoctorData) => {
    const profile = await authService.registerDoctor(data);
    setUser(profile);
    return profile;
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
        registerWorker,
        registerDoctor,
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
