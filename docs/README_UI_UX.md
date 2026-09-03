# RuralDR-XAI: Web UI/UX Platform

Premium, immersive 3D medical-AI platform for diabetic retinopathy screening in rural healthcare settings.

## 🎯 Status: Phase 2 ✅ Complete

**Foundation Build Complete** — React + Vite + TypeScript frontend with FastAPI backend adapter, ready for Phase 3 (3D retina visualization).

## 📋 Quick Navigation

### For Getting Started
- **[QUICK_START.md](QUICK_START.md)** - Get running in 5 minutes
- **[frontend/README.md](frontend/README.md)** - Frontend development guide

### For Understanding Architecture
- **[IMPLEMENTATION_OVERVIEW.md](IMPLEMENTATION_OVERVIEW.md)** - Complete system overview
- **[docs/UI_ARCHITECTURE.md](docs/UI_ARCHITECTURE.md)** - Detailed architecture (500+ lines)
- **[docs/UI_INTEGRATION.md](docs/UI_INTEGRATION.md)** - API integration patterns

### For Build Details
- **[STAGE_2_COMPLETION.md](STAGE_2_COMPLETION.md)** - Build completion report
- **[frontend/](frontend/)** - React source code
- **[src/api/main.py](src/api/main.py)** - FastAPI adapter

---

## 🚀 Quick Start (5 Minutes)

### Prerequisites
- Python 3.8+
- Node.js 18+

### Run Application

**Terminal 1: Backend**
```bash
python -m uvicorn src.api.main:app --reload
```

**Terminal 2: Frontend**
```bash
cd frontend
npm install
npm run dev
```

**Open Browser**: http://localhost:5173

### Test Workflow
1. Click "Start Screening"
2. Upload a fundus image (JPEG, PNG, BMP, or TIFF)
3. Watch progress bar (0-100%)
4. View results with DR grade, confidence, Grad-CAM, lesion detection

---

## 📦 What's Included

### ✅ Frontend (React + Vite + TypeScript)

**Location**: `frontend/`

- Landing page with features overview
- Image upload workflow with preview
- Results visualization with:
  - DR classification (0-4 severity)
  - Confidence scores
  - Grad-CAM visualization
  - Lesion segmentation display
  - Evidence report

**Components**:
- Reusable UI components (Button, GlassCard, Spinner)
- Page templates (Landing, Upload, Results)
- Custom hooks for state management
- Axios API client with full TypeScript types

### ✅ Backend Adapter (FastAPI)

**Location**: `src/api/main.py`

- Image upload endpoint
- Pipeline processing orchestration
- Status polling support
- Result retrieval with image serving

**Endpoints**:
- `GET /api/health` - Health check
- `POST /api/upload` - Upload image
- `POST /api/process` - Start processing
- `GET /api/status` - Poll progress
- `GET /api/results` - Get results
- `GET /api/static/results/...` - Serve images

### ✅ Design System

**Colors**: Medical-focused palette (clinical blue, cyan, warning orange, critical red)

**Typography**: Inter (primary) + IBM Plex Mono (code)

**Components**: Glassmorphism cards, smooth animations, gradient text

### ✅ Documentation

- UI Architecture (500+ lines)
- API Integration Guide (400+ lines)
- Frontend Development Guide (300+ lines)
- Quick Start Guide (200+ lines)
- Build Completion Report
- This Overview

---

## 🏗️ Architecture

### System Flow

```
User Interface (React)
        ↓
  Vite Dev Server
        ↓
  HTTP/REST API
        ↓
  FastAPI Adapter
        ↓
  Existing Python ML Pipeline
        ↓
  Results (DR grade, confidence, Grad-CAM, lesion masks)
```

### Key Principles

**1. No ML Code Duplication**
- FastAPI calls existing Python functions directly
- Results match CLI exactly

**2. Thin Adapter Layer**
- Only handles HTTP, JSON serialization, job tracking
- All ML logic remains in original pipeline

**3. Type-Safe Integration**
- TypeScript frontend with full API types
- Pydantic models in FastAPI
- Zero `any` types

**4. Incremental Development**
- Phase 2: Foundation ✅
- Phase 3: 3D Retina (upcoming)
- Phase 4: Advanced features
- Phase 5: Production deployment

---

## 📁 Project Structure

