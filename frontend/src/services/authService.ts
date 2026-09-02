/**
 * Authentication Service for RuralDR-XAI
 * Connects to FastAPI backend with JWT tokens and role verification.
 */

import apiClient from './api';
import { UserProfile, UserRole } from '@/types/api';

const AUTH_STORAGE_KEY = 'ruraldr_auth_user';
const TOKEN_STORAGE_KEY = 'ruraldr_jwt_token';


interface LoginApiResponse {
  access_token: string;
  token_type: string;
  user: {
    id: number;
    role: 'worker' | 'doctor';
    email: string;
    mobile: string;
    full_name: string;
    reg_number?: string;
    facility_name?: string;
    location_id?: number;
    verification_status: string;
    is_verified: boolean;
  };
}

export const authService = {
  getCurrentUser(): UserProfile | null {
    try {
      const stored = localStorage.getItem(AUTH_STORAGE_KEY);
      if (stored) {
        return JSON.parse(stored) as UserProfile;
      }
    } catch {
      // ignore
    }
    return null;
  },

  getToken(): string | null {
    return localStorage.getItem(TOKEN_STORAGE_KEY);
  },

  async loginWorker(emailOrMobile: string, password: string): Promise<UserProfile> {
    const response = await apiClient.post<LoginApiResponse>('/api/v1/auth/login', {
      identifier: emailOrMobile.trim(),
      password: password.trim(),
    });

    const { access_token, user } = response.data;
    localStorage.setItem(TOKEN_STORAGE_KEY, access_token);

    const profile: UserProfile = {
      id: `HW-${user.id}`,
      role: 'worker',
      name: user.full_name,
      email: user.email,
      mobile: user.mobile,
      regNumber: user.reg_number,
      centerName: user.facility_name || 'Primary Health Centre',
      isVerified: user.is_verified,
    };

    localStorage.setItem(AUTH_STORAGE_KEY, JSON.stringify(profile));
    return profile;
  },

  async loginDoctor(regNumber: string, emailOrMobile: string, password: string): Promise<UserProfile> {
    const response = await apiClient.post<LoginApiResponse>('/api/v1/auth/login', {
      identifier: (regNumber.trim() || emailOrMobile.trim()),
      password: password.trim(),
      reg_number: regNumber.trim(),
    });

    const { access_token, user } = response.data;
    localStorage.setItem(TOKEN_STORAGE_KEY, access_token);

    const profile: UserProfile = {
      id: `DR-${user.id}`,
      role: 'doctor',
      name: user.full_name,
      email: user.email,
      mobile: user.mobile,
      regNumber: user.reg_number,
      centerName: user.facility_name || 'Regional Eye Centre',
      isVerified: user.is_verified,
    };

    localStorage.setItem(AUTH_STORAGE_KEY, JSON.stringify(profile));
    return profile;
  },

  async verifySession(): Promise<UserProfile | null> {
    const token = this.getToken();
    if (!token) return null;

    try {
      const response = await apiClient.get<LoginApiResponse['user']>('/api/v1/auth/me');
      const user = response.data;
      const profile: UserProfile = {
        id: user.role === 'worker' ? `HW-${user.id}` : `DR-${user.id}`,
        role: user.role,
        name: user.full_name,
        email: user.email,
        mobile: user.mobile,
        regNumber: user.reg_number,
        centerName: user.facility_name || 'Health Facility',
        isVerified: user.is_verified,
      };
      localStorage.setItem(AUTH_STORAGE_KEY, JSON.stringify(profile));
      return profile;
    } catch {
      this.logout();
      return null;
    }
  },

  logout(): void {
    localStorage.removeItem(TOKEN_STORAGE_KEY);
    localStorage.removeItem(AUTH_STORAGE_KEY);
  },

  isAuthenticated(): boolean {
    return this.getToken() !== null && this.getCurrentUser() !== null;
  },

  hasRole(role: UserRole): boolean {
    const user = this.getCurrentUser();
    return user !== null && user.role === role;
  },
};
