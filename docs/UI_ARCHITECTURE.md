# RuralDR-XAI Frontend Architecture

## Overview

The RuralDR-XAI web UI is a premium, immersive 3D medical-AI platform built around a React + Vite + TypeScript frontend that integrates with an existing Python ML pipeline through a FastAPI adapter layer.

```
┌─────────────────────────────────────────────────────┐
│         React Frontend (Vite + TypeScript)          │
│  - 3D Retina Visualization (Three.js + R3F)        │
│  - Landing Page                                      │
│  - Dashboard & Workflows                             │
│  - Image Upload & Processing                         │
│  - Results & Report Visualization                    │
└───────────────────────┬─────────────────────────────┘
                        │
                        ↓ HTTP/REST
┌─────────────────────────────────────────────────────┐
│              FastAPI Adapter Layer                   │
│  - /api/upload (image upload & processing)          │
│  - /api/process (pipeline orchestration)            │
│  - /api/results (retrieve results)                  │
│  - /api/static (serve processed images)             │
└───────────────────────┬─────────────────────────────┘
                        │
                        ↓ (imports & direct calls)
┌─────────────────────────────────────────────────────┐
│    Existing Python ML Pipeline (READ-ONLY)          │
│  - ExplainableScreeningPipeline                     │
│  - ImageQualityGate                                  │
│  - DRClassifier                                      │
│  - GradCAM (XAI)                                     │
│  - LesionSegmenter                                   │
│  - AdaptiveEnhancer                                  │
└─────────────────────────────────────────────────────┘
```

## Frontend Architecture

### Technology Stack

- **Framework**: React 18+ with TypeScript
- **Build Tool**: Vite (fast HMR, optimized builds)
- **3D Rendering**: Three.js + React Three Fiber (@react-three/fiber)
- **3D Utilities**: @react-three/drei (pre-built 3D components)
- **State Management**: React Context API + hooks
- **HTTP Client**: Axios or Fetch API
- **Styling**: Tailwind CSS + CSS Modules
- **Animation**: Framer Motion (optional, for UI animations)
- **Code Quality**: ESLint, Prettier, TypeScript strict mode

### Directory Structure

```
frontend/
├── src/
│   ├── components/
│   │   ├── 3d/
│   │   │   ├── RetinaScene.tsx          # Main 3D retina component
│   │   │   ├── RetinaGeometry.tsx       # Retina mesh generation
│   │   │   ├── RetinaMaterial.tsx       # Custom material with glow
│   │   │   ├── VascularSystem.tsx       # Blood vessel visualization
│   │   │   ├── ParticleSystem.tsx       # Ambient particles
│   │   │   ├── RetinaLighting.tsx       # Lighting setup
│   │   │   └── RetinaCamera.tsx         # Camera controls
│   │   │
│   │   ├── layout/
│   │   │   ├── Navbar.tsx               # Navigation header
│   │   │   ├── Section.tsx              # Reusable section container
│   │   │   ├── Footer.tsx               # Footer
│   │   │   └── AnimatedContainer.tsx    # Staggered reveal animations
│   │   │
│   │   ├── ui/
│   │   │   ├── GlassCard.tsx            # Glassmorphism card
│   │   │   ├── GlowBorder.tsx           # Animated glowing border
│   │   │   ├── Button.tsx               # Button variants
│   │   │   ├── Badge.tsx                # Status badges
│   │   │   ├── Spinner.tsx              # Loading indicator
│   │   │   ├── Modal.tsx                # Modal dialog
│   │   │   └── Tooltip.tsx              # Hover tooltips
│   │   │
│   │   ├── medical/
│   │   │   ├── FundusViewer.tsx         # Fundus image viewer with zoom/pan
│   │   │   ├── ResultsCard.tsx          # DR grade & confidence display
│   │   │   ├── EvidencePanel.tsx        # Lesion evidence summary
│   │   │   ├── PipelineTimeline.tsx     # Processing steps visualization
│   │   │   ├── ReportGenerator.tsx      # Report display/export
│   │   │   └── XAIVisualization.tsx     # Grad-CAM overlay viewer
│   │   │
│   │   ├── pages/
│   │   │   ├── LandingPage.tsx
│   │   │   ├── DashboardPage.tsx
│   │   │   ├── UploadPage.tsx
│   │   │   ├── ProcessingPage.tsx
│   │   │   ├── ResultsPage.tsx
│   │   │   └── NotFoundPage.tsx
│   │   │
│   │   └── forms/
│   │       └── ImageUploadForm.tsx
│   │
│   ├── hooks/
│   │   ├── useApi.ts                   # API call hook
│   │   ├── useProcessing.ts            # Processing state management
│   │   ├── useResults.ts               # Results caching
│   │   └── useResponsive.ts            # Responsive utilities
│   │
│   ├── services/
│   │   ├── api.ts                      # Axios/Fetch API client
│   │   ├── processing.ts               # Processing workflow
│   │   ├── storage.ts                  # Local storage utilities
│   │   └── errors.ts                   # Error handling
│   │
│   ├── types/
│   │   ├── api.ts                      # API response types
│   │   ├── processing.ts               # Processing state types
│   │   └── ui.ts                       # UI component types
│   │
│   ├── styles/
│   │   ├── globals.css                 # Global styles
│   │   ├── theme.css                   # Design system (colors, spacing)
│   │   ├── animations.css              # Keyframe animations
│   │   └── 3d.css                      # 3D-specific styles
│   │
│   ├── utils/
│   │   ├── math.ts                     # Math utilities (interpolation, etc)
│   │   ├── format.ts                   # Data formatting
│   │   └── validation.ts               # Input validation
│   │
│   ├── App.tsx
│   ├── main.tsx
│   └── index.css
│
├── public/
│   ├── models/                         # 3D models if needed
│   └── images/                         # Static assets
│
├── index.html
├── vite.config.ts
├── tsconfig.json
├── tailwind.config.js
└── package.json
```

