/**
 * Authentication Service for RuralDR-XAI (SIH26038)
 * Connects to FastAPI backend with JWT tokens, role enforcement, and real registration.
 * Absolutely NO mock/fake hardcoded users.
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
    verification_status: 'PENDING' | 'VERIFIED' | 'REJECTED';
    is_verified: boolean;
  };
}

export interface RegisterWorkerData {
  full_name: string;
  professional_id: string;
  mobile: string;
  email: string;
  healthcare_centre_name: string;
  location_id?: number;
  password: string;
}

export interface RegisterDoctorData {
  full_name: string;
  medical_reg_number: string;
  mobile: string;
  email: string;
  hospital_name: string;
  location_id?: number;
  speciality?: string;
  password: string;
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

  async login(identifier: string, password: string): Promise<UserProfile> {
    const response = await apiClient.post<LoginApiResponse>('/api/v1/auth/login', {
      identifier: identifier.trim(),
      password: password.trim(),
    });

    const { access_token, user } = response.data;
    localStorage.setItem(TOKEN_STORAGE_KEY, access_token);

    const profile: UserProfile = {
      id: user.role === 'worker' ? `HW-${user.id}` : `DR-${user.id}`,
      role: user.role,
      name: user.full_name,
      email: user.email,
      mobile: user.mobile,
      regNumber: user.reg_number,
      centerName: user.facility_name || (user.role === 'worker' ? 'Primary Health Centre' : 'Eye Care Hospital'),
      isVerified: user.is_verified,
      verificationStatus: user.verification_status || (user.is_verified ? 'VERIFIED' : 'PENDING'),
    };

    localStorage.setItem(AUTH_STORAGE_KEY, JSON.stringify(profile));
    return profile;
  },

  async loginWorker(emailOrMobile: string, password: string): Promise<UserProfile> {
    return this.login(emailOrMobile, password);
  },

  async loginDoctor(regNumberOrEmail: string, emailOrMobile: string, password: string): Promise<UserProfile> {
    const identifier = regNumberOrEmail.trim() || emailOrMobile.trim();
    return this.login(identifier, password);
  },

  async registerWorker(data: RegisterWorkerData): Promise<UserProfile> {
    const response = await apiClient.post<LoginApiResponse>('/api/v1/auth/register/worker', data);
    const { access_token, user } = response.data;
    localStorage.setItem(TOKEN_STORAGE_KEY, access_token);

    const profile: UserProfile = {
      id: `HW-${user.id}`,
      role: 'worker',
      name: user.full_name,
      email: user.email,
      mobile: user.mobile,
      regNumber: user.reg_number,
      centerName: user.facility_name || data.healthcare_centre_name,
      isVerified: user.is_verified,
      verificationStatus: user.verification_status,
    };

    localStorage.setItem(AUTH_STORAGE_KEY, JSON.stringify(profile));
    return profile;
  },

  async registerDoctor(data: RegisterDoctorData): Promise<UserProfile> {
    const response = await apiClient.post<LoginApiResponse>('/api/v1/auth/register/doctor', data);
    const { access_token, user } = response.data;
    localStorage.setItem(TOKEN_STORAGE_KEY, access_token);

    const profile: UserProfile = {
      id: `DR-${user.id}`,
      role: 'doctor',
      name: user.full_name,
      email: user.email,
      mobile: user.mobile,
      regNumber: user.reg_number,
      centerName: user.facility_name || data.hospital_name,
      isVerified: user.is_verified,
      verificationStatus: user.verification_status,
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
        verificationStatus: user.verification_status || (user.is_verified ? 'VERIFIED' : 'PENDING'),
      };
      localStorage.setItem(AUTH_STORAGE_KEY, JSON.stringify(profile));
      return profile;
    } catch {
      this.logout();
      return null;
    }
  },

  logout(): void {
    try {
      apiClient.post('/api/v1/auth/logout').catch(() => {});
    } catch {
      // ignore
    }
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
