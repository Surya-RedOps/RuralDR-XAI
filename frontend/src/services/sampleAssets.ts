/**
 * Visual Asset Generator for RuralDR-XAI prototype
 * Generates realistic SVG data URIs for retina stages, Grad-CAM overlays, lesion masks,
 * invalid non-fundus images, and poor quality images.
 */

function createSvgDataUri(svgContent: string): string {
  return `data:image/svg+xml;utf8,${encodeURIComponent(svgContent.trim())}`;
}

// 1. Normal Fundus (DR Grade 0)
export const NORMAL_FUNDUS_SVG = createSvgDataUri(`
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 800 800" width="800" height="800">
  <defs>
    <radialGradient id="bgGlow" cx="50%" cy="50%" r="50%">
      <stop offset="0%" stop-color="#bf360c" />
      <stop offset="45%" stop-color="#871b05" />
      <stop offset="75%" stop-color="#4a0c02" />
      <stop offset="95%" stop-color="#190401" />
      <stop offset="100%" stop-color="#000000" />
    </radialGradient>
    <radialGradient id="opticDisc" cx="45%" cy="45%" r="50%">
      <stop offset="0%" stop-color="#ffecb3" />
      <stop offset="40%" stop-color="#ffe082" />
      <stop offset="80%" stop-color="#ffb74d" />
      <stop offset="100%" stop-color="#d84315" />
    </radialGradient>
    <radialGradient id="maculaGlow" cx="50%" cy="50%" r="50%">
      <stop offset="0%" stop-color="#2a0501" />
      <stop offset="50%" stop-color="#4e0d02" />
      <stop offset="100%" stop-color="transparent" />
    </radialGradient>
    <filter id="blurFilter" x="-20%" y="-20%" width="140%" height="140%">
      <feGaussianBlur stdDeviation="3" />
    </filter>
  </defs>

  <!-- Background Fundus Field -->
  <rect width="800" height="800" fill="#000000" />
  <circle cx="400" cy="400" r="370" fill="url(#bgGlow)" />
  
  <!-- Choroidal texture layers -->
  <circle cx="400" cy="400" r="365" fill="none" stroke="#ff7043" stroke-width="2" opacity="0.15" />
  
  <!-- Macula Region -->
  <circle cx="480" cy="420" r="70" fill="url(#maculaGlow)" opacity="0.85" />
  <circle cx="480" cy="420" r="8" fill="#1b0000" opacity="0.6" />

  <!-- Optic Disc -->
  <ellipse cx="280" cy="390" rx="42" ry="48" fill="url(#opticDisc)" opacity="0.95" />
  <ellipse cx="276" cy="388" rx="20" ry="24" fill="#fff9c4" opacity="0.9" />

  <!-- Retinal Vasculature Tree (Arteries & Veins) -->
  <g stroke="#670d02" stroke-width="8" fill="none" stroke-linecap="round" stroke-linejoin="round" opacity="0.85">
    <!-- Superior temporal arcade -->
    <path d="M 280,380 C 290,320 340,240 430,220 C 510,200 610,240 680,310" />
    <path d="M 430,220 C 470,170 530,150 600,160" stroke-width="4" />
    <!-- Inferior temporal arcade -->
    <path d="M 280,400 C 300,470 350,560 440,580 C 530,600 620,550 690,470" />
    <path d="M 440,580 C 480,630 550,650 620,640" stroke-width="4" />
    <!-- Superior nasal arcade -->
    <path d="M 270,370 C 240,300 200,240 130,220" stroke-width="6" />
    <!-- Inferior nasal arcade -->
    <path d="M 270,410 C 230,480 180,540 120,570" stroke-width="6" />
  </g>

  <!-- Fine vessels -->
  <g stroke="#a71d0d" stroke-width="3.5" fill="none" stroke-linecap="round" opacity="0.9">
    <path d="M 280,385 C 320,335 380,270 460,250 C 540,230 630,270 670,320" />
    <path d="M 280,395 C 310,455 370,530 450,550 C 530,570 610,520 660,460" />
    <path d="M 460,250 C 480,290 500,340 510,380" stroke-width="1.8" />
    <path d="M 450,550 C 475,500 495,460 505,430" stroke-width="1.8" />
  </g>

  <!-- Vignette / Camera Aperture Rim -->
  <circle cx="400" cy="400" r="370" fill="none" stroke="#000000" stroke-width="30" />
  <circle cx="400" cy="400" r="360" fill="none" stroke="#111111" stroke-width="8" opacity="0.6" />
</svg>
`);

