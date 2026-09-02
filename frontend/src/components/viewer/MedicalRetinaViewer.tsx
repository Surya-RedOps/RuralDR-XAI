import React, { useState, useRef } from 'react';
import { getGradCamOverlaySvg, getLesionMaskOverlaySvg } from '@/services/sampleAssets';

interface MedicalRetinaViewerProps {
  imageUrl: string;
  grade?: number;
  altText?: string;
  className?: string;
  showControls?: boolean;
}

export type ActiveOverlay = 'original' | 'gradcam' | 'lesions';

export const MedicalRetinaViewer: React.FC<MedicalRetinaViewerProps> = ({
  imageUrl,
  grade = 2,
  altText = 'Retinal Fundus Image',
  className = '',
  showControls = true,
}) => {
  const [activeOverlay, setActiveOverlay] = useState<ActiveOverlay>('original');
  const [zoom, setZoom] = useState<number>(1);
  const [pan, setPan] = useState<{ x: number; y: number }>({ x: 0, y: 0 });
  const [isDragging, setIsDragging] = useState<boolean>(false);
  const [dragStart, setDragStart] = useState<{ x: number; y: number }>({ x: 0, y: 0 });
  const [heatmapOpacity, setHeatmapOpacity] = useState<number>(0.75);
  const [showGrid, setShowGrid] = useState<boolean>(false);
  const containerRef = useRef<HTMLDivElement>(null);

  const gradCamOverlayUrl = getGradCamOverlaySvg(grade);
  const lesionOverlayUrl = getLesionMaskOverlaySvg(grade);

  const handleZoomIn = () => setZoom((prev) => Math.min(prev + 0.5, 4));
  const handleZoomOut = () => {
    setZoom((prev) => {
      const next = Math.max(prev - 0.5, 1);
      if (next === 1) setPan({ x: 0, y: 0 });
      return next;
    });
  };

  const handleReset = () => {
    setZoom(1);
    setPan({ x: 0, y: 0 });
  };

  const handleMouseDown = (e: React.MouseEvent) => {
    if (zoom <= 1) return;
    setIsDragging(true);
    setDragStart({ x: e.clientX - pan.x, y: e.clientY - pan.y });
  };

  const handleMouseMove = (e: React.MouseEvent) => {
    if (!isDragging || zoom <= 1) return;
    setPan({
      x: e.clientX - dragStart.x,
      y: e.clientY - dragStart.y,
    });
  };

  const handleMouseUp = () => setIsDragging(false);

  return (
    <div className={`flex flex-col bg-[#09090b] rounded-2xl border border-white/10 overflow-hidden ${className}`}>
      {/* Top Controls Toolbar */}
      {showControls && (
        <div className="flex flex-wrap items-center justify-between gap-3 px-4 py-3 bg-[#111114] border-b border-white/[0.08]">
          {/* Overlay Selector Tabs */}
          <div className="flex items-center gap-1 bg-black/40 p-1 rounded-xl border border-white/5">
            <button
              onClick={() => setActiveOverlay('original')}
              className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-all ${
                activeOverlay === 'original'
                  ? 'bg-white text-black font-semibold shadow-sm'
                  : 'text-neutral-400 hover:text-white hover:bg-white/5'
              }`}
            >
              Original Fundus
            </button>
            <button
              onClick={() => setActiveOverlay('gradcam')}
              className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-all flex items-center gap-1.5 ${
                activeOverlay === 'gradcam'
                  ? 'bg-gradient-to-r from-teal-500 to-cyan-500 text-black font-semibold shadow-sm'
                  : 'text-neutral-400 hover:text-white hover:bg-white/5'
              }`}
            >
              <span className="w-2 h-2 rounded-full bg-cyan-400 animate-pulse" />
              <span>AI Grad-CAM</span>
            </button>
            <button
              onClick={() => setActiveOverlay('lesions')}
              className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-all flex items-center gap-1.5 ${
                activeOverlay === 'lesions'
                  ? 'bg-gradient-to-r from-red-500 to-amber-500 text-white font-semibold shadow-sm'
                  : 'text-neutral-400 hover:text-white hover:bg-white/5'
              }`}
            >
              <span className="w-2 h-2 rounded-full bg-red-400" />
              <span>Lesion Evidence</span>
            </button>
          </div>

          {/* Zoom & View Controls */}
          <div className="flex items-center gap-2">
            {activeOverlay === 'gradcam' && (
              <div className="hidden sm:flex items-center gap-2 px-2.5 py-1 rounded-lg bg-black/40 border border-white/5 text-xs text-neutral-300">
                <span>Intensity:</span>
                <input
                  type="range"
                  min="0.2"
                  max="1.0"
                  step="0.05"
                  value={heatmapOpacity}
                  onChange={(e) => setHeatmapOpacity(parseFloat(e.target.value))}
                  className="w-16 h-1 bg-white/20 rounded-lg appearance-none cursor-pointer accent-cyan-400"
                />
                <span className="font-mono text-[10px] text-cyan-400">{Math.round(heatmapOpacity * 100)}%</span>
              </div>
            )}

            <button
              onClick={() => setShowGrid((prev) => !prev)}
              className={`p-1.5 rounded-lg text-xs transition-colors border ${
                showGrid
                  ? 'bg-cyan-500/20 text-cyan-300 border-cyan-500/30'
                  : 'text-neutral-400 hover:text-white bg-black/30 border-white/5'
              }`}
              title="Toggle Retinal Quadrant Grid"
            >
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <rect x="3" y="3" width="18" height="18" rx="2" />
                <line x1="3" y1="12" x2="21" y2="12" />
                <line x1="12" y1="3" x2="12" y2="21" />
              </svg>
            </button>

            <div className="flex items-center bg-black/40 rounded-lg border border-white/5 overflow-hidden text-xs">
              <button
                onClick={handleZoomOut}
                disabled={zoom <= 1}
                className="px-2.5 py-1.5 text-neutral-400 hover:text-white disabled:opacity-30 transition-colors"
                title="Zoom out"
              >
                -
              </button>
              <span className="px-2 text-neutral-300 font-mono text-[11px] min-w-[40px] text-center">
                {zoom.toFixed(1)}x
              </span>
              <button
                onClick={handleZoomIn}
                disabled={zoom >= 4}
                className="px-2.5 py-1.5 text-neutral-400 hover:text-white disabled:opacity-30 transition-colors"
                title="Zoom in"
              >
                +
              </button>
            </div>

            <button
              onClick={handleReset}
              className="px-2.5 py-1.5 rounded-lg text-xs text-neutral-400 hover:text-white bg-black/40 border border-white/5 hover:border-white/10 transition-colors"
              title="Reset Zoom & Pan"
            >
              Reset
            </button>
          </div>
        </div>
      )}

      {/* Main Canvas Viewport */}
      <div
        ref={containerRef}
        onMouseDown={handleMouseDown}
        onMouseMove={handleMouseMove}
        onMouseUp={handleMouseUp}
        onMouseLeave={handleMouseUp}
        className={`relative aspect-square w-full max-h-[520px] bg-black flex items-center justify-center overflow-hidden select-none ${
          zoom > 1 ? (isDragging ? 'cursor-grabbing' : 'cursor-grab') : 'cursor-default'
        }`}
      >
        {/* Retinal Image Container with Pan/Zoom Transform */}
        <div
          style={{
            transform: `scale(${zoom}) translate(${pan.x / zoom}px, ${pan.y / zoom}px)`,
            transition: isDragging ? 'none' : 'transform 0.2s cubic-bezier(0.16, 1, 0.3, 1)',
          }}
          className="relative w-full h-full flex items-center justify-center pointer-events-none"
        >
          {/* Base Fundus Image */}
          <img
            src={imageUrl}
            alt={altText}
            className="w-full h-full object-contain max-h-[520px]"
            draggable={false}
          />

          {/* Grad-CAM Heatmap Layer */}
          {activeOverlay === 'gradcam' && (
            <img
              src={gradCamOverlayUrl}
              alt="Grad-CAM Class Activation Map"
              style={{ opacity: heatmapOpacity }}
              className="absolute inset-0 w-full h-full object-contain pointer-events-none mix-blend-screen transition-opacity"
              draggable={false}
            />
          )}

          {/* Lesion Segmentation Mask Layer */}
          {activeOverlay === 'lesions' && (
            <img
              src={lesionOverlayUrl}
              alt="Lesion Segmentation Overlay"
              className="absolute inset-0 w-full h-full object-contain pointer-events-none transition-opacity"
              draggable={false}
            />
          )}

          {/* Medical Quadrant Grid Overlay */}
          {showGrid && (
            <div className="absolute inset-0 pointer-events-none flex items-center justify-center">
              <div className="w-[90%] h-[90%] border border-cyan-500/20 rounded-full relative">
                <div className="absolute inset-0 grid grid-cols-2 grid-rows-2">
                  <div className="border-r border-b border-cyan-500/20 p-2 text-[9px] font-mono text-cyan-400/60">
                    ST (Superior Temporal)
                  </div>
                  <div className="border-b border-cyan-500/20 p-2 text-[9px] font-mono text-cyan-400/60 text-right">
                    SN (Superior Nasal)
                  </div>
                  <div className="border-r border-cyan-500/20 p-2 text-[9px] font-mono text-cyan-400/60 flex items-end">
                    IT (Inferior Temporal)
                  </div>
                  <div className="p-2 text-[9px] font-mono text-cyan-400/60 flex items-end justify-end">
                    IN (Inferior Nasal)
                  </div>
                </div>
                {/* Central Foveal Circle Target */}
                <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-12 h-12 border border-dashed border-yellow-400/40 rounded-full" />
              </div>
            </div>
          )}
        </div>

        {/* Viewport Meta Badges */}
        <div className="absolute bottom-3 left-3 flex items-center gap-2 pointer-events-none">
          <span className="px-2 py-0.5 rounded bg-black/70 backdrop-blur-md border border-white/10 text-[10px] font-mono text-neutral-300">
            Field: 45° Posterior Pole
          </span>
          <span className="px-2 py-0.5 rounded bg-black/70 backdrop-blur-md border border-white/10 text-[10px] font-mono text-neutral-400">
            1024×1024 RGB
          </span>
        </div>

        {/* Active Overlay Indicator */}
        <div className="absolute top-3 right-3 pointer-events-none">
          {activeOverlay === 'gradcam' && (
            <div className="px-2.5 py-1 rounded-md bg-cyan-950/80 backdrop-blur-md border border-cyan-500/30 text-[10px] text-cyan-300 font-medium flex items-center gap-1.5">
              <span className="w-1.5 h-1.5 rounded-full bg-cyan-400" />
              <span>Grad-CAM Activation Active</span>
            </div>
          )}
          {activeOverlay === 'lesions' && (
            <div className="px-2.5 py-1 rounded-md bg-red-950/80 backdrop-blur-md border border-red-500/30 text-[10px] text-red-300 font-medium flex items-center gap-1.5">
              <span className="w-1.5 h-1.5 rounded-full bg-red-400" />
              <span>Lesion Segmentation Active</span>
            </div>
          )}
        </div>
      </div>

      {/* Legend for Lesion Evidence when active */}
      {activeOverlay === 'lesions' && (
        <div className="px-4 py-2.5 bg-[#111114] border-t border-white/[0.08] flex flex-wrap items-center justify-between gap-3 text-xs">
          <span className="text-neutral-400 font-medium text-[11px]">Detected Biomarkers:</span>
          <div className="flex flex-wrap items-center gap-4 text-[11px]">
            <div className="flex items-center gap-1.5">
              <span className="w-2.5 h-2.5 rounded-full bg-[#ff1744]" />
              <span className="text-neutral-200">Microaneurysms</span>
            </div>
            <div className="flex items-center gap-1.5">
              <span className="w-2.5 h-2.5 rounded-full bg-[#dc2626]" />
              <span className="text-neutral-200">Hemorrhages</span>
            </div>
            <div className="flex items-center gap-1.5">
              <span className="w-2.5 h-2.5 rounded-full bg-[#fbc02d]" />
              <span className="text-neutral-200">Hard Exudates</span>
            </div>
            <div className="flex items-center gap-1.5">
              <span className="w-2.5 h-2.5 rounded-full bg-[#38bdf8]" />
              <span className="text-neutral-200">Cotton Wool Spots</span>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