### Component Architecture

#### 3D Rendering

**RetinaScene** is the master 3D component:
- Manages Three.js scene, camera, and renderer
- Handles mouse interaction (parallax, rotation)
- Manages scroll-based camera animation
- Orchestrates child 3D components:
  - RetinaGeometry: Sphere-based retina mesh with procedural bumps
  - VascularSystem: Line-based blood vessel network
  - ParticleSystem: Floating particle effects
  - RetinaLighting: Directional + point lights with subtle glow

**Performance considerations:**
- Uses React Three Fiber `useFrame()` sparingly
- Offloads heavy computations to shaders (GLSL)
- Implements LOD (level of detail) for high-poly geometry
- Prefers instanced rendering for particles
- Uses canvas-based rendering with fallback to canvas 2D

#### UI Components

**Glassmorphism System:**
- GlassCard: Base card with backdrop blur, semi-transparency
- GlowBorder: Animated border glow with CSS animations
- Layered depth using z-index and shadow hierarchy

**Medical Components:**
- FundusViewer: Image viewer with OpenSeadragon or custom WebGL viewer
  - Supports zoom, pan, reset
  - Overlay rendering for Grad-CAM and segmentation masks
  - Smooth interpolation during pan/zoom
  
- ResultsCard: Displays DR grade, severity, confidence
  - Animated number reveal
  - Color-coded severity level
  - Real data only (no placeholder values)

- EvidencePanel: Lesion detection results
  - Lists detected lesion types with confidence
  - Shows region counts and area percentages
  - Links to segmentation masks

- XAIVisualization: Grad-CAM overlay
  - Interactive opacity slider
  - Layer toggle
  - Colormap selection (heatmap, viridis, etc.)
  - Fullscreen mode

#### State Management

Uses React Context + Hooks:
- `ProcessingContext`: Current processing job state
- `ResultsContext`: Cached results from API
- `UIContext`: UI theme, responsiveness, sidebar state
- `useApi()`: Generic hook for API calls with loading/error states
- `useProcessing()`: Manages image upload → processing → results workflow

### Design System

#### Typography

```css
/* Primary: Scientific sans-serif */
--font-primary: 'Inter', system-ui, sans-serif;

/* Mono: For technical information */
--font-mono: 'IBM Plex Mono', monospace;

/* Scale: 12px base → golden ratio */
--text-xs: 0.75rem;      /* 12px */
--text-sm: 0.875rem;     /* 14px */
--text-base: 1rem;       /* 16px */
--text-lg: 1.125rem;     /* 18px */
--text-xl: 1.5rem;       /* 24px */
--text-2xl: 2rem;        /* 32px */
--text-3xl: 2.5rem;      /* 40px */
--text-4xl: 3.5rem;      /* 56px */
```

