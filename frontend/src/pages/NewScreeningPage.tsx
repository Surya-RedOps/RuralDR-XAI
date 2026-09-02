import React, { useState, useRef } from 'react';
import { Link } from 'react-router-dom';
import { useAuth } from '@/context/AuthContext';
import { AppHeader } from '@/components/layout/AppHeader';
import { MedicalRetinaViewer } from '@/components/viewer/MedicalRetinaViewer';
import { screeningService, SAMPLE_IMAGE_OPTIONS } from '@/services/screeningService';
import { hospitalService } from '@/services/hospitalService';
import { caseService } from '@/services/caseService';
import {
  PatientInfo,
  ScreeningLocation,
  HospitalFacility,
  ScreeningResult,
  ImageValidationResult,
  SampleImageOption,
  ScreeningCase,
} from '@/types/api';

const STEPS = [
  { n: '01', title: 'Patient' },
  { n: '02', title: 'Location' },
  { n: '03', title: 'Fundus Image' },
  { n: '04', title: 'AI Screening' },
  { n: '05', title: 'Result' },
  { n: '06', title: 'Referral' },
];

const SCAN_MESSAGES = [
  'Checking image type (Fundus verification)...',
  'Analyzing optical quality & field illumination (FIQA)...',
  'Locating optic disc, macula & vascular arcades...',
  'Evaluating lesion biomarkers (microaneurysms, hemorrhages, exudates)...',
  'Estimating DR severity grade & Class Activation Map (Grad-CAM)...',
  'Validating prediction safety & generating clinical evidence report...',
];