```
RuralDR-XAI/
├── frontend/                    # React + Vite application
│   ├── src/
│   │   ├── components/          # UI components
│   │   ├── pages/               # Page components (Landing, Upload, Results)
│   │   ├── hooks/               # useProcessing hook
│   │   ├── services/            # API client
│   │   ├── types/               # TypeScript types
│   │   ├── utils/               # Utilities
│   │   ├── App.tsx              # Router setup
│   │   ├── main.tsx             # Entry point
│   │   └── index.css            # Global styles
│   ├── vite.config.ts
│   ├── tsconfig.json
│   ├── tailwind.config.js
│   ├── package.json
│   └── README.md
│
├── src/
│   ├── api/
│   │   ├── main.py              # FastAPI adapter (complete)
│   │   └── __init__.py
│   └── [existing ML modules]
│
├── docs/
│   ├── UI_ARCHITECTURE.md       # Complete architecture
│   └── UI_INTEGRATION.md        # API patterns
│
├── QUICK_START.md               # 5-min setup guide
├── IMPLEMENTATION_OVERVIEW.md   # System overview
├── STAGE_2_COMPLETION.md        # Build report
└── README.md                     # This file
```

---

## 🎨 Design System

### Colors
- **Primary**: #0a0e27 (deep navy)
- **Accent**: #0096ff (clinical blue)
- **Secondary**: #00d9ff (cyan)
- **Medical**: #ff4757 (critical red)
- **Success**: #2ed573 (green)

### Typography
- **Primary Font**: Inter (sans-serif)
- **Mono Font**: IBM Plex Mono
- **Scale**: 12px, 14px, 16px, 18px, 24px, 32px, 40px, 56px

### Components
- Glass cards with backdrop blur
- Smooth animations (fade, slide, scale)
- Interactive hover states
- Gradient accents

---

## 📊 API Response Example

```json
{
  "case_id": "8dafa62f-9322-...",
  "quality": {
    "status": "GRADEABLE",
    "score": 0.87
  },
  "classification": {
    "dr_grade": 2,
    "severity": "Moderate Non-Proliferative",
    "confidence": 0.92,
    "class_probabilities": [0.01, 0.05, 0.92, 0.02, 0.00],
    "is_referable": true
  },
  "gradcam": {
    "overlay_url": "/api/static/results/{job_id}/gradcam_overlay.png",
    "activation_coverage": 0.65,
    "peak_intensity": 0.95
  },
  "segmentation": {
    "lesions": [
      {
        "type": "exudate",
        "detected": true,
        "area_pct": 2.3,
        "confidence": 0.78,
        "mask_url": "/api/static/results/{job_id}/exudate_mask.png"
      }
    ]
  }
}
```

---

## 🔧 Development

### Frontend Development
```bash
cd frontend
npm install          # Install dependencies
npm run dev          # Start dev server (http://localhost:5173)
npm run type-check   # TypeScript checking
npm run build        # Production build
npm run format       # Format code
```

### Backend Development
```bash
# Start with auto-reload
python -m uvicorn src.api.main:app --reload --host 0.0.0.0 --port 8000

# Verify health
curl http://localhost:8000/api/health
```

---

## 🧪 Testing the Workflow

### Manual Testing
1. Start backend + frontend
2. Navigate to http://localhost:5173
3. Click "Start Screening"
4. Upload a fundus image
5. Watch processing progress
6. Review results page

### API Testing
```bash
# Health check
curl http://localhost:8000/api/health

# Upload (requires actual image file)
curl -F "file=@image.jpg" http://localhost:8000/api/upload

# Check results
curl "http://localhost:8000/api/results?job_id=<job_id>"
```

---

## 🚧 Known Limitations (Phase 2)

**Intentional (to be addressed in later phases)**:

- ❌ No 3D retina visualization (Phase 3)
- ❌ No persistent database (Phase 5)
- ❌ No user authentication (Phase 4)
- ❌ No production deployment (Phase 5)
- ❌ No advanced testing (Phase 5)

**Design rationale**: Build solid foundation first, add complexity incrementally.

---

## 📈 Roadmap

### Phase 2 ✅ Complete
- [x] React + TypeScript foundation
- [x] Tailwind design system
- [x] Landing, upload, results pages
- [x] FastAPI adapter
- [x] Full integration

### Phase 3 🔄 Next: 3D Retina Visualization
- [ ] Three.js + React Three Fiber integration
- [ ] RetinaScene component (3D retina mesh)
- [ ] Vascular system visualization
- [ ] Particle effects
- [ ] Interactive controls (parallax, scroll)
- [ ] Integrate into landing page

### Phase 4: Advanced Features
- [ ] Dark/light theme
- [ ] Report generation/export
- [ ] Image comparison viewer
- [ ] Processing history
- [ ] User preferences