// 2. Mild NPDR Fundus (DR Grade 1 - Microaneurysms)
export const MILD_NPDR_FUNDUS_SVG = createSvgDataUri(`
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 800 800" width="800" height="800">
  <defs>
    <radialGradient id="bgGlow1" cx="50%" cy="50%" r="50%">
      <stop offset="0%" stop-color="#bf360c" />
      <stop offset="45%" stop-color="#871b05" />
      <stop offset="75%" stop-color="#4a0c02" />
      <stop offset="95%" stop-color="#190401" />
      <stop offset="100%" stop-color="#000000" />
    </radialGradient>
    <radialGradient id="opticDisc1" cx="45%" cy="45%" r="50%">
      <stop offset="0%" stop-color="#ffecb3" />
      <stop offset="40%" stop-color="#ffe082" />
      <stop offset="80%" stop-color="#ffb74d" />
      <stop offset="100%" stop-color="#d84315" />
    </radialGradient>
    <radialGradient id="maculaGlow1" cx="50%" cy="50%" r="50%">
      <stop offset="0%" stop-color="#2a0501" />
      <stop offset="50%" stop-color="#4e0d02" />
      <stop offset="100%" stop-color="transparent" />
    </radialGradient>
  </defs>

  <rect width="800" height="800" fill="#000000" />
  <circle cx="400" cy="400" r="370" fill="url(#bgGlow1)" />
  <circle cx="480" cy="420" r="70" fill="url(#maculaGlow1)" opacity="0.85" />
  <ellipse cx="280" cy="390" rx="42" ry="48" fill="url(#opticDisc1)" opacity="0.95" />
  <ellipse cx="276" cy="388" rx="20" ry="24" fill="#fff9c4" opacity="0.9" />

  <!-- Vasculature -->
  <g stroke="#670d02" stroke-width="7" fill="none" stroke-linecap="round" opacity="0.85">
    <path d="M 280,380 C 290,320 340,240 430,220 C 510,200 610,240 680,310" />
    <path d="M 280,400 C 300,470 350,560 440,580 C 530,600 620,550 690,470" />
    <path d="M 270,370 C 240,300 200,240 130,220" stroke-width="5" />
    <path d="M 270,410 C 230,480 180,540 120,570" stroke-width="5" />
  </g>

  <!-- Mild Lesions: Isolated Microaneurysms (tiny red punctate dots) -->
  <g fill="#450000" stroke="#ff1744" stroke-width="1.2">
    <circle cx="420" cy="340" r="3.5" />
    <circle cx="445" cy="325" r="3" />
    <circle cx="530" cy="360" r="4" />
    <circle cx="510" cy="480" r="3.5" />
    <circle cx="400" cy="490" r="3" />
    <circle cx="560" cy="430" r="3.5" />
  </g>

  <!-- Vignette -->
  <circle cx="400" cy="400" r="370" fill="none" stroke="#000000" stroke-width="30" />
</svg>
`);

