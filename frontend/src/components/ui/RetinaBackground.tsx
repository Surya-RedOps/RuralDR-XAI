import React, { useEffect, useRef, useCallback } from 'react';

interface Particle {
  x: number; y: number;
  vx: number; vy: number;
  r: number;
  alpha: number; alphaDir: number;
  hue: number;
}

interface Props {
  intensity?: 'low' | 'medium' | 'high';
  className?: string;
}

const COUNTS = { low: 30, medium: 60, high: 100 };
const MAX_DIST = 130;

export const RetinaBackground: React.FC<Props> = ({ intensity = 'medium', className = '' }) => {
  const canvasRef  = useRef<HTMLCanvasElement>(null);
  const particles  = useRef<Particle[]>([]);
  const mouse      = useRef({ x: -9999, y: -9999 });
  const raf        = useRef<number>(0);
  const reduced    = typeof window !== 'undefined'
    ? window.matchMedia('(prefers-reduced-motion: reduce)').matches : false;
  const count = reduced ? 0 : COUNTS[intensity];

  const init = useCallback((w: number, h: number) => {
    particles.current = Array.from({ length: count }, () => ({
      x: Math.random() * w,
      y: Math.random() * h,
      vx: (Math.random() - 0.5) * 0.22,
      vy: (Math.random() - 0.5) * 0.22,
      r: Math.random() * 1.8 + 0.4,
      alpha: Math.random() * 0.35 + 0.08,
      alphaDir: Math.random() > 0.5 ? 1 : -1,
      hue: Math.random() > 0.85 ? 1 : 0, // occasional warm tint
    }));
  }, [count]);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    const resize = () => {
      canvas.width  = canvas.offsetWidth;
      canvas.height = canvas.offsetHeight;
      init(canvas.width, canvas.height);
    };
    resize();
    const ro = new ResizeObserver(resize);
    ro.observe(canvas);

    const onMove = (e: MouseEvent) => {
      const r = canvas.getBoundingClientRect();
      mouse.current = { x: e.clientX - r.left, y: e.clientY - r.top };
    };
    const onLeave = () => { mouse.current = { x: -9999, y: -9999 }; };
    canvas.addEventListener('mousemove', onMove, { passive: true });
    canvas.addEventListener('mouseleave', onLeave);

    const draw = () => {
      const w = canvas.width, h = canvas.height;
      ctx.clearRect(0, 0, w, h);
      const ps = particles.current;
      const mx = mouse.current.x, my = mouse.current.y;

      for (const p of ps) {
        const dx = p.x - mx, dy = p.y - my;
        const d  = Math.sqrt(dx * dx + dy * dy);
        if (d < 90) {
          const f = (90 - d) / 90 * 0.5;
          p.vx += (dx / d) * f;
          p.vy += (dy / d) * f;
        }
        p.vx *= 0.975; p.vy *= 0.975;
        p.x  += p.vx;  p.y  += p.vy;
        if (p.x < 0) p.x = w; if (p.x > w) p.x = 0;
        if (p.y < 0) p.y = h; if (p.y > h) p.y = 0;
        p.alpha += p.alphaDir * 0.0025;
        if (p.alpha > 0.45 || p.alpha < 0.05) p.alphaDir *= -1;

        const color = p.hue
          ? `rgba(220,160,160,${p.alpha})`
          : `rgba(200,200,200,${p.alpha})`;
        ctx.beginPath();
        ctx.arc(p.x, p.y, p.r, 0, Math.PI * 2);
        ctx.fillStyle = color;
        ctx.fill();
      }

      for (let i = 0; i < ps.length; i++) {
        for (let j = i + 1; j < ps.length; j++) {
          const dx = ps[i].x - ps[j].x, dy = ps[i].y - ps[j].y;
          const d  = Math.sqrt(dx * dx + dy * dy);
          if (d < MAX_DIST) {
            const a = (1 - d / MAX_DIST) * 0.07;
            ctx.beginPath();
            ctx.moveTo(ps[i].x, ps[i].y);
            ctx.lineTo(ps[j].x, ps[j].y);
            ctx.strokeStyle = `rgba(200,200,200,${a})`;
            ctx.lineWidth = 0.5;
            ctx.stroke();
          }
        }
      }
      raf.current = requestAnimationFrame(draw);
    };

    if (!reduced) raf.current = requestAnimationFrame(draw);
    return () => {
      cancelAnimationFrame(raf.current);
      ro.disconnect();
      canvas.removeEventListener('mousemove', onMove);
      canvas.removeEventListener('mouseleave', onLeave);
    };
  }, [init, reduced]);

  const animDur = reduced ? '0s' : undefined;

  return (
    <div className={`absolute inset-0 overflow-hidden pointer-events-none ${className}`} aria-hidden="true">

      {/* Deep radial glow layers */}
      <div className="absolute inset-0" style={{
        background: `
          radial-gradient(ellipse 80% 70% at 50% 50%, rgba(185,28,28,0.07) 0%, transparent 65%),
          radial-gradient(ellipse 45% 45% at 50% 50%, rgba(185,28,28,0.05) 0%, transparent 55%),
          radial-gradient(ellipse 110% 90% at 50% 50%, rgba(6,182,212,0.025) 0%, transparent 75%)
        `
      }} />

      {/* SVG: rings + vascular paths */}
      <svg className="absolute inset-0 w-full h-full" xmlns="http://www.w3.org/2000/svg" preserveAspectRatio="xMidYMid slice">
        <defs>
          <radialGradient id="rg1" cx="50%" cy="50%" r="50%">
            <stop offset="0%"   stopColor="rgba(185,28,28,0.2)" />
            <stop offset="100%" stopColor="rgba(185,28,28,0)" />
          </radialGradient>
          <filter id="glow">
            <feGaussianBlur stdDeviation="3" result="blur" />
            <feMerge><feMergeNode in="blur"/><feMergeNode in="SourceGraphic"/></feMerge>
          </filter>
        </defs>

        {/* Concentric rings — slow counter-rotating */}
        {[160, 260, 360, 460, 560, 660].map((r, i) => (
          <circle key={r} cx="50%" cy="50%" r={r} fill="none"
            stroke={i === 2 ? 'rgba(185,28,28,0.12)' : 'rgba(255,255,255,0.03)'}
            strokeWidth={i === 2 ? '1.5' : '1'}
            style={{
              transformOrigin: '50% 50%',
              animation: animDur ? 'none' : `spin-slow ${20 + i * 7}s linear infinite ${i % 2 ? 'reverse' : ''}`,
            }}
          />
        ))}

        {/* Vascular tree — drawn on mount */}
        <g opacity="0.18" stroke="rgba(220,220,220,1)" strokeWidth="0.7" fill="none"
          style={{ filter: 'url(#glow)' }}>
          {/* Main vessels from optic disc ~(58%, 48%) */}
          <path strokeDasharray="400" strokeDashoffset="400"
            d="M 58% 48% Q 62% 35% 72% 22%"
            style={{ animation: animDur ? 'none' : 'drawLine 2.5s ease-out 0.3s forwards' }} />
          <path strokeDasharray="400" strokeDashoffset="400"
            d="M 58% 48% Q 70% 44% 84% 38%"
            style={{ animation: animDur ? 'none' : 'drawLine 2.5s ease-out 0.5s forwards' }} />
          <path strokeDasharray="400" strokeDashoffset="400"
            d="M 58% 48% Q 68% 58% 78% 72%"
            style={{ animation: animDur ? 'none' : 'drawLine 2.5s ease-out 0.7s forwards' }} />
          <path strokeDasharray="400" strokeDashoffset="400"
            d="M 58% 48% Q 48% 62% 36% 76%"
            style={{ animation: animDur ? 'none' : 'drawLine 2.5s ease-out 0.9s forwards' }} />
          <path strokeDasharray="400" strokeDashoffset="400"
            d="M 58% 48% Q 42% 46% 26% 42%"
            style={{ animation: animDur ? 'none' : 'drawLine 2.5s ease-out 1.1s forwards' }} />
          <path strokeDasharray="400" strokeDashoffset="400"
            d="M 58% 48% Q 46% 36% 32% 24%"
            style={{ animation: animDur ? 'none' : 'drawLine 2.5s ease-out 1.3s forwards' }} />
          {/* Secondary branches */}
          <path strokeDasharray="200" strokeDashoffset="200" strokeWidth="0.5"
            d="M 72% 22% Q 76% 16% 82% 12%"
            style={{ animation: animDur ? 'none' : 'drawLine 1.8s ease-out 1.5s forwards' }} />
          <path strokeDasharray="200" strokeDashoffset="200" strokeWidth="0.5"
            d="M 84% 38% Q 90% 32% 94% 26%"
            style={{ animation: animDur ? 'none' : 'drawLine 1.8s ease-out 1.6s forwards' }} />
          <path strokeDasharray="200" strokeDashoffset="200" strokeWidth="0.5"
            d="M 78% 72% Q 84% 80% 88% 86%"
            style={{ animation: animDur ? 'none' : 'drawLine 1.8s ease-out 1.7s forwards' }} />
          <path strokeDasharray="200" strokeDashoffset="200" strokeWidth="0.5"
            d="M 36% 76% Q 28% 84% 20% 90%"
            style={{ animation: animDur ? 'none' : 'drawLine 1.8s ease-out 1.8s forwards' }} />
          <path strokeDasharray="200" strokeDashoffset="200" strokeWidth="0.5"
            d="M 26% 42% Q 16% 40% 8% 36%"
            style={{ animation: animDur ? 'none' : 'drawLine 1.8s ease-out 1.9s forwards' }} />
          <path strokeDasharray="200" strokeDashoffset="200" strokeWidth="0.5"
            d="M 32% 24% Q 24% 16% 16% 10%"
            style={{ animation: animDur ? 'none' : 'drawLine 1.8s ease-out 2.0s forwards' }} />
        </g>

        {/* Optic disc */}
        <circle cx="58%" cy="48%" r="22" fill="rgba(255,255,255,0.015)" stroke="rgba(255,255,255,0.06)" strokeWidth="1.5" />
        <circle cx="58%" cy="48%" r="10" fill="rgba(255,255,255,0.025)" />

        {/* Fovea */}
        <circle cx="42%" cy="50%" r="8" fill="none" stroke="rgba(255,255,255,0.04)" strokeWidth="1" />
      </svg>

      {/* Particle canvas */}
      <canvas ref={canvasRef} className="absolute inset-0 w-full h-full" style={{ pointerEvents: 'all' }} />
    </div>
  );
};
