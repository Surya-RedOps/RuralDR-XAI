# RuralDR-XAI Frontend-Backend Integration Guide

## Overview

This document describes exactly how the React frontend integrates with the existing Python ML pipeline through a thin FastAPI adapter layer.

**CRITICAL PRINCIPLE**: The FastAPI layer is a stateless adapter that:
1. Accepts image uploads
2. Calls the existing Python pipeline functions
3. Returns results as JSON
4. Serves generated images

It does NOT contain business logic, AI algorithms, or model inference code.

## Existing Python Pipeline Structure

### ExplainableScreeningPipeline

**Location**: `src/ai/explainability/pipeline.py`

**Main Function**: `ExplainableScreeningPipeline.process()`

```python
class ExplainableScreeningPipeline:
    def process(
        self,
        image_input: Union[str, Path, np.ndarray, Image.Image],
        output_dir: str,
        run_segmentation: bool = True,
    ) -> ExplainableScreeningResult:
        """
        Orchestrates the full pipeline:
        1. Quality Gate Assessment
        2. DR Classification (if gradeable)
        3. Grad-CAM Visualization
        4. Lesion Segmentation
        
        Args:
            image_input: Path to image file or image object
            output_dir: Directory for output images/reports
            run_segmentation: Whether to run segmentation
            
        Returns:
            ExplainableScreeningResult with all pipeline outputs
        """
```

**Input Types Accepted:**
- File path (str or Path)
- numpy array (RGB uint8)
- PIL Image
- OpenCV Mat

**Output**: `ExplainableScreeningResult` object with:
- `case_id`: Unique identifier
- `quality_status`: GRADEABLE | UNGRADABLE | BORDERLINE
- `quality_score`: Float 0-1
- `dr_grade`: 0-4 (severity level)
- `severity`: String description
- `classification_confidence`: Float 0-1
- `class_probabilities`: List of 5 probabilities (one per grade)
- `is_referable`: Boolean (grade >= 2)
- `gradcam_result`: GradCAMResult object
- `segmentation_result`: LesionDetectionResult object
- Processing timing information

### Helper Functions Used by Frontend

**Generate Evidence Report:**
```python
from src.ai.explainability.evidence import generate_evidence_report

report = generate_evidence_report(result: ExplainableScreeningResult)
# Returns: Dict with structured evidence for doctor dashboard
```

**Image Enhancement** (optional, may be pre-applied):
```python
from src.preprocess.enhance import AdaptiveEnhancer

enhancer = AdaptiveEnhancer()
enhanced = enhancer.enhance(image_rgb_array)
```

## FastAPI Adapter Layer Implementation

### Location: `src/api/main.py` (NEW FILE TO CREATE)

### Dependencies

```python
from fastapi import FastAPI, UploadFile, HTTPException, File
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
from pathlib import Path
import uuid
import asyncio
import threading
from datetime import datetime
import traceback

# Existing project imports (these work, tested)
from src.ai.explainability.pipeline import ExplainableScreeningPipeline
from src.ai.explainability.evidence import generate_evidence_report
from src.core.config import RESULTS_DIR  # Assuming this exists
```

### Core Endpoints

#### 1. Health Check

```python
@app.get("/api/health")
async def health():
    """Simple health check endpoint"""
    return {
        "status": "ok",
        "backend": "available",
        "timestamp": datetime.utcnow().isoformat()
    }
```

#### 2. Image Upload

**Endpoint**: `POST /api/upload`

```python
class UploadResponse(BaseModel):
    upload_id: str
    filename: str
    size_bytes: int
    message: str

@app.post("/api/upload", response_model=UploadResponse)
async def upload_image(file: UploadFile = File(...)):
    """
    Accept fundus image upload.
    Save temporarily for processing.
    """
    # Validate image format
    valid_formats = {'image/jpeg', 'image/png', 'image/bmp', 'image/tiff'}
    if file.content_type not in valid_formats:
        raise HTTPException(400, "Invalid image format. Use JPEG, PNG, BMP, or TIFF")
    
    # Validate file size (max 50MB)
    contents = await file.read()
    if len(contents) > 50 * 1024 * 1024:
        raise HTTPException(413, "File too large. Maximum 50MB")
    
    # Generate unique ID for this upload
    upload_id = str(uuid.uuid4())
    upload_dir = Path(RESULTS_DIR) / "uploads" / upload_id
    upload_dir.mkdir(parents=True, exist_ok=True)
    
    # Save image
    file_path = upload_dir / file.filename
    with open(file_path, 'wb') as f:
        f.write(contents)
    
    return UploadResponse(
        upload_id=upload_id,
        filename=file.filename,
        size_bytes=len(contents),
        message="Image uploaded successfully"
    )
```