// 3. Moderate NPDR Fundus (DR Grade 2 - Microaneurysms + Hemorrhages + Hard Exudates)
export const MODERATE_NPDR_FUNDUS_SVG = createSvgDataUri(`
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 800 800" width="800" height="800">
  <defs>
    <radialGradient id="bgGlow2" cx="50%" cy="50%" r="50%">
      <stop offset="0%" stop-color="#b73007" />
      <stop offset="45%" stop-color="#7f1704" />
      <stop offset="75%" stop-color="#460a01" />
      <stop offset="100%" stop-color="#000000" />
    </radialGradient>
    <radialGradient id="opticDisc2" cx="45%" cy="45%" r="50%">
      <stop offset="0%" stop-color="#ffe082" />
      <stop offset="60%" stop-color="#ffb74d" />
      <stop offset="100%" stop-color="#d84315" />
    </radialGradient>
    <radialGradient id="exudateGrad" cx="50%" cy="50%" r="50%">
      <stop offset="0%" stop-color="#ffffff" />
      <stop offset="40%" stop-color="#fff59d" />
      <stop offset="100%" stop-color="#fbc02d" />
    </radialGradient>
  </defs>

  <rect width="800" height="800" fill="#000000" />
  <circle cx="400" cy="400" r="370" fill="url(#bgGlow2)" />
  <circle cx="480" cy="420" r="70" fill="#2a0501" opacity="0.85" />
  <ellipse cx="280" cy="390" rx="42" ry="48" fill="url(#opticDisc2)" opacity="0.95" />

  <!-- Vasculature -->
  <g stroke="#590a01" stroke-width="7" fill="none" stroke-linecap="round" opacity="0.85">
    <path d="M 280,380 C 290,320 340,240 430,220 C 510,200 610,240 680,310" />
    <path d="M 280,400 C 300,470 350,560 440,580 C 530,600 620,550 690,470" />
    <path d="M 270,370 C 240,300 200,240 130,220" stroke-width="5" />
    <path d="M 270,410 C 230,480 180,540 120,570" stroke-width="5" />
  </g>

  <!-- Microaneurysms -->
  <g fill="#450000" stroke="#d50000" stroke-width="1.5">
    <circle cx="410" cy="330" r="4" /><circle cx="440" cy="310" r="4.5" />
    <circle cx="390" cy="270" r="3.5" /><circle cx="520" cy="340" r="4" />
    <circle cx="560" cy="370" r="5" /><circle cx="510" cy="490" r="4" />
    <circle cx="370" cy="480" r="4" /><circle cx="430" cy="520" r="4.5" />
  </g>

  <!-- Blot Hemorrhages (dark red irregular spots) -->
  <g fill="#3e0000" stroke="#8b0000" stroke-width="2" opacity="0.95">
    <path d="M 460,310 Q 475,305 480,320 Q 475,335 455,325 Z" />
    <path d="M 540,460 Q 560,450 565,475 Q 545,490 535,470 Z" />
    <path d="M 380,360 Q 395,355 400,375 Q 380,385 375,370 Z" />
    <path d="M 490,260 Q 505,250 515,270 Q 495,285 485,270 Z" />
  </g>

  <!-- Hard Exudates (bright yellow lipid deposits in circinate rings) -->
  <g fill="url(#exudateGrad)" stroke="#f57f17" stroke-width="0.8" opacity="0.95">
    <ellipse cx="530" cy="390" rx="6" ry="4" /><ellipse cx="545" cy="395" rx="7" ry="5" />
    <ellipse cx="560" cy="410" rx="5" ry="6" /><ellipse cx="540" cy="415" rx="6" ry="4" />
    <ellipse cx="520" cy="405" rx="5" ry="4" />
    <circle cx="550" cy="380" r="3" /><circle cx="565" cy="425" r="3.5" />
  </g>

  <!-- Vignette -->
  <circle cx="400" cy="400" r="370" fill="none" stroke="#000000" stroke-width="30" />
</svg>
`);

