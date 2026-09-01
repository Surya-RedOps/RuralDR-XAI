import React, { useEffect, useRef, useState } from 'react';
import { Link } from 'react-router-dom';
import { Button } from '@/components/ui/Button';
import { GlassCard } from '@/components/ui/GlassCard';
import { RetinaBackground } from '@/components/ui/RetinaBackground';
import { FundusCanvas } from '@/components/ui/FundusCanvas';
import { useScrollReveal } from '@/hooks/useScrollReveal';

const DR_STAGES = [
  { grade: 0, name: 'No DR',        color: '#22c55e', bg: 'rgba(34,197,94,0.07)',   border: 'rgba(34,197,94,0.18)',   desc: 'No signs of diabetic retinopathy. Regular monitoring recommended.', signs: ['Normal retinal appearance', 'No vascular abnormalities', 'Annual screening advised'] },
  { grade: 1, name: 'Mild NPDR',    color: '#84cc16', bg: 'rgba(132,204,22,0.07)',  border: 'rgba(132,204,22,0.18)',  desc: 'Mild non-proliferative DR. Microaneurysms present in the retina.', signs: ['Microaneurysms detected', 'Minor vascular changes', '6-month follow-up'] },
  { grade: 2, name: 'Moderate NPDR',color: '#f59e0b', bg: 'rgba(245,158,11,0.07)', border: 'rgba(245,158,11,0.18)', desc: 'More than microaneurysms but less than severe NPDR. Specialist review needed.', signs: ['Hemorrhages present', 'Hard exudates visible', 'Specialist referral advised'] },
  { grade: 3, name: 'Severe NPDR',  color: '#f97316', bg: 'rgba(249,115,22,0.07)', border: 'rgba(249,115,22,0.18)', desc: 'Severe NPDR. High risk of progression to proliferative disease.', signs: ['Extensive hemorrhages', 'Venous beading', 'Urgent referral required'] },
  { grade: 4, name: 'PDR',          color: '#ef4444', bg: 'rgba(239,68,68,0.07)',  border: 'rgba(239,68,68,0.18)',  desc: 'Proliferative DR. New vessel growth. Vision-threatening condition.', signs: ['Neovascularization', 'Vitreous hemorrhage risk', 'Immediate treatment needed'] },
];

const FEATURES = [
  { n: '01', title: 'Quality Assessment',  desc: 'Automated fundus image quality evaluation to ensure diagnostic reliability before analysis begins.' },
  { n: '02', title: 'DR Classification',   desc: 'AI-powered diabetic retinopathy grading across 5 severity levels using deep learning.' },
  { n: '03', title: 'Grad-CAM XAI',        desc: 'Gradient-weighted Class Activation Maps reveal exactly where the model focuses its attention.' },
  { n: '04', title: 'Lesion Detection',    desc: 'Automatic segmentation of microaneurysms, hard/soft exudates, and hemorrhages.' },
  { n: '05', title: 'Clinical Report',     desc: 'Structured evidence-based reports with findings ready for ophthalmologist review and action.' },
  { n: '06', title: 'Rural Optimized',     desc: 'Designed for low-bandwidth environments and diverse fundus camera hardware in the field.' },
];

const PIPELINE = [
  { step: 'Upload',         desc: 'Fundus image ingestion & validation' },
  { step: 'Quality Gate',   desc: 'Automated gradability assessment' },
  { step: 'Classification', desc: 'DR severity grading (Grade 0–4)' },
  { step: 'Grad-CAM',       desc: 'Attention heatmap generation' },
  { step: 'Segmentation',   desc: 'Lesion & vessel mask extraction' },
  { step: 'Report',         desc: 'Clinical evidence summary output' },
];

/* ── Counter ── */
const Counter: React.FC<{ to: string; label: string; delay?: number }> = ({ to, label, delay = 0 }) => {
  const ref = useRef<HTMLDivElement>(null);
  const [vis, setVis] = useState(false);
  useEffect(() => {
    const el = ref.current; if (!el) return;
    const obs = new IntersectionObserver(([e]) => { if (e.isIntersecting) { setVis(true); obs.disconnect(); } }, { threshold: 0.4 });
    obs.observe(el);
    return () => obs.disconnect();
  }, []);
  return (
    <div ref={ref} className="text-center py-8 px-6" style={{ opacity: vis ? 1 : 0, transform: vis ? 'none' : 'translateY(14px)', transition: `opacity 0.6s ease ${delay}ms, transform 0.6s ease ${delay}ms` }}>
      <div className="t-display-md text-text-0 mb-2">{to}</div>
      <div className="t-label text-text-3">{label}</div>
    </div>
  );
};

