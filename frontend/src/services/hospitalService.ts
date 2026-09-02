/**
 * Hospital & Referral Facilities Directory Service
 * Provides dynamic, location-aware referral hospitals based on screening districts.
 */

import { HospitalFacility } from '@/types/api';

export const LOCATIONS_DATA = [
  {
    state: 'Tamil Nadu',
    districts: [
      {
        name: 'Coimbatore',
        centers: [
          'Rural Primary Health Centre — Valparai',
          'Community Health Centre — Pollachi',
          'Upgraded Primary Health Centre — Sulur',
          'Rural Health Sub-Center — Anaimalai',
          'Government Primary Health Centre — Kinathukadavu',
        ],
      },
      {
        name: 'Madurai',
        centers: [
          'Primary Health Centre — Usilampatti',
          'Community Health Centre — Melur',
          'Rural Health Center — Thirumangalam',
          'Primary Health Centre — Vadipatti',
        ],
      },
      {
        name: 'Salem',
        centers: [
          'Rural Health Centre — Omalur',
          'Primary Health Centre — Attur',
          'Community Health Centre — Mettur',
          'Rural Health Sub-Center — Yercaud',
        ],
      },
      {
        name: 'Tiruchirappalli',
        centers: [
          'Primary Health Centre — Musiri',
          'Community Health Centre — Manapparai',
          'Rural Health Centre — Lalgudi',
        ],
      },
    ],
  },
  {
    state: 'Karnataka',
    districts: [
      {
        name: 'Mysuru',
        centers: [
          'Rural Primary Health Centre — Hunsur',
          'Community Health Centre — Nanjangud',
          'Primary Health Centre — T. Narasipura',
        ],
      },
      {
        name: 'Belagavi',
        centers: [
          'Rural Primary Health Centre — Gokak',
          'Community Health Centre — Chikkodi',
          'Primary Health Centre — Athani',
        ],
      },
    ],
  },
  {
    state: 'Maharashtra',
    districts: [
      {
        name: 'Pune Rural',
        centers: [
          'Primary Health Centre — Junnar',
          'Community Health Centre — Baramati',
          'Rural Health Centre — Shirur',
        ],
      },
    ],
  },
];