**Frontend Usage:**
```typescript
const formData = new FormData();
formData.append('file', imageFile);

const response = await fetch('/api/upload', {
  method: 'POST',
  body: formData
});

const { upload_id } = await response.json();
// Use upload_id for next step
```

#### 3. Start Processing

**Endpoint**: `POST /api/process`

**State Management**: Global job tracking dictionary

```python
# Global job tracking (replace with database in production)
JOBS = {}  # { job_id: { status, upload_id, results, error, ... } }

class ProcessRequest(BaseModel):
    upload_id: str
    run_segmentation: bool = True

class ProcessResponse(BaseModel):
    job_id: str
    status: str
    message: str

@app.post("/api/process", response_model=ProcessResponse)
async def start_processing(request: ProcessRequest):
    """
    Start the pipeline processing in background thread.
    Returns immediately with job_id for polling.
    """
    # Validate upload exists
    upload_dir = Path(RESULTS_DIR) / "uploads" / request.upload_id
    if not upload_dir.exists():
        raise HTTPException(404, "Upload not found")
    
    # Find image file
    image_files = list(upload_dir.glob("*"))
    if not image_files:
        raise HTTPException(400, "No image file in upload directory")
    
    image_path = image_files[0]
    
    # Create job
    job_id = str(uuid.uuid4())
    JOBS[job_id] = {
        "status": "processing",
        "upload_id": request.upload_id,
        "image_path": str(image_path),
        "results": None,
        "error": None,
        "progress_pct": 0,
        "current_step": "Initializing...",
        "created_at": datetime.utcnow(),
    }
    
    # Start processing in background thread
    thread = threading.Thread(
        target=_run_pipeline,
        args=(job_id, str(image_path), request.run_segmentation),
        daemon=True
    )
    thread.start()
    
    return ProcessResponse(
        job_id=job_id,
        status="processing",
        message="Pipeline started"
    )

def _run_pipeline(job_id: str, image_path: str, run_segmentation: bool):
    """Background worker that runs the actual pipeline"""
    try:
        job = JOBS[job_id]
        
        # Initialize pipeline
        job["current_step"] = "Loading model..."
        job["progress_pct"] = 5
        pipeline = ExplainableScreeningPipeline()
        
        # Process image
        job["current_step"] = "Processing image..."
        job["progress_pct"] = 15
        
        result = pipeline.process(
            image_input=image_path,
            output_dir=str(Path(RESULTS_DIR) / "results" / job_id),
            run_segmentation=run_segmentation,
        )
        
        job["progress_pct"] = 85
        job["current_step"] = "Generating report..."
        
        # Generate evidence report
        evidence_report = generate_evidence_report(result)
        
        # Convert result to JSON-serializable dict
        job["results"] = {
            "case_id": result.case_id,
            "quality": {
                "status": str(result.quality_status),
                "score": float(result.quality_score),
                "message": f"Image quality: {result.quality_status}"
            },
            "classification": {
                "dr_grade": result.dr_grade,
                "severity": result.severity,
                "confidence": float(result.classification_confidence),
                "class_probabilities": [float(p) for p in result.class_probabilities],
                "is_referable": bool(result.is_referable),
            },
            "gradcam": _serialize_gradcam(result.gradcam_result, job_id),
            "segmentation": _serialize_segmentation(result.segmentation_result, job_id),
            "processing_times": {
                "quality_gate_ms": int(result.quality_gate_time_ms),
                "classification_ms": int(result.classification_time_ms),
                "gradcam_ms": int(result.gradcam_time_ms),
                "segmentation_ms": int(result.segmentation_time_ms),
                "total_ms": int(result.total_pipeline_time_ms),
            },
            "evidence_report": evidence_report,
        }
        
        job["status"] = "completed"
        job["progress_pct"] = 100
        job["current_step"] = "Complete"
        
    except Exception as e:
        job["status"] = "failed"
        job["error"] = str(e)
        job["progress_pct"] = 0
        job["current_step"] = "Error"
        # Log traceback for debugging
        import logging
        logging.error(f"Pipeline error in job {job_id}: {traceback.format_exc()}")

def _serialize_gradcam(gradcam_result, job_id: str) -> dict:
    """Convert GradCAMResult to JSON-serializable dict"""
    if not gradcam_result:
        return None
    
    return {
        "is_valid": bool(gradcam_result.is_valid),
        "target_class": gradcam_result.target_class,
        "target_class_name": gradcam_result.target_class_name,
        "activation_coverage": float(gradcam_result.activation_coverage),
        "peak_intensity": float(gradcam_result.peak_intensity),
        "quality_flags": list(gradcam_result.quality_flags or []),
        # Image paths are served by /api/static/
        "overlay_url": f"/api/static/results/{job_id}/gradcam_overlay.png",
    }

def _serialize_segmentation(segmentation_result, job_id: str) -> dict:
    """Convert LesionDetectionResult to JSON-serializable dict"""
    if not segmentation_result:
        return None
    
    lesions = []
    for lesion in segmentation_result.lesions:
        lesions.append({
            "type": lesion.lesion_type,
            "detected": bool(lesion.detected),
            "num_regions": int(lesion.num_connected_components),
            "area_pct": float(lesion.relative_area_pct),
            "confidence": float(lesion.mean_confidence),
            "mask_url": f"/api/static/results/{job_id}/{lesion.lesion_type}_mask.png",
        })
    
    return {
        "lesions": lesions,
        "input_resolution": segmentation_result.input_resolution,
    }
```

