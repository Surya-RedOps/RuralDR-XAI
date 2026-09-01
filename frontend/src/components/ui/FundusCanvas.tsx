import React, { useEffect, useRef } from 'react';

export const FundusCanvas: React.FC = () => {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const rafRef    = useRef<number>(0);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    const SIZE = 520;
    canvas.width  = SIZE;
    canvas.height = SIZE;
    const CX = SIZE / 2, CY = SIZE / 2, R = SIZE / 2 - 2;

    /* ── helpers ── */
    const rnd  = (a: number, b: number) => a + Math.random() * (b - a);
    const clip  = () => { ctx.beginPath(); ctx.arc(CX, CY, R, 0, Math.PI * 2); ctx.clip(); };

    /* ── draw static fundus once ── */
    const drawFundus = () => {
      ctx.save();
      ctx.beginPath(); ctx.arc(CX, CY, R, 0, Math.PI * 2); ctx.clip();

      /* 1. Base retinal background — warm amber-orange */
      const bg = ctx.createRadialGradient(CX, CY, 0, CX, CY, R);
      bg.addColorStop(0,    '#7a3010');
      bg.addColorStop(0.35, '#6b2a0c');
      bg.addColorStop(0.7,  '#5a2008');
      bg.addColorStop(1,    '#3a1205');
      ctx.fillStyle = bg;
      ctx.fillRect(0, 0, SIZE, SIZE);

      /* 2. Subtle texture noise */
      for (let i = 0; i < 18000; i++) {
        const x = Math.random() * SIZE, y = Math.random() * SIZE;
        const v = rnd(0, 0.06);
        ctx.fillStyle = `rgba(255,200,120,${v})`;
        ctx.fillRect(x, y, 1, 1);
      }

      /* 3. Radial illumination — brighter centre */
      const illum = ctx.createRadialGradient(CX, CY - 20, 0, CX, CY, R);
      illum.addColorStop(0,   'rgba(255,180,80,0.22)');
      illum.addColorStop(0.5, 'rgba(200,100,30,0.08)');
      illum.addColorStop(1,   'rgba(0,0,0,0.35)');
      ctx.fillStyle = illum;
      ctx.fillRect(0, 0, SIZE, SIZE);

      /* 4. Optic disc — bright yellowish oval, right of centre */
      const OX = CX + 80, OY = CY - 10;
      const disc = ctx.createRadialGradient(OX, OY, 0, OX, OY, 52);
      disc.addColorStop(0,    'rgba(255,240,180,0.95)');
      disc.addColorStop(0.25, 'rgba(255,210,120,0.85)');
      disc.addColorStop(0.55, 'rgba(220,150,60,0.5)');
      disc.addColorStop(1,    'rgba(180,80,20,0)');
      ctx.fillStyle = disc;
      ctx.beginPath(); ctx.ellipse(OX, OY, 52, 44, -0.15, 0, Math.PI * 2); ctx.fill();

      /* disc rim */
      ctx.strokeStyle = 'rgba(255,220,140,0.35)';
      ctx.lineWidth = 2;
      ctx.beginPath(); ctx.ellipse(OX, OY, 38, 32, -0.15, 0, Math.PI * 2); ctx.stroke();

      /* 5. Fovea — dark depression left of centre */
      const FX = CX - 55, FY = CY + 8;
      const fov = ctx.createRadialGradient(FX, FY, 0, FX, FY, 28);
      fov.addColorStop(0,   'rgba(30,8,2,0.85)');
      fov.addColorStop(0.5, 'rgba(60,15,5,0.5)');
      fov.addColorStop(1,   'rgba(100,30,10,0)');
      ctx.fillStyle = fov;
      ctx.beginPath(); ctx.ellipse(FX, FY, 28, 22, 0, 0, Math.PI * 2); ctx.fill();

      /* foveal reflex */
      const fref = ctx.createRadialGradient(FX - 4, FY - 4, 0, FX, FY, 10);
      fref.addColorStop(0,   'rgba(255,240,200,0.45)');
      fref.addColorStop(1,   'rgba(255,200,100,0)');
      ctx.fillStyle = fref;
      ctx.beginPath(); ctx.ellipse(FX - 4, FY - 4, 10, 7, -0.4, 0, Math.PI * 2); ctx.fill();

      /* 6. Blood vessels — branching from optic disc */
      const drawVessel = (
        x: number, y: number,
        angle: number, length: number,
        width: number, depth: number,
        isArtery: boolean
      ) => {
        if (depth > 5 || length < 8) return;
        const ex = x + Math.cos(angle) * length;
        const ey = y + Math.sin(angle) * length;
        const cx1 = x + Math.cos(angle - 0.3) * length * 0.5;
        const cy1 = y + Math.sin(angle - 0.3) * length * 0.5;

        ctx.beginPath();
        ctx.moveTo(x, y);
        ctx.quadraticCurveTo(cx1, cy1, ex, ey);
        ctx.strokeStyle = isArtery
          ? `rgba(200,60,40,${0.75 - depth * 0.1})`
          : `rgba(140,30,20,${0.65 - depth * 0.1})`;
        ctx.lineWidth = Math.max(0.4, width);
        ctx.lineCap = 'round';
        ctx.stroke();

        /* branch */
        const spread = rnd(0.3, 0.55);
        drawVessel(ex, ey, angle - spread, length * rnd(0.6, 0.78), width * 0.65, depth + 1, isArtery);
        drawVessel(ex, ey, angle + spread * rnd(0.5, 0.9), length * rnd(0.55, 0.72), width * 0.6, depth + 1, isArtery);
      };

      /* main trunks from disc */
      const trunks = [
        { a: -2.4,  l: 130, w: 3.2, art: true  },
        { a: -1.8,  l: 120, w: 2.8, art: false },
        { a: -0.9,  l: 140, w: 3.0, art: true  },
        { a: -0.2,  l: 110, w: 2.6, art: false },
        { a:  0.5,  l: 130, w: 2.9, art: true  },
        { a:  1.3,  l: 120, w: 2.7, art: false },
        { a:  2.0,  l: 100, w: 2.4, art: true  },
        { a:  2.8,  l: 115, w: 2.5, art: false },
      ];
      trunks.forEach(({ a, l, w, art }) => drawVessel(OX, OY, a, l, w, 0, art));

      /* 7. Subtle vignette */
      const vig = ctx.createRadialGradient(CX, CY, R * 0.55, CX, CY, R);
      vig.addColorStop(0,   'rgba(0,0,0,0)');
      vig.addColorStop(0.7, 'rgba(0,0,0,0.15)');
      vig.addColorStop(1,   'rgba(0,0,0,0.65)');
      ctx.fillStyle = vig;
      ctx.fillRect(0, 0, SIZE, SIZE);

      ctx.restore();
    };

    /* ── draw scan overlay each frame ── */
    const drawScan = (t: number) => {
      ctx.save();
      clip();

      /* slow breathing glow on disc */
      const pulse = 0.12 + Math.sin(t * 0.0018) * 0.06;
      const OX = CX + 80, OY = CY - 10;
      const dg = ctx.createRadialGradient(OX, OY, 0, OX, OY, 55);
      dg.addColorStop(0,   `rgba(255,240,160,${pulse})`);
      dg.addColorStop(1,   'rgba(255,200,80,0)');
      ctx.fillStyle = dg;
      ctx.beginPath(); ctx.ellipse(OX, OY, 55, 46, -0.15, 0, Math.PI * 2); ctx.fill();

      /* scan line */
      const sy = ((t * 0.04) % (R * 2)) - R + CY;
      const scanGrad = ctx.createLinearGradient(0, sy - 6, 0, sy + 6);
      scanGrad.addColorStop(0,   'rgba(6,182,212,0)');
      scanGrad.addColorStop(0.5, 'rgba(6,182,212,0.35)');
      scanGrad.addColorStop(1,   'rgba(6,182,212,0)');
      ctx.fillStyle = scanGrad;
      ctx.fillRect(CX - R, sy - 6, R * 2, 12);

      /* scan line bright centre */
      ctx.beginPath();
      ctx.moveTo(CX - R, sy);
      ctx.lineTo(CX + R, sy);
      ctx.strokeStyle = 'rgba(6,182,212,0.5)';
      ctx.lineWidth = 0.8;
      ctx.stroke();

      ctx.restore();
    };

    /* ── static layer drawn once ── */
    drawFundus();
    const staticData = ctx.getImageData(0, 0, SIZE, SIZE);

    /* ── animation loop ── */
    let t = 0;
    const loop = () => {
      ctx.putImageData(staticData, 0, 0);
      drawScan(t);
      t++;
      rafRef.current = requestAnimationFrame(loop);
    };

    const reduced = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
    if (!reduced) rafRef.current = requestAnimationFrame(loop);

    return () => cancelAnimationFrame(rafRef.current);
  }, []);

  return (
    <canvas
      ref={canvasRef}
      style={{
        width: '100%',
        height: '100%',
        borderRadius: '50%',
        display: 'block',
      }}
      aria-label="Photorealistic retinal fundus visualization"
    />
  );
};