/* ── Nav ── */
const Nav: React.FC = () => {
  const ref = useRef<HTMLElement>(null);
  useEffect(() => {
    const fn = () => {
      if (!ref.current) return;
      const s = window.scrollY > 30;
      ref.current.style.background = s ? 'rgba(0,0,0,0.88)' : 'transparent';
      ref.current.style.borderBottomColor = s ? 'rgba(255,255,255,0.07)' : 'transparent';
    };
    window.addEventListener('scroll', fn, { passive: true });
    return () => window.removeEventListener('scroll', fn);
  }, []);
  return (
    <nav ref={ref} className="fixed top-0 left-0 right-0 z-50" style={{ borderBottom: '1px solid transparent', backdropFilter: 'blur(20px)', WebkitBackdropFilter: 'blur(20px)', transition: 'background 0.4s, border-color 0.4s' }}>
      <div className="w-full px-6 lg:px-14">
        <div className="flex items-center justify-between h-16">
          <div className="flex items-center gap-3">
            <svg width="26" height="26" viewBox="0 0 26 26" fill="none">
              <circle cx="13" cy="13" r="11" stroke="rgba(255,255,255,0.15)" strokeWidth="1"/>
              <circle cx="13" cy="13" r="6"  stroke="rgba(255,255,255,0.25)" strokeWidth="1"/>
              <circle cx="13" cy="13" r="2.5" fill="rgba(255,255,255,0.6)"/>
            </svg>
            <span className="t-label text-text-1 tracking-widest">RuralDR-XAI</span>
          </div>
          <div className="flex items-center gap-6">
            <a href="#about"    className="t-small text-text-3 hover:text-text-1 transition-colors hidden md:block">About</a>
            <a href="#features" className="t-small text-text-3 hover:text-text-1 transition-colors hidden md:block">Features</a>
            <a href="#stages"   className="t-small text-text-3 hover:text-text-1 transition-colors hidden md:block">DR Stages</a>
            <Link to="/upload"><Button size="sm" variant="primary">Start Screening</Button></Link>
          </div>
        </div>
      </div>
    </nav>
  );
};