#### 4. Poll Processing Status

**Endpoint**: `GET /api/status?job_id=<job_id>`

```python
class StatusResponse(BaseModel):
    job_id: str
    status: str  # processing, completed, failed
    progress_pct: int
    current_step: str
    error: Optional[str] = None

@app.get("/api/status", response_model=StatusResponse)
async def get_status(job_id: str):
    """Poll job status (client calls every 1-2 seconds)"""
    if job_id not in JOBS:
        raise HTTPException(404, "Job not found")
    
    job = JOBS[job_id]
    return StatusResponse(
        job_id=job_id,
        status=job["status"],
        progress_pct=job["progress_pct"],
        current_step=job["current_step"],
        error=job["error"]
    )
```

**Frontend Usage:**
```typescript
const pollStatus = async (jobId: string) => {
  while (true) {
    const response = await fetch(`/api/status?job_id=${jobId}`);
    const status = await response.json();
    
    setStatus(status.status);
    setProgress(status.progress_pct);
    setCurrentStep(status.current_step);
    
    if (status.status === 'completed' || status.status === 'failed') {
      break;
    }
    
    await new Promise(resolve => setTimeout(resolve, 1000)); // Wait 1s
  }
};
```

#### 5. Get Results

**Endpoint**: `GET /api/results?job_id=<job_id>`

```python
@app.get("/api/results")
async def get_results(job_id: str):
    """Retrieve completed results with all data and image URLs"""
    if job_id not in JOBS:
        raise HTTPException(404, "Job not found")
    
    job = JOBS[job_id]
    if job["status"] == "processing":
        raise HTTPException(202, "Job still processing")
    if job["status"] == "failed":
        raise HTTPException(400, {"error": job["error"]})
    
    return job["results"]
```

**Frontend Usage:**
```typescript
const response = await fetch(`/api/results?job_id=${jobId}`);
const results = await response.json();

console.log(results.classification.dr_grade);  // 0-4
console.log(results.classification.confidence); // 0-1
console.log(results.gradcam.overlay_url);      // URL to image
```

#### 6. Serve Generated Images

**Endpoint**: `GET /api/static/results/{job_id}/{filename}`

```python
@app.get("/api/static/results/{job_id}/{filename}")
async def serve_result_image(job_id: str, filename: str):
    """Serve Grad-CAM overlays, segmentation masks, and other generated images"""
    result_path = Path(RESULTS_DIR) / "results" / job_id / filename
    
    if not result_path.exists():
        raise HTTPException(404, "Image not found")
    
    return FileResponse(
        path=result_path,
        media_type="image/png",
        headers={"Cache-Control": "public, max-age=31536000"}  # 1 year cache
    )
```

### Error Handling

```python
@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": exc.status_code,
            "message": exc.detail,
            "details": {}
        }
    )

@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    return JSONResponse(
        status_code=500,
        content={
            "error": "backend_error",
            "message": "Unexpected server error",
            "details": {"type": type(exc).__name__}
        }
    )
```

### CORS Configuration

```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

### App Initialization

```python
app = FastAPI(
    title="RuralDR-XAI Backend API",
    description="Thin adapter for ML pipeline",
    version="1.0.0"
)

# Mount static files directory
static_results_dir = Path(RESULTS_DIR) / "results"
static_results_dir.mkdir(parents=True, exist_ok=True)
app.mount("/api/static", StaticFiles(directory=static_results_dir), name="static")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
```

## Frontend Integration Points

### 1. Axios Client Setup

**File**: `frontend/src/services/api.ts`

```typescript
import axios from 'axios';

