import React, { useState, useEffect, useRef } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { Container } from '@/components/layout/Section';
import { Button } from '@/components/ui/Button';
import { GlassCard } from '@/components/ui/GlassCard';
import { RetinaBackground } from '@/components/ui/RetinaBackground';
import { useScrollReveal } from '@/hooks/useScrollReveal';
import { ScreeningResult } from '@/types/api';
import { formatPercent, formatTime, formatLesionType, formatCaseId } from '@/utils/format';

/* ─── Severity config ───────────────────────────────────────────────────── */
const SEVERITY_CONFIG: Record<number, { color: string; bg: string; border: string; badge: string }> = {
  0: { color: '#22c55e', bg: 'rgba(34,197,94,0.08)',  border: 'rgba(34,197,94,0.2)',  badge: 'badge-success' },
  1: { color: '#f59e0b', bg: 'rgba(245,158,11,0.08)', border: 'rgba(245,158,11,0.2)', badge: 'badge-warning' },
  2: { color: '#f59e0b', bg: 'rgba(245,158,11,0.08)', border: 'rgba(245,158,11,0.2)', badge: 'badge-warning' },
  3: { color: '#ef4444', bg: 'rgba(239,68,68,0.08)',  border: 'rgba(239,68,68,0.2)',  badge: 'badge-error' },
  4: { color: '#ef4444', bg: 'rgba(239,68,68,0.08)',  border: 'rgba(239,68,68,0.2)',  badge: 'badge-error' },
};

/* ─── Animated number ───────────────────────────────────────────────────── */
const AnimatedValue: React.FC<{ target: number; suffix?: string; decimals?: number }> = ({
  target, suffix = '', decimals = 1,
}) => {
  const [val, setVal] = useState(0);
  const rafRef = useRef<number>(0);

  useEffect(() => {
    const start = performance.now();
    const duration = 900;
    const animate = (now: number) => {
      const t = Math.min((now - start) / duration, 1);
      const ease = 1 - Math.pow(1 - t, 3);
      setVal(target * ease);
      if (t < 1) rafRef.current = requestAnimationFrame(animate);
    };
    rafRef.current = requestAnimationFrame(animate);
    return () => cancelAnimationFrame(rafRef.current);
  }, [target]);

  return <>{val.toFixed(decimals)}{suffix}</>;
};

/* ─── Probability bar ───────────────────────────────────────────────────── */
const ProbBar: React.FC<{ grade: number; prob: number; isActive: boolean }> = ({ grade, prob, isActive }) => {
  const [width, setWidth] = useState(0);
  useEffect(() => {
    const t = setTimeout(() => setWidth(prob * 100), 100 + grade * 80);
    return () => clearTimeout(t);
  }, [prob, grade]);

  const cfg = SEVERITY_CONFIG[grade] ?? SEVERITY_CONFIG[0];
  return (
    <div className="flex items-center gap-3">
      <span className="t-label text-text-3 w-14 flex-shrink-0">Grade {grade}</span>
      <div className="flex-1 progress-track" style={{ height: '4px' }}>
        <div
          style={{
            height: '100%',
            width: `${width}%`,
            background: isActive ? cfg.color : 'rgba(255,255,255,0.15)',
            borderRadius: '9999px',
            transition: 'width 0.7s cubic-bezier(0.16,1,0.3,1)',
          }}
        />
      </div>
      <span className="t-label text-text-2 w-12 text-right flex-shrink-0">
        {(prob * 100).toFixed(1)}%
      </span>
    </div>
  );
};

/* ─── Image viewer ──────────────────────────────────────────────────────── */
const ImageViewer: React.FC<{ src: string; label: string }> = ({ src, label }) => {
  const [zoomed, setZoomed] = useState(false);
  return (
    <div className="relative group cursor-zoom-in" onClick={() => setZoomed(true)}>
      <img
        src={src}
        alt={label}
        className="w-full rounded-lg object-cover"
        style={{ maxHeight: '280px', objectFit: 'cover' }}
      />
      <div className="absolute inset-0 rounded-lg opacity-0 group-hover:opacity-100 transition-opacity flex items-center justify-center"
        style={{ background: 'rgba(0,0,0,0.4)' }}>
        <span className="t-label text-white">Expand</span>
      </div>
      <p className="t-label text-text-3 mt-2 text-center">{label}</p>

      {/* Lightbox */}
      {zoomed && (
        <div
          className="fixed inset-0 z-50 flex items-center justify-center bg-black/90 backdrop-blur-sm"
          onClick={() => setZoomed(false)}
        >
          <img src={src} alt={label} className="max-w-4xl max-h-screen w-full object-contain rounded-xl p-4" />
          <button
            className="absolute top-4 right-4 text-white/60 hover:text-white t-label"
            onClick={() => setZoomed(false)}
            aria-label="Close"
          >
            ✕ Close
          </button>
        </div>
      )}
    </div>
  );
};

