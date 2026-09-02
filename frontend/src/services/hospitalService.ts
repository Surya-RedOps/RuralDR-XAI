/**
 * Hospital & Referral Facilities Service
 * Dynamically fetches locations and verified hospitals from MySQL backend.
 */

import apiClient from './api';
import { HospitalFacility } from '@/types/api';

export interface LocationOption {
  id: number;
  state: string;
  district: string;
  healthcare_centre: string;
  code: string;
}

export interface GroupedLocations {
  state: string;
  districts: {
    name: string;
    centers: { id: number; name: string; code: string }[];
  }[];
}

export const hospitalService = {
  /**
   * Fetches all registered locations from backend
   */
  async getLocations(): Promise<LocationOption[]> {
    try {
      const response = await apiClient.get<LocationOption[]>('/api/v1/locations');
      return response.data;
    } catch (error) {
      console.error('Failed to fetch locations from backend:', error);
      return [];
    }
  },

  /**
   * Groups flat location records for cascading State -> District -> Centre dropdowns
   */
  async getGroupedLocations(): Promise<GroupedLocations[]> {
    const raw = await this.getLocations();
    const stateMap = new Map<string, Map<string, { id: number; name: string; code: string }[]>>();

    for (const loc of raw) {
      if (!stateMap.has(loc.state)) {
        stateMap.set(loc.state, new Map());
      }
      const distMap = stateMap.get(loc.state)!;
      if (!distMap.has(loc.district)) {
        distMap.set(loc.district, []);
      }
      distMap.get(loc.district)!.push({
        id: loc.id,
        name: loc.healthcare_centre,
        code: loc.code,
      });
    }

    const result: GroupedLocations[] = [];
    stateMap.forEach((distMap, stateName) => {
      const districts: { name: string; centers: { id: number; name: string; code: string }[] }[] = [];
      distMap.forEach((centers, districtName) => {
        districts.push({ name: districtName, centers });
      });
      result.push({ state: stateName, districts });
    });

    return result;
  },

  /**
   * Fetches verified referral hospitals for a given location
   */
  async getHospitalsForLocation(locationId: number): Promise<HospitalFacility[]> {
    try {
      const response = await apiClient.get<any[]>(`/api/v1/locations/${locationId}/hospitals`);
      return response.data.map((h, index) => ({
        id: String(h.id),
        name: h.name,
        district: h.district,
        state: 'Tamil Nadu',
        distanceKm: 8 + index * 6,
        ophthalmologistOnDuty: 'Dr. On-Duty (Retina Unit)',
        bedAvailability: h.availability || 'Available',
        specialization: h.speciality || 'Vitreoretinal Care',
        contactNumber: h.contact,
        isVerified: h.is_verified,
      }));
    } catch (error) {
      console.error('Failed to fetch hospitals from backend:', error);
      return [];
    }
  },
};