/* ── Hero ── */
const Hero: React.FC = () => (
  <section className="relative min-h-screen flex items-center overflow-hidden bg-bg-0">
    <RetinaBackground intensity="high" />
    <div className="scan-line" />
    <div className="relative z-10 w-full px-6 lg:px-14 pt-24 pb-20">
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-16 items-center">
        <div>
          <div className="reveal-fade mb-8 flex items-center gap-3 flex-wrap">
            <span className="badge badge-info">AI-Powered Screening</span>
            <span className="t-label text-text-3">v2.0</span>
            <span className="w-px h-3 bg-text-3 opacity-30" />
            <span className="t-label text-text-3 anim-flicker">● LIVE</span>
          </div>
          <h1 className="t-display text-text-0 reveal-blur delay-1" style={{ lineHeight: '0.93', marginBottom: '1.5rem' }}>
            Retinal AI<br />
            <span style={{ background: 'linear-gradient(135deg,#fff 0%,#444 100%)', WebkitBackgroundClip: 'text', WebkitTextFillColor: 'transparent', backgroundClip: 'text' }}>
              for Rural
            </span><br />
            Healthcare
          </h1>
          <p className="t-subheading text-text-2 mb-10 max-w-xl reveal-up delay-2">
            Advanced diabetic retinopathy screening with explainable AI.
            Bringing precision medicine to underserved communities worldwide.
          </p>
          <div className="flex flex-wrap gap-4 reveal-up delay-3">
            <Link to="/upload"><Button size="xl" variant="primary">Start Screening</Button></Link>
            <a href="#about"><Button size="xl" variant="outline">Learn More</Button></a>
          </div>
          <div className="mt-14 grid grid-cols-3 gap-6 reveal-fade delay-4">
            {[{ v: '0–4', l: 'DR Grades' }, { v: 'Grad-CAM', l: 'XAI Method' }, { v: '4 Classes', l: 'Lesion Types' }].map(({ v, l }) => (
              <div key={l} className="border-l pl-4" style={{ borderColor: 'rgba(255,255,255,0.1)' }}>
                <p className="t-subheading text-text-1 font-semibold">{v}</p>
                <p className="t-label text-text-3 mt-1">{l}</p>
              </div>
            ))}
          </div>
        </div>

        {/* Fundus image */}
        <div className="reveal-scale delay-2 flex items-center justify-center">
          <div className="relative w-full max-w-md aspect-square">

            {/* Outer ambient glow */}
            <div className="absolute inset-0 rounded-full anim-breathe pointer-events-none"
              style={{ background: 'radial-gradient(circle, rgba(160,60,10,0.35) 0%, rgba(100,20,5,0.15) 50%, transparent 75%)', transform: 'scale(1.08)' }} />

            {/* Thin rotating ring */}
            <div className="absolute inset-0 rounded-full pointer-events-none"
              style={{ border: '1px solid rgba(200,100,40,0.2)', animation: 'spin-slow 30s linear infinite' }} />
            <div className="absolute rounded-full pointer-events-none"
              style={{ inset: '-8px', border: '1px solid rgba(255,255,255,0.05)', animation: 'spin-slow 50s linear infinite reverse' }} />

            {/* Canvas fundus */}
            <div className="absolute inset-0 rounded-full overflow-hidden"
              style={{ boxShadow: '0 0 60px rgba(140,50,10,0.5), 0 0 120px rgba(100,30,5,0.3), inset 0 0 30px rgba(0,0,0,0.6)' }}>
              <FundusCanvas />
            </div>

            {/* Floating anatomy labels */}
            {[
              { l: 'Optic Disc', t: '8%',  le: '62%', d: 0 },
              { l: 'Fovea',      t: '42%', le: '14%', d: 1 },
              { l: 'Vessels',    t: '72%', le: '52%', d: 2 },
              { l: 'Macula',     t: '26%', le: '30%', d: 3 },
            ].map(({ l, t, le, d }) => (
              <div key={l} className="absolute flex items-center gap-1.5 pointer-events-none"
                style={{ top: t, left: le, animation: `float ${4.5 + d * 0.7}s ease-in-out ${d * 0.5}s infinite`, zIndex: 10 }}>
                <div className="w-1 h-1 rounded-full" style={{ background: 'rgba(255,180,80,0.7)' }} />
                <span className="t-label whitespace-nowrap" style={{ color: 'rgba(255,200,120,0.7)', textShadow: '0 1px 4px rgba(0,0,0,0.8)' }}>{l}</span>
              </div>
            ))}

            {/* LIVE badge */}
            <div className="absolute bottom-6 left-1/2 -translate-x-1/2 pointer-events-none"
              style={{ zIndex: 10 }}>
              <span className="badge badge-info anim-flicker" style={{ backdropFilter: 'blur(8px)', background: 'rgba(6,182,212,0.12)' }}>● Fundus Scan</span>
            </div>
          </div>
        </div>
      </div>
    </div>
    <div className="absolute bottom-0 left-0 right-0 h-40 pointer-events-none" style={{ background: 'linear-gradient(to bottom, transparent, #000)' }} />
  </section>
);

/* ── About ── */
const About: React.FC = () => (
  <section id="about" className="relative py-32 overflow-hidden" style={{ background: 'var(--bg-1)' }}>
    <RetinaBackground intensity="low" className="opacity-25" />
    <div className="relative z-10 w-full px-6 lg:px-14">
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-16 items-start mb-20">
        <div className="sr-left">
          <p className="t-label text-text-3 mb-4">The Problem</p>
          <h2 className="t-display-md text-text-0">Diabetic Retinopathy is the leading cause of preventable blindness</h2>
        </div>
        <div className="sr-right">
          <p className="t-body text-text-2 mb-5">Over 537 million people worldwide live with diabetes. Without timely screening, diabetic retinopathy silently progresses until vision loss becomes irreversible. In rural and underserved regions, access to ophthalmologists is critically limited.</p>
          <p className="t-body text-text-2">RuralDR-XAI bridges this gap by bringing hospital-grade AI screening to any clinic with a fundus camera — delivering explainable, trustworthy results that clinicians can act on immediately.</p>
        </div>
      </div>
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-px rounded-2xl overflow-hidden" style={{ background: 'rgba(255,255,255,0.04)' }}>
        {[{ v: '537M+', l: 'People with diabetes globally' }, { v: '1 in 3', l: 'Diabetics develop retinopathy' }, { v: '90%', l: 'Vision loss is preventable' }, { v: '5 Grades', l: 'DR severity classification' }].map(({ v, l }, i) => (
          <div key={l} className="sr" style={{ background: 'var(--bg-1)', transitionDelay: `${i * 80}ms` }}>
            <Counter to={v} label={l} delay={i * 100} />
          </div>
        ))}
      </div>
    </div>
  </section>
);