#### Color Palette

```
Background:
  --bg-primary: #0a0e27       /* Deep navy */
  --bg-secondary: #1a1f3a     /* Slightly lighter navy */
  --bg-tertiary: #2a2f4a      /* Card background */

Text:
  --text-primary: #f0f4ff     /* Near-white */
  --text-secondary: #a0aac0   /* Muted gray */
  --text-tertiary: #808a9f    /* Dimmer gray */

Accents (Medical + Scientific):
  --accent-primary: #0096ff   /* Clinical blue */
  --accent-secondary: #00d9ff /* Cyan (oxygen, vitality) */
  --accent-medical: #ff4757   /* Medical red (critical) */
  --accent-warning: #ffa502   /* Warning orange */
  --accent-success: #2ed573   /* Success green */

Glassmorphism:
  --glass-bg: rgba(255, 255, 255, 0.05)
  --glass-border: rgba(255, 255, 255, 0.1)
```

#### Spacing Scale

```
0, 2px, 4px, 8px, 12px, 16px, 24px, 32px, 48px, 64px, 96px
(Multiples of 4px, with 2px and 12px as exceptions)
```

#### Border Radius

```
0px, 4px, 8px, 12px, 16px, 999px (pill)
```

## API Integration

### Backend Endpoints (FastAPI)

The frontend communicates with the backend through these REST endpoints:

#### `/api/health` (GET)
Health check endpoint.

**Response:**
```json
{ "status": "ok", "backend": "available" }
```

#### `/api/upload` (POST)
Upload a fundus image file.

**Request:**
- Multipart form data with `file` (image file)
- Optional: `case_id` (client-side identifier)

**Response:**
```json
{
  "upload_id": "uuid",
  "filename": "original_filename.jpg",
  "size_bytes": 2048576,
  "message": "Image uploaded successfully"
}
```

#### `/api/process` (POST)
Trigger the full explainability pipeline on an uploaded image.

**Request:**
```json
{
  "upload_id": "uuid",
  "run_segmentation": true
}
```

**Response:**
```json
{
  "job_id": "uuid",
  "status": "processing",
  "message": "Pipeline started"
}
```

#### `/api/status` (GET)
Poll processing job status.

**Query:** `?job_id=uuid`

**Response:**
```json
{
  "job_id": "uuid",
  "status": "completed|processing|failed",
  "progress_pct": 45,
  "current_step": "Running Grad-CAM",
  "error": null
}
```

#### `/api/results` (GET)
Retrieve completed results.

**Query:** `?job_id=uuid`

**Response:**
```json
{
  "case_id": "uuid",
  "quality": {
    "status": "GRADEABLE",
    "score": 0.87,
    "message": "Image quality acceptable"
  },
  "classification": {
    "dr_grade": 2,
    "severity": "Moderate Non-Proliferative",
    "confidence": 0.92,
    "class_probabilities": [0.01, 0.05, 0.92, 0.02, 0.00],
    "is_referable": true
  },
  "gradcam": {
    "overlay_url": "/api/static/results/uuid/gradcam_overlay.png",
    "activation_coverage": 0.65,
    "peak_intensity": 0.95,
    "quality_flags": []
  },
  "segmentation": {
    "lesions": [
      {
        "type": "exudate",
        "detected": true,
        "num_regions": 3,
        "area_pct": 2.3,
        "confidence": 0.78,
        "mask_url": "/api/static/results/uuid/exudate_mask.png"
      }
    ]
  },
  "processing_times": {
    "quality_gate_ms": 150,
    "classification_ms": 200,
    "gradcam_ms": 180,
    "segmentation_ms": 450,
    "total_ms": 980
  },
  "evidence_report": { /* Full evidence report */ }
}
```

#### `/api/static/results/{result_id}/{filename}` (GET)
Retrieve generated images (Grad-CAM overlays, segmentation masks, etc.)

### Error Handling

All endpoints return error responses in this format:

```json
{
  "error": "error_code",
  "message": "Human-readable error description",
  "details": {}
}
```