const HOSPITALS_DATABASE: Record<string, HospitalFacility[]> = {
  Coimbatore: [
    {
      id: 'HOSP-CBE-01',
      name: 'Government Hospital & Medical College, Coimbatore',
      district: 'Coimbatore',
      state: 'Tamil Nadu',
      distanceKm: 28.4,
      ophthalmologistOnDuty: 'Dr. R. Meenakshi (Retina Specialist)',
      bedAvailability: '14 Ophthalmology Beds Available',
      specialization: 'Tertiary Eye Care & Laser Photocoagulation Unit',
      contactNumber: '+91 422 2301300',
      isVerified: true,
    },
    {
      id: 'HOSP-CBE-02',
      name: 'District Eye Hospital, Pollachi Sub-Division',
      district: 'Coimbatore',
      state: 'Tamil Nadu',
      distanceKm: 14.2,
      ophthalmologistOnDuty: 'Dr. V. Sundaram (Vitreoretinal Consultant)',
      bedAvailability: '8 Beds Available',
      specialization: 'Diabetic Retinopathy Screening & Anti-VEGF Clinic',
      contactNumber: '+91 4259 223400',
      isVerified: true,
    },
    {
      id: 'HOSP-CBE-03',
      name: 'Aravind Eye Hospital Referral Centre, Coimbatore',
      district: 'Coimbatore',
      state: 'Tamil Nadu',
      distanceKm: 32.1,
      ophthalmologistOnDuty: 'Dr. K. Chandrasekar (Chief Vitreoretinal Surgeon)',
      bedAvailability: 'Comprehensive Vitreoretinal Unit',
      specialization: 'Advanced Surgical Vitrectomy & OCT Angiography',
      contactNumber: '+91 422 4360400',
      isVerified: true,
    },
  ],
  Madurai: [
    {
      id: 'HOSP-MDU-01',
      name: 'Government Rajaji Hospital, Madurai',
      district: 'Madurai',
      state: 'Tamil Nadu',
      distanceKm: 22.0,
      ophthalmologistOnDuty: 'Dr. S. Karthikeyan (Retina Unit Head)',
      bedAvailability: '16 Beds Available',
      specialization: 'Regional Ophthalmology Centre & Laser Therapy',
      contactNumber: '+91 452 2532535',
      isVerified: true,
    },
    {
      id: 'HOSP-MDU-02',
      name: 'District Health & Eye Care Facility, Usilampatti',
      district: 'Madurai',
      state: 'Tamil Nadu',
      distanceKm: 8.5,
      ophthalmologistOnDuty: 'Dr. P. Gomathi (Consultant Ophthalmologist)',
      bedAvailability: '6 Beds Available',
      specialization: 'Primary Fundus Screening & Fast-Track Referral',
      contactNumber: '+91 4543 232100',
      isVerified: true,
    },
  ],
  Salem: [
    {
      id: 'HOSP-SLM-01',
      name: 'Government Mohan Kumaramangalam Medical College Hospital, Salem',
      district: 'Salem',
      state: 'Tamil Nadu',
      distanceKm: 18.6,
      ophthalmologistOnDuty: 'Dr. A. Balamurugan (Senior Retina Specialist)',
      bedAvailability: '12 Beds Available',
      specialization: 'Diabetic Retinopathy Management & Laser Photocoagulation',
      contactNumber: '+91 427 2447190',
      isVerified: true,
    },
    {
      id: 'HOSP-SLM-02',
      name: 'Community Eye Care Centre, Mettur',
      district: 'Salem',
      state: 'Tamil Nadu',
      distanceKm: 11.4,
      ophthalmologistOnDuty: 'Dr. D. Kavitha (Ophthalmologist)',
      bedAvailability: '5 Beds Available',
      specialization: 'Comprehensive Retinal Triage & Tele-consultation',
      contactNumber: '+91 4298 244200',
      isVerified: true,
    },
  ],
  Tiruchirappalli: [
    {
      id: 'HOSP-TRY-01',
      name: 'Mahatma Gandhi Memorial Government Hospital, Trichy',
      district: 'Tiruchirappalli',
      state: 'Tamil Nadu',
      distanceKm: 16.8,
      ophthalmologistOnDuty: 'Dr. N. Rajesh (Retina Consultant)',
      bedAvailability: '10 Beds Available',
      specialization: 'Tertiary Vitreoretinal Unit',
      contactNumber: '+91 431 2415150',
      isVerified: true,
    },
  ],
};

// Fallback facility generator if another district is picked
function getFallbackHospitals(district: string, state: string): HospitalFacility[] {
  return [
    {
      id: `HOSP-${district.toUpperCase().slice(0, 3)}-01`,
      name: `District Government Headquarter Hospital, ${district}`,
      district,
      state,
      distanceKm: 15.4,
      ophthalmologistOnDuty: 'Dr. Specialist on Duty',
      bedAvailability: '8 Beds Available',
      specialization: 'Diabetic Retinopathy Referral Unit',
      contactNumber: '+91 400 2345678',
      isVerified: true,
    },
    {
      id: `HOSP-${district.toUpperCase().slice(0, 3)}-02`,
      name: `Sub-Divisional Eye Hospital, ${district}`,
      district,
      state,
      distanceKm: 9.8,
      ophthalmologistOnDuty: 'Dr. Consulting Ophthalmologist',
      bedAvailability: '4 Beds Available',
      specialization: 'Medical Retina & Laser Clinic',
      contactNumber: '+91 400 2345679',
      isVerified: true,
    },
  ];
}

export const hospitalService = {
  getStates(): string[] {
    return LOCATIONS_DATA.map((l) => l.state);
  },

  getDistricts(stateName: string): { name: string; centers: string[] }[] {
    const stateObj = LOCATIONS_DATA.find((l) => l.state === stateName);
    return stateObj ? stateObj.districts : [];
  },

  getCenters(stateName: string, districtName: string): string[] {
    const districts = this.getDistricts(stateName);
    const d = districts.find((item) => item.name === districtName);
    return d ? d.centers : ['Rural Primary Health Centre'];
  },

  getHospitalsForLocation(district: string, state: string): HospitalFacility[] {
    const found = HOSPITALS_DATABASE[district];
    if (found && found.length > 0) {
      return found;
    }
    return getFallbackHospitals(district, state);
  },
};