// 4. Severe NPDR Fundus (DR Grade 3 - 4-quadrant hemorrhages, venous beading, cotton wool spots)
export const SEVERE_NPDR_FUNDUS_SVG = createSvgDataUri(`
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 800 800" width="800" height="800">
  <defs>
    <radialGradient id="bgGlow3" cx="50%" cy="50%" r="50%">
      <stop offset="0%" stop-color="#aa2805" />
      <stop offset="45%" stop-color="#721403" />
      <stop offset="80%" stop-color="#3d0801" />
      <stop offset="100%" stop-color="#000000" />
    </radialGradient>
    <radialGradient id="cottonWool" cx="50%" cy="50%" r="50%">
      <stop offset="0%" stop-color="#ffffff" />
      <stop offset="50%" stop-color="#e0e0e0" />
      <stop offset="100%" stop-color="transparent" />
    </radialGradient>
  </defs>

  <rect width="800" height="800" fill="#000000" />
  <circle cx="400" cy="400" r="370" fill="url(#bgGlow3)" />
  <ellipse cx="280" cy="390" rx="42" ry="48" fill="#ffb74d" opacity="0.95" />

  <!-- Venous beading & tortuous vessels -->
  <g stroke="#4f0801" stroke-width="8" fill="none" stroke-linecap="round" opacity="0.9">
    <path d="M 280,380 Q 320,330 360,300 Q 400,260 460,230 Q 530,200 630,240" />
    <path d="M 280,400 Q 330,480 380,520 Q 430,570 510,580 Q 590,580 660,510" />
  </g>

  <!-- Heavy 4-Quadrant Blot & Flame Hemorrhages -->
  <g fill="#2e0000" stroke="#700000" stroke-width="2">
    <path d="M 330,280 Q 370,270 380,305 Q 350,330 320,300 Z" />
    <path d="M 480,210 Q 520,190 535,230 Q 500,250 470,230 Z" />
    <path d="M 340,490 Q 380,480 395,515 Q 360,545 330,520 Z" />
    <path d="M 510,520 Q 555,500 570,540 Q 530,570 495,545 Z" />
    <path d="M 600,340 Q 640,325 650,365 Q 615,390 590,365 Z" />
    <path d="M 210,340 Q 240,330 245,360 Q 220,380 200,360 Z" />
  </g>

  <!-- Cotton Wool Spots (soft fluffy white retinal nerve fiber infarctions) -->
  <g fill="url(#cottonWool)" opacity="0.85">
    <ellipse cx="430" cy="270" rx="18" ry="12" />
    <ellipse cx="500" cy="330" rx="22" ry="14" />
    <ellipse cx="420" cy="460" rx="20" ry="15" />
    <ellipse cx="560" cy="470" rx="16" ry="12" />
  </g>

  <!-- Exudates -->
  <g fill="#ffee58" opacity="0.9">
    <circle cx="490" cy="380" r="4" /><circle cx="500" cy="390" r="5" />
    <circle cx="515" cy="385" r="4.5" /><circle cx="510" cy="405" r="4" />
  </g>

  <!-- Vignette -->
  <circle cx="400" cy="400" r="370" fill="none" stroke="#000000" stroke-width="30" />
</svg>
`);

// 5. PDR Fundus (DR Grade 4 - Neovascularization + Preretinal Hemorrhage + Severe Proliferation)
export const PDR_FUNDUS_SVG = createSvgDataUri(`
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 800 800" width="800" height="800">
  <defs>
    <radialGradient id="bgGlow4" cx="50%" cy="50%" r="50%">
      <stop offset="0%" stop-color="#991f03" />
      <stop offset="40%" stop-color="#661002" />
      <stop offset="80%" stop-color="#330601" />
      <stop offset="100%" stop-color="#000000" />
    </radialGradient>
  </defs>

  <rect width="800" height="800" fill="#000000" />
  <circle cx="400" cy="400" r="370" fill="url(#bgGlow4)" />
  <ellipse cx="280" cy="390" rx="42" ry="48" fill="#ffa726" opacity="0.9" />

  <!-- Neovascularization at Disc (NVD) - Frond of fragile new vessels -->
  <g stroke="#ff1744" stroke-width="2.5" fill="none" opacity="0.95">
    <path d="M 280,390 C 290,360 315,350 325,370 C 335,390 310,410 330,425" />
    <path d="M 280,390 C 270,360 250,355 240,375 C 235,395 260,410 250,430" />
    <path d="M 280,380 C 300,340 320,330 340,345 C 360,360 340,380 365,395" />
  </g>

  <!-- Large Pre-retinal / Vitreous Hemorrhage (boat-shaped gravity fluid level) -->
  <g fill="#210000" stroke="#520000" stroke-width="3" opacity="0.95">
    <path d="M 440,360 C 520,360 590,380 610,420 C 620,460 560,500 480,500 C 420,500 400,450 410,410 Z" />
    <path d="M 330,220 C 390,210 440,230 460,260 C 440,290 380,290 340,270 Z" />
  </g>

  <!-- Extensive Fibrovascular proliferation & exudation -->
  <g stroke="#fff9c4" stroke-width="2" fill="none" opacity="0.85">
    <path d="M 300,370 Q 360,330 440,350" />
    <path d="M 310,410 Q 380,450 460,430" />
  </g>

  <!-- Vignette -->
  <circle cx="400" cy="400" r="370" fill="none" stroke="#000000" stroke-width="30" />
</svg>
`);