Common errors:
- `invalid_image`: Image format not supported or corrupted
- `processing_failed`: Pipeline error (see details for specifics)
- `file_too_large`: Image exceeds size limit
- `job_not_found`: Job ID does not exist or expired
- `backend_unavailable`: Python backend not responding

## Data Flow

### Image Processing Workflow

```
User uploads image
  ↓
Frontend: POST /api/upload
  ↓
Backend: Validate image, save to temp storage
  ↓
Frontend: POST /api/process (with upload_id)
  ↓
Backend: Queue job, start pipeline
  ↓
Frontend: Poll /api/status (every 1-2s)
  ↓
User sees: "Processing... [step name]"
  ↓
Backend: Complete pipeline
  ↓
Frontend: GET /api/results (final status = "completed")
  ↓
Frontend: Display results with images from /api/static/
  ↓
User reviews: Quality, Classification, Grad-CAM, Segmentation
```

### Frontend State Management

**Processing State:**
```typescript
interface ProcessingState {
  status: 'idle' | 'uploading' | 'processing' | 'completed' | 'error';
  currentStep?: string;
  progressPct?: number;
  uploadId?: string;
  jobId?: string;
  error?: string;
  results?: ProcessingResults;
}
```

**Results are cached in:**
- React Context (in-memory during session)
- Local Storage (persist across page reloads)

## Responsive Design Strategy

### Breakpoints

```
Mobile:   < 640px (phones)
Tablet:   640px - 1024px
Desktop:  > 1024px
```

### Adaptive Rendering

- **Mobile**: 3D retina disabled or simplified (2D version)
- **Tablet**: 3D retina enabled, reduced particle count
- **Desktop**: Full 3D retina with all effects

### Image Viewer

- Mobile: Full-screen single-image view, thumb controls
- Tablet: Side-by-side comparison with toggles
- Desktop: Overlay-based comparison with opacity slider

## Accessibility Strategy

### Keyboard Navigation

- Tab-navigate through all interactive elements
- Enter/Space to activate buttons
- Arrow keys to adjust sliders
- Escape to close modals
- `?` to show keyboard shortcuts

### Screen Reader Support

- Semantic HTML (nav, main, section, article)
- ARIA labels for 3D elements
- Alt text for all medical images
- Skip links to main content

### Reduced Motion

Respect `prefers-reduced-motion`:
```css
@media (prefers-reduced-motion: reduce) {
  * {
    animation: none !important;
    transition: none !important;
  }
  /* Disable 3D retina rotation, but keep static 3D scene */
}
```

### Color Contrast

- WCAG AA minimum (4.5:1 for text)
- Medical UI uses color + symbols (not color-only indicators)
- Red/green colorblind-friendly palette

## Performance Optimization Strategy

### Code Splitting

- Lazy-load 3D scene (not needed for mobile)
- Code-split pages with React.lazy()
- Tree-shake unused 3D libraries

### Asset Optimization

- Compress images (Grad-CAM, segmentation masks) with sharp/ImageMagick
- Use WebP with PNG fallback
- Lazy-load off-screen images

### 3D Rendering

- Use WebGL compression (DXT, etc.)
- Implement frustum culling
- Use InstancedMesh for particles
- Disable vsync for non-animation frames
- Canvas resolution scaling (DPR detection)

### Caching

- HTTP caching headers for static assets (1 year for versioned files)
- Service Worker for offline fallback
- Result caching (images served from API with far-future expires)

## Browser Support

- **Primary**: Chrome 90+, Edge 90+, Firefox 88+, Safari 14+
- **Fallback**: Canvas 2D rendering if WebGL unavailable
- **Graceful degradation**: 3D retina → static image if needed

## Development Workflow

### Setup

```bash
cd frontend
npm install
npm run dev  # Vite dev server on localhost:5173
npm run build
npm run preview
```

### Testing

- Unit tests: Vitest + React Testing Library
- E2E tests: Playwright
- Visual regression: Percy or similar
- Performance: Lighthouse CI

### Git Workflow

```
main (production)
├── surya (UI/UX work)
│   ├── feat/landing-3d-retina
│   ├── feat/medical-image-viewer
│   ├── feat/results-visualization
│   └── ...
```

---

**Last Updated**: 2026-09-01  
**Status**: Architecture definition pre-implementation
