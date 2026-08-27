"""
RuralDR-XAI FastAPI Local Screening Server
Provides REST endpoints and serves the offline-first Clinician Dashboard.
"""

from typing import Optional, Dict
from pathlib import Path
import base64
import cv2
import numpy as np
import torch
from fastapi import FastAPI, File, UploadFile, HTTPException, Query
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware

from ..core.config import RESULTS_DIR
from ..core.contracts import ScreeningResult
from ..engine.orchestrator import ScreeningOrchestrator
from ..reporting.pdf_generator import generate_clinical_pdf_report
from ..edge.offline_sync import OfflineEdgeSync
from .schemas import HealthResponse, ScreeningApiResponse, BatchSyncResponse

app = FastAPI(
    title="RuralDR-XAI Screening API",
    description="Explainable AI for Diabetic Retinopathy Screening in Rural India (SIH26038)",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize Orchestrator and Edge Sync
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
orchestrator = ScreeningOrchestrator(device=device)
edge_sync = OfflineEdgeSync()

# In-memory cache for fast report generation
latest_results_cache: Dict[str, tuple] = {}  # case_id -> (ScreeningResult, composite_image_np)


def numpy_to_data_uri(img_rgb: np.ndarray, quality: int = 85) -> str:
    """Encodes an RGB numpy array to a base64 JPEG data URI."""
    bgr = cv2.cvtColor(img_rgb, cv2.COLOR_RGB2BGR)
    _, buffer = cv2.imencode(".jpg", bgr, [int(cv2.IMWRITE_JPEG_QUALITY), quality])
    b64 = base64.b64encode(buffer).decode("utf-8")
    return f"data:image/jpeg;base64,{b64}"


@app.get("/", response_class=HTMLResponse)
async def serve_ui():
    ui_path = Path(__file__).resolve().parent.parent / "ui" / "index.html"
    if not ui_path.is_file():
        raise HTTPException(status_code=404, detail="UI index.html not found.")
    with open(ui_path, "r", encoding="utf-8") as f:
        return f.read()


@app.get("/health", response_model=HealthResponse)
async def health_check():
    gpu_available = torch.cuda.is_available()
    gpu_name = torch.cuda.get_device_name(0) if gpu_available else None
    return HealthResponse(
        status="ONLINE",
        version="1.0.0",
        device=str(device),
        gpu_available=gpu_available,
        gpu_name=gpu_name,
        offline_mode=True,
    )


@app.post("/api/v1/screen", response_model=ScreeningApiResponse)
async def screen_fundus_image(file: UploadFile = File(...)):
    contents = await file.read()
    nparr = np.frombuffer(contents, np.uint8)
    img_bgr = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

    if img_bgr is None:
        raise HTTPException(status_code=400, detail="Uploaded file is not a valid image.")

    img_rgb = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2RGB)
    case_id = Path(file.filename).stem if file.filename else "CASE-ANON"

    result, visual_layers = orchestrator.process_image(img_rgb, case_id=case_id)

    # Save to local offline queue
    edge_sync.enqueue_case(result)

    # Convert visual layers to data URIs for client display
    visual_urls = {}
    for key, layer_img in visual_layers.items():
        if isinstance(layer_img, np.ndarray):
            if layer_img.ndim == 2 and layer_img.dtype == np.uint8:
                # Convert binary mask to RGB overlay
                rgb_mask = cv2.cvtColor(layer_img, cv2.COLOR_GRAY2RGB)
                visual_urls[key] = numpy_to_data_uri(rgb_mask)
            elif layer_img.ndim == 3:
                visual_urls[key] = numpy_to_data_uri(layer_img)

    # Cache composite view for PDF generation
    composite_np = visual_layers.get("composite_annotated", img_rgb)
    latest_results_cache[result.case_id] = (result, composite_np)

    return ScreeningApiResponse(
        success=True,
        result=result,
        visual_urls=visual_urls,
        message="Screening completed.",
    )


@app.get("/api/v1/export-pdf")
async def export_pdf(case_id: str = Query(..., description="Case identifier")):
    if case_id not in latest_results_cache:
        raise HTTPException(status_code=404, detail="Case record not found in active session.")

    result, composite_np = latest_results_cache[case_id]
    pdf_path = RESULTS_DIR / f"reports/{case_id}_clinical_report.pdf"
    generate_clinical_pdf_report(result, composite_np, pdf_path)

    return FileResponse(
        path=str(pdf_path),
        filename=f"Report_{case_id}.pdf",
        media_type="application/pdf",
    )


@app.get("/api/v1/queue")
async def get_offline_queue():
    pending = edge_sync.list_pending_cases()
    return {"pending_count": len(pending), "cases": pending}


@app.post("/api/v1/sync", response_model=BatchSyncResponse)
async def trigger_sync():
    res = edge_sync.sync_batch_to_central_server()
    return BatchSyncResponse(
        synced_count=res["synced_count"],
        status=res["status"],
        timestamp=res.get("timestamp", ""),
    )