// 6. Invalid Non-Fundus Image (Modern Automobile / Car Test Image)
export const INVALID_CAR_SVG = createSvgDataUri(`
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 800 600" width="800" height="600">
  <defs>
    <linearGradient id="skyGrad" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0%" stop-color="#1e293b" />
      <stop offset="60%" stop-color="#334155" />
      <stop offset="100%" stop-color="#64748b" />
    </linearGradient>
    <linearGradient id="carBody" x1="0" y1="0" x2="1" y2="0">
      <stop offset="0%" stop-color="#0284c7" />
      <stop offset="50%" stop-color="#38bdf8" />
      <stop offset="100%" stop-color="#0369a1" />
    </linearGradient>
  </defs>
  <rect width="800" height="600" fill="url(#skyGrad)" />
  <!-- Road -->
  <rect y="440" width="800" height="160" fill="#0f172a" />
  <line x1="0" y1="520" x2="800" y2="520" stroke="#f1f5f9" stroke-width="4" stroke-dasharray="30 20" />
  
  <!-- Car Silhouette -->
  <g transform="translate(160, 260)">
    <!-- Main Body -->
    <path d="M 40,110 C 60,70 120,40 180,30 L 320,30 C 370,30 420,70 460,100 L 490,115 C 500,120 510,135 500,150 L 20,150 C 10,140 15,120 40,110 Z" fill="url(#carBody)" />
    <!-- Cabin Windows -->
    <path d="M 175,38 L 315,38 C 350,38 385,65 410,95 L 140,95 C 150,70 165,48 175,38 Z" fill="#0f172a" opacity="0.85" />
    <line x1="270" y1="38" x2="270" y2="95" stroke="#38bdf8" stroke-width="4" />
    <!-- Wheels -->
    <circle cx="120" cy="150" r="42" fill="#020617" stroke="#94a3b8" stroke-width="8" />
    <circle cx="120" cy="150" r="16" fill="#cbd5e1" />
    <circle cx="390" cy="150" r="42" fill="#020617" stroke="#94a3b8" stroke-width="8" />
    <circle cx="390" cy="150" r="16" fill="#cbd5e1" />
    <!-- Headlight -->
    <polygon points="485,115 505,120 495,135 475,130" fill="#fef08a" />
  </g>
  <!-- Label badge indicating test image -->
  <rect x="20" y="20" width="220" height="34" rx="6" fill="rgba(0,0,0,0.6)" stroke="#ef4444" stroke-width="1.5" />
  <text x="32" y="42" fill="#f87171" font-family="sans-serif" font-size="14" font-weight="bold">NON-FUNDUS TEST ASSET</text>
</svg>
`);

// 7. Poor Quality Blurry Fundus Image
export const POOR_QUALITY_FUNDUS_SVG = createSvgDataUri(`
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 800 800" width="800" height="800">
  <defs>
    <filter id="heavyBlur" x="-30%" y="-30%" width="160%" height="160%">
      <feGaussianBlur stdDeviation="28" />
    </filter>
  </defs>
  <rect width="800" height="800" fill="#050505" />
  <!-- Extremely out of focus dark orange shape -->
  <circle cx="390" cy="410" r="320" fill="#421305" filter="url(#heavyBlur)" />
  <circle cx="330" cy="380" r="100" fill="#a03b08" filter="url(#heavyBlur)" opacity="0.6" />
  <!-- Overexposed flash artifact on top right -->
  <ellipse cx="580" cy="240" rx="90" ry="60" fill="#ffffff" filter="url(#heavyBlur)" opacity="0.7" />
  <!-- Dust artifact on lens -->
  <circle cx="320" cy="480" r="45" fill="#000000" opacity="0.5" filter="url(#heavyBlur)" />
  <!-- Severe dark vignette -->
  <circle cx="400" cy="400" r="380" fill="none" stroke="#000000" stroke-width="120" />
</svg>
`);

