import React, { useEffect, useRef, useState } from 'react';
import { Link } from 'react-router-dom';
import { Button } from '@/components/ui/Button';
import { GlassCard } from '@/components/ui/GlassCard';
import { RetinaBackground } from '@/components/ui/RetinaBackground';
import { FundusCanvas } from '@/components/ui/FundusCanvas';
import { useScrollReveal } from '@/hooks/useScrollReveal';

const DR_STAGES = [
  { grade: 0, name: 'No DR',         color: '#22c55e', bg: 'rgba(34,197,94,0.07)',   border: 'rgba(34,197,94,0.18)',   desc: 'No signs of diabetic retinopathy. Regular monitoring recommended.', signs: ['Normal retinal appearance', 'No vascular abnormalities', 'Annual screening advised'] },
  { grade: 1, name: 'Mild NPDR',     color: '#84cc16', bg: 'rgba(132,204,22,0.07)',  border: 'rgba(132,204,22,0.18)',  desc: 'Mild non-proliferative DR. Microaneurysms present in the retina.', signs: ['Microaneurysms detected', 'Minor vascular changes', '6-month follow-up'] },
  { grade: 2, name: 'Moderate NPDR', color: '#f59e0b', bg: 'rgba(245,158,11,0.07)', border: 'rgba(245,158,11,0.18)', desc: 'More than microaneurysms but less than severe NPDR. Specialist review needed.', signs: ['Hemorrhages present', 'Hard exudates visible', 'Specialist referral advised'] },
  { grade: 3, name: 'Severe NPDR',   color: '#f97316', bg: 'rgba(249,115,22,0.07)', border: 'rgba(249,115,22,0.18)', desc: 'Severe NPDR. High risk of progression to proliferative disease.', signs: ['Extensive hemorrhages', 'Venous beading', 'Urgent referral required'] },
  { grade: 4, name: 'PDR',           color: '#ef4444', bg: 'rgba(239,68,68,0.07)',  border: 'rgba(239,68,68,0.18)',  desc: 'Proliferative DR. New vessel growth. Vision-threatening condition.', signs: ['Neovascularization', 'Vitreous hemorrhage risk', 'Immediate treatment needed'] },
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

const STAGE_EXTRA = [
  { action: 'Annual monitoring',   risk: 'Minimal',  patients: 'Routine diabetic care' },
  { action: '6-month follow-up',   risk: 'Low',      patients: 'Close observation needed' },
  { action: 'Specialist referral', risk: 'Moderate', patients: 'Ophthalmologist review' },
  { action: 'Urgent referral',     risk: 'High',     patients: 'Immediate specialist care' },
  { action: 'Immediate treatment', risk: 'Critical', patients: 'Laser / surgical intervention' },
];

/* ── StageIcon ── */
const StageIcon: React.FC<{ grade: number; color: string; size?: number }> = ({ grade, color, size = 22 }) => {
  const icons = [
    <svg key={0} width={size} height={size} viewBox="0 0 24 24" fill="none" stroke={color} strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
      <ellipse cx="12" cy="12" rx="10" ry="6" /><circle cx="12" cy="12" r="2.5" fill={color} stroke="none" /><circle cx="12" cy="12" r="1" fill="#000" stroke="none" />
    </svg>,
    <svg key={1} width={size} height={size} viewBox="0 0 24 24" fill="none" stroke={color} strokeWidth="1.5" strokeLinecap="round">
      <circle cx="10" cy="10" r="6" /><line x1="14.5" y1="14.5" x2="20" y2="20" /><line x1="7" y1="10" x2="13" y2="10" strokeWidth="1" /><line x1="10" y1="7" x2="10" y2="13" strokeWidth="1" />
    </svg>,
    <svg key={2} width={size} height={size} viewBox="0 0 24 24" fill="none" stroke={color} strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
      <path d="M12 3L22 20H2L12 3Z" /><line x1="12" y1="10" x2="12" y2="14" /><circle cx="12" cy="17" r="0.8" fill={color} stroke="none" />
    </svg>,
    <svg key={3} width={size} height={size} viewBox="0 0 24 24" fill="none" stroke={color} strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
      <polyline points="2,12 6,12 8,6 10,18 13,9 15,14 17,12 22,12" />
    </svg>,
    <svg key={4} width={size} height={size} viewBox="0 0 24 24" fill="none" stroke={color} strokeWidth="1.5" strokeLinecap="round">
      <rect x="9" y="3" width="6" height="18" rx="1" /><rect x="3" y="9" width="18" height="6" rx="1" />
    </svg>,
  ];
  return icons[grade];
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
  const scrollTo = (id: string) => document.getElementById(id)?.scrollIntoView({ behavior: 'smooth' });
  return (
    <nav ref={ref} className="fixed top-0 left-0 right-0 z-50" style={{ borderBottom: '1px solid transparent', backdropFilter: 'blur(20px)', WebkitBackdropFilter: 'blur(20px)', transition: 'background 0.4s, border-color 0.4s' }}>
      <div className="w-full px-6 lg:px-14">
        <div className="flex items-center justify-between h-16">
          <button onClick={() => window.scrollTo({ top: 0, behavior: 'smooth' })} className="flex items-center gap-3">
            <svg width="26" height="26" viewBox="0 0 26 26" fill="none">
              <circle cx="13" cy="13" r="11" stroke="rgba(255,255,255,0.15)" strokeWidth="1"/>
              <circle cx="13" cy="13" r="6"  stroke="rgba(255,255,255,0.25)" strokeWidth="1"/>
              <circle cx="13" cy="13" r="2.5" fill="rgba(255,255,255,0.6)"/>
            </svg>
            <span className="t-label text-text-1 tracking-widest">RuralDR-XAI</span>
          </button>
          <div className="flex items-center gap-6">
            <button onClick={() => scrollTo('about')}    className="t-small text-text-3 hover:text-text-1 transition-colors hidden md:block">About</button>
            <button onClick={() => scrollTo('features')} className="t-small text-text-3 hover:text-text-1 transition-colors hidden md:block">Features</button>
            <button onClick={() => scrollTo('stages')}   className="t-small text-text-3 hover:text-text-1 transition-colors hidden md:block">DR Stages</button>
            <Link to="/select-role"><Button size="sm" variant="primary">Start Screening</Button></Link>
          </div>
        </div>
      </div>
    </nav>
  );
};

/* ── Hero ── */
const Hero: React.FC = () => {
  const [mouse, setMouse] = useState({ x: 0, y: 0, hovered: false });
  const handleMouseMove = (e: React.MouseEvent<HTMLDivElement>) => {
    const rect = e.currentTarget.getBoundingClientRect();
    setMouse({ x: ((e.clientX - rect.left) / rect.width - 0.5) * 2, y: ((e.clientY - rect.top) / rect.height - 0.5) * 2, hovered: true });
  };
  const tiltX = mouse.hovered ? mouse.y * -10 : 0;
  const tiltY = mouse.hovered ? mouse.x *  10 : 0;
  return (
    <section className="landing-section flex items-center" style={{ minHeight: '100vh' }}
      onMouseMove={handleMouseMove} onMouseLeave={() => setMouse(m => ({ ...m, hovered: false }))}>
      <div className="relative w-full px-6 lg:px-14 pt-20 pb-16 z-10">
        <div className="w-full grid grid-cols-1 lg:grid-cols-2 gap-12 lg:gap-20 items-center">
          <div>
            <div className="reveal-fade mb-7 flex items-center gap-3 flex-wrap">
              <span className="badge badge-info">AI-Powered Screening</span>
              <span className="t-label text-text-3 anim-flicker">● LIVE</span>
            </div>
            <h1 className="reveal-blur delay-1 text-text-0" style={{ fontFamily: "'Syne', sans-serif", fontSize: 'clamp(2.8rem, 5.5vw, 5.5rem)', fontWeight: 800, letterSpacing: '-0.04em', lineHeight: 1.0, marginBottom: '1.5rem' }}>
              Retinal AI<br />
              <span style={{ background: 'linear-gradient(135deg,#fff 20%,#666 100%)', WebkitBackgroundClip: 'text', WebkitTextFillColor: 'transparent', backgroundClip: 'text' }}>for Rural</span><br />
              Healthcare
            </h1>
            <p className="reveal-up delay-2 text-text-2" style={{ fontSize: 'clamp(1rem,1.6vw,1.15rem)', lineHeight: 1.75, maxWidth: '440px', marginBottom: '2.5rem' }}>
              Advanced diabetic retinopathy screening with explainable AI. Bringing precision medicine to underserved communities worldwide.
            </p>
            <div className="reveal-up delay-3 flex flex-wrap gap-4 mb-14">
              <Link to="/select-role"><Button size="xl" variant="primary">Start Screening</Button></Link>
              <button onClick={() => document.getElementById('about')?.scrollIntoView({ behavior: 'smooth' })}><Button size="xl" variant="outline">Learn More</Button></button>
            </div>
            <div className="reveal-fade delay-4 flex flex-wrap gap-8">
              {[{ v: '0–4', l: 'DR Grades' }, { v: 'Grad-CAM', l: 'XAI Method' }, { v: '4 Classes', l: 'Lesion Types' }].map(({ v, l }) => (
                <div key={l} className="border-l pl-4" style={{ borderColor: 'rgba(255,255,255,0.12)' }}>
                  <p style={{ fontFamily: "'Syne',sans-serif", fontSize: '1.25rem', fontWeight: 700, color: '#fff', marginBottom: '2px' }}>{v}</p>
                  <p className="t-label text-text-3">{l}</p>
                </div>
              ))}
            </div>
          </div>
          <div className="reveal-scale delay-2 flex items-center justify-center">
            <div className="relative" style={{ width: 'min(90%, 520px)', aspectRatio: '1', cursor: 'crosshair' }}>
              <div style={{ width: '100%', height: '100%', transform: `perspective(900px) rotateX(${tiltX}deg) rotateY(${tiltY}deg)`, transition: mouse.hovered ? 'transform 0.08s ease' : 'transform 0.6s ease', transformStyle: 'preserve-3d' }}>
                <div className="absolute rounded-full anim-breathe pointer-events-none" style={{ inset: '-20%', background: 'radial-gradient(circle, rgba(160,55,8,0.35) 0%, rgba(80,20,3,0.12) 55%, transparent 75%)', zIndex: 0 }} />
                <div className="absolute rounded-full pointer-events-none" style={{ inset: '-5%', border: '1px solid rgba(200,100,40,0.18)', animation: 'spin-slow 32s linear infinite', zIndex: 1 }} />
                <div className="absolute rounded-full pointer-events-none" style={{ inset: '-11%', border: '1px solid rgba(255,255,255,0.05)', animation: 'spin-slow 52s linear infinite reverse', zIndex: 1 }} />
                <svg className="absolute pointer-events-none" style={{ inset: '-5%', width: '110%', height: '110%', zIndex: 2, animation: 'spin-slow 32s linear infinite' }} viewBox="0 0 100 100">
                  {Array.from({ length: 32 }).map((_, i) => {
                    const a = (i / 32) * Math.PI * 2; const r1 = 49, r2 = i % 8 === 0 ? 44 : 47;
                    return <line key={i} x1={50 + Math.cos(a) * r1} y1={50 + Math.sin(a) * r1} x2={50 + Math.cos(a) * r2} y2={50 + Math.sin(a) * r2} stroke="rgba(200,120,40,0.22)" strokeWidth="0.5" />;
                  })}
                </svg>
                <div className="absolute inset-0 rounded-full overflow-hidden" style={{ zIndex: 3, boxShadow: mouse.hovered ? '0 0 100px rgba(180,70,10,0.7),0 0 200px rgba(120,40,5,0.35)' : '0 0 70px rgba(150,55,8,0.5),0 0 140px rgba(100,30,5,0.25)', transition: 'box-shadow 0.4s ease' }}>
                  <FundusCanvas mouseX={mouse.x} mouseY={mouse.y} hovered={mouse.hovered} />
                </div>
                {[{ l: 'Optic Disc', top: '5%', left: '66%' }, { l: 'Fovea', top: '42%', left: '-12%' }, { l: 'Macula', top: '20%', left: '16%' }, { l: 'Vessels', top: '76%', left: '56%' }].map(({ l, top, left }, i) => (
                  <div key={l} className="absolute flex items-center gap-1.5 pointer-events-none" style={{ top, left, animation: `float ${4.8 + i * 0.6}s ease-in-out ${i * 0.45}s infinite`, zIndex: 5 }}>
                    <div className="w-1.5 h-1.5 rounded-full" style={{ background: 'rgba(255,180,80,0.7)', boxShadow: '0 0 5px rgba(255,160,60,0.7)' }} />
                    <span className="t-label whitespace-nowrap" style={{ color: 'rgba(255,205,130,0.8)', textShadow: '0 1px 6px rgba(0,0,0,0.95)' }}>{l}</span>
                  </div>
                ))}
                <div className="absolute left-1/2 -translate-x-1/2 pointer-events-none" style={{ bottom: '-9%', zIndex: 5 }}>
                  <span className="badge badge-info anim-flicker" style={{ backdropFilter: 'blur(10px)', background: 'rgba(6,182,212,0.1)', border: '1px solid rgba(6,182,212,0.25)' }}>● Fundus Scan Active</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
};

/* ── About ── */
const About: React.FC = () => (
  <section id="about" className="landing-section flex items-center">
    <div className="relative z-10 w-full px-6 lg:px-14 py-32">
      <div className="max-w-6xl mx-auto">
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-16 items-start mb-20">
          <div className="sr-zoom">
            <p className="t-label text-text-3 mb-4">The Problem</p>
            <h2 className="t-display-md text-text-0">Diabetic Retinopathy is the leading cause of preventable blindness</h2>
          </div>
          <div className="sr-zoom" style={{ transitionDelay: '120ms' }}>
            <p className="t-body text-text-2 mb-5">Over 537 million people worldwide live with diabetes. Without timely screening, diabetic retinopathy silently progresses until vision loss becomes irreversible. In rural and underserved regions, access to ophthalmologists is critically limited.</p>
            <p className="t-body text-text-2">RuralDR-XAI bridges this gap by bringing hospital-grade AI screening to any clinic with a fundus camera — delivering explainable, trustworthy results that clinicians can act on immediately.</p>
          </div>
        </div>
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-px rounded-2xl overflow-hidden" style={{ background: 'rgba(255,255,255,0.04)' }}>
          {[{ v: '537M+', l: 'People with diabetes globally' }, { v: '1 in 3', l: 'Diabetics develop retinopathy' }, { v: '90%', l: 'Vision loss is preventable' }, { v: '5 Grades', l: 'DR severity classification' }].map(({ v, l }, i) => (
            <div key={l} className="sr-zoom" style={{ background: 'rgba(0,0,0,0.4)', transitionDelay: `${i * 90}ms`, padding: '2.5rem 1.5rem', textAlign: 'center' }}>
              <div className="t-display-md text-text-0 mb-2">{v}</div>
              <div className="t-label text-text-3">{l}</div>
            </div>
          ))}
        </div>
        <div className="mt-12 grid grid-cols-1 md:grid-cols-3 gap-6">
          {[{ icon: '🌍', title: 'Global Reach', desc: 'Deployable in low-resource settings across Africa, Asia, and Latin America.' }, { icon: '🔬', title: 'Clinical Grade', desc: 'Validated AI models trained on diverse, multi-ethnic fundus datasets.' }, { icon: '⚡', title: 'Real-time Results', desc: 'Full analysis pipeline completes in seconds, not hours.' }].map(({ icon, title, desc }, i) => (
            <div key={title} className="sr-zoom rounded-xl p-6" style={{ background: 'rgba(255,255,255,0.03)', border: '1px solid rgba(255,255,255,0.07)', transitionDelay: `${i * 80}ms` }}>
              <div style={{ fontSize: '2rem', marginBottom: '0.75rem' }}>{icon}</div>
              <h3 className="t-small font-semibold text-text-1 mb-2">{title}</h3>
              <p className="t-small text-text-3" style={{ lineHeight: 1.7 }}>{desc}</p>
            </div>
          ))}
        </div>
      </div>
    </div>
  </section>
);

/* ── Stages ── */
const Stages: React.FC = () => {
  const [active, setActive] = useState(0);
  const lightRef = useRef<HTMLDivElement>(null);
  const s  = DR_STAGES[active];
  const ex = STAGE_EXTRA[active];
  return (
    <section id="stages" className="landing-section flex items-center"
      onMouseMove={(e) => {
        if (!lightRef.current) return;
        const rect = e.currentTarget.getBoundingClientRect();
        const px = ((e.clientX - rect.left) / rect.width  * 100).toFixed(1);
        const py = ((e.clientY - rect.top)  / rect.height * 100).toFixed(1);
        lightRef.current.style.background = `radial-gradient(ellipse 65% 50% at ${px}% ${py}%, rgba(160,55,8,0.18) 0%, transparent 60%)`;
      }}>
      <div ref={lightRef} className="absolute inset-0 pointer-events-none" style={{ zIndex: 0, transition: 'background 0.15s ease' }} />
      <div className="relative z-10 w-full px-6 lg:px-14 py-32">
        <div className="max-w-6xl mx-auto">
          <div className="mb-3 sr-zoom"><span className="badge badge-neutral">Disease Progression</span></div>
          <h2 className="t-heading text-text-0 mb-6 sr-zoom" style={{ transitionDelay: '60ms' }}>DR Severity Stages</h2>
          <div className="mb-8 sr-zoom" style={{ transitionDelay: '80ms' }}>
            <div className="flex rounded-xl overflow-hidden" style={{ height: '5px' }}>
              {DR_STAGES.map(st => <button key={st.grade} onClick={() => setActive(st.grade)} className="flex-1 transition-all duration-300" style={{ background: st.color, opacity: active === st.grade ? 1 : 0.22 }} />)}
            </div>
            <div className="flex mt-2">
              {DR_STAGES.map(st => <div key={st.grade} className="flex-1 text-center"><span className="t-label" style={{ color: active === st.grade ? st.color : 'var(--text-3)', transition: 'color 0.3s' }}>{st.name}</span></div>)}
            </div>
          </div>
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-8 items-start">
            <div className="space-y-2 sr-zoom" style={{ transitionDelay: '100ms' }}>
              {DR_STAGES.map(st => (
                <button key={st.grade} onClick={() => setActive(st.grade)} className="w-full text-left p-4 rounded-xl transition-all duration-300 flex items-center gap-4"
                  style={{ background: active === st.grade ? st.bg : 'rgba(255,255,255,0.02)', border: `1px solid ${active === st.grade ? st.border : 'rgba(255,255,255,0.05)'}`, transform: active === st.grade ? 'translateX(6px)' : 'none', boxShadow: active === st.grade ? `0 0 20px ${st.color}18` : 'none' }}>
                  <div className="w-9 h-9 rounded-full flex items-center justify-center flex-shrink-0 t-label font-bold" style={{ background: active === st.grade ? `${st.color}22` : 'rgba(255,255,255,0.04)', color: active === st.grade ? st.color : 'var(--text-3)', border: `1px solid ${active === st.grade ? st.border : 'rgba(255,255,255,0.08)'}` }}>{st.grade}</div>
                  <div className="flex-1 min-w-0">
                    <span className="t-small font-semibold block" style={{ color: active === st.grade ? st.color : 'var(--text-2)' }}>{st.name}</span>
                    <span className="t-label text-text-3 block mt-0.5">{STAGE_EXTRA[st.grade].action}</span>
                  </div>
                  <StageIcon grade={st.grade} color={active === st.grade ? st.color : 'rgba(255,255,255,0.25)'} size={18} />
                </button>
              ))}
            </div>
            <div className="sr-zoom" style={{ transitionDelay: '160ms' }}>
              <div className="rounded-2xl overflow-hidden" style={{ background: s.bg, border: `1px solid ${s.border}`, transition: 'all 0.4s ease', boxShadow: `0 0 40px ${s.color}12` }}>
                <div className="px-7 pt-7 pb-5" style={{ borderBottom: `1px solid ${s.border}` }}>
                  <div className="flex items-center gap-4 mb-3">
                    <div className="w-12 h-12 rounded-full flex items-center justify-center" style={{ background: `${s.color}22`, border: `1px solid ${s.border}` }}><StageIcon grade={s.grade} color={s.color} size={24} /></div>
                    <div><p className="t-label text-text-3 mb-0.5">Grade {s.grade} · {ex.risk} Risk</p><h3 className="t-heading text-text-0" style={{ fontSize: '1.25rem' }}>{s.name}</h3></div>
                  </div>
                  <p className="t-body text-text-2">{s.desc}</p>
                </div>
                <div className="px-7 py-5" style={{ borderBottom: `1px solid ${s.border}` }}>
                  <p className="t-label text-text-3 mb-3">Clinical Signs</p>
                  <div className="space-y-2">{s.signs.map(sign => <div key={sign} className="flex items-center gap-3"><div className="w-1.5 h-1.5 rounded-full flex-shrink-0" style={{ background: s.color }} /><span className="t-small text-text-2">{sign}</span></div>)}</div>
                </div>
                <div className="px-7 py-5" style={{ borderBottom: `1px solid ${s.border}` }}>
                  <div className="grid grid-cols-2 gap-4">
                    <div><p className="t-label text-text-3 mb-1">Recommended Action</p><p className="t-small font-semibold" style={{ color: s.color }}>{ex.action}</p></div>
                    <div><p className="t-label text-text-3 mb-1">Patient Pathway</p><p className="t-small text-text-2">{ex.patients}</p></div>
                  </div>
                </div>
                <div className="px-7 py-5">
                  <div className="flex justify-between mb-2"><span className="t-label text-text-3">Severity Level</span><span className="t-label font-semibold" style={{ color: s.color }}>{['None','Low','Moderate','High','Critical'][s.grade]}</span></div>
                  <div className="progress-track" style={{ height: '5px' }}><div style={{ height: '100%', width: `${(s.grade + 1) * 20}%`, background: s.color, borderRadius: '9999px', transition: 'width 0.5s ease', boxShadow: `0 0 8px ${s.color}60` }} /></div>
                  <div className="flex justify-between mt-1"><span className="t-label text-text-3">Grade 0</span><span className="t-label text-text-3">Grade 4</span></div>
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
  <section id="features" className="landing-section flex items-center">
    <div className="relative z-10 w-full px-6 lg:px-14 py-32">
      <div className="max-w-6xl mx-auto">
        <div className="mb-16 sr-zoom">
          <p className="t-label text-text-3 mb-3">Capabilities</p>
          <h2 className="t-heading text-text-0">Key Features</h2>
        </div>
        <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
          {FEATURES.map((f, i) => (
            <GlassCard key={f.title} tilt className="p-7 sr-zoom" style={{ transitionDelay: `${i * 70}ms` }}>
              <p className="t-label text-text-3 mb-3">{f.n}</p>
              <h3 className="t-small font-semibold text-text-1 mb-3" style={{ fontSize: '1rem' }}>{f.title}</h3>
              <p className="t-small text-text-3" style={{ lineHeight: '1.7' }}>{f.desc}</p>
            </GlassCard>
          ))}
        </div>
      </div>
    </div>
  </section>
);

/* ── Pipeline ── */
const Pipeline: React.FC = () => (
  <section className="landing-section flex items-center">
    <div className="relative z-10 w-full px-6 lg:px-14 py-32">
      <div className="max-w-6xl mx-auto">
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-16 items-center">
          <div className="sr-zoom">
            <p className="t-label text-text-3 mb-4">How it works</p>
            <h2 className="t-heading text-text-0 mb-6">Analysis Pipeline</h2>
            <p className="t-body text-text-2 mb-8">Every fundus image passes through a rigorous multi-stage pipeline — from quality validation to explainable AI output — in seconds.</p>
            <Link to="/select-role"><Button size="lg" variant="primary">Try it Now</Button></Link>
          </div>
          <div className="space-y-2">
            {PIPELINE.map((item, i) => (
              <div key={item.step} className="flex items-center gap-5 p-4 rounded-xl sr-zoom" style={{ transitionDelay: `${i * 80}ms`, background: 'rgba(255,255,255,0.02)', border: '1px solid rgba(255,255,255,0.05)' }}>
                <div className="w-10 h-10 rounded-full flex items-center justify-center flex-shrink-0 t-label text-text-3" style={{ background: 'rgba(255,255,255,0.04)', border: '1px solid rgba(255,255,255,0.08)' }}>{String(i + 1).padStart(2, '0')}</div>
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
    </div>
  </section>
);

/* ── CTA ── */
const CTA: React.FC = () => (
  <section className="landing-section flex items-center justify-center text-center">
    <div className="scan-line" />
    <div className="relative z-10 w-full px-6 lg:px-14 py-40">
      <div className="sr-zoom max-w-3xl mx-auto">
        <p className="t-label text-text-3 mb-6">Get Started</p>
        <h2 className="t-display-md text-text-0 mb-6">Ready to screen for diabetic retinopathy?</h2>
        <p className="t-body text-text-2 mb-12 max-w-xl mx-auto">Upload a fundus image to begin AI-powered diabetic retinopathy screening with full explainability.</p>
        <Link to="/select-role"><Button size="xl" variant="primary">Start Screening Now</Button></Link>
      </div>
      <div className="mt-20 pt-10" style={{ borderTop: '1px solid rgba(255,255,255,0.05)' }}>
        <div className="flex items-center justify-center gap-3 mb-2">
          <svg width="18" height="18" viewBox="0 0 20 20" fill="none">
            <circle cx="10" cy="10" r="8" stroke="rgba(255,255,255,0.15)" strokeWidth="1"/>
            <circle cx="10" cy="10" r="4" stroke="rgba(255,255,255,0.2)" strokeWidth="1"/>
            <circle cx="10" cy="10" r="1.5" fill="rgba(255,255,255,0.5)"/>
          </svg>
          <span className="t-label text-text-3">RuralDR-XAI</span>
        </div>
        <p className="t-small text-text-3">© 2026 · AI-assisted screening tool · Requires clinical confirmation</p>
      </div>
    </div>
  </section>
);

/* ── LandingPage ── */
const LandingPage: React.FC = () => {
  useScrollReveal();
  return (
    <div className="relative" style={{ background: '#000' }}>
      {/* Single shared background fixed behind all sections */}
      <div className="fixed inset-0 pointer-events-none" style={{ zIndex: 0 }}>
        <RetinaBackground intensity="medium" className="opacity-40" />
      </div>
      <Nav />
      <Hero />
      <About />
      <Stages />
      <Features />
      <Pipeline />
      <CTA />
    </div>
  );
};

export default LandingPage;
