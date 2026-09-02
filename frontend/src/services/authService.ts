/**
 * Authentication Service for RuralDR-XAI prototype
 * Manages Healthcare Worker and Doctor authentication with role protection and mock sessions.
 */

import { UserProfile, UserRole } from '@/types/api';

const AUTH_STORAGE_KEY = 'ruraldr_auth_user';

export const MOCK_USERS: Record<UserRole, UserProfile> = {
  worker: {
    id: 'HW-TN-4091',
    role: 'worker',
    name: 'Lakshmi Narayanan, ANM',
    email: 'worker@ruraldrxai.demo',
    mobile: '+91 98402 12345',
    centerName: 'Primary Health Centre — Valparai, Coimbatore',
    isVerified: true,
  },
  doctor: {
    id: 'DR-OPH-8842',
    role: 'doctor',
    name: 'Dr. S. K. Aravind, MS (Ophthalmology)',
    email: 'doctor@ruraldrxai.demo',
    mobile: '+91 94431 56789',
    regNumber: 'MCI-TN-2018-84729',
    centerName: 'Regional Eye Centre, Coimbatore Medical College Hospital',
    isVerified: true,
  },
};

export const authService = {
  getCurrentUser(): UserProfile | null {
    try {
      const stored = localStorage.getItem(AUTH_STORAGE_KEY);
      if (stored) {
        return JSON.parse(stored) as UserProfile;
      }
    } catch {
      // ignore JSON parse error
    }
    return null;
  },

  async loginWorker(emailOrMobile: string, password: string): Promise<UserProfile> {
    // Simulate brief network latency for realistic UX
    await new Promise((res) => setTimeout(res, 600));

    // Allow demo user or any valid format for easy evaluation
    if (!emailOrMobile.trim() || !password.trim()) {
      throw new Error('Please enter registered mobile/email and password.');
    }

    const profile: UserProfile = {
      ...MOCK_USERS.worker,
      email: emailOrMobile.includes('@') ? emailOrMobile : MOCK_USERS.worker.email,
    };

    localStorage.setItem(AUTH_STORAGE_KEY, JSON.stringify(profile));
    return profile;
  },

  async loginDoctor(regNumber: string, emailOrMobile: string, password: string): Promise<UserProfile> {
    await new Promise((res) => setTimeout(res, 600));

    if (!regNumber.trim() || !emailOrMobile.trim() || !password.trim()) {
      throw new Error('Please enter Medical Registration Number, email/mobile, and password.');
    }

    const profile: UserProfile = {
      ...MOCK_USERS.doctor,
      regNumber: regNumber.trim().toUpperCase(),
      email: emailOrMobile.includes('@') ? emailOrMobile : MOCK_USERS.doctor.email,
    };

    localStorage.setItem(AUTH_STORAGE_KEY, JSON.stringify(profile));
    return profile;
  },

  logout(): void {
    localStorage.removeItem(AUTH_STORAGE_KEY);
  },

  isAuthenticated(): boolean {
    return this.getCurrentUser() !== null;
  },

  hasRole(role: UserRole): boolean {
    const user = this.getCurrentUser();
    return user !== null && user.role === role;
  },
};