// Grad-CAM Heatmap Overlay Generator (Transparent SVG Heatmap)
export function getGradCamOverlaySvg(grade: number): string {
  if (grade === 0) {
    // Normal: very low diffused activation around optic nerve only
    return createSvgDataUri(`
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 800 800" width="800" height="800">
  <defs>
    <radialGradient id="h0" cx="35%" cy="48%" r="30%">
      <stop offset="0%" stop-color="#06b6d4" stop-opacity="0.3" />
      <stop offset="60%" stop-color="#3b82f6" stop-opacity="0.15" />
      <stop offset="100%" stop-color="transparent" stop-opacity="0" />
    </radialGradient>
  </defs>
  <circle cx="400" cy="400" r="370" fill="url(#h0)" />
</svg>`);
  }

  // Moderate/Severe/PDR: Concentrated hot spot activation over temporal arcades and lesions
  return createSvgDataUri(`
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 800 800" width="800" height="800">
  <defs>
    <!-- Primary Hot Spot -->
    <radialGradient id="hotSpot1" cx="62%" cy="46%" r="28%">
      <stop offset="0%" stop-color="#ef4444" stop-opacity="0.85" />
      <stop offset="25%" stop-color="#f59e0b" stop-opacity="0.75" />
      <stop offset="55%" stop-color="#10b981" stop-opacity="0.55" />
      <stop offset="80%" stop-color="#06b6d4" stop-opacity="0.3" />
      <stop offset="100%" stop-color="transparent" stop-opacity="0" />
    </radialGradient>
    <!-- Secondary Hot Spot -->
    <radialGradient id="hotSpot2" cx="54%" cy="33%" r="22%">
      <stop offset="0%" stop-color="#dc2626" stop-opacity="0.8" />
      <stop offset="35%" stop-color="#eab308" stop-opacity="0.65" />
      <stop offset="70%" stop-color="#06b6d4" stop-opacity="0.35" />
      <stop offset="100%" stop-color="transparent" stop-opacity="0" />
    </radialGradient>
    <!-- Inferior Spot -->
    <radialGradient id="hotSpot3" cx="58%" cy="63%" r="24%">
      <stop offset="0%" stop-color="#f97316" stop-opacity="0.75" />
      <stop offset="40%" stop-color="#eab308" stop-opacity="0.55" />
      <stop offset="75%" stop-color="#3b82f6" stop-opacity="0.25" />
      <stop offset="100%" stop-color="transparent" stop-opacity="0" />
    </radialGradient>
  </defs>
  <rect width="800" height="800" fill="transparent" />
  <circle cx="400" cy="400" r="370" fill="url(#hotSpot1)" />
  <circle cx="400" cy="400" r="370" fill="url(#hotSpot2)" />
  <circle cx="400" cy="400" r="370" fill="url(#hotSpot3)" />
</svg>`);
}

// Lesion Mask Overlay Generator
export function getLesionMaskOverlaySvg(grade: number): string {
  if (grade === 0) {
    return createSvgDataUri(`<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 800 800" width="800" height="800"></svg>`);
  }

  return createSvgDataUri(`
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 800 800" width="800" height="800">
  <!-- Microaneurysms (Red) -->
  <g fill="#ff1744" stroke="#ffffff" stroke-width="1.5">
    <circle cx="410" cy="330" r="6" /><circle cx="440" cy="310" r="7" />
    <circle cx="390" cy="270" r="5" /><circle cx="520" cy="340" r="6" />
    <circle cx="560" cy="370" r="7" /><circle cx="510" cy="490" r="6" />
    <circle cx="370" cy="480" r="5.5" /><circle cx="430" cy="520" r="6.5" />
  </g>

  <!-- Hemorrhages (Crimson polygon contours) -->
  <g fill="rgba(220,38,38,0.7)" stroke="#ff4d4d" stroke-width="2">
    <path d="M 455,305 Q 478,300 485,322 Q 478,340 450,328 Z" />
    <path d="M 535,455 Q 565,445 570,478 Q 545,498 530,475 Z" />
    <path d="M 375,355 Q 400,350 405,378 Q 380,390 370,372 Z" />
  </g>

  <!-- Hard Exudates (Yellow polygon contours) -->
  <g fill="rgba(255,235,59,0.85)" stroke="#fff59d" stroke-width="1.5">
    <ellipse cx="530" cy="390" rx="9" ry="6" />
    <ellipse cx="548" cy="395" rx="10" ry="7" />
    <ellipse cx="562" cy="412" rx="8" ry="9" />
    <ellipse cx="540" cy="417" rx="9" ry="6" />
    <ellipse cx="520" cy="405" rx="7" ry="6" />
  </g>
</svg>`);
}
