import React, { useState, useRef, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { AppHeader } from '@/components/layout/AppHeader';
import { MedicalRetinaViewer } from '@/components/viewer/MedicalRetinaViewer';
import { screeningService, SAMPLE_IMAGE_OPTIONS } from '@/services/screeningService';
import { hospitalService, GroupedLocations } from '@/services/hospitalService';
import { caseService } from '@/services/caseService';
import {
  PatientInfo,
  HospitalFacility,
  ScreeningResult,
  ImageValidationResult,
  SampleImageOption,
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
  '01 Validating retinal fundus image...',
  '02 Checking optical quality and illumination (FIQA)...',
  '03 Detecting retinal structures & landmarks...',
  '04 Classifying DR severity grade (ResNet18)...',
  '05 Generating Grad-CAM explainability heatmap...',
  '06 Validating prediction safety & generating report...',
];

const NewScreeningPage: React.FC = () => {
  const fileInputRef = useRef<HTMLInputElement>(null);

  // Workflow Step State (1 to 6)
  const [currentStep, setCurrentStep] = useState<number>(1);

  // Dynamic Case ID
  const [activeCaseId, setActiveCaseId] = useState<string>('');

  // Step 1: Patient Details
  const [patient, setPatient] = useState<PatientInfo>({
    patientId: `PID-${Math.floor(1000 + Math.random() * 9000)}`,
    age: 54,
    gender: 'Male',
    screeningDate: new Date().toISOString().split('T')[0],
    notes: 'Routine rural diabetic retinopathy screening. Mild visual blur reported.',
  });

  // Step 2: Location
  const [groupedLocations, setGroupedLocations] = useState<GroupedLocations[]>([]);
  const [selectedState, setSelectedState] = useState<string>('Tamil Nadu');
  const [selectedDistrict, setSelectedDistrict] = useState<string>('Coimbatore');
  const [selectedLocationId, setSelectedLocationId] = useState<number>(1);
  const [selectedCenterName, setSelectedCenterName] = useState<string>('Primary Health Centre — Valparai');

  // Step 3: Fundus Upload State
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [imageUrl, setImageUrl] = useState<string>(SAMPLE_IMAGE_OPTIONS[0].imageUrl);
  const [selectedSample, setSelectedSample] = useState<SampleImageOption | null>(SAMPLE_IMAGE_OPTIONS[0]);
  const [imageMeta, setImageMeta] = useState({
    filename: 'sample_fundus.jpg',
    resolution: '1024×1024 RGB',
    sizeKb: 2450,
  });

  // Step 4: AI Scanning State
  const [, setIsScanning] = useState<boolean>(false);
  const [scanMessageIndex, setScanMessageIndex] = useState<number>(0);
  const [validationResult, setValidationResult] = useState<ImageValidationResult | null>(null);
  const [screeningResult, setScreeningResult] = useState<ScreeningResult | null>(null);
  const [scanError, setScanError] = useState<string | null>(null);

  // Step 6: Referral State
  const [hospitals, setHospitals] = useState<HospitalFacility[]>([]);
  const [selectedHospital, setSelectedHospital] = useState<HospitalFacility | null>(null);
  const [referralNotes, setReferralNotes] = useState<string>('Specialist review requested for referable diabetic retinopathy findings.');
  const [referralSubmitting, setReferralSubmitting] = useState<boolean>(false);
  const [referralSuccess, setReferralSuccess] = useState<boolean>(false);

  // Load locations from backend
  useEffect(() => {
    hospitalService.getGroupedLocations().then((groups) => {
      if (groups.length > 0) {
        setGroupedLocations(groups);
        const firstState = groups[0];
        setSelectedState(firstState.state);
        if (firstState.districts.length > 0) {
          const firstDist = firstState.districts[0];
          setSelectedDistrict(firstDist.name);
          if (firstDist.centers.length > 0) {
            setSelectedLocationId(firstDist.centers[0].id);
            setSelectedCenterName(firstDist.centers[0].name);
          }
        }
      }
    });
  }, []);

  // Update district/center when state changes
  const handleStateChange = (stateName: string) => {
    setSelectedState(stateName);
    const st = groupedLocations.find((g) => g.state === stateName);
    if (st && st.districts.length > 0) {
      const dist = st.districts[0];
      setSelectedDistrict(dist.name);
      if (dist.centers.length > 0) {
        setSelectedLocationId(dist.centers[0].id);
        setSelectedCenterName(dist.centers[0].name);
      }
    }
  };

  const handleDistrictChange = (distName: string) => {
    setSelectedDistrict(distName);
    const st = groupedLocations.find((g) => g.state === selectedState);
    if (st) {
      const dist = st.districts.find((d) => d.name === distName);
      if (dist && dist.centers.length > 0) {
        setSelectedLocationId(dist.centers[0].id);
        setSelectedCenterName(dist.centers[0].name);
      }
    }
  };

  const handleCenterChange = (locId: number) => {
    setSelectedLocationId(locId);
    const st = groupedLocations.find((g) => g.state === selectedState);
    if (st) {
      const dist = st.districts.find((d) => d.name === selectedDistrict);
      const center = dist?.centers.find((c) => c.id === locId);
      if (center) {
        setSelectedCenterName(center.name);
      }
    }
  };

  // Handle file upload
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

  const handleSelectSample = (sample: SampleImageOption) => {
    setSelectedSample(sample);
    setSelectedFile(null);
    setImageUrl(sample.imageUrl);
    setImageMeta({
      filename: `${sample.id}.jpg`,
      resolution: '1024×1024 Standard',
      sizeKb: 1820,
    });
  };

  // Execute Step 4: Multi-stage AI screening with safety gates
  const startAIScreening = async () => {
    setCurrentStep(4);
    setIsScanning(true);
    setScanMessageIndex(0);
    setValidationResult(null);
    setScreeningResult(null);
    setScanError(null);

    // Progressive message interval for UX transparency
    const timer = setInterval(() => {
      setScanMessageIndex((prev) => (prev < SCAN_MESSAGES.length - 1 ? prev + 1 : prev));
    }, 700);

    try {
      // 1. Create or ensure Screening Case in MySQL
      let caseId = activeCaseId;
      if (!caseId) {
        const created = await caseService.createCase({
          patientId: patient.patientId,
          age: patient.age,
          gender: patient.gender,
          locationId: selectedLocationId,
          notes: patient.notes,
        });
        caseId = created.case_id;
        setActiveCaseId(caseId);
      }

      // 2. Upload file or sample image to backend storage
      let uploadFile = selectedFile;
      if (!uploadFile) {
        // Fetch sample image as blob
        try {
          const res = await fetch(imageUrl);
          const blob = await res.blob();
          uploadFile = new File([blob], imageMeta.filename, { type: blob.type || 'image/jpeg' });
        } catch {
          // Fallback dummy file if fetch fails
          const emptyBlob = new Blob([''], { type: 'image/jpeg' });
          uploadFile = new File([emptyBlob], imageMeta.filename, { type: 'image/jpeg' });
        }
      }

      await screeningService.uploadImage(caseId, uploadFile);

      // 3. Stage 1 & 2: Fundus Modality Verification & Quality Gate
      const validation = await screeningService.validateImage(caseId);
      setValidationResult(validation);

      // Check rejection at Modality Gate (e.g. Porsche car, wallpaper, face, screenshot)
      if (!validation.isValidFundus) {
        clearInterval(timer);
        setIsScanning(false);
        setCurrentStep(5); // Show rejection screen
        return;
      }

      // Check failure at Quality Gate
      if (validation.validationError === 'POOR_QUALITY') {
        clearInterval(timer);
        setIsScanning(false);
        setCurrentStep(5); // Show quality warning screen
        return;
      }

      // 4. Stage 3 & 4: Deep DR Classification & Explainability
      const result = await screeningService.screenImage(caseId, imageUrl);
      setScreeningResult(result);

      clearInterval(timer);
      setIsScanning(false);
      setCurrentStep(5);
    } catch (err: any) {
      clearInterval(timer);
      setIsScanning(false);
      setScanError(err.message || 'AI Screening execution failed. Please check backend connection.');
    }
  };

  // Load hospitals when entering referral step
  const handleProceedToReferral = async () => {
    setCurrentStep(6);
    const facilities = await hospitalService.getHospitalsForLocation(selectedLocationId);
    setHospitals(facilities);
    if (facilities.length > 0) {
      setSelectedHospital(facilities[0]);
    }
  };

  // Submit referral to MySQL
  const handleConfirmReferral = async () => {
    if (!selectedHospital || !activeCaseId) return;
    setReferralSubmitting(true);
    try {
      await caseService.referCase(activeCaseId, parseInt(selectedHospital.id), referralNotes);
      setReferralSuccess(true);
    } catch (err) {
      console.error('Referral failed:', err);
      alert('Failed to submit referral. Please try again.');
    } finally {
      setReferralSubmitting(false);
    }
  };

  const getSeverityBadge = (grade: number) => {
    switch (grade) {
      case 0:
        return <span className="px-3 py-1 rounded-full text-xs font-semibold bg-emerald-500/10 text-emerald-400 border border-emerald-500/30">Level 0 · No Diabetic Retinopathy</span>;
      case 1:
        return <span className="px-3 py-1 rounded-full text-xs font-semibold bg-lime-500/10 text-lime-400 border border-lime-500/30">Level 1 · Mild NPDR</span>;
      case 2:
        return <span className="px-3 py-1 rounded-full text-xs font-semibold bg-amber-500/10 text-amber-400 border border-amber-500/30">Level 2 · Moderate NPDR</span>;
      case 3:
        return <span className="px-3 py-1 rounded-full text-xs font-semibold bg-orange-500/10 text-orange-400 border border-orange-500/30">Level 3 · Severe NPDR</span>;
      case 4:
        return <span className="px-3 py-1 rounded-full text-xs font-semibold bg-red-500/10 text-red-400 border border-red-500/30">Level 4 · Proliferative DR</span>;
      default:
        return null;
    }
  };

  return (
    <div className="min-h-screen bg-[#070709] text-white flex flex-col">
      <AppHeader />

      <main className="flex-1 max-w-6xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Step Progress Tracker */}
        <div className="mb-8">
          <div className="flex items-center justify-between mb-4">
            <div>
              <div className="flex items-center gap-2">
                <span className="text-xs font-mono text-teal-400 uppercase">Screening Workflow</span>
                {activeCaseId && (
                  <span className="text-[11px] font-mono px-2 py-0.5 rounded bg-white/5 border border-white/10 text-neutral-300">
                    Case: {activeCaseId}
                  </span>
                )}
              </div>
              <h1 className="text-xl sm:text-2xl font-bold font-['Syne'] text-white">
                {currentStep === 1 && 'Patient Information'}
                {currentStep === 2 && 'Healthcare Center & Location'}
                {currentStep === 3 && 'Fundus Image Acquisition'}
                {currentStep === 4 && 'Multi-Stage AI Evaluation'}
                {currentStep === 5 && 'AI Screening Diagnostic Result'}
                {currentStep === 6 && 'Specialist Referral Routing'}
              </h1>
            </div>
            <span className="text-xs font-mono text-neutral-400">Step 0{currentStep} of 06</span>
          </div>

          {/* Stepper Progress Bar */}
          <div className="grid grid-cols-6 gap-2">
            {STEPS.map((step, idx) => {
              const stepNum = idx + 1;
              const isPast = stepNum < currentStep;
              const isCurrent = stepNum === currentStep;

              return (
                <div
                  key={step.n}
                  className={`h-2 rounded-full transition-all ${
                    isCurrent
                      ? 'bg-teal-400'
                      : isPast
                      ? 'bg-emerald-500/60'
                      : 'bg-white/10'
                  }`}
                />
              );
            })}
          </div>
        </div>

        {/* ========================================================================= */}
        {/* STEP 01: Patient Details */}
        {/* ========================================================================= */}
        {currentStep === 1 && (
          <div className="max-w-2xl mx-auto rounded-3xl bg-[#0a0a0d] border border-white/[0.08] p-6 sm:p-10">
            <h2 className="text-lg font-bold font-['Syne'] text-white mb-2">Patient Case Details</h2>
            <p className="text-xs text-neutral-400 mb-6">
              Enter the patient identifier and clinical notes for this retinal screening session.
            </p>

            <form
              onSubmit={(e) => {
                e.preventDefault();
                setCurrentStep(2);
              }}
              className="space-y-4"
            >
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <div>
                  <label className="text-[11px] font-mono text-neutral-400 uppercase block mb-1.5">
                    Patient ID
                  </label>
                  <input
                    type="text"
                    required
                    value={patient.patientId}
                    onChange={(e) => setPatient({ ...patient, patientId: e.target.value })}
                    className="w-full bg-[#111116] border border-white/10 rounded-xl px-4 py-2.5 text-xs text-white focus:outline-none focus:border-teal-500 font-mono"
                  />
                </div>

                <div>
                  <label className="text-[11px] font-mono text-neutral-400 uppercase block mb-1.5">
                    Age
                  </label>
                  <input
                    type="number"
                    required
                    min={1}
                    max={120}
                    value={patient.age}
                    onChange={(e) => setPatient({ ...patient, age: parseInt(e.target.value) || 0 })}
                    className="w-full bg-[#111116] border border-white/10 rounded-xl px-4 py-2.5 text-xs text-white focus:outline-none focus:border-teal-500"
                  />
                </div>
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <div>
                  <label className="text-[11px] font-mono text-neutral-400 uppercase block mb-1.5">
                    Gender
                  </label>
                  <select
                    value={patient.gender}
                    onChange={(e) => setPatient({ ...patient, gender: e.target.value as any })}
                    className="w-full bg-[#111116] border border-white/10 rounded-xl px-4 py-2.5 text-xs text-white focus:outline-none focus:border-teal-500"
                  >
                    <option value="Male">Male</option>
                    <option value="Female">Female</option>
                    <option value="Other">Other</option>
                  </select>
                </div>

                <div>
                  <label className="text-[11px] font-mono text-neutral-400 uppercase block mb-1.5">
                    Screening Date
                  </label>
                  <input
                    type="date"
                    value={patient.screeningDate}
                    onChange={(e) => setPatient({ ...patient, screeningDate: e.target.value })}
                    className="w-full bg-[#111116] border border-white/10 rounded-xl px-4 py-2.5 text-xs text-white focus:outline-none focus:border-teal-500"
                  />
                </div>
              </div>

              <div>
                <label className="text-[11px] font-mono text-neutral-400 uppercase block mb-1.5">
                  Clinical Notes (Optional)
                </label>
                <textarea
                  rows={3}
                  value={patient.notes || ''}
                  onChange={(e) => setPatient({ ...patient, notes: e.target.value })}
                  placeholder="Reported symptoms, duration of diabetes, visual complaints..."
                  className="w-full bg-[#111116] border border-white/10 rounded-xl p-3 text-xs text-white placeholder-neutral-500 focus:outline-none focus:border-teal-500"
                />
              </div>

              <div className="pt-4 flex justify-end">
                <button
                  type="submit"
                  className="px-6 py-3 rounded-2xl bg-white hover:bg-teal-400 text-black font-bold text-xs transition-all shadow-lg"
                >
                  Proceed to Location →
                </button>
              </div>
            </form>
          </div>
        )}

        {/* ========================================================================= */}
        {/* STEP 02: Location Selection */}
        {/* ========================================================================= */}
        {currentStep === 2 && (
          <div className="max-w-2xl mx-auto rounded-3xl bg-[#0a0a0d] border border-white/[0.08] p-6 sm:p-10">
            <h2 className="text-lg font-bold font-['Syne'] text-white mb-2">Location & Health Facility</h2>
            <p className="text-xs text-neutral-400 mb-6">
              Select the primary health center where this screening is being performed.
            </p>

            <form
              onSubmit={(e) => {
                e.preventDefault();
                setCurrentStep(3);
              }}
              className="space-y-4"
            >
              <div>
                <label className="text-[11px] font-mono text-neutral-400 uppercase block mb-1.5">
                  State
                </label>
                <select
                  value={selectedState}
                  onChange={(e) => handleStateChange(e.target.value)}
                  className="w-full bg-[#111116] border border-white/10 rounded-xl px-4 py-2.5 text-xs text-white focus:outline-none focus:border-teal-500"
                >
                  {groupedLocations.map((g) => (
                    <option key={g.state} value={g.state}>
                      {g.state}
                    </option>
                  ))}
                </select>
              </div>

              <div>
                <label className="text-[11px] font-mono text-neutral-400 uppercase block mb-1.5">
                  District
                </label>
                <select
                  value={selectedDistrict}
                  onChange={(e) => handleDistrictChange(e.target.value)}
                  className="w-full bg-[#111116] border border-white/10 rounded-xl px-4 py-2.5 text-xs text-white focus:outline-none focus:border-teal-500"
                >
                  {groupedLocations
                    .find((g) => g.state === selectedState)
                    ?.districts.map((d) => (
                      <option key={d.name} value={d.name}>
                        {d.name}
                      </option>
                    ))}
                </select>
              </div>

              <div>
                <label className="text-[11px] font-mono text-neutral-400 uppercase block mb-1.5">
                  Healthcare Centre
                </label>
                <select
                  value={selectedLocationId}
                  onChange={(e) => handleCenterChange(parseInt(e.target.value))}
                  className="w-full bg-[#111116] border border-white/10 rounded-xl px-4 py-2.5 text-xs text-white focus:outline-none focus:border-teal-500"
                >
                  {groupedLocations
                    .find((g) => g.state === selectedState)
                    ?.districts.find((d) => d.name === selectedDistrict)
                    ?.centers.map((c) => (
                      <option key={c.id} value={c.id}>
                        {c.name} ({c.code})
                      </option>
                    ))}
                </select>
              </div>

              <div className="p-4 rounded-2xl bg-teal-500/5 border border-teal-500/20 text-xs text-neutral-300">
                <p className="font-semibold text-teal-400 mb-1">Selected Unit: {selectedCenterName}</p>
                <p className="text-[11px] text-neutral-400">
                  Location is stored with the case record in MySQL to filter nearby verified referral eye hospitals.
                </p>
              </div>

              <div className="pt-4 flex items-center justify-between">
                <button
                  type="button"
                  onClick={() => setCurrentStep(1)}
                  className="px-4 py-2 rounded-xl bg-white/5 hover:bg-white/10 text-neutral-400 hover:text-white text-xs"
                >
                  ← Back
                </button>
                <button
                  type="submit"
                  className="px-6 py-3 rounded-2xl bg-white hover:bg-teal-400 text-black font-bold text-xs transition-all shadow-lg"
                >
                  Proceed to Upload →
                </button>
              </div>
            </form>
          </div>
        )}

        {/* ========================================================================= */}
        {/* STEP 03: Fundus Image Upload */}
        {/* ========================================================================= */}
        {currentStep === 3 && (
          <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
            <div className="lg:col-span-7 rounded-3xl bg-[#0a0a0d] border border-white/[0.08] p-6 sm:p-8 space-y-6">
              <div>
                <h2 className="text-lg font-bold font-['Syne'] text-white mb-1">Fundus Image Upload</h2>
                <p className="text-xs text-neutral-400">
                  Upload a standard retinal fundus photograph captured from a tabletop or portable fundus camera.
                </p>
              </div>

              {/* Upload Dropzone */}
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
                <p className="text-xs text-neutral-500 mb-3">Supported formats: JPEG, PNG, TIFF, BMP</p>
                <button
                  type="button"
                  className="px-4 py-2 rounded-lg bg-white/10 group-hover:bg-teal-400 group-hover:text-black text-white text-xs font-medium transition-colors"
                >
                  Select File from Device
                </button>
              </div>

              {/* Quick Sample Selector for Live Demonstration */}
              <div className="pt-4 border-t border-white/[0.06]">
                <div className="flex items-center justify-between mb-3">
                  <span className="text-xs font-semibold text-neutral-300">⚡ Test Presets (Validation & Safety Gate Tests)</span>
                  <span className="text-[10px] text-neutral-500 font-mono">1-Click Load</span>
                </div>
                <div className="grid grid-cols-1 sm:grid-cols-3 gap-2.5">
                  {SAMPLE_IMAGE_OPTIONS.map((sample) => (
                    <button
                      key={sample.id}
                      type="button"
                      onClick={() => handleSelectSample(sample)}
                      className={`p-3 rounded-xl border text-left transition-all ${
                        selectedSample?.id === sample.id
                          ? 'bg-teal-500/10 border-teal-500/40 text-white shadow-sm'
                          : 'bg-black/30 border-white/[0.05] text-neutral-400 hover:text-neutral-200'
                      }`}
                    >
                      <p className="text-xs font-semibold mb-1">{sample.label}</p>
                      <p className="text-[10px] text-neutral-500 line-clamp-1">{sample.subtitle}</p>
                    </button>
                  ))}
                </div>
              </div>
            </div>

            {/* Right Preview Panel */}
            <div className="lg:col-span-5 rounded-3xl bg-[#0a0a0d] border border-white/[0.08] p-6 sm:p-8 flex flex-col justify-between">
              <div>
                <div className="flex items-center justify-between mb-4">
                  <h3 className="text-sm font-semibold text-white">Image Preview</h3>
                  <span className="text-[10px] font-mono text-neutral-400">{imageMeta.filename}</span>
                </div>

                <div className="aspect-square w-full rounded-2xl bg-black border border-white/10 overflow-hidden flex items-center justify-center mb-4">
                  {imageUrl ? (
                    <img src={imageUrl} alt="Fundus Preview" className="w-full h-full object-contain" />
                  ) : (
                    <span className="text-xs text-neutral-500 font-mono">No Image</span>
                  )}
                </div>

                <div className="p-3 rounded-xl bg-black/40 border border-white/5 text-xs text-neutral-400 space-y-1 font-mono">
                  <div className="flex justify-between">
                    <span>Resolution:</span>
                    <span className="text-white">{imageMeta.resolution}</span>
                  </div>
                  <div className="flex justify-between">
                    <span>File Size:</span>
                    <span className="text-white">{imageMeta.sizeKb} KB</span>
                  </div>
                </div>
              </div>

              <div className="pt-6 flex items-center justify-between">
                <button
                  type="button"
                  onClick={() => setCurrentStep(2)}
                  className="px-4 py-2 rounded-xl bg-white/5 hover:bg-white/10 text-neutral-400 hover:text-white text-xs"
                >
                  ← Back
                </button>
                <button
                  type="button"
                  onClick={startAIScreening}
                  className="px-6 py-3 rounded-2xl bg-teal-500 hover:bg-teal-400 text-black font-bold text-xs transition-all shadow-lg"
                >
                  Run AI Screening Pipeline →
                </button>
              </div>
            </div>
          </div>
        )}

        {/* ========================================================================= */}
        {/* STEP 04: AI Scanning Progress Animation */}
        {/* ========================================================================= */}
        {currentStep === 4 && (
          <div className="max-w-2xl mx-auto rounded-3xl bg-[#0a0a0d] border border-white/[0.08] p-8 sm:p-12 text-center">
            <div className="relative w-24 h-24 mx-auto mb-8">
              <div className="absolute inset-0 rounded-full border-4 border-teal-500/20 animate-ping" />
              <div className="absolute inset-0 rounded-full border-4 border-teal-400 border-t-transparent animate-spin" />
              <div className="absolute inset-3 rounded-full bg-black flex items-center justify-center">
                <span className="text-xl">👁️</span>
              </div>
            </div>

            <h2 className="text-xl font-bold font-['Syne'] text-white mb-2">Analyzing Retinal Image</h2>
            <p className="text-xs text-neutral-400 mb-8 max-w-md mx-auto">
              Executing multi-gate clinical safety checks, FIQA quality scoring, and explainable AI inference.
            </p>

            {/* Sequence Status List */}
            <div className="space-y-3 max-w-md mx-auto text-left">
              {SCAN_MESSAGES.map((msg, idx) => {
                const isPassed = idx < scanMessageIndex;
                const isCurrent = idx === scanMessageIndex;

                return (
                  <div
                    key={idx}
                    className={`flex items-center gap-3 p-3 rounded-xl border text-xs transition-all ${
                      isCurrent
                        ? 'bg-teal-500/10 border-teal-500/40 text-teal-300 font-semibold'
                        : isPassed
                        ? 'bg-black/30 border-white/5 text-neutral-400'
                        : 'bg-black/10 border-transparent text-neutral-600'
                    }`}
                  >
                    <span className="font-mono">
                      {isPassed ? '✓' : isCurrent ? '●' : '○'}
                    </span>
                    <span>{msg}</span>
                  </div>
                );
              })}
            </div>

            {scanError && (
              <div className="mt-6 p-4 rounded-2xl bg-red-500/10 border border-red-500/30 text-xs text-red-400">
                {scanError}
              </div>
            )}
          </div>
        )}

        {/* ========================================================================= */}
        {/* STEP 05: AI Screening Diagnostic Result */}
        {/* ========================================================================= */}
        {currentStep === 5 && (
          <div className="space-y-6">
            {/* ------------------------------------------------------------------- */}
            {/* SAFETY GATE 1 FAILURE: Non-Fundus Image Rejection (Porsche test) */}
            {/* ------------------------------------------------------------------- */}
            {validationResult && !validationResult.isValidFundus ? (
              <div className="max-w-2xl mx-auto rounded-3xl bg-[#12080a] border border-red-500/30 p-8 sm:p-10 text-center space-y-6">
                <div className="w-16 h-16 rounded-2xl bg-red-500/10 border border-red-500/30 text-red-400 flex items-center justify-center mx-auto text-2xl">
                  ⚠️
                </div>
                <div>
                  <span className="text-[11px] font-mono px-3 py-1 rounded-full bg-red-500/10 text-red-400 border border-red-500/30 uppercase">
                    Modality Gate Verification: FAILED
                  </span>
                  <h2 className="text-2xl font-bold font-['Syne'] text-white mt-3 mb-2">
                    Image Not Recognized
                  </h2>
                  <p className="text-sm text-neutral-300 max-w-md mx-auto leading-relaxed">
                    {validationResult.rejectionReason || 'This image does not appear to be a retinal fundus photograph.'}
                  </p>
                </div>

                <div className="p-4 rounded-2xl bg-black/60 border border-white/5 text-xs text-neutral-400 text-left space-y-2">
                  <p className="font-semibold text-white">Clinical AI Safety Guarantee:</p>
                  <p>
                    • DR classification, Grad-CAM saliency mapping, and lesion segmentation are <strong>strictly halted</strong> on non-retinal inputs.
                  </p>
                  <p>
                    • No false positive diagnoses are generated for non-medical photographs.
                  </p>
                </div>

                <div className="pt-2 flex justify-center">
                  <button
                    onClick={() => setCurrentStep(3)}
                    className="px-6 py-3.5 rounded-2xl bg-white hover:bg-neutral-200 text-black font-bold text-xs transition-all shadow-lg"
                  >
                    Upload Another Image
                  </button>
                </div>
              </div>
            ) : validationResult && validationResult.validationError === 'POOR_QUALITY' ? (
              /* ------------------------------------------------------------------- */
              /* SAFETY GATE 2 FAILURE: Poor Optical Quality (FIQA Gate) */
              /* ------------------------------------------------------------------- */
              <div className="max-w-2xl mx-auto rounded-3xl bg-[#140f08] border border-amber-500/30 p-8 sm:p-10 text-center space-y-6">
                <div className="w-16 h-16 rounded-2xl bg-amber-500/10 border border-amber-500/30 text-amber-400 flex items-center justify-center mx-auto text-2xl">
                  🔍
                </div>
                <div>
                  <span className="text-[11px] font-mono px-3 py-1 rounded-full bg-amber-500/10 text-amber-400 border border-amber-500/30 uppercase">
                    Image Quality Insufficient (FIQA Gate)
                  </span>
                  <h2 className="text-2xl font-bold font-['Syne'] text-white mt-3 mb-2">
                    Recapture Recommended
                  </h2>
                  <p className="text-sm text-neutral-300 max-w-md mx-auto leading-relaxed">
                    Severe optical blur, lighting artifacts, or dark peripheral falloff detected. Unreliable for autonomous AI grading.
                  </p>
                </div>

                <div className="p-4 rounded-2xl bg-black/60 border border-white/5 text-xs text-neutral-400 text-left space-y-1.5">
                  <p className="font-semibold text-white mb-1">Recapture Recommendations:</p>
                  <p>• Adjust objective lens focus directly on retinal blood vessels.</p>
                  <p>• Ensure patient pupil is properly aligned with camera optical axis.</p>
                  <p>• Increase flash intensity or re-center fundus field.</p>
                </div>

                <div className="pt-2 flex justify-center">
                  <button
                    onClick={() => setCurrentStep(3)}
                    className="px-6 py-3.5 rounded-2xl bg-amber-500 hover:bg-amber-400 text-black font-bold text-xs transition-all shadow-lg"
                  >
                    Recapture / Re-upload Clearer Image
                  </button>
                </div>
              </div>
            ) : screeningResult ? (
              /* ------------------------------------------------------------------- */
              /* VALID RETINAL FUNDUS RESULT */
              /* ------------------------------------------------------------------- */
              <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
                {/* Left Column: Result Details & Evidence (7 cols) */}
                <div className="lg:col-span-7 space-y-6">
                  {/* Primary Diagnosis Card */}
                  <div className="rounded-3xl bg-[#0a0a0d] border border-white/[0.08] p-6 sm:p-8">
                    <div className="flex items-center justify-between mb-4">
                      {getSeverityBadge(screeningResult.classification.dr_grade)}
                      <span className="text-xs font-mono text-teal-400">
                        AI Confidence: {Math.round(screeningResult.classification.confidence * 100)}%
                      </span>
                    </div>

                    <h2 className="text-2xl sm:text-3xl font-bold font-['Syne'] text-white mb-2">
                      {screeningResult.classification.severity}
                    </h2>
                    <p className="text-xs text-neutral-400 leading-relaxed mb-6">
                      {screeningResult.evidence_report.primaryEvidence || 'Multi-stage deep learning analysis completed.'}
                    </p>

                    {/* Quality & Safety Metrics */}
                    <div className="grid grid-cols-3 gap-3 p-4 rounded-2xl bg-black/40 border border-white/5 text-xs font-mono">
                      <div>
                        <p className="text-neutral-500 text-[10px]">FIQA Quality</p>
                        <p className="font-bold text-white mt-0.5">{screeningResult.quality.score}%</p>
                      </div>
                      <div>
                        <p className="text-neutral-500 text-[10px]">Field View</p>
                        <p className="font-bold text-white mt-0.5">{screeningResult.validation.fieldVisibilityPct}%</p>
                      </div>
                      <div>
                        <p className="text-neutral-500 text-[10px]">Modality</p>
                        <p className="font-bold text-teal-400 mt-0.5">Fundus ✓</p>
                      </div>
                    </div>
                  </div>

                  {/* Biomarker Lesions Breakdown */}
                  <div className="rounded-3xl bg-[#0a0a0d] border border-white/[0.08] p-6">
                    <h3 className="text-sm font-semibold text-white font-['Syne'] mb-3">Detected Retinal Lesions</h3>
                    {screeningResult.segmentation?.lesions && screeningResult.segmentation.lesions.length > 0 ? (
                      <div className="grid grid-cols-2 gap-3">
                        {screeningResult.segmentation.lesions.map((l, idx) => (
                          <div key={idx} className="p-3 rounded-xl bg-black/40 border border-white/5 flex items-center justify-between text-xs">
                            <span className="text-neutral-300">{l.type}</span>
                            <span className="font-mono text-teal-400 font-semibold">{l.num_regions} regions</span>
                          </div>
                        ))}
                      </div>
                    ) : (
                      <p className="text-xs text-neutral-500 italic">No microaneurysms, hemorrhages, or exudates detected.</p>
                    )}
                  </div>
                </div>

                {/* Right Column: Retinal Viewer & Next Action (5 cols) */}
                <div className="lg:col-span-5 space-y-6">
                  {/* Interactive Retinal Viewer */}
                  <div className="rounded-3xl bg-[#0a0a0d] border border-white/[0.08] p-4 sm:p-6">
                    <MedicalRetinaViewer
                      imageUrl={imageUrl}
                      gradCamUrl={screeningResult.gradcam?.overlay_url}
                      grade={screeningResult.classification.dr_grade}
                      className="w-full"
                    />
                  </div>

                  {/* Referral Decision Action */}
                  <div className="rounded-3xl bg-[#0a0a0d] border border-white/[0.08] p-6">
                    {screeningResult.classification.dr_grade === 0 ? (
                      <div className="space-y-4">
                        <div className="p-4 rounded-2xl bg-emerald-500/10 border border-emerald-500/20 text-xs text-emerald-300">
                          <p className="font-bold mb-1">No Referral Required</p>
                          <p className="text-neutral-400">
                            Patient presents no diabetic retinopathy lesions. Routine 12-month follow-up screening recommended.
                          </p>
                        </div>
                        <Link
                          to={`/report/${activeCaseId}`}
                          className="block w-full py-3.5 rounded-2xl bg-white hover:bg-neutral-200 text-black font-bold text-xs text-center transition-all shadow-lg"
                        >
                          View & Print Screening Report →
                        </Link>
                      </div>
                    ) : (
                      <div className="space-y-4">
                        <div className="p-4 rounded-2xl bg-amber-500/10 border border-amber-500/20 text-xs text-amber-300">
                          <p className="font-bold mb-1">Clinical Referral Recommended</p>
                          <p className="text-neutral-400">
                            Diabetic retinopathy detected (Level {screeningResult.classification.dr_grade}). Proceed to select a verified eye care facility.
                          </p>
                        </div>
                        <button
                          onClick={handleProceedToReferral}
                          className="w-full py-3.5 rounded-2xl bg-teal-500 hover:bg-teal-400 text-black font-bold text-xs transition-all shadow-lg"
                        >
                          Proceed to Hospital Referral (Step 06) →
                        </button>
                      </div>
                    )}
                  </div>
                </div>
              </div>
            ) : null}
          </div>
        )}

        {/* ========================================================================= */}
        {/* STEP 06: Specialist Referral Routing */}
        {/* ========================================================================= */}
        {currentStep === 6 && (
          <div className="max-w-3xl mx-auto rounded-3xl bg-[#0a0a0d] border border-white/[0.08] p-6 sm:p-10 space-y-6">
            {!referralSuccess ? (
              <>
                <div>
                  <h2 className="text-lg font-bold font-['Syne'] text-white mb-1">Select Verified Referral Hospital</h2>
                  <p className="text-xs text-neutral-400">
                    Routing Case <span className="text-white font-mono">{activeCaseId}</span> from {selectedDistrict}, {selectedState}.
                  </p>
                </div>

                {/* Hospital Selection List */}
                <div className="space-y-3">
                  {hospitals.length === 0 ? (
                    <div className="p-8 rounded-2xl bg-black/40 border border-white/10 text-center">
                      <div className="w-10 h-10 rounded-full bg-white/5 border border-white/10 flex items-center justify-center mx-auto mb-3 text-neutral-400">
                        🏥
                      </div>
                      <p className="text-xs font-semibold text-neutral-300">
                        No verified referral facilities available for this location.
                      </p>
                      <p className="text-[11px] text-neutral-500 mt-1 font-mono">
                        Authoritative healthcare facility registry integration required for this district.
                      </p>
                    </div>
                  ) : (
                    hospitals.map((hosp) => (
                      <div
                        key={hosp.id}
                        onClick={() => setSelectedHospital(hosp)}
                        className={`p-4 rounded-2xl border cursor-pointer transition-all ${
                          selectedHospital?.id === hosp.id
                            ? 'bg-teal-500/10 border-teal-500/40 ring-1 ring-teal-500'
                            : 'bg-black/30 border-white/5 hover:border-white/20'
                        }`}
                      >
                        <div className="flex items-center justify-between mb-1">
                          <h3 className="text-xs font-bold text-white">{hosp.name}</h3>
                          <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
                            ✓ Verified
                          </span>
                        </div>
                        <p className="text-[11px] text-neutral-400 mb-2">{hosp.specialization} · {hosp.bedAvailability}</p>
                        <div className="flex items-center gap-4 text-[10px] font-mono text-neutral-500">
                          <span>📞 {hosp.contactNumber}</span>
                          <span>📍 {hosp.district}</span>
                        </div>
                      </div>
                    ))
                  )}
                </div>

                {/* Referral Notes */}
                <div>
                  <label className="text-[11px] font-mono text-neutral-400 uppercase block mb-1.5">
                    Referral Notes for Ophthalmologist
                  </label>
                  <textarea
                    rows={2}
                    value={referralNotes}
                    onChange={(e) => setReferralNotes(e.target.value)}
                    className="w-full bg-[#111116] border border-white/10 rounded-xl p-3 text-xs text-white placeholder-neutral-500 focus:outline-none focus:border-teal-500"
                  />
                </div>

                <div className="pt-4 flex items-center justify-between">
                  <button
                    type="button"
                    onClick={() => setCurrentStep(5)}
                    className="px-4 py-2 rounded-xl bg-white/5 hover:bg-white/10 text-neutral-400 hover:text-white text-xs"
                  >
                    ← Back to Result
                  </button>
                  <button
                    type="button"
                    disabled={referralSubmitting || !selectedHospital}
                    onClick={handleConfirmReferral}
                    className="px-6 py-3 rounded-2xl bg-teal-500 hover:bg-teal-400 text-black font-bold text-xs transition-all shadow-lg disabled:opacity-50"
                  >
                    {referralSubmitting ? 'Sending Referral...' : 'Send Case to Doctor Queue →'}
                  </button>
                </div>
              </>
            ) : (
              /* Success Confirmation Banner */
              <div className="text-center py-8 space-y-6">
                <div className="w-16 h-16 rounded-full bg-emerald-500/10 border border-emerald-500/30 text-emerald-400 flex items-center justify-center mx-auto text-2xl font-bold">
                  ✓
                </div>
                <div>
                  <span className="text-[11px] font-mono px-3 py-1 rounded-full bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
                    REFERRAL DISPATCHED
                  </span>
                  <h2 className="text-2xl font-bold font-['Syne'] text-white mt-3 mb-2">
                    Case Successfully Referred
                  </h2>
                  <p className="text-xs text-neutral-400 max-w-md mx-auto leading-relaxed">
                    Case <span className="text-white font-mono">{activeCaseId}</span> has been routed to{' '}
                    <strong className="text-white">{selectedHospital?.name}</strong>. It is now active in the Vitreoretinal Specialist Review Queue.
                  </p>
                </div>

                <div className="flex flex-wrap items-center justify-center gap-3 pt-4">
                  <Link
                    to={`/report/${activeCaseId}`}
                    className="px-6 py-3 rounded-2xl bg-white hover:bg-neutral-200 text-black font-bold text-xs transition-all"
                  >
                    View Official Report
                  </Link>
                  <Link
                    to="/worker/dashboard"
                    className="px-6 py-3 rounded-2xl bg-white/5 hover:bg-white/10 text-neutral-300 text-xs font-medium border border-white/10 transition-colors"
                  >
                    Return to Dashboard
                  </Link>
                </div>
              </div>
            )}
          </div>
        )}
      </main>
    </div>
  );
};

export default NewScreeningPage;
