import React, { useEffect, useRef } from 'react';

interface Props {
  /** parent passes mouse position relative to the fundus container, normalised -1..1 */
  mouseX?: number;
  mouseY?: number;
  hovered?: boolean;
}

export const FundusCanvas: React.FC<Props> = ({ mouseX = 0, mouseY = 0, hovered = false }) => {
  const canvasRef  = useRef<HTMLCanvasElement>(null);
  const rafRef     = useRef<number>(0);
  const mouseRef   = useRef({ x: mouseX, y: mouseY, hovered });

  // keep ref in sync without re-running effect
  useEffect(() => { mouseRef.current = { x: mouseX, y: mouseY, hovered }; }, [mouseX, mouseY, hovered]);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    const SIZE = 640;
    canvas.width  = SIZE;
    canvas.height = SIZE;
    const CX = SIZE / 2, CY = SIZE / 2, R = SIZE / 2 - 2;
    const rnd = (a: number, b: number) => a + Math.random() * (b - a);

    type Seg = { x1:number; y1:number; x2:number; y2:number; w:number; art:boolean; depth:number };
    const segments: Seg[] = [];

    const buildVessel = (x:number,y:number,angle:number,length:number,width:number,depth:number,isArtery:boolean,seed:number) => {
      if (depth > 6 || length < 7) return;
      const s1 = Math.sin(seed * 127.1) * 43758.5453;
      const s2 = Math.sin(seed * 311.7) * 43758.5453;
      const jitter = (s1 - Math.floor(s1) - 0.5) * 0.25;
      const ex = x + Math.cos(angle + jitter) * length;
      const ey = y + Math.sin(angle + jitter) * length;
      segments.push({ x1:x, y1:y, x2:ex, y2:ey, w:width, art:isArtery, depth });
      const spread = 0.32 + (s2 - Math.floor(s2)) * 0.28;
      buildVessel(ex,ey,angle-spread,length*0.68,width*0.62,depth+1,isArtery,seed+1);
      buildVessel(ex,ey,angle+spread*0.8,length*0.62,width*0.58,depth+1,isArtery,seed+7);
    };

    const OX = CX + 88, OY = CY - 12;
    [
      {a:-2.5,l:145,w:3.8,art:true, s:1 },{a:-1.9,l:135,w:3.2,art:false,s:10},
      {a:-1.1,l:155,w:3.6,art:true, s:20},{a:-0.3,l:125,w:3.0,art:false,s:30},
      {a: 0.4,l:148,w:3.4,art:true, s:40},{a: 1.1,l:138,w:3.1,art:false,s:50},
      {a: 1.9,l:118,w:2.8,art:true, s:60},{a: 2.7,l:130,w:2.9,art:false,s:70},
      {a: 3.3,l:110,w:2.6,art:true, s:80},
    ].forEach(({a,l,w,art,s})=>buildVessel(OX,OY,a,l,w,0,art,s));

    const drawFundus = () => {
      ctx.save();
      ctx.beginPath(); ctx.arc(CX,CY,R,0,Math.PI*2); ctx.clip();

      // base sphere gradient
      const bg = ctx.createRadialGradient(CX-60,CY-80,20,CX,CY,R);
      bg.addColorStop(0,'#9a4018'); bg.addColorStop(0.2,'#7a3010');
      bg.addColorStop(0.5,'#622408'); bg.addColorStop(0.78,'#4a1a05'); bg.addColorStop(1,'#280a02');
      ctx.fillStyle=bg; ctx.fillRect(0,0,SIZE,SIZE);

      // texture
      for(let i=0;i<28000;i++){
        const x=Math.random()*SIZE,y=Math.random()*SIZE,v=rnd(0,0.055);
        ctx.fillStyle=`rgba(255,190,100,${v})`; ctx.fillRect(x,y,1,1);
      }

      // choroidal patches
      for(let i=0;i<60;i++){
        const px=rnd(CX-R*0.8,CX+R*0.8),py=rnd(CY-R*0.8,CY+R*0.8),pr=rnd(18,55);
        const pg=ctx.createRadialGradient(px,py,0,px,py,pr);
        pg.addColorStop(0,`rgba(30,8,2,${rnd(0.04,0.12)})`); pg.addColorStop(1,'rgba(30,8,2,0)');
        ctx.fillStyle=pg; ctx.beginPath(); ctx.ellipse(px,py,pr,pr*rnd(0.6,1),rnd(0,Math.PI),0,Math.PI*2); ctx.fill();
      }

      // illumination
      const illum=ctx.createRadialGradient(CX-30,CY-40,0,CX,CY,R);
      illum.addColorStop(0,'rgba(255,200,100,0.28)'); illum.addColorStop(0.3,'rgba(220,120,40,0.12)');
      illum.addColorStop(0.65,'rgba(150,60,10,0.04)'); illum.addColorStop(1,'rgba(0,0,0,0.4)');
      ctx.fillStyle=illum; ctx.fillRect(0,0,SIZE,SIZE);

      // vessels
      segments.forEach(({x1,y1,x2,y2,w,art,depth})=>{
        ctx.beginPath(); ctx.moveTo(x1,y1); ctx.lineTo(x2,y2);
        ctx.strokeStyle=art?`rgba(220,80,50,${0.18-depth*0.02})`:`rgba(160,40,20,${0.14-depth*0.015})`;
        ctx.lineWidth=Math.max(0.5,w*2.2); ctx.lineCap='round'; ctx.stroke();
        ctx.beginPath(); ctx.moveTo(x1,y1); ctx.lineTo(x2,y2);
        ctx.strokeStyle=art?`rgba(210,65,40,${0.82-depth*0.1})`:`rgba(145,28,18,${0.72-depth*0.09})`;
        ctx.lineWidth=Math.max(0.4,w); ctx.stroke();
        if(art&&w>1.2){
          ctx.beginPath(); ctx.moveTo(x1,y1); ctx.lineTo(x2,y2);
          ctx.strokeStyle=`rgba(255,140,100,${0.22-depth*0.03})`; ctx.lineWidth=Math.max(0.2,w*0.3); ctx.stroke();
        }
      });

      // optic disc
      const disc=ctx.createRadialGradient(OX-8,OY-8,0,OX,OY,58);
      disc.addColorStop(0,'rgba(255,248,200,0.98)'); disc.addColorStop(0.18,'rgba(255,230,150,0.92)');
      disc.addColorStop(0.4,'rgba(240,190,90,0.75)'); disc.addColorStop(0.65,'rgba(210,140,50,0.4)'); disc.addColorStop(1,'rgba(180,80,20,0)');
      ctx.fillStyle=disc; ctx.beginPath(); ctx.ellipse(OX,OY,58,50,-0.18,0,Math.PI*2); ctx.fill();
      const cup=ctx.createRadialGradient(OX,OY,0,OX,OY,28);
      cup.addColorStop(0,'rgba(255,255,220,0.6)'); cup.addColorStop(0.5,'rgba(240,210,140,0.3)'); cup.addColorStop(1,'rgba(200,150,60,0)');
      ctx.fillStyle=cup; ctx.beginPath(); ctx.ellipse(OX,OY,28,22,-0.18,0,Math.PI*2); ctx.fill();
      ctx.strokeStyle='rgba(255,230,150,0.3)'; ctx.lineWidth=1.5;
      ctx.beginPath(); ctx.ellipse(OX,OY,44,37,-0.18,0,Math.PI*2); ctx.stroke();

      // fovea
      const FX=CX-60,FY=CY+10;
      const fov=ctx.createRadialGradient(FX,FY,0,FX,FY,32);
      fov.addColorStop(0,'rgba(20,5,1,0.9)'); fov.addColorStop(0.4,'rgba(50,12,4,0.6)'); fov.addColorStop(1,'rgba(100,30,8,0)');
      ctx.fillStyle=fov; ctx.beginPath(); ctx.ellipse(FX,FY,32,25,0,0,Math.PI*2); ctx.fill();
      const fref=ctx.createRadialGradient(FX-5,FY-5,0,FX,FY,12);
      fref.addColorStop(0,'rgba(255,245,210,0.5)'); fref.addColorStop(1,'rgba(255,200,100,0)');
      ctx.fillStyle=fref; ctx.beginPath(); ctx.ellipse(FX-5,FY-5,12,8,-0.5,0,Math.PI*2); ctx.fill();

      // sphere rim shading
      const sphere=ctx.createRadialGradient(CX,CY,R*0.45,CX,CY,R);
      sphere.addColorStop(0,'rgba(0,0,0,0)'); sphere.addColorStop(0.6,'rgba(0,0,0,0.08)');
      sphere.addColorStop(0.82,'rgba(0,0,0,0.3)'); sphere.addColorStop(1,'rgba(0,0,0,0.75)');
      ctx.fillStyle=sphere; ctx.fillRect(0,0,SIZE,SIZE);

      ctx.restore();
    };

    const drawOverlay = (t: number) => {
      ctx.save();
      ctx.beginPath(); ctx.arc(CX,CY,R,0,Math.PI*2); ctx.clip();

      const { x: mx, y: my, hovered: isHovered } = mouseRef.current;

      // dynamic specular — follows mouse on hover, drifts slowly when idle
      const specAngle = isHovered
        ? Math.atan2(my, mx)
        : t * 0.004;
      const specDist  = isHovered ? 0.55 : 0.38;
      const specIntensity = isHovered ? 0.32 : 0.16;
      const sx = CX + Math.cos(specAngle - Math.PI) * R * specDist;
      const sy2 = CY + Math.sin(specAngle - Math.PI) * R * specDist;
      const spec = ctx.createRadialGradient(sx, sy2, 0, sx, sy2, isHovered ? 140 : 110);
      spec.addColorStop(0,   `rgba(255,245,210,${specIntensity})`);
      spec.addColorStop(0.4, `rgba(255,210,140,${specIntensity * 0.35})`);
      spec.addColorStop(1,   'rgba(255,180,80,0)');
      ctx.fillStyle = spec; ctx.fillRect(0,0,SIZE,SIZE);

      // vessel pulse — stronger on hover
      const pulseSpeed = isHovered ? 0.045 : 0.022;
      const pulseAmp   = isHovered ? 0.18  : 0.10;
      const pulse = 0.5 + Math.sin(t * pulseSpeed) * 0.5;
      segments.forEach(({x1,y1,x2,y2,w,art,depth})=>{
        if(depth>2) return;
        const a = art
          ? (pulseAmp + pulse * pulseAmp) * (1 - depth * 0.25)
          : (pulseAmp * 0.5 + pulse * pulseAmp * 0.5) * (1 - depth * 0.25);
        ctx.beginPath(); ctx.moveTo(x1,y1); ctx.lineTo(x2,y2);
        ctx.strokeStyle=art?`rgba(255,120,80,${a})`:`rgba(200,60,40,${a*0.7})`;
        ctx.lineWidth=Math.max(0.5,w*(isHovered?2.0:1.6)); ctx.lineCap='round'; ctx.stroke();
      });

      // optic disc glow — brighter on hover
      const discBase = isHovered ? 0.22 : 0.14;
      const discPulse = discBase + Math.sin(t * 0.018) * 0.07;
      const dg=ctx.createRadialGradient(OX-6,OY-6,0,OX,OY,65);
      dg.addColorStop(0,`rgba(255,248,180,${discPulse})`);
      dg.addColorStop(0.5,`rgba(255,200,80,${discPulse*0.4})`);
      dg.addColorStop(1,'rgba(255,160,40,0)');
      ctx.fillStyle=dg; ctx.beginPath(); ctx.ellipse(OX,OY,65,56,-0.18,0,Math.PI*2); ctx.fill();

      // scan line
      const scanY = ((t * 0.035) % (R * 2.1)) - R * 0.05 + CY - R;
      const sg=ctx.createLinearGradient(0,scanY-8,0,scanY+8);
      sg.addColorStop(0,'rgba(6,182,212,0)'); sg.addColorStop(0.5,'rgba(6,182,212,0.28)'); sg.addColorStop(1,'rgba(6,182,212,0)');
      ctx.fillStyle=sg; ctx.fillRect(CX-R,scanY-8,R*2,16);
      ctx.beginPath(); ctx.moveTo(CX-R,scanY); ctx.lineTo(CX+R,scanY);
      ctx.strokeStyle='rgba(6,182,212,0.45)'; ctx.lineWidth=0.7; ctx.stroke();

      // hover edge glow
      if (isHovered) {
        const edge = ctx.createRadialGradient(CX,CY,R*0.75,CX,CY,R);
        edge.addColorStop(0,'rgba(255,140,60,0)');
        edge.addColorStop(0.7,'rgba(255,120,40,0.06)');
        edge.addColorStop(1,'rgba(255,100,20,0.18)');
        ctx.fillStyle=edge; ctx.fillRect(0,0,SIZE,SIZE);
      }

      ctx.restore();
    };

    drawFundus();
    const staticData = ctx.getImageData(0,0,SIZE,SIZE);
    let t = 0;
    const reduced = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
    const loop = () => {
      ctx.putImageData(staticData,0,0);
      drawOverlay(t++);
      rafRef.current = requestAnimationFrame(loop);
    };
    if (!reduced) rafRef.current = requestAnimationFrame(loop);
    return () => cancelAnimationFrame(rafRef.current);
  }, []);

  return (
    <canvas
      ref={canvasRef}
      style={{ width:'100%', height:'100%', borderRadius:'50%', display:'block' }}
      aria-label="Photorealistic retinal fundus visualization"
    />
  );
};
