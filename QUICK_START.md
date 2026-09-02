# 🚀 RuralDR-XAI Quick Start Guide

Get the complete UI/UX system running in 5 minutes.

## Prerequisites

- Python 3.8+ (for backend)
- Node.js 18+ (for frontend)
- A modern web browser

## Installation & Setup

### Step 1: Install Backend Dependencies

```bash
# From project root
pip install fastapi uvicorn pydantic

# Verify existing ML pipeline is available
python -c "from src.ai.explainability.pipeline import ExplainableScreeningPipeline; print('✓ ML pipeline available')"
```

### Step 2: Install Frontend Dependencies

```bash
cd frontend
npm install
```

This installs:
- React 18
- Vite
- TypeScript
- Tailwind CSS
- Axios
- React Router

### Step 3: Create Frontend Environment

```bash
cd frontend
cp .env.example .env
```

The `.env` file should have:
```
VITE_API_URL=http://localhost:8000
```

## Running the Application

### Terminal 1: Start FastAPI Backend

```bash
# From project root
python -m uvicorn src.api.main:app --reload --host 0.0.0.0 --port 8000
```

You should see:
```
Uvicorn running on http://0.0.0.0:8000
```

**Verify it works**:
```bash
curl http://localhost:8000/api/health
# Should return: {"status":"ok","backend":"available",...}
```

### Terminal 2: Start Frontend Development Server

```bash
# From project root
cd frontend
npm run dev
```

You should see:
```
VITE v5.0.0  ready in 123 ms

➜  Local:   http://localhost:5173/
```

## Testing the Complete Flow

### 1. Open Application

Navigate to: **http://localhost:5173**

You should see the RuralDR-XAI landing page with:
- Navigation bar with "Start Screening" button
- Hero section with title and features
- Feature cards describing the platform

### 2. Upload an Image

1. Click "Start Screening" or navigate to `/upload`
2. Click "Select Image" button
3. Choose a fundus image file (JPEG, PNG, TIFF, or BMP)
4. Preview appears showing the selected image
5. Click "Start Analysis"

### 3. Watch Processing

You'll see a progress bar with:
- Real-time progress percentage (0-100%)
- Current processing step
  - "Loading model..."
  - "Processing image..."
  - "Running Grad-CAM..."
  - "Running lesion segmentation..."
  - "Generating report..."

This connects to the FastAPI backend which runs the actual Python ML pipeline.

### 4. View Results

When complete, you're redirected to the Results page showing:
- **DR Grade**: 0-4 (severity level)
- **Severity**: Text description
- **Confidence**: AI prediction confidence
- **Image Quality**: Quality assessment
- **Class Distribution**: Graph of all severity probabilities
- **Grad-CAM**: Model attention visualization (if available)
- **Lesion Detection**: Detected retinal features with confidence scores

## API Endpoints

All available at `http://localhost:8000/api`:

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/health` | GET | Health check |
| `/upload` | POST | Upload image |
| `/process` | POST | Start pipeline |
| `/status?job_id=` | GET | Poll progress |
| `/results?job_id=` | GET | Get results |
| `/static/results/{job_id}/{file}` | GET | Get result images |

**Test an endpoint**:
```bash
curl http://localhost:8000/api/health
```

## File Structure Reference

```
RuralDR-XAI/
├── frontend/                    # React + Vite application
│   ├── src/
│   │   ├── components/          # React components
│   │   ├── pages/               # Page components
│   │   ├── hooks/               # Custom hooks
│   │   ├── services/            # API client
│   │   ├── types/               # TypeScript types
│   │   ├── utils/               # Utility functions
│   │   ├── App.tsx              # Main app
│   │   └── main.tsx             # Entry point
│   ├── vite.config.ts
│   ├── package.json
│   └── README.md
│
├── src/
│   ├── api/
│   │   └── main.py              # FastAPI adapter
│   └── [existing ML code]       # READ-ONLY
│
└── docs/
    ├── UI_ARCHITECTURE.md
    └── UI_INTEGRATION.md
```

## Development Workflows

### Making UI Changes

1. Edit files in `frontend/src/`
2. Vite automatically reloads (HMR)
3. Check browser console for errors

### Adding a New Component

```bash
# Create new component file
touch frontend/src/components/ui/MyComponent.tsx
```

Example template:
```tsx
import React from 'react';

interface MyComponentProps {
  // Props here
}

export const MyComponent: React.FC<MyComponentProps> = ({ }) => {
  return (
    <div className="p-4">
      {/* Component content */}
    </div>
  );
};
```

### Type-Checking Code

```bash
cd frontend
npm run type-check
```

Should show no errors.

### Building for Production

```bash
cd frontend
npm run build
```

Creates optimized build in `frontend/dist/`.

## Troubleshooting

### "Cannot connect to API"

1. Check backend is running: `curl http://localhost:8000/api/health`
2. Verify CORS is enabled in `src/api/main.py`
3. Check `.env` file has correct API URL

### "Image upload fails"

1. Check file format (JPEG, PNG, TIFF, BMP)
2. Check file size (max 50MB)
3. Check backend logs for errors

### "Processing hangs"

1. Check if ML pipeline is accessible (Python imports work)
2. Check models are loaded correctly
3. Monitor backend terminal for errors

### "Results page blank"

1. Check browser console for JavaScript errors
2. Verify results API returned data
3. Check Network tab to see actual response

### "Can't run npm commands"

```bash
# Clear cache
rm -rf node_modules
rm package-lock.json

# Reinstall
npm install

# Retry
npm run dev
```

## Next Steps

### Phase 3: 3D Retina Visualization

The foundation is ready for 3D components. To add Three.js:

```bash
cd frontend
npm install three @react-three/fiber @react-three/drei
```

Then create:
```
frontend/src/components/3d/
├── RetinaScene.tsx
├── RetinaGeometry.tsx
├── VascularSystem.tsx
└── ParticleSystem.tsx
```

See `docs/UI_ARCHITECTURE.md` section 8 for full 3D implementation guide.

## Helpful Resources

- **Vite**: https://vitejs.dev/
- **React**: https://react.dev/
- **TypeScript**: https://www.typescriptlang.org/
- **Tailwind CSS**: https://tailwindcss.com/
- **FastAPI**: https://fastapi.tiangolo.com/
- **Three.js**: https://threejs.org/
- **React Three Fiber**: https://docs.pmnd.rs/react-three-fiber/

## Project Documentation

- `docs/UI_ARCHITECTURE.md` - Complete frontend architecture
- `docs/UI_INTEGRATION.md` - Backend integration patterns
- `frontend/README.md` - Frontend development guide
- `STAGE_2_COMPLETION.md` - Build completion report

## Support

For issues:
1. Check the troubleshooting section above
2. Review browser console (F12)
3. Check backend terminal for errors
4. Check `frontend/README.md` for more details

---

**Status**: Foundation Phase Complete ✅  
**Ready for**: Phase 3 - 3D Retina Visualization  
**Last Updated**: 2026-09-01