/* ─── Main page ─────────────────────────────────────────────────────────── */
const ResultsPage: React.FC = () => {
  useParams();
  const navigate = useNavigate();
  const [results, setResults] = useState<ScreeningResult | null>(null);
  const [activeLayer, setActiveLayer] = useState<string | null>(null);
  useScrollReveal();

  useEffect(() => {
    const stored = sessionStorage.getItem('screeningResults');
    if (stored) setResults(JSON.parse(stored));
  }, []);

  /* ── Empty state ── */
  if (!results) {
    return (
      <div className="min-h-screen bg-bg-0 flex items-center justify-center">
        <RetinaBackground intensity="low" />
        <Container className="relative z-10 text-center">
          <div className="max-w-sm mx-auto">
            <svg width="48" height="48" viewBox="0 0 48 48" fill="none" className="mx-auto mb-6 text-text-3">
              <circle cx="24" cy="24" r="20" stroke="currentColor" strokeWidth="1.5" />
              <path d="M24 16 L24 26 M24 32 L24 33" stroke="currentColor" strokeWidth="2" strokeLinecap="round" />
            </svg>
            <h1 className="t-heading text-text-0 mb-3">Results Not Found</h1>
            <p className="t-body text-text-2 mb-8">No screening result available. Start a screening to see analysis here.</p>
            <Button onClick={() => navigate('/upload')} variant="primary">Back to Upload</Button>
          </div>
        </Container>
      </div>
    );
  }

  const grade = results.classification.dr_grade;
  const cfg   = SEVERITY_CONFIG[grade] ?? SEVERITY_CONFIG[0];

  /* ── Lesion layers for the layer panel ── */
  const layers = results.segmentation?.lesions ?? [];
  const detectedLayers = layers.filter(l => l.detected);
  const currentLayerData = layers.find(l => l.type === activeLayer);

  return (
    <div className="min-h-screen bg-bg-0">
      {/* Nav */}
      <nav className="fixed top-0 left-0 right-0 z-50 glass" style={{ borderBottom: '1px solid rgba(255,255,255,0.06)' }}>
        <Container>
          <div className="flex items-center justify-between h-14">
            <button onClick={() => navigate('/')} className="t-label text-text-1 tracking-widest hover:text-text-0 transition-colors">
              RuralDR-XAI
            </button>
            <Button onClick={() => navigate('/upload')} variant="outline" size="sm">New Analysis</Button>
          </div>
        </Container>
      </nav>

      {/* Hero — grade display */}
      <div className="relative pt-14 overflow-hidden" style={{ background: 'var(--bg-1)' }}>
        <RetinaBackground intensity="medium" className="opacity-60" />
        <Container className="relative z-10 py-16">
          <div className="flex flex-col md:flex-row md:items-end gap-8">
            {/* Grade */}
            <div
              className="inline-flex flex-col items-center justify-center w-36 h-36 rounded-full flex-shrink-0"
              style={{ background: cfg.bg, border: `2px solid ${cfg.border}`, boxShadow: `0 0 40px ${cfg.bg}` }}
            >
              <span className="t-label text-text-3 mb-1">Grade</span>
              <span className="text-5xl font-bold" style={{ color: cfg.color }}>
                <AnimatedValue target={grade} decimals={0} />
              </span>
            </div>

            <div>
              <p className="t-label text-text-3 mb-2">Case {formatCaseId(results.case_id)}</p>
              <h1 className="t-heading text-text-0 mb-2">{results.classification.severity}</h1>
              <div className="flex flex-wrap items-center gap-3">
                <span className={`badge ${cfg.badge}`}>
                  {results.classification.is_referable ? '⚠ Referral Recommended' : 'No Referral Required'}
                </span>
                <span className="badge badge-neutral">
                  Confidence: <AnimatedValue target={results.classification.confidence * 100} suffix="%" />
                </span>
                <span className={`badge ${results.quality.status === 'GRADEABLE' ? 'badge-success' : results.quality.status === 'BORDERLINE' ? 'badge-warning' : 'badge-error'}`}>
                  {results.quality.status}
                </span>
              </div>
              {results.classification.is_referable && (
                <p className="t-small mt-3" style={{ color: cfg.color }}>
                  This result requires clinical confirmation by a qualified ophthalmologist.
                </p>
              )}
            </div>
          </div>
        </Container>
        <div className="absolute bottom-0 left-0 right-0 h-16 pointer-events-none"
          style={{ background: 'linear-gradient(to bottom, transparent, #000)' }} />
      </div>

      {/* Body */}
      <div className="bg-bg-0 py-12">
        <Container>
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">

            {/* Left column */}
            <div className="lg:col-span-2 space-y-6">

              {/* Grade distribution */}
              <GlassCard className="p-6 sr">
                <p className="t-label text-text-3 mb-5">Severity Grade Distribution</p>
                <div className="space-y-3">
                  {results.classification.class_probabilities.map((prob, g) => (
                    <ProbBar key={g} grade={g} prob={prob} isActive={g === grade} />
                  ))}
                </div>
              </GlassCard>

              {/* Grad-CAM */}
              {results.gradcam && (
                <GlassCard className="p-6 sr">
                  <div className="flex items-center justify-between mb-5">
                    <p className="t-label text-text-3">Model Attention — Grad-CAM</p>
                    <span className="badge badge-info">
                      {results.gradcam.target_class_name}
                    </span>
                  </div>

                  <div className="grid grid-cols-2 gap-4 mb-5 text-center">
                    {[
                      { label: 'Activation Coverage', value: formatPercent(results.gradcam.activation_coverage) },
                      { label: 'Peak Intensity',       value: results.gradcam.peak_intensity.toFixed(4) },
                    ].map(({ label, value }) => (
                      <div key={label} className="p-3 rounded-lg" style={{ background: 'rgba(255,255,255,0.03)', border: '1px solid rgba(255,255,255,0.06)' }}>
                        <p className="t-label text-text-3 mb-1">{label}</p>
                        <p className="t-subheading text-text-1">{value}</p>
                      </div>
                    ))}
                  </div>

                  {results.gradcam.quality_flags.length > 0 && (
                    <div className="mb-4 flex flex-wrap gap-2">
                      {results.gradcam.quality_flags.map(flag => (
                        <span key={flag} className="badge badge-warning">{flag}</span>
                      ))}
                    </div>
                  )}

                  {results.gradcam.overlay_url && (
                    <ImageViewer src={results.gradcam.overlay_url} label="Grad-CAM Overlay" />
                  )}
                </GlassCard>
              )}

              {/* Lesion workspace */}
              {layers.length > 0 && (
                <GlassCard className="p-6 sr">
                  <p className="t-label text-text-3 mb-5">Retinal Feature Analysis</p>

                  {/* Layer selector */}
                  <div className="flex flex-wrap gap-2 mb-5">
                    {layers.map(l => (
                      <button
                        key={l.type}
                        onClick={() => setActiveLayer(activeLayer === l.type ? null : l.type)}
                        className={`badge cursor-pointer transition-all ${l.detected ? (activeLayer === l.type ? 'badge-warning' : 'badge-neutral') : 'badge-neutral opacity-40'}`}
                        style={{ pointerEvents: l.detected ? 'auto' : 'none' }}
                      >
                        {l.detected && <span className="w-1.5 h-1.5 rounded-full bg-current" />}
                        {formatLesionType(l.type)}
                      </button>
                    ))}
                  </div>

                  {/* Active layer detail */}
                  {currentLayerData && currentLayerData.detected && (
                    <div className="mb-5 p-4 rounded-xl" style={{ background: 'rgba(255,255,255,0.03)', border: '1px solid rgba(255,255,255,0.08)' }}>
                      <div className="grid grid-cols-3 gap-4 text-center mb-4">
                        {[
                          { label: 'Regions',    value: String(currentLayerData.num_regions) },
                          { label: 'Area',       value: currentLayerData.area_pct.toFixed(2) + '%' },
                          { label: 'Confidence', value: formatPercent(currentLayerData.confidence) },
                        ].map(({ label, value }) => (
                          <div key={label}>
                            <p className="t-label text-text-3 mb-1">{label}</p>
                            <p className="t-small font-semibold text-text-1">{value}</p>
                          </div>
                        ))}
                      </div>
                      {currentLayerData.mask_url && (
                        <ImageViewer src={currentLayerData.mask_url} label={`${formatLesionType(currentLayerData.type)} Mask`} />
                      )}
                    </div>
                  )}

                  {/* All lesion summary */}
                  <div className="space-y-2">
                    {layers.map(l => (
                      <div key={l.type} className="flex items-center justify-between py-2"
                        style={{ borderBottom: '1px solid rgba(255,255,255,0.04)' }}>
                        <span className="t-small text-text-2">{formatLesionType(l.type)}</span>
                        <span className={`t-label ${l.detected ? 'text-c-warning' : 'text-text-3'}`}>
                          {l.detected ? `${l.num_regions} region${l.num_regions !== 1 ? 's' : ''}` : 'Not detected'}
                        </span>
                      </div>
                    ))}
                  </div>
                </GlassCard>
              )}
            </div>

            {/* Right column */}
            <div className="space-y-4">

              {/* Quality */}
              <GlassCard className="p-5 sr">
                <p className="t-label text-text-3 mb-4">Image Quality</p>
                <div className="flex items-center justify-between mb-3">
                  <span className="t-small font-semibold text-text-1">{results.quality.status}</span>
                  <span className="t-small text-text-2">{formatPercent(results.quality.score)}</span>
                </div>
                <div className="progress-track mb-3">
                  <div className="progress-fill" style={{ width: `${results.quality.score * 100}%` }} />
                </div>
                <p className="t-small text-text-3">{results.quality.message}</p>
              </GlassCard>

              {/* Processing times */}
              <GlassCard className="p-5 sr delay-1">
                <p className="t-label text-text-3 mb-4">Processing Times</p>
                <div className="space-y-2">
                  {[
                    { label: 'Quality Gate',    ms: results.processing_times.quality_gate_ms },
                    { label: 'Classification',  ms: results.processing_times.classification_ms },
                    { label: 'Grad-CAM',        ms: results.processing_times.gradcam_ms },
                    { label: 'Segmentation',    ms: results.processing_times.segmentation_ms },
                  ].map(({ label, ms }) => (
                    <div key={label} className="flex items-center justify-between">
                      <span className="t-small text-text-3">{label}</span>
                      <span className="t-mono text-text-2">{formatTime(ms)}</span>
                    </div>
                  ))}
                  <div className="divider my-2" />
                  <div className="flex items-center justify-between">
                    <span className="t-small font-semibold text-text-1">Total</span>
                    <span className="t-mono text-text-1">{formatTime(results.processing_times.total_ms)}</span>
                  </div>
                </div>
              </GlassCard>

              {/* Case info */}
              <GlassCard className="p-5 sr delay-2">
                <p className="t-label text-text-3 mb-4">Case Information</p>
                <div className="space-y-2">
                  <div className="flex items-center justify-between">
                    <span className="t-small text-text-3">Case ID</span>
                    <span className="t-mono text-text-2">{formatCaseId(results.case_id)}</span>
                  </div>
                  {results.segmentation && (
                    <div className="flex items-center justify-between">
                      <span className="t-small text-text-3">Resolution</span>
                      <span className="t-mono text-text-2">{results.segmentation.input_resolution}</span>
                    </div>
                  )}
                  <div className="flex items-center justify-between">
                    <span className="t-small text-text-3">Detected Lesions</span>
                    <span className="t-mono text-text-2">{detectedLayers.length} / {layers.length}</span>
                  </div>
                </div>
              </GlassCard>

              {/* Actions */}
              <div className="space-y-2 sr delay-3">
                <Button onClick={() => navigate('/upload')} variant="primary" size="md" className="w-full">
                  Analyse Another Image
                </Button>
                <Button onClick={() => navigate('/')} variant="outline" size="md" className="w-full">
                  Back to Home
                </Button>
              </div>
            </div>
          </div>
        </Container>
      </div>
    </div>
  );
};

export default ResultsPage;
