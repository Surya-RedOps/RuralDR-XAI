import React, { useState, useRef, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { Container } from '@/components/layout/Section';
import { Button } from '@/components/ui/Button';
import { GlassCard } from '@/components/ui/GlassCard';
import { RetinaBackground } from '@/components/ui/RetinaBackground';
import { useProcessing } from '@/hooks/useProcessing';

const FORMATS = [
  { ext: 'JPEG', note: '.jpg, .jpeg' },
  { ext: 'PNG',  note: '.png' },
  { ext: 'TIFF', note: '.tiff, .tif' },
  { ext: 'BMP',  note: '.bmp' },
];

const REQUIREMENTS = [
  'Color fundus photograph (RGB)',
  'Minimum resolution: 512×512 pixels',
  'Maximum file size: 50 MB',
  'Clear optic disc and macula visible',
  'Minimal artifacts or blur',
];

const PIPELINE_STEPS = [
  'Quality Gate',
  'Classification',
  'Grad-CAM',
  'Segmentation',
  'Report',
];

const UploadPage: React.FC = () => {
  const navigate = useNavigate();
  const { state, uploadImage, processImage, reset } = useProcessing();
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [previewUrl, setPreviewUrl] = useState<string | null>(null);
  const [dragOver, setDragOver] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const applyFile = (file: File) => {
    setSelectedFile(file);
    const reader = new FileReader();
    reader.onload = (e) => setPreviewUrl(e.target?.result as string);
    reader.readAsDataURL(file);
  };

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) applyFile(file);
  };

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setDragOver(false);
    const file = e.dataTransfer.files?.[0];
    if (file) applyFile(file);
  }, []);

  const handleDragOver = (e: React.DragEvent) => { e.preventDefault(); setDragOver(true); };
  const handleDragLeave = () => setDragOver(false);

  const handleProcess = async () => {
    if (!selectedFile) return;
    try {
      const uploadId = await uploadImage(selectedFile);
      const results = await processImage(uploadId, true);
      sessionStorage.setItem('screeningResults', JSON.stringify(results));
      navigate(`/results/${results.case_id}`);
    } catch {
      // error already in state
    }
  };

  const clearFile = () => {
    setSelectedFile(null);
    setPreviewUrl(null);
    if (fileInputRef.current) fileInputRef.current.value = '';
    reset();
  };

  const isProcessing = state.status === 'uploading' || state.status === 'processing';
  const currentStepIdx = PIPELINE_STEPS.findIndex(s =>
    state.currentStep?.toLowerCase().includes(s.toLowerCase())
  );

  return (
    <div className="min-h-screen bg-bg-0">
      {/* Nav */}
      <nav className="fixed top-0 left-0 right-0 z-50 glass" style={{ borderBottom: '1px solid rgba(255,255,255,0.06)' }}>
        <Container>
          <div className="flex items-center justify-between h-14">
            <button
              onClick={() => navigate('/')}
              className="t-label text-text-1 tracking-widest hover:text-text-0 transition-colors"
            >
              RuralDR-XAI
            </button>
          </div>
        </Container>
      </nav>

      {/* Hero area */}
      <div className="relative pt-14 overflow-hidden" style={{ minHeight: '30vh', background: 'var(--bg-1)' }}>
        <RetinaBackground intensity="low" className="opacity-50" />
        <Container className="relative z-10 py-16">
          <p className="t-label text-text-3 mb-3">Step 1 of 2</p>
          <h1 className="t-heading text-text-0 mb-2">Upload Fundus Image</h1>
          <p className="t-body text-text-2 max-w-lg">
            Select a retinal fundus image to begin diabetic retinopathy screening.
          </p>
        </Container>
        <div className="absolute bottom-0 left-0 right-0 h-16 pointer-events-none"
          style={{ background: 'linear-gradient(to bottom, transparent, #000)' }} />
      </div>

      {/* Main content */}
      <div className="relative bg-bg-0 py-12">
        <Container>
          <div className="grid grid-cols-1 lg:grid-cols-5 gap-6">

            {/* Upload zone — 3 cols */}
            <div className="lg:col-span-3">
              <input
                ref={fileInputRef}
                type="file"
                accept="image/*"
                onChange={handleFileSelect}
                className="hidden"
                aria-label="Select fundus image"
              />

              {previewUrl ? (
                <GlassCard className="overflow-hidden">
                  {/* Image preview */}
                  <div className="relative">
                    <img
                      src={previewUrl}
                      alt="Fundus image preview"
                      className="w-full object-cover"
                      style={{ maxHeight: '420px', objectFit: 'cover' }}
                    />
                    {/* Retina frame overlay */}
                    <div className="absolute inset-0 pointer-events-none"
                      style={{
                        background: 'radial-gradient(ellipse 60% 60% at 50% 50%, transparent 40%, rgba(0,0,0,0.5) 100%)',
                        boxShadow: 'inset 0 0 40px rgba(0,0,0,0.6)',
                      }}
                    />
                    {/* Corner brackets */}
                    {['top-3 left-3', 'top-3 right-3', 'bottom-3 left-3', 'bottom-3 right-3'].map((pos, i) => (
                      <div key={i} className={`absolute ${pos} w-5 h-5`}
                        style={{
                          borderTop:    i < 2 ? '1.5px solid rgba(255,255,255,0.4)' : 'none',
                          borderBottom: i >= 2 ? '1.5px solid rgba(255,255,255,0.4)' : 'none',
                          borderLeft:   i % 2 === 0 ? '1.5px solid rgba(255,255,255,0.4)' : 'none',
                          borderRight:  i % 2 === 1 ? '1.5px solid rgba(255,255,255,0.4)' : 'none',
                        }}
                      />
                    ))}
                  </div>
                  <div className="p-4 flex items-center justify-between gap-4">
                    <div>
                      <p className="t-small text-text-1 font-medium truncate max-w-xs">{selectedFile?.name}</p>
                      <p className="t-label text-text-3 mt-0.5">
                        {selectedFile ? (selectedFile.size / 1024 / 1024).toFixed(2) + ' MB' : ''}
                      </p>
                    </div>
                    <Button onClick={clearFile} variant="ghost" size="sm">Change</Button>
                  </div>
                </GlassCard>
              ) : (
                <div
                  onClick={() => fileInputRef.current?.click()}
                  onDrop={handleDrop}
                  onDragOver={handleDragOver}
                  onDragLeave={handleDragLeave}
                  role="button"
                  tabIndex={0}
                  onKeyDown={(e) => e.key === 'Enter' && fileInputRef.current?.click()}
                  aria-label="Upload fundus image"
                  className="card cursor-pointer flex flex-col items-center justify-center text-center"
                  style={{
                    minHeight: '380px',
                    borderStyle: 'dashed',
                    borderColor: dragOver ? 'rgba(255,255,255,0.3)' : 'rgba(255,255,255,0.1)',
                    background: dragOver ? 'rgba(255,255,255,0.04)' : 'rgba(255,255,255,0.02)',
                    transition: 'all 0.2s ease',
                  }}
                >
                  {/* Retina icon */}
                  <div className="relative mb-6">
                    <svg width="64" height="64" viewBox="0 0 64 64" fill="none" className="text-text-3">
                      <circle cx="32" cy="32" r="28" stroke="currentColor" strokeWidth="1" opacity="0.3" />
                      <circle cx="32" cy="32" r="18" stroke="currentColor" strokeWidth="1" opacity="0.5" />
                      <circle cx="32" cy="32" r="8"  stroke="currentColor" strokeWidth="1.5" opacity="0.8" />
                      <circle cx="32" cy="32" r="3"  fill="currentColor" opacity="0.6" />
                      <path d="M32 4 L32 10 M32 54 L32 60 M4 32 L10 32 M54 32 L60 32" stroke="currentColor" strokeWidth="1" strokeLinecap="round" opacity="0.3" />
                    </svg>
                    {dragOver && (
                      <div className="absolute inset-0 flex items-center justify-center">
                        <div className="w-16 h-16 rounded-full border border-white/20 animate-pulse-ring" />
                      </div>
                    )}
                  </div>
                  <p className="t-subheading text-text-1 mb-2">
                    {dragOver ? 'Drop to upload' : 'Upload Fundus Image'}
                  </p>
                  <p className="t-small text-text-3 mb-6">
                    Click to browse or drag and drop your fundus image
                  </p>
                  <Button variant="outline" size="md" onClick={(e) => { e.stopPropagation(); fileInputRef.current?.click(); }}>
                    Select Image
                  </Button>
                </div>
              )}

              {/* Action buttons */}
              {previewUrl && state.status === 'idle' && (
                <div className="mt-4 flex gap-3">
                  <Button onClick={handleProcess} variant="primary" size="lg" className="flex-1">
                    Start Analysis
                  </Button>
                  <Button onClick={clearFile} variant="outline" size="lg">
                    Cancel
                  </Button>
                </div>
              )}
            </div>

            {/* Sidebar — 2 cols */}
            <div className="lg:col-span-2 space-y-4">

              {/* Processing status */}
              {isProcessing && (
                <GlassCard className="p-5">
                  <p className="t-label text-text-3 mb-4">
                    {state.status === 'uploading' ? 'Uploading' : 'Analysing'}
                  </p>

                  {/* Progress bar */}
                  <div className="progress-track mb-4">
                    <div className="progress-fill" style={{ width: `${state.progress}%` }} />
                  </div>
                  <p className="t-small text-text-2 mb-5">{state.progress}% complete</p>

                  {/* Pipeline steps */}
                  <div className="space-y-2">
                    {PIPELINE_STEPS.map((step, i) => {
                      const done    = i < currentStepIdx;
                      const active  = i === currentStepIdx;
                      return (
                        <div key={step} className="flex items-center gap-3">
                          <div
                            className="w-5 h-5 rounded-full flex items-center justify-center flex-shrink-0"
                            style={{
                              background: done ? 'rgba(34,197,94,0.15)' : active ? 'rgba(6,182,212,0.15)' : 'rgba(255,255,255,0.04)',
                              border: `1px solid ${done ? 'rgba(34,197,94,0.4)' : active ? 'rgba(6,182,212,0.4)' : 'rgba(255,255,255,0.08)'}`,
                            }}
                          >
                            {done ? (
                              <svg width="10" height="10" viewBox="0 0 10 10" fill="none">
                                <path d="M2 5 L4 7 L8 3" stroke="#22c55e" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" />
                              </svg>
                            ) : active ? (
                              <div className="w-2 h-2 rounded-full bg-c-processing animate-pulse" />
                            ) : null}
                          </div>
                          <span className={`t-small ${done ? 'text-text-3 line-through' : active ? 'text-text-1' : 'text-text-3'}`}>
                            {step}
                          </span>
                        </div>
                      );
                    })}
                  </div>

                  {state.error && (
                    <div className="mt-4 p-3 rounded-lg" style={{ background: 'rgba(239,68,68,0.08)', border: '1px solid rgba(239,68,68,0.2)' }}>
                      <p className="t-small text-c-error">{state.error}</p>
                    </div>
                  )}
                </GlassCard>
              )}

              {/* Formats */}
              <GlassCard className="p-5">
                <p className="t-label text-text-3 mb-4">Supported Formats</p>
                <div className="grid grid-cols-2 gap-2">
                  {FORMATS.map(({ ext, note }) => (
                    <div key={ext} className="flex items-center gap-2">
                      <svg width="12" height="12" viewBox="0 0 12 12" fill="none">
                        <path d="M2 6 L5 9 L10 3" stroke="#22c55e" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" />
                      </svg>
                      <div>
                        <span className="t-small text-text-1 font-medium">{ext}</span>
                        <span className="t-label text-text-3 ml-1">{note}</span>
                      </div>
                    </div>
                  ))}
                </div>
              </GlassCard>

              {/* Requirements */}
              <GlassCard className="p-5">
                <p className="t-label text-text-3 mb-4">Image Requirements</p>
                <ul className="space-y-2">
                  {REQUIREMENTS.map((req) => (
                    <li key={req} className="flex items-start gap-2">
                      <span className="text-text-3 mt-0.5 flex-shrink-0">·</span>
                      <span className="t-small text-text-2">{req}</span>
                    </li>
                  ))}
                </ul>
              </GlassCard>
            </div>
          </div>
        </Container>
      </div>
    </div>
  );
};

export default UploadPage;