### Phase 5: Production Deployment
- [ ] Database integration (PostgreSQL)
- [ ] Authentication (OAuth2/JWT)
- [ ] User accounts and history
- [ ] Email notifications
- [ ] Docker containerization
- [ ] Kubernetes deployment
- [ ] SSL/TLS certificates
- [ ] CDN for assets
- [ ] Performance optimization
- [ ] Comprehensive logging

---

## 💡 How to Extend

### Add a New Page
```tsx
// 1. Create component
// frontend/src/pages/MyPage.tsx
export default function MyPage() { ... }

// 2. Add route
// frontend/src/App.tsx
<Route path="/mypage" element={<MyPage />} />

// 3. Link from navigation
<Link to="/mypage">My Page</Link>
```

### Add a New Component
```tsx
// frontend/src/components/ui/MyComponent.tsx
interface MyComponentProps { ... }
export const MyComponent: React.FC<MyComponentProps> = (props) => {
  return <div>...</div>;
};
```

### Add an API Endpoint
```python
# src/api/main.py
@app.get("/api/myendpoint")
async def my_endpoint():
    return { "data": "value" }

# frontend/src/services/api.ts
export async function myEndpoint() {
  const response = await apiClient.get("/api/myendpoint");
  return response.data;
}

# frontend/src/types/api.ts
export interface MyResponse { data: string; }
```

---

## 🐛 Troubleshooting

### Backend won't start
```bash
# Check Python version
python --version  # Should be 3.8+

# Check dependencies
pip install fastapi uvicorn pydantic

# Check ML pipeline
python -c "from src.ai.explainability.pipeline import ExplainableScreeningPipeline"
```

### Frontend won't start
```bash
cd frontend
rm -rf node_modules
rm package-lock.json
npm install
npm run dev
```

### API connection fails
- Verify backend is running on :8000
- Check CORS settings in src/api/main.py
- Verify frontend .env has correct API_URL
- Check browser Network tab for actual error

### Image upload hangs
- Check file format (JPEG, PNG, BMP, TIFF)
- Check file size (max 50MB)
- Check backend logs for errors
- Try smaller test image

See **[QUICK_START.md](QUICK_START.md)** for more troubleshooting.

---

## 📚 Documentation

| Document | Purpose | Length |
|----------|---------|--------|
| [QUICK_START.md](QUICK_START.md) | Get started in 5 min | 200 lines |
| [IMPLEMENTATION_OVERVIEW.md](IMPLEMENTATION_OVERVIEW.md) | Complete system overview | 600 lines |
| [docs/UI_ARCHITECTURE.md](docs/UI_ARCHITECTURE.md) | Detailed architecture | 500 lines |
| [docs/UI_INTEGRATION.md](docs/UI_INTEGRATION.md) | API integration patterns | 400 lines |
| [frontend/README.md](frontend/README.md) | Frontend guide | 300 lines |
| [STAGE_2_COMPLETION.md](STAGE_2_COMPLETION.md) | Build completion report | 200 lines |

---

## 🤝 Support

**Quick Help**:
1. Check [QUICK_START.md](QUICK_START.md) Troubleshooting section
2. Review [frontend/README.md](frontend/README.md) for setup issues
3. Check browser console (F12) for errors
4. Check backend terminal output
5. Review API response in Network tab

**For Complex Issues**:
1. Read [docs/UI_ARCHITECTURE.md](docs/UI_ARCHITECTURE.md)
2. Review [docs/UI_INTEGRATION.md](docs/UI_INTEGRATION.md)
3. Check source code comments
4. Review test flow in [IMPLEMENTATION_OVERVIEW.md](IMPLEMENTATION_OVERVIEW.md)

---

## 📄 License

All UI/UX code follows the existing RuralDR-XAI project license.

---

## ✨ Summary

**Phase 2 Deliverables**:
- ✅ Production-quality React frontend
- ✅ FastAPI backend adapter
- ✅ Complete type safety
- ✅ Premium design system
- ✅ Full integration
- ✅ Comprehensive documentation

**Ready For**:
- Phase 3: 3D retina visualization
- Phase 4: Advanced features
- Phase 5: Production deployment

**Next Step**: See [QUICK_START.md](QUICK_START.md) to run the application.

---

**Status**: Phase 2 ✅ Complete  
**Framework**: React 18 + Vite + TypeScript  
**Backend**: FastAPI (Python)  
**Design**: Tailwind CSS + Medical Focus  
**Ready for**: Phase 3 Development  

**Last Updated**: 2026-09-01  
**Contact**: See project documentation