/* ── DR Stages ── */
const Stages: React.FC = () => {
  const [active, setActive] = useState(0);
  const s = DR_STAGES[active];
  return (
    <section id="stages" className="relative py-32 bg-bg-0 overflow-hidden">
      <RetinaBackground intensity="low" className="opacity-20" />
      <div className="relative z-10 w-full px-6 lg:px-14">
        <div className="mb-16 sr">
          <p className="t-label text-text-3 mb-3">Disease Progression</p>
          <h2 className="t-heading text-text-0">DR Severity Stages</h2>
        </div>
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-12 items-start">
          {/* Stage selector */}
          <div className="space-y-2 sr-left">
            {DR_STAGES.map((st, i) => (
              <button key={st.grade} onClick={() => setActive(i)}
                className="w-full text-left p-5 rounded-xl transition-all duration-300 flex items-center gap-5"
                style={{ background: active === i ? st.bg : 'rgba(255,255,255,0.02)', border: `1px solid ${active === i ? st.border : 'rgba(255,255,255,0.05)'}`, transform: active === i ? 'translateX(6px)' : 'none' }}>
                <div className="w-10 h-10 rounded-full flex items-center justify-center flex-shrink-0 t-label font-bold"
                  style={{ background: active === i ? `${st.color}22` : 'rgba(255,255,255,0.04)', color: active === i ? st.color : 'var(--text-3)', border: `1px solid ${active === i ? st.border : 'rgba(255,255,255,0.08)'}` }}>
                  {st.grade}
                </div>
                <div className="flex-1">
                  <span className="t-small font-semibold" style={{ color: active === i ? st.color : 'var(--text-2)' }}>{st.name}</span>
                </div>
                {active === i && <div className="w-1.5 h-1.5 rounded-full flex-shrink-0" style={{ background: st.color }} />}
              </button>
            ))}
          </div>

          {/* Stage detail */}
          <div className="sr-right">
            <div className="p-8 rounded-2xl" style={{ background: s.bg, border: `1px solid ${s.border}`, transition: 'all 0.4s ease' }}>
              <div className="flex items-center gap-4 mb-6">
                <div className="w-14 h-14 rounded-full flex items-center justify-center" style={{ background: `${s.color}22`, border: `1px solid ${s.border}` }}>
                  <span className="t-heading font-bold" style={{ color: s.color }}>{s.grade}</span>
                </div>
                <div>
                  <p className="t-label text-text-3 mb-1">Grade {s.grade}</p>
                  <h3 className="t-heading text-text-0">{s.name}</h3>
                </div>
              </div>
              <p className="t-body text-text-2 mb-8">{s.desc}</p>
              <div className="space-y-3">
                {s.signs.map((sign) => (
                  <div key={sign} className="flex items-center gap-3">
                    <div className="w-1.5 h-1.5 rounded-full flex-shrink-0" style={{ background: s.color }} />
                    <span className="t-small text-text-2">{sign}</span>
                  </div>
                ))}
              </div>
              {/* Severity bar */}
              <div className="mt-8">
                <div className="flex justify-between mb-2">
                  <span className="t-label text-text-3">Severity</span>
                  <span className="t-label" style={{ color: s.color }}>{['None', 'Low', 'Moderate', 'High', 'Critical'][s.grade]}</span>
                </div>
                <div className="progress-track" style={{ height: '6px' }}>
                  <div style={{ height: '100%', width: `${(s.grade + 1) * 20}%`, background: s.color, borderRadius: '9999px', transition: 'width 0.5s ease' }} />
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
};

/* ── Features ── */
const Features: React.FC = () => (
  <section id="features" className="relative py-32 overflow-hidden" style={{ background: 'var(--bg-1)' }}>
    <RetinaBackground intensity="low" className="opacity-20" />
    <div className="relative z-10 w-full px-6 lg:px-14">
      <div className="mb-16 sr">
        <p className="t-label text-text-3 mb-3">Capabilities</p>
        <h2 className="t-heading text-text-0">Key Features</h2>
      </div>
      <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
        {FEATURES.map((f, i) => (
          <GlassCard key={f.title} tilt className="p-7 sr" style={{ transitionDelay: `${i * 60}ms` }}>
            <p className="t-label text-text-3 mb-3">{f.n}</p>
            <h3 className="t-small font-semibold text-text-1 mb-3" style={{ fontSize: '1rem' }}>{f.title}</h3>
            <p className="t-small text-text-3" style={{ lineHeight: '1.7' }}>{f.desc}</p>
          </GlassCard>
        ))}
      </div>
    </div>
  </section>
);

/* ── Pipeline ── */
const Pipeline: React.FC = () => (
  <section className="relative py-32 bg-bg-0 overflow-hidden">
    <RetinaBackground intensity="medium" className="opacity-30" />
    <div className="relative z-10 w-full px-6 lg:px-14">
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-16 items-center">
        <div className="sr-left">
          <p className="t-label text-text-3 mb-4">How it works</p>
          <h2 className="t-heading text-text-0 mb-6">Analysis Pipeline</h2>
          <p className="t-body text-text-2 mb-8">Every fundus image passes through a rigorous multi-stage pipeline — from quality validation to explainable AI output — in seconds.</p>
          <Link to="/upload"><Button size="lg" variant="primary">Try it Now</Button></Link>
        </div>
        <div className="sr-right space-y-2">
          {PIPELINE.map((item, i) => (
            <div key={item.step} className="flex items-center gap-5 p-4 rounded-xl sr" style={{ transitionDelay: `${i * 70}ms`, background: 'rgba(255,255,255,0.02)', border: '1px solid rgba(255,255,255,0.05)' }}>
              <div className="w-10 h-10 rounded-full flex items-center justify-center flex-shrink-0 t-label text-text-3" style={{ background: 'rgba(255,255,255,0.04)', border: '1px solid rgba(255,255,255,0.08)' }}>
                {String(i + 1).padStart(2, '0')}
              </div>
              <div className="flex-1 flex items-center justify-between gap-4">
                <span className="t-small font-semibold text-text-1">{item.step}</span>
                <span className="t-small text-text-3 text-right hidden sm:block">{item.desc}</span>
              </div>
              <div className="w-1.5 h-1.5 rounded-full flex-shrink-0" style={{ background: 'rgba(255,255,255,0.12)' }} />
            </div>
          ))}
        </div>
      </div>
    </div>
  </section>
);

/* ── CTA ── */
const CTA: React.FC = () => (
  <section className="relative py-40 overflow-hidden" style={{ background: 'var(--bg-1)' }}>
    <RetinaBackground intensity="high" />
    <div className="scan-line" />
    <div className="relative z-10 w-full px-6 lg:px-14 text-center">
      <div className="sr max-w-3xl mx-auto">
        <p className="t-label text-text-3 mb-6">Get Started</p>
        <h2 className="t-display-md text-text-0 mb-6">Ready to screen for diabetic retinopathy?</h2>
        <p className="t-body text-text-2 mb-12 max-w-xl mx-auto">Upload a fundus image to begin AI-powered diabetic retinopathy screening with full explainability.</p>
        <Link to="/upload"><Button size="xl" variant="primary">Start Screening Now</Button></Link>
      </div>
    </div>
  </section>
);

/* ── Footer ── */
const Footer: React.FC = () => (
  <footer style={{ borderTop: '1px solid rgba(255,255,255,0.05)', background: 'var(--bg-0)' }}>
    <div className="w-full px-6 lg:px-14 py-10 flex flex-col sm:flex-row items-center justify-between gap-4">
      <div className="flex items-center gap-3">
        <svg width="20" height="20" viewBox="0 0 20 20" fill="none">
          <circle cx="10" cy="10" r="8" stroke="rgba(255,255,255,0.15)" strokeWidth="1"/>
          <circle cx="10" cy="10" r="4" stroke="rgba(255,255,255,0.2)" strokeWidth="1"/>
          <circle cx="10" cy="10" r="1.5" fill="rgba(255,255,255,0.5)"/>
        </svg>
        <span className="t-label text-text-3">RuralDR-XAI</span>
      </div>
      <p className="t-small text-text-3 text-center">© 2026 · AI-assisted screening tool · Requires clinical confirmation</p>
      <span className="t-label text-text-3">v2.0</span>
    </div>
  </footer>
);

/* ── Page ── */
const LandingPage: React.FC = () => {
  useScrollReveal();
  return (
    <div className="min-h-screen bg-bg-0">
      <Nav />
      <Hero />
      <About />
      <Stages />
      <Features />
      <Pipeline />
      <CTA />
      <Footer />
    </div>
  );
};

export default LandingPage;
