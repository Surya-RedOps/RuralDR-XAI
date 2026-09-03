/**
 * Location Hierarchy Service for RuralDR-XAI (SIH26038)
 * Connects to authoritative FastAPI endpoints:
 * - State list (28 Indian states + UTs)
 * - Districts belonging to State
 * - Primary Healthcare Centers belonging to District (Worker)
 * - Referral Eye Hospitals belonging to District (Doctor)
 */

import apiClient from './api';
import { StateItem, DistrictItem, HealthcareCenterItem, HospitalItem } from '@/types/api';

export const locationService = {
  async getStates(): Promise<StateItem[]> {
    const response = await apiClient.get<StateItem[]>('/api/v1/locations/states');
    return response.data;
  },

  async getDistricts(stateId: number): Promise<DistrictItem[]> {
    const response = await apiClient.get<DistrictItem[]>(`/api/v1/locations/states/${stateId}/districts`);
    return response.data;
  },

  async getHealthcareCenters(districtId: number): Promise<HealthcareCenterItem[]> {
    const response = await apiClient.get<HealthcareCenterItem[]>(`/api/v1/locations/districts/${districtId}/healthcare-centers`);
    return response.data;
  },

  async getHospitals(districtId: number): Promise<HospitalItem[]> {
    const response = await apiClient.get<HospitalItem[]>(`/api/v1/locations/districts/${districtId}/hospitals`);
    return response.data;
  },
};