const API_BASE_URL = process.env.VITE_API_URL || 'http://localhost:8000';

const apiClient = axios.create({
  baseURL: API_BASE_URL,
  timeout: 30000,
});

// Interceptor for error handling
apiClient.interceptors.response.use(
  response => response,
  error => {
    console.error('API Error:', error.response?.data || error.message);
    return Promise.reject(error);
  }
);

export default apiClient;
```

### 2. Processing Hook

**File**: `frontend/src/hooks/useProcessing.ts`

```typescript
import { useState, useCallback } from 'react';
import apiClient from '../services/api';

interface ProcessingState {
  status: 'idle' | 'uploading' | 'processing' | 'completed' | 'failed';
  progress: number;
  currentStep: string;
  error?: string;
  results?: any;
}

export function useProcessing() {
  const [state, setState] = useState<ProcessingState>({ 
    status: 'idle', 
    progress: 0,
    currentStep: ''
  });

  const uploadImage = useCallback(async (file: File) => {
    setState(prev => ({ ...prev, status: 'uploading' }));
    
    const formData = new FormData();
    formData.append('file', file);
    
    try {
      const { data } = await apiClient.post('/api/upload', formData);
      return data.upload_id;
    } catch (error) {
      setState(prev => ({ ...prev, status: 'failed', error: 'Upload failed' }));
      throw error;
    }
  }, []);

  const processImage = useCallback(async (uploadId: string, runSegmentation = true) => {
    setState(prev => ({ ...prev, status: 'processing', progress: 0 }));
    
    try {
      const { data: jobData } = await apiClient.post('/api/process', {
        upload_id: uploadId,
        run_segmentation: runSegmentation,
      });
      
      const jobId = jobData.job_id;
      
      // Poll for completion
      while (true) {
        const { data: statusData } = await apiClient.get('/api/status', {
          params: { job_id: jobId }
        });
        
        setState(prev => ({
          ...prev,
          progress: statusData.progress_pct,
          currentStep: statusData.current_step,
        }));
        
        if (statusData.status === 'completed') {
          const { data: results } = await apiClient.get('/api/results', {
            params: { job_id: jobId }
          });
          
          setState(prev => ({
            ...prev,
            status: 'completed',
            progress: 100,
            results,
          }));
          return results;
        }
        
        if (statusData.status === 'failed') {
          setState(prev => ({
            ...prev,
            status: 'failed',
            error: statusData.error,
          }));
          throw new Error(statusData.error);
        }
        
        await new Promise(resolve => setTimeout(resolve, 1000));
      }
    } catch (error) {
      setState(prev => ({ 
        ...prev, 
        status: 'failed', 
        error: error.message 
      }));
      throw error;
    }
  }, []);

  return { state, uploadImage, processImage };
}
```

## Example Frontend Usage

```typescript
function ImageUploadPage() {
  const { state, uploadImage, processImage } = useProcessing();

  const handleUpload = async (file: File) => {
    const uploadId = await uploadImage(file);
    const results = await processImage(uploadId, true);
    
    // Navigate to results page
    navigate(`/results/${results.case_id}`);
  };

  return (
    <div>
      <input type="file" onChange={e => handleUpload(e.target.files[0])} />
      {state.status === 'processing' && (
        <div>
          <ProgressBar value={state.progress} />
          <p>{state.currentStep}</p>
        </div>
      )}
    </div>
  );
}
```

## Important Implementation Notes

### 1. No Data Duplication

The FastAPI adapter does NOT:
- Reimplement image quality checking
- Reimplement DR classification
- Recompute segmentation
- Cache results beyond the current job

It only:
- Validates uploads
- Calls existing functions
- Converts outputs to JSON
- Serves generated images

### 2. Image Path Handling

The Python pipeline saves generated images to:
```
results/
  └── {job_id}/
      ├── gradcam_overlay.png
      ├── exudate_mask.png
      ├── hemorrhage_mask.png
      └── ...
```

The API serves these via `/api/static/results/{job_id}/{filename}`.

### 3. JSON Serialization

The result objects are converted to JSON using:
- `float()` for numpy/torch scalars
- `bool()` for boolean values
- `int()` for integer values
- `str()` for enums
- Lists for array outputs

### 4. Error Context

Errors include:
- Original Python exception message
- Job ID for debugging
- User-friendly message for frontend display

### 5. Memory Management

For production:
- Replace in-memory JOBS dict with Redis or database
- Implement result cleanup (delete old results after TTL)
- Add job timeout (cancel jobs running > 5 minutes)
- Stream large result images instead of loading fully

---

**Integration Status**: Ready for implementation  
**Last Updated**: 2026-09-01