const NewScreeningPage: React.FC = () => {
  const { user } = useAuth();
  const fileInputRef = useRef<HTMLInputElement>(null);

  // Workflow Step State (1 to 6)
  const [currentStep, setCurrentStep] = useState<number>(1);

  // Step 1: Patient Details
  const [patient, setPatient] = useState<PatientInfo>({
    patientId: `PID-${Math.floor(1000 + Math.random() * 9000)}`,
    age: 54,
    gender: 'Male',
    screeningDate: new Date().toISOString().split('T')[0],
    hba1c: '8.4%',
    diabetesDuration: '7 years',
    notes: 'Routine rural diabetic retinopathy screening. Mild visual blur reported.',
  });

  // Step 2: Location
  const [location, setLocation] = useState<ScreeningLocation>({
    state: 'Tamil Nadu',
    district: 'Coimbatore',
    centerName: 'Rural Primary Health Centre — Valparai',
  });

  // Step 3: Fundus Upload State
  const [, setSelectedFile] = useState<File | null>(null);
  const [imageUrl, setImageUrl] = useState<string>(SAMPLE_IMAGE_OPTIONS[0].imageUrl);
  const [selectedSample, setSelectedSample] = useState<SampleImageOption | null>(SAMPLE_IMAGE_OPTIONS[0]);
  const [imageMeta, setImageMeta] = useState({
    filename: 'sample_moderate_npdr_fundus.png',
    resolution: '1024×1024 RGB',
    sizeKb: 2450,
  });

  // Step 4: AI Scanning State
  const [isScanning, setIsScanning] = useState<boolean>(false);
  const [scanMessageIndex, setScanMessageIndex] = useState<number>(0);
  const [validationResult, setValidationResult] = useState<ImageValidationResult | null>(null);
  const [screeningResult, setScreeningResult] = useState<ScreeningResult | null>(null);

  // Step 6: Referral State
  const [selectedHospital, setSelectedHospital] = useState<HospitalFacility | null>(null);
  const [referralSent, setReferralSent] = useState<boolean>(false);
  const [referralSuccessCase, setReferralSuccessCase] = useState<ScreeningCase | null>(null);

  // Handle custom file upload
  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      setSelectedFile(file);
      setSelectedSample(null);
      const reader = new FileReader();
      reader.onload = (event) => {
        const result = event.target?.result as string;
        setImageUrl(result);
        setImageMeta({
          filename: file.name,
          resolution: 'Fundus Camera Image',
          sizeKb: Math.round(file.size / 1024),
        });
      };
      reader.readAsDataURL(file);
    }
  };

  // Handle choosing a sample test image
  const handleSelectSample = (sample: SampleImageOption) => {
    setSelectedSample(sample);
    setSelectedFile(null);
    setImageUrl(sample.imageUrl);
    setImageMeta({
      filename: `${sample.id}.svg`,
      resolution: '1024×1024 RGB Standard',
      sizeKb: 1820,
    });
  };

  // Execute Step 4: Multi-stage AI validation and screening
  const startAIScreening = async () => {
    setCurrentStep(4);
    setIsScanning(true);
    setScanMessageIndex(0);
    setValidationResult(null);
    setScreeningResult(null);

    // Progressive scanning messages
    const interval = setInterval(() => {
      setScanMessageIndex((prev) => (prev < SCAN_MESSAGES.length - 1 ? prev + 1 : prev));
    }, 600);

    try {
      // 1. Pre-validation check (Fundus vs Non-Fundus and Quality Gate)
      const validation = await screeningService.validateImage(imageUrl, {
        name: imageMeta.filename,
        size: imageMeta.sizeKb * 1024,
      });

      setValidationResult(validation);

      if (!validation.isValidFundus || validation.validationError === 'POOR_QUALITY') {
        clearInterval(interval);
        setIsScanning(false);
        return;
      }

      // 2. Full AI Screening for valid fundus
      const caseId = caseService.generateNextCaseId();
      const results = await screeningService.screenImage(caseId, imageUrl, selectedSample?.expectedGrade);
      setScreeningResult(results);

      // Preselect first hospital for the district if referral is required
      const availableHospitals = hospitalService.getHospitalsForLocation(location.district, location.state);
      if (availableHospitals.length > 0) {
        setSelectedHospital(availableHospitals[0]);
      }

      clearInterval(interval);
      setIsScanning(false);
      setCurrentStep(5); // Advance to Result
    } catch (err) {
      clearInterval(interval);
      setIsScanning(false);
    }
  };

  // Complete Referral or Finish Screening
  const handleSendReferral = () => {
    if (!screeningResult) return;

    const newCaseId = caseService.generateNextCaseId();
    const isReferralNeeded = screeningResult.classification.is_referable;

    const newCase: ScreeningCase = {
      id: newCaseId,
      createdAt: new Date().toISOString(),
      updatedAt: new Date().toISOString(),
      status: isReferralNeeded ? 'REFERRED' : 'COMPLETED',
      priority:
        screeningResult.classification.dr_grade >= 4
          ? 'CRITICAL'
          : screeningResult.classification.dr_grade === 3
          ? 'HIGH'
          : screeningResult.classification.dr_grade === 2
          ? 'MEDIUM'
          : screeningResult.classification.dr_grade === 1
          ? 'REVIEW'
          : 'LOW',
      patient,
      location,
      workerId: user?.id || 'HW-TN-4091',
      workerName: user?.name || 'Healthcare Worker',
      originalImageUrl: imageUrl,
      imageMeta,
      screeningResult,
      referral: isReferralNeeded
        ? {
            required: true,
            referredAt: new Date().toISOString(),
            reason: `Referred based on AI detection of ${screeningResult.classification.severity}`,
            hospital: selectedHospital || undefined,
          }
        : { required: false },
    };

    caseService.createCase(newCase);
    setReferralSuccessCase(newCase);
    setReferralSent(true);
  };

  return (
    <div className="min-h-screen bg-[#070709] text-white flex flex-col">
      <AppHeader />

      <main className="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Workflow Progress Stepper */}
        <div className="mb-8">
          <div className="flex items-center justify-between overflow-x-auto pb-4 gap-2">
            {STEPS.map((step, idx) => {
              const stepNum = idx + 1;
              const isPast = stepNum < currentStep;
              const isCurrent = stepNum === currentStep;

              return (
                <div
                  key={step.n}
                  className={`flex items-center gap-3 px-4 py-2.5 rounded-xl border flex-shrink-0 transition-all ${
                    isCurrent
                      ? 'bg-teal-500/10 border-teal-500/30 text-teal-300 shadow-md shadow-teal-950/20'
                      : isPast
                      ? 'bg-white/[0.02] border-white/10 text-neutral-400'
                      : 'bg-transparent border-white/[0.04] text-neutral-600'
                  }`}
                >
                  <span
                    className={`w-6 h-6 rounded-full flex items-center justify-center text-[10px] font-mono font-bold ${
                      isCurrent
                        ? 'bg-teal-400 text-black'
                        : isPast
                        ? 'bg-white/10 text-neutral-300'
                        : 'bg-white/5 text-neutral-600'
                    }`}
                  >
                    {isPast ? '✓' : step.n}
                  </span>
                  <span className="text-xs font-semibold">{step.title}</span>
                </div>
              );
            })}
          </div>
        </div>

        {/* ========================================================================= */}
        {/* STEP 1: PATIENT DETAILS */}
        {/* ========================================================================= */}
        {currentStep === 1 && (
          <div className="max-w-2xl mx-auto rounded-3xl bg-[#0c0d12] border border-white/[0.08] p-8">
            <div className="mb-6">
              <span className="text-teal-400 text-xs font-mono">Step 01 of 06</span>
              <h2 className="text-2xl font-bold font-['Syne'] text-white mt-1">Create Screening Case</h2>
              <p className="text-xs text-neutral-400 mt-1">
                Enter basic patient demographic information. Full personal identifiers are masked for clinical privacy.
              </p>
            </div>

            <div className="space-y-5">
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <div>
                  <label className="block text-xs font-medium text-neutral-300 mb-1.5">Patient ID / Token</label>
                  <input
                    type="text"
                    required
                    value={patient.patientId}
                    onChange={(e) => setPatient({ ...patient, patientId: e.target.value })}
                    className="w-full px-4 py-2.5 rounded-xl bg-black/50 border border-white/10 text-xs text-white font-mono focus:outline-none focus:border-teal-400"
                  />
                </div>

                <div>
                  <label className="block text-xs font-medium text-neutral-300 mb-1.5">Screening Date</label>
                  <input
                    type="date"
                    value={patient.screeningDate}
                    onChange={(e) => setPatient({ ...patient, screeningDate: e.target.value })}
                    className="w-full px-4 py-2.5 rounded-xl bg-black/50 border border-white/10 text-xs text-white focus:outline-none focus:border-teal-400"
                  />
                </div>
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <div>
                  <label className="block text-xs font-medium text-neutral-300 mb-1.5">Age</label>
                  <input
                    type="number"
                    min="18"
                    max="110"
                    value={patient.age}
                    onChange={(e) => setPatient({ ...patient, age: parseInt(e.target.value, 10) || 0 })}
                    className="w-full px-4 py-2.5 rounded-xl bg-black/50 border border-white/10 text-xs text-white focus:outline-none focus:border-teal-400"
                  />
                </div>

                <div>
                  <label className="block text-xs font-medium text-neutral-300 mb-1.5">Gender</label>
                  <select
                    value={patient.gender}
                    onChange={(e) => setPatient({ ...patient, gender: e.target.value as any })}
                    className="w-full px-4 py-2.5 rounded-xl bg-black/50 border border-white/10 text-xs text-white focus:outline-none focus:border-teal-400"
                  >
                    <option value="Male">Male</option>
                    <option value="Female">Female</option>
                    <option value="Other">Other</option>
                  </select>
                </div>
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <div>
                  <label className="block text-xs font-medium text-neutral-300 mb-1.5">
                    HbA1c Level <span className="text-neutral-500">(Optional)</span>
                  </label>
                  <input
                    type="text"
                    placeholder="e.g. 8.2%"
                    value={patient.hba1c}
                    onChange={(e) => setPatient({ ...patient, hba1c: e.target.value })}
                    className="w-full px-4 py-2.5 rounded-xl bg-black/50 border border-white/10 text-xs text-white focus:outline-none focus:border-teal-400"
                  />
                </div>

                <div>
                  <label className="block text-xs font-medium text-neutral-300 mb-1.5">
                    Diabetes Duration <span className="text-neutral-500">(Optional)</span>
                  </label>
                  <input
                    type="text"
                    placeholder="e.g. 5 years"
                    value={patient.diabetesDuration}
                    onChange={(e) => setPatient({ ...patient, diabetesDuration: e.target.value })}
                    className="w-full px-4 py-2.5 rounded-xl bg-black/50 border border-white/10 text-xs text-white focus:outline-none focus:border-teal-400"
                  />
                </div>
              </div>

              <div>
                <label className="block text-xs font-medium text-neutral-300 mb-1.5">Clinical Notes</label>
                <textarea
                  rows={3}
                  value={patient.notes}
                  onChange={(e) => setPatient({ ...patient, notes: e.target.value })}
                  placeholder="Record symptoms, visual complaints, or blood pressure..."
                  className="w-full px-4 py-2.5 rounded-xl bg-black/50 border border-white/10 text-xs text-white focus:outline-none focus:border-teal-400"
                />
              </div>

              <div className="pt-4 flex items-center justify-end">
                <button
                  type="button"
                  onClick={() => setCurrentStep(2)}
                  className="px-6 py-3 rounded-xl bg-white hover:bg-teal-400 text-black font-semibold text-xs transition-colors flex items-center gap-2"
                >
                  <span>Continue to Location</span>
                  <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                    <path d="M5 12h14" />
                    <path d="M12 5l7 7-7 7" />
                  </svg>
                </button>
              </div>
            </div>
          </div>
        )}

        {/* ========================================================================= */}
        {/* STEP 2: SCREENING LOCATION */}
        {/* ========================================================================= */}
        {currentStep === 2 && (
          <div className="max-w-2xl mx-auto rounded-3xl bg-[#0c0d12] border border-white/[0.08] p-8">
            <div className="mb-6">
              <span className="text-teal-400 text-xs font-mono">Step 02 of 06</span>
              <h2 className="text-2xl font-bold font-['Syne'] text-white mt-1">Screening Location</h2>
              <p className="text-xs text-neutral-400 mt-1">
                Select your current primary health center location. This determines automated referral hospital routing.
              </p>
            </div>

            <div className="space-y-5">
              <div>
                <label className="block text-xs font-medium text-neutral-300 mb-1.5">State</label>
                <select
                  value={location.state}
                  onChange={(e) => {
                    const newState = e.target.value;
                    const districts = hospitalService.getDistricts(newState);
                    const firstDistrict = districts[0]?.name || 'Coimbatore';
                    const firstCenter = districts[0]?.centers[0] || 'Rural Primary Health Centre';
                    setLocation({
                      state: newState,
                      district: firstDistrict,
                      centerName: firstCenter,
                    });
                  }}
                  className="w-full px-4 py-2.5 rounded-xl bg-black/50 border border-white/10 text-xs text-white focus:outline-none focus:border-teal-400"
                >
                  {hospitalService.getStates().map((st) => (
                    <option key={st} value={st}>
                      {st}
                    </option>
                  ))}
                </select>
              </div>

              <div>
                <label className="block text-xs font-medium text-neutral-300 mb-1.5">District</label>
                <select
                  value={location.district}
                  onChange={(e) => {
                    const newDistrict = e.target.value;
                    const centers = hospitalService.getCenters(location.state, newDistrict);
                    setLocation({
                      ...location,
                      district: newDistrict,
                      centerName: centers[0] || 'Rural Health Centre',
                    });
                  }}
                  className="w-full px-4 py-2.5 rounded-xl bg-black/50 border border-white/10 text-xs text-white focus:outline-none focus:border-teal-400"
                >
                  {hospitalService.getDistricts(location.state).map((d) => (
                    <option key={d.name} value={d.name}>
                      {d.name}
                    </option>
                  ))}
                </select>
              </div>

              <div>
                <label className="block text-xs font-medium text-neutral-300 mb-1.5">Healthcare Center</label>
                <select
                  value={location.centerName}
                  onChange={(e) => setLocation({ ...location, centerName: e.target.value })}
                  className="w-full px-4 py-2.5 rounded-xl bg-black/50 border border-white/10 text-xs text-white focus:outline-none focus:border-teal-400"
                >
                  {hospitalService.getCenters(location.state, location.district).map((c) => (
                    <option key={c} value={c}>
                      {c}
                    </option>
                  ))}
                </select>
              </div>

              {/* Current Location Summary Badge */}
              <div className="p-4 rounded-2xl bg-teal-500/5 border border-teal-500/20">
                <p className="text-[11px] font-mono text-teal-300 uppercase tracking-wider mb-1">
                  Current Screening Facility
                </p>
                <p className="text-xs font-bold text-white">{location.centerName}</p>
                <p className="text-[11px] text-neutral-400">
                  {location.district} District, {location.state}
                </p>
              </div>

              <div className="pt-4 flex items-center justify-between">
                <button
                  type="button"
                  onClick={() => setCurrentStep(1)}
                  className="px-5 py-2.5 rounded-xl bg-white/5 hover:bg-white/10 text-neutral-300 text-xs font-medium transition-colors"
                >
                  Back
                </button>
                <button
                  type="button"
                  onClick={() => setCurrentStep(3)}
                  className="px-6 py-3 rounded-xl bg-white hover:bg-teal-400 text-black font-semibold text-xs transition-colors flex items-center gap-2"
                >
                  <span>Continue to Image Upload</span>
                  <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                    <path d="M5 12h14" />
                    <path d="M12 5l7 7-7 7" />
                  </svg>
                </button>
              </div>
            </div>
          </div>
        )}

        {/* ========================================================================= */}
        {/* STEP 3: FUNDUS IMAGE UPLOAD */}
        {/* ========================================================================= */}
        {currentStep === 3 && (
          <div className="grid grid-cols-1 lg:grid-cols-12 gap-8">
            {/* Left Upload Area & Sample Picker (7 cols) */}
            <div className="lg:col-span-7 space-y-6">
              <div className="rounded-3xl bg-[#0c0d12] border border-white/[0.08] p-6 sm:p-8">
                <div className="mb-6">
                  <span className="text-teal-400 text-xs font-mono">Step 03 of 06</span>
                  <h2 className="text-2xl font-bold font-['Syne'] text-white mt-1">Upload Fundus Image</h2>
                  <p className="text-xs text-neutral-400 mt-1">
                    Upload a clear retinal fundus photograph captured using a fundus camera or ophthalmoscope adapter.
                  </p>
                </div>

                {/* Dropzone / Upload Box */}
                <input
                  type="file"
                  ref={fileInputRef}
                  onChange={handleFileChange}
                  accept="image/jpeg,image/png,image/tiff,image/bmp"
                  className="hidden"
                />

                <div
                  onClick={() => fileInputRef.current?.click()}
                  className="border-2 border-dashed border-white/15 hover:border-teal-400/50 rounded-2xl p-8 text-center cursor-pointer transition-all bg-black/40 hover:bg-white/[0.01] group"
                >
                  <div className="w-12 h-12 rounded-xl bg-teal-500/10 border border-teal-500/20 text-teal-400 flex items-center justify-center mx-auto mb-4 group-hover:scale-110 transition-transform">
                    <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                      <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" />
                      <polyline points="17 8 12 3 7 8" />
                      <line x1="12" y1="3" x2="12" y2="15" />
                    </svg>
                  </div>
                  <p className="text-sm font-semibold text-white mb-1">Click to browse or Drag & Drop fundus scan</p>
                  <p className="text-xs text-neutral-500 mb-3">Supported formats: JPEG, PNG, TIFF, BMP (Max 50MB)</p>
                  <button
                    type="button"
                    className="px-4 py-2 rounded-lg bg-white/10 group-hover:bg-teal-400 group-hover:text-black text-white text-xs font-medium transition-colors"
                  >
                    Select File from Device
                  </button>
                </div>

                {/* Built-in Sample Image Selector for Instant Testing */}
                <div className="mt-6 pt-6 border-t border-white/[0.06]">
                  <div className="flex items-center justify-between mb-3">
                    <span className="text-xs font-semibold text-neutral-300">
                      ⚡ Quick Sample Selector (Prototype Testing)
                    </span>
                    <span className="text-[10px] text-neutral-500 font-mono">1-Click Test</span>
                  </div>
                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-2.5">
                    {SAMPLE_IMAGE_OPTIONS.map((sample) => (
                      <button
                        key={sample.id}
                        type="button"
                        onClick={() => handleSelectSample(sample)}
                        className={`p-3 rounded-xl border text-left transition-all ${
                          selectedSample?.id === sample.id
                            ? 'bg-teal-500/10 border-teal-500/40 text-white shadow-sm'
                            : 'bg-black/30 border-white/[0.05] text-neutral-400 hover:text-neutral-200 hover:border-white/15'
                        }`}
                      >
                        <div className="flex items-center gap-2 mb-1">
                          <span
                            className={`w-2 h-2 rounded-full ${
                              sample.expectedStatus === 'INVALID'
                                ? 'bg-red-500'
                                : sample.expectedStatus === 'POOR_QUALITY'
                                ? 'bg-amber-500'
                                : 'bg-teal-400'
                            }`}
                          />
                          <span className="text-xs font-semibold">{sample.label}</span>
                        </div>
                        <p className="text-[10px] text-neutral-500 line-clamp-1">{sample.subtitle}</p>
                      </button>
                    ))}
                  </div>
                </div>

                {/* Image Requirements Checklist */}
                <div className="mt-6 p-4 rounded-2xl bg-[#09090b] border border-white/5 space-y-2 text-xs text-neutral-400">
                  <p className="font-semibold text-neutral-300 text-[11px] uppercase font-mono">
                    Image Quality Requirements
                  </p>
                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 text-[11px]">
                    <div className="flex items-center gap-1.5">
                      <span className="text-teal-400">✓</span> Color fundus photograph (RGB)
                    </div>
                    <div className="flex items-center gap-1.5">
                      <span className="text-teal-400">✓</span> Minimum 512 × 512 resolution
                    </div>
                    <div className="flex items-center gap-1.5">
                      <span className="text-teal-400">✓</span> Clear retinal field, minimal blur
                    </div>
                    <div className="flex items-center gap-1.5">
                      <span className="text-teal-400">✓</span> Optic disc & macula visible
                    </div>
                  </div>
                </div>
              </div>
            </div>

            {/* Right Image Preview & Action (5 cols) */}
            <div className="lg:col-span-5 flex flex-col justify-between rounded-3xl bg-[#0c0d12] border border-white/[0.08] p-6 sm:p-8">
              <div>
                <div className="flex items-center justify-between mb-4">
                  <h3 className="text-sm font-semibold text-white">Retinal Preview</h3>
                  <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-white/5 border border-white/10 text-neutral-300">
                    Ready for Ingestion
                  </span>
                </div>

                {/* Preview Frame */}
                <div className="aspect-square w-full rounded-2xl bg-black border border-white/10 overflow-hidden relative flex items-center justify-center mb-4">
                  <img src={imageUrl} alt="Fundus Preview" className="w-full h-full object-contain" />
                  <div className="absolute inset-0 border border-white/10 rounded-2xl pointer-events-none" />
                </div>

                {/* Meta details */}
                <div className="p-3.5 rounded-xl bg-black/40 border border-white/5 space-y-1.5 text-xs">
                  <div className="flex justify-between">
                    <span className="text-neutral-500">Filename:</span>
                    <span className="font-mono text-neutral-300 truncate max-w-[180px]">{imageMeta.filename}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-neutral-500">Resolution:</span>
                    <span className="font-mono text-neutral-300">{imageMeta.resolution}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-neutral-500">File Size:</span>
                    <span className="font-mono text-neutral-300">{imageMeta.sizeKb} KB</span>
                  </div>
                </div>
              </div>

              {/* Actions */}
              <div className="pt-6 border-t border-white/[0.06] flex items-center justify-between gap-3">
                <button
                  type="button"
                  onClick={() => setCurrentStep(2)}
                  className="px-5 py-2.5 rounded-xl bg-white/5 hover:bg-white/10 text-neutral-300 text-xs font-medium transition-colors"
                >
                  Back
                </button>
                <button
                  type="button"
                  onClick={startAIScreening}
                  className="flex-1 py-3.5 px-6 rounded-xl bg-white hover:bg-teal-400 text-black font-bold text-xs transition-all shadow-xl flex items-center justify-center gap-2"
                >
                  <span>Run AI Screening</span>
                  <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
                    <path d="M5 12h14" />
                    <path d="M12 5l7 7-7 7" />
                  </svg>
                </button>
              </div>
            </div>
          </div>
        )}

        {/* ========================================================================= */}
        {/* STEP 4: AI SCANNING & VALIDATION PIPELINE */}
        {/* ========================================================================= */}
        {currentStep === 4 && (
          <div className="max-w-2xl mx-auto rounded-3xl bg-[#0c0d12] border border-white/[0.08] p-8 text-center">
            {/* 4A: Scanning Animation in Progress */}
            {isScanning && (
              <div className="py-8">
                <div className="relative w-64 h-64 mx-auto mb-8 rounded-full border border-teal-500/30 bg-black overflow-hidden flex items-center justify-center">
                  <img src={imageUrl} alt="Scanning Retina" className="w-full h-full object-contain opacity-70" />

                  {/* Radar Scanning Line */}
                  <div className="absolute inset-0 pointer-events-none">
                    <div className="w-full h-1 bg-gradient-to-r from-transparent via-cyan-400 to-transparent animate-[scan_2s_ease-in-out_infinite]" />
                  </div>
                  <div className="absolute inset-0 border-2 border-teal-400/40 rounded-full animate-ping opacity-25 pointer-events-none" />
                </div>

                <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-teal-500/10 border border-teal-500/20 text-teal-400 text-xs font-mono mb-4">
                  <span className="w-2 h-2 rounded-full bg-teal-400 animate-pulse" />
                  <span>SIH26038 Multistage Inference Active</span>
                </div>

                <h3 className="text-xl font-bold font-['Syne'] text-white mb-2">
                  {SCAN_MESSAGES[scanMessageIndex]}
                </h3>
                <p className="text-xs text-neutral-500 max-w-md mx-auto">
                  Executing Fundus Verification → FIQA Quality Gate → Retinal Segmentation → Grad-CAM XAI
                </p>
              </div>
            )}

            {/* 4B: INVALID IMAGE STATE (Non-Fundus Rejection) */}
            {!isScanning && validationResult && !validationResult.isValidFundus && (
              <div className="py-6">
                <div className="w-16 h-16 rounded-2xl bg-red-500/10 border border-red-500/30 text-red-400 flex items-center justify-center mx-auto mb-6">
                  <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                    <circle cx="12" cy="12" r="10" />
                    <line x1="15" y1="9" x2="9" y2="15" />
                    <line x1="9" y1="9" x2="15" y2="15" />
                  </svg>
                </div>

                <span className="px-3 py-1 rounded-full bg-red-500/10 border border-red-500/20 text-red-400 font-mono text-xs uppercase">
                  Image Not Recognized
                </span>

                <h2 className="text-2xl font-bold font-['Syne'] text-white mt-3 mb-3">
                  Non-Fundus Photograph Rejected
                </h2>

                <p className="text-xs sm:text-sm text-neutral-300 max-w-lg mx-auto leading-relaxed mb-6">
                  {validationResult.rejectionReason}
                </p>

                <div className="p-4 rounded-2xl bg-black/50 border border-white/5 text-left max-w-md mx-auto mb-8 text-xs text-neutral-400 space-y-1.5">
                  <div className="flex justify-between">
                    <span>Fundus Biomarker Match:</span>
                    <span className="text-red-400 font-mono">0.0% (Failed)</span>
                  </div>
                  <div className="flex justify-between">
                    <span>Retinal Structure Presence:</span>
                    <span className="text-red-400 font-mono">Not Detected</span>
                  </div>
                  <div className="flex justify-between">
                    <span>Safety Gate Status:</span>
                    <span className="text-red-400 font-semibold">Classification Halted</span>
                  </div>
                </div>

                <div className="flex flex-col sm:flex-row items-center justify-center gap-3">
                  <button
                    type="button"
                    onClick={() => setCurrentStep(3)}
                    className="w-full sm:w-auto px-6 py-3 rounded-xl bg-white hover:bg-teal-400 text-black font-semibold text-xs transition-colors"
                  >
                    Upload Another Image
                  </button>
                  <button
                    type="button"
                    onClick={() => handleSelectSample(SAMPLE_IMAGE_OPTIONS[0])}
                    className="w-full sm:w-auto px-6 py-3 rounded-xl bg-white/5 hover:bg-white/10 text-neutral-300 text-xs font-medium transition-colors"
                  >
                    Load Valid DR Sample
                  </button>
                </div>
              </div>
            )}

            {/* 4C: POOR QUALITY IMAGE STATE (FIQA Rejection) */}
            {!isScanning && validationResult && validationResult.validationError === 'POOR_QUALITY' && (
              <div className="py-6">
                <div className="w-16 h-16 rounded-2xl bg-amber-500/10 border border-amber-500/30 text-amber-400 flex items-center justify-center mx-auto mb-6">
                  <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                    <path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z" />
                    <line x1="12" y1="9" x2="12" y2="13" />
                    <line x1="12" y1="17" x2="12.01" y2="17" />
                  </svg>
                </div>

                <span className="px-3 py-1 rounded-full bg-amber-500/10 border border-amber-500/20 text-amber-400 font-mono text-xs uppercase">
                  Image Quality Insufficient (FIQA Gate)
                </span>

                <h2 className="text-2xl font-bold font-['Syne'] text-white mt-3 mb-3">
                  Retake / Recapture Required
                </h2>

                <p className="text-xs sm:text-sm text-neutral-300 max-w-lg mx-auto leading-relaxed mb-6">
                  {validationResult.rejectionReason}
                </p>

                <div className="p-4 rounded-2xl bg-black/50 border border-white/5 text-left max-w-md mx-auto mb-8 text-xs text-neutral-400 space-y-2">
                  <div className="flex justify-between">
                    <span>Quality Index Score:</span>
                    <span className="text-amber-400 font-mono font-bold">{validationResult.qualityScore}% (Min: 65%)</span>
                  </div>
                  <div className="flex justify-between">
                    <span>Optical Blur:</span>
                    <span className="text-amber-400 font-mono">{validationResult.blurLevel}</span>
                  </div>
                  <div className="flex justify-between">
                    <span>Retinal Field Visibility:</span>
                    <span className="text-amber-400 font-mono">{validationResult.fieldVisibilityPct}%</span>
                  </div>
                  <div className="flex justify-between">
                    <span>Status:</span>
                    <span className="text-amber-300 font-semibold">Needs Recapture</span>
                  </div>
                </div>

                <div className="flex flex-col sm:flex-row items-center justify-center gap-3">
                  <button
                    type="button"
                    onClick={() => setCurrentStep(3)}
                    className="w-full sm:w-auto px-6 py-3 rounded-xl bg-white hover:bg-amber-400 text-black font-semibold text-xs transition-colors"
                  >
                    Upload Better Image
                  </button>
                  <button
                    type="button"
                    onClick={() => handleSelectSample(SAMPLE_IMAGE_OPTIONS[0])}
                    className="w-full sm:w-auto px-6 py-3 rounded-xl bg-white/5 hover:bg-white/10 text-neutral-300 text-xs font-medium transition-colors"
                  >
                    Load Standard Sample
                  </button>
                </div>
              </div>
            )}
          </div>
        )}

        {/* ========================================================================= */}
        {/* STEP 5: AI RESULT & EXPLAINABILITY */}
        {/* ========================================================================= */}
        {currentStep === 5 && screeningResult && (
          <div className="grid grid-cols-1 lg:grid-cols-12 gap-8">
            {/* Left Interactive Medical Retina Viewer (7 cols) */}
            <div className="lg:col-span-7 space-y-4">
              <MedicalRetinaViewer
                imageUrl={imageUrl}
                grade={screeningResult.classification.dr_grade}
                altText="Screening Output"
              />

              {/* AI Safety Checklist Section */}
              <div className="p-4 rounded-2xl bg-[#0c0d12] border border-white/[0.08]">
                <div className="flex items-center justify-between mb-3">
                  <span className="text-xs font-bold text-neutral-200">AI Screening Safety Audit</span>
                  <span className="text-[10px] font-mono text-emerald-400">✓ All Gates Passed</span>
                </div>
                <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 text-[11px]">
                  <div className="p-2.5 rounded-xl bg-black/40 border border-white/5 text-neutral-300 flex items-center gap-2">
                    <span className="text-emerald-400">✓</span>
                    <span>Fundus Verified</span>
                  </div>
                  <div className="p-2.5 rounded-xl bg-black/40 border border-white/5 text-neutral-300 flex items-center gap-2">
                    <span className="text-emerald-400">✓</span>
                    <span>Quality {screeningResult.quality.score}%</span>
                  </div>
                  <div className="p-2.5 rounded-xl bg-black/40 border border-white/5 text-neutral-300 flex items-center gap-2">
                    <span className="text-emerald-400">✓</span>
                    <span>Confidence {Math.round(screeningResult.classification.confidence * 100)}%</span>
                  </div>
                  <div className="p-2.5 rounded-xl bg-black/40 border border-white/5 text-neutral-300 flex items-center gap-2">
                    <span className="text-emerald-400">✓</span>
                    <span>XAI Generated</span>
                  </div>
                </div>
              </div>
            </div>

            {/* Right Diagnosis & Severity Panel (5 cols) */}
            <div className="lg:col-span-5 flex flex-col justify-between rounded-3xl bg-[#0c0d12] border border-white/[0.08] p-6 sm:p-8">
              <div>
                <div className="flex items-center justify-between mb-3">
                  <span className="text-teal-400 text-xs font-mono">Step 05 of 06 · AI Finding</span>
                  <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-white/5 border border-white/10 text-neutral-300">
                    Case {screeningResult.case_id}
                  </span>
                </div>

                <div className="mb-4">
                  <span
                    className={`inline-block px-3 py-1 rounded-full text-xs font-bold uppercase tracking-wider mb-2 ${
                      screeningResult.classification.dr_grade === 0
                        ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/20'
                        : screeningResult.classification.dr_grade === 1
                        ? 'bg-lime-500/10 text-lime-400 border border-lime-500/20'
                        : screeningResult.classification.dr_grade === 2
                        ? 'bg-amber-500/10 text-amber-400 border border-amber-500/20'
                        : screeningResult.classification.dr_grade === 3
                        ? 'bg-orange-500/10 text-orange-400 border border-orange-500/20'
                        : 'bg-red-500/10 text-red-400 border border-red-500/20'
                    }`}
                  >
                    LEVEL {screeningResult.classification.dr_grade} · DR STAGE
                  </span>
                  <h2 className="text-2xl font-bold font-['Syne'] text-white">
                    {screeningResult.classification.severity}
                  </h2>
                </div>

                {/* Metrics */}
                <div className="grid grid-cols-2 gap-3 mb-6">
                  <div className="p-3.5 rounded-xl bg-black/40 border border-white/5">
                    <span className="text-[11px] text-neutral-500">AI Confidence</span>
                    <p className="text-xl font-bold text-white font-['Syne']">
                      {Math.round(screeningResult.classification.confidence * 100)}%
                    </p>
                  </div>
                  <div className="p-3.5 rounded-xl bg-black/40 border border-white/5">
                    <span className="text-[11px] text-neutral-500">Image Quality</span>
                    <p className="text-xl font-bold text-teal-400 font-['Syne']">
                      {screeningResult.quality.score}%
                    </p>
                  </div>
                </div>

                {/* Evidence breakdown */}
                <div className="space-y-3 mb-6 text-xs">
                  <div className="p-3.5 rounded-xl bg-black/40 border border-white/5">
                    <span className="text-[11px] font-mono text-neutral-400 block mb-1">Primary Biomarker Evidence:</span>
                    <p className="text-neutral-200 leading-relaxed">
                      {screeningResult.evidence_report.primaryEvidence}
                    </p>
                  </div>
                  <div className="p-3.5 rounded-xl bg-black/40 border border-white/5">
                    <span className="text-[11px] font-mono text-neutral-400 block mb-1">Recommended Action:</span>
                    <p className="text-neutral-200 leading-relaxed">
                      {screeningResult.evidence_report.recommendedFollowup}
                    </p>
                  </div>
                </div>
              </div>

              {/* Bottom Action */}
              <div className="pt-4 border-t border-white/[0.06] flex items-center justify-between gap-3">
                <button
                  type="button"
                  onClick={() => setCurrentStep(3)}
                  className="px-5 py-2.5 rounded-xl bg-white/5 hover:bg-white/10 text-neutral-300 text-xs font-medium transition-colors"
                >
                  Re-upload
                </button>
                <button
                  type="button"
                  onClick={() => setCurrentStep(6)}
                  className="flex-1 py-3.5 px-6 rounded-xl bg-white hover:bg-teal-400 text-black font-bold text-xs transition-all shadow-xl flex items-center justify-center gap-2"
                >
                  <span>Proceed to Referral Routing</span>
                  <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
                    <path d="M5 12h14" />
                    <path d="M12 5l7 7-7 7" />
                  </svg>
                </button>
              </div>
            </div>
          </div>
        )}

        {/* ========================================================================= */}
        {/* STEP 6: REFERRAL LOGIC & HOSPITAL SELECTION */}
        {/* ========================================================================= */}
        {currentStep === 6 && screeningResult && !referralSent && (
          <div className="max-w-3xl mx-auto rounded-3xl bg-[#0c0d12] border border-white/[0.08] p-8">
            <div className="mb-6">
              <span className="text-teal-400 text-xs font-mono">Step 06 of 06</span>
              <h2 className="text-2xl font-bold font-['Syne'] text-white mt-1">
                {screeningResult.classification.dr_grade === 0
                  ? 'Screening Complete · No Referral Required'
                  : 'Referral Recommended · Select Facility'}
              </h2>
              <p className="text-xs text-neutral-400 mt-1">
                {screeningResult.classification.dr_grade === 0
                  ? 'No diabetic retinopathy pathology detected. Patient should be scheduled for annual routine re-screening.'
                  : `Clinical review is recommended for Level ${screeningResult.classification.dr_grade} (${screeningResult.classification.severity}). Select destination eye care center.`}
              </p>
            </div>

            {/* Case where DR = 0 (No referral needed) */}
            {screeningResult.classification.dr_grade === 0 ? (
              <div className="py-6 space-y-6 text-center">
                <div className="w-16 h-16 rounded-2xl bg-emerald-500/10 border border-emerald-500/30 text-emerald-400 flex items-center justify-center mx-auto">
                  <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                    <polyline points="20 6 9 17 4 12" />
                  </svg>
                </div>

                <div className="p-4 rounded-2xl bg-black/40 border border-white/5 max-w-md mx-auto text-left text-xs space-y-2">
                  <div className="flex justify-between">
                    <span className="text-neutral-400">Patient:</span>
                    <span className="font-semibold text-white">{patient.patientId}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-neutral-400">AI Result:</span>
                    <span className="text-emerald-400 font-semibold">Grade 0 · No DR Detected</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-neutral-400">Follow-up:</span>
                    <span className="text-neutral-200">12 Months (Routine Annual Checkup)</span>
                  </div>
                </div>

                <button
                  type="button"
                  onClick={handleSendReferral}
                  className="px-8 py-3.5 rounded-xl bg-white hover:bg-emerald-400 text-black font-bold text-xs transition-colors shadow-lg"
                >
                  Complete & Save Screening Case
                </button>
              </div>
            ) : (
              /* Case where DR >= 1 (Referral needed) */
              <div className="space-y-6">
                {/* Location indicator */}
                <div className="p-3.5 rounded-xl bg-teal-500/5 border border-teal-500/20 flex items-center justify-between text-xs">
                  <div>
                    <span className="text-neutral-400">Screening Origin: </span>
                    <span className="font-semibold text-white">{location.centerName}</span>
                  </div>
                  <span className="font-mono text-teal-300">{location.district}</span>
                </div>

                {/* Dynamic Hospital Facility Cards */}
                <div>
                  <label className="block text-xs font-semibold text-neutral-300 mb-3 uppercase font-mono">
                    Available Referral Facilities in {location.district}
                  </label>
                  <div className="space-y-3">
                    {hospitalService.getHospitalsForLocation(location.district, location.state).map((hosp) => (
                      <div
                        key={hosp.id}
                        onClick={() => setSelectedHospital(hosp)}
                        className={`p-4 rounded-2xl border cursor-pointer transition-all ${
                          selectedHospital?.id === hosp.id
                            ? 'bg-teal-500/10 border-teal-500/40 shadow-lg shadow-teal-950/20'
                            : 'bg-black/30 border-white/5 hover:border-white/15'
                        }`}
                      >
                        <div className="flex items-start justify-between gap-3 mb-2">
                          <div>
                            <div className="flex items-center gap-2">
                              <h4 className="text-sm font-bold text-white">{hosp.name}</h4>
                              <span className="text-[10px] font-mono px-1.5 py-0.5 rounded bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
                                ✓ Verified Facility
                              </span>
                            </div>
                            <p className="text-xs text-neutral-400 mt-0.5">{hosp.specialization}</p>
                          </div>
                          <div className="text-right flex-shrink-0">
                            <span className="text-xs font-bold text-teal-300 font-mono">{hosp.distanceKm} km</span>
                            <span className="block text-[10px] text-neutral-500">Transit Distance</span>
                          </div>
                        </div>

                        <div className="flex flex-wrap items-center gap-4 text-[11px] text-neutral-400 pt-2 border-t border-white/5">
                          <span>👤 {hosp.ophthalmologistOnDuty}</span>
                          <span>🛏️ {hosp.bedAvailability}</span>
                          <span>📞 {hosp.contactNumber}</span>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>

                {/* Submit Referral Button */}
                <div className="pt-4 flex items-center justify-between">
                  <button
                    type="button"
                    onClick={() => setCurrentStep(5)}
                    className="px-5 py-2.5 rounded-xl bg-white/5 hover:bg-white/10 text-neutral-300 text-xs font-medium transition-colors"
                  >
                    Back to Result
                  </button>
                  <button
                    type="button"
                    disabled={!selectedHospital}
                    onClick={handleSendReferral}
                    className="px-8 py-3.5 rounded-xl bg-white hover:bg-teal-400 text-black font-bold text-xs transition-all shadow-xl flex items-center gap-2 disabled:opacity-40"
                  >
                    <span>Send Case to Doctor</span>
                    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
                      <path d="M5 12h14" />
                      <path d="M12 5l7 7-7 7" />
                    </svg>
                  </button>
                </div>
              </div>
            )}
          </div>
        )}

        {/* ========================================================================= */}
        {/* REFERRAL CONFIRMATION SCREEN */}
        {/* ========================================================================= */}
        {referralSent && referralSuccessCase && (
          <div className="max-w-2xl mx-auto rounded-3xl bg-[#0c0d12] border border-white/[0.08] p-8 text-center">
            <div className="w-16 h-16 rounded-2xl bg-teal-500/10 border border-teal-500/30 text-teal-400 flex items-center justify-center mx-auto mb-6">
              <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <path d="M22 11.08V12a10 10 0 1 1-5.93-9.14" />
                <polyline points="22 4 12 14.01 9 11.01" />
              </svg>
            </div>

            <span className="px-3 py-1 rounded-full bg-teal-500/10 border border-teal-500/20 text-teal-400 font-mono text-xs uppercase">
              {referralSuccessCase.referral?.required ? 'Case Successfully Referred' : 'Screening Case Completed'}
            </span>

            <h2 className="text-2xl font-bold font-['Syne'] text-white mt-3 mb-2">
              Case ID: {referralSuccessCase.id}
            </h2>

            {referralSuccessCase.referral?.required && (
              <p className="text-xs text-neutral-400 mb-6">
                Routed to: {referralSuccessCase.referral.hospital?.name}
              </p>
            )}

            {/* Clinical Workflow Timeline */}
            <div className="p-6 rounded-2xl bg-black/40 border border-white/5 text-left max-w-md mx-auto mb-8">
              <p className="text-[11px] font-mono text-neutral-400 uppercase mb-4">Case Progression Timeline</p>
              <div className="space-y-4 text-xs">
                <div className="flex items-center gap-3">
                  <div className="w-5 h-5 rounded-full bg-emerald-500/20 text-emerald-400 flex items-center justify-center text-[10px] font-bold">
                    ✓
                  </div>
                  <div className="flex-1 flex justify-between">
                    <span className="text-white font-medium">Retinal Scan Captured</span>
                    <span className="text-neutral-500 font-mono text-[10px]">Passed</span>
                  </div>
                </div>

                <div className="flex items-center gap-3">
                  <div className="w-5 h-5 rounded-full bg-emerald-500/20 text-emerald-400 flex items-center justify-center text-[10px] font-bold">
                    ✓
                  </div>
                  <div className="flex-1 flex justify-between">
                    <span className="text-white font-medium">AI Multistage Screening</span>
                    <span className="text-emerald-400 font-mono text-[10px]">
                      Level {referralSuccessCase.screeningResult?.classification.dr_grade}
                    </span>
                  </div>
                </div>

                {referralSuccessCase.referral?.required && (
                  <div className="flex items-center gap-3">
                    <div className="w-5 h-5 rounded-full bg-emerald-500/20 text-emerald-400 flex items-center justify-center text-[10px] font-bold">
                      ✓
                    </div>
                    <div className="flex-1 flex justify-between">
                      <span className="text-white font-medium">Referral Dispatched</span>
                      <span className="text-neutral-400 font-mono text-[10px]">Transferred</span>
                    </div>
                  </div>
                )}

                <div className="flex items-center gap-3">
                  <div className="w-5 h-5 rounded-full bg-amber-500/20 text-amber-400 flex items-center justify-center text-[10px] font-bold animate-pulse">
                    ●
                  </div>
                  <div className="flex-1 flex justify-between">
                    <span className="text-amber-300 font-medium">Doctor Clinical Review</span>
                    <span className="text-amber-400 font-mono text-[10px]">Queued</span>
                  </div>
                </div>
              </div>
            </div>

            {/* Navigation Actions */}
            <div className="flex flex-col sm:flex-row items-center justify-center gap-3">
              <Link
                to={`/report/${referralSuccessCase.id}`}
                className="w-full sm:w-auto px-6 py-3 rounded-xl bg-white hover:bg-teal-400 text-black font-semibold text-xs transition-colors"
              >
                View Case Report
              </Link>
              <Link
                to="/worker/dashboard"
                className="w-full sm:w-auto px-6 py-3 rounded-xl bg-white/5 hover:bg-white/10 text-neutral-300 text-xs font-medium transition-colors"
              >
                Back to Dashboard
              </Link>
            </div>
          </div>
        )}
      </main>
    </div>
  );
};

export default NewScreeningPage;
