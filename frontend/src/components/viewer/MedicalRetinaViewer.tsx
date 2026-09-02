import React, { useState, useRef } from 'react';
import { getGradCamOverlaySvg, getLesionMaskOverlaySvg } from '@/services/sampleAssets';

interface MedicalRetinaViewerProps {
  imageUrl: string;
  gradCamUrl?: string;
  lesionOverlayUrl?: string;
  grade?: number;
  altText?: string;
  className?: string;
  showControls?: boolean;
}

export type ActiveOverlay = 'original' | 'gradcam' | 'lesions';

export const MedicalRetinaViewer: React.FC<MedicalRetinaViewerProps> = ({
  imageUrl,
  gradCamUrl,
  lesionOverlayUrl,
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

  const activeGradCamUrl = gradCamUrl || getGradCamOverlaySvg(grade);
  const activeLesionUrl = lesionOverlayUrl || getLesionMaskOverlaySvg(grade);

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

            <div className="flex items-center gap-1 bg-black/40 p-1 rounded-lg border border-white/5">
              <button
                onClick={handleZoomIn}
                title="Zoom In"
                className="w-7 h-7 rounded flex items-center justify-center text-neutral-400 hover:text-white hover:bg-white/10 text-xs"
              >
                +
              </button>
              <span className="text-[11px] font-mono text-neutral-300 px-1">{zoom.toFixed(1)}x</span>
              <button
                onClick={handleZoomOut}
                title="Zoom Out"
                className="w-7 h-7 rounded flex items-center justify-center text-neutral-400 hover:text-white hover:bg-white/10 text-xs"
              >
                -
              </button>
              <button
                onClick={handleReset}
                title="Reset View"
                className="px-2 py-1 rounded text-[10px] font-mono text-neutral-400 hover:text-white hover:bg-white/10"
              >
                Reset
              </button>
            </div>

            <button
              onClick={() => setShowGrid((prev) => !prev)}
              className={`px-2.5 py-1.5 rounded-lg text-xs font-mono transition-colors ${
                showGrid
                  ? 'bg-teal-500/20 text-teal-300 border border-teal-500/30'
                  : 'bg-black/40 text-neutral-400 hover:text-white border border-white/5'
              }`}
            >
              Grid
            </button>
          </div>
        </div>
      )}

      {/* Main Image Viewport Area */}
      <div
        ref={containerRef}
        onMouseDown={handleMouseDown}
        onMouseMove={handleMouseMove}
        onMouseUp={handleMouseUp}
        onMouseLeave={handleMouseUp}
        className={`relative aspect-square sm:aspect-[4/3] w-full bg-[#050507] flex items-center justify-center overflow-hidden select-none ${
          zoom > 1 ? 'cursor-grab active:cursor-grabbing' : 'cursor-default'
        }`}
      >
        {/* Retinal Image Layers */}
        <div
          style={{
            transform: `translate(${pan.x}px, ${pan.y}px) scale(${zoom})`,
            transition: isDragging ? 'none' : 'transform 0.15s ease-out',
            transformOrigin: 'center center',
          }}
          className="relative w-full h-full flex items-center justify-center max-w-[800px] max-h-[800px]"
        >
          {/* Base Fundus Image */}
          {imageUrl ? (
            <img
              src={imageUrl}
              alt={altText}
              className="w-full h-full object-contain pointer-events-none"
            />
          ) : (
            <div className="text-xs text-neutral-500 font-mono">No Image Loaded</div>
          )}

          {/* Grad-CAM Heatmap Layer */}
          {activeOverlay === 'gradcam' && activeGradCamUrl && (
            <div
              style={{ opacity: heatmapOpacity }}
              className="absolute inset-0 pointer-events-none transition-opacity duration-200 flex items-center justify-center"
            >
              <img
                src={activeGradCamUrl}
                alt="AI Grad-CAM Overlay"
                className="w-full h-full object-contain mix-blend-screen"
              />
            </div>
          )}

          {/* Lesion Segmentation Layer */}
          {activeOverlay === 'lesions' && activeLesionUrl && (
            <div className="absolute inset-0 pointer-events-none flex items-center justify-center">
              <img
                src={activeLesionUrl}
                alt="Lesion Segmentation Overlay"
                className="w-full h-full object-contain"
              />
            </div>
          )}

          {/* Calibrated Clinical Grid Overlay */}
          {showGrid && (
            <div className="absolute inset-0 pointer-events-none grid grid-cols-4 grid-rows-4 border border-teal-500/20">
              {Array.from({ length: 16 }).map((_, i) => (
                <div key={i} className="border border-teal-500/10 flex items-start p-1">
                  <span className="text-[9px] font-mono text-teal-400/40">{`Q${i + 1}`}</span>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Bottom Left Mode Badge */}
        <div className="absolute bottom-3 left-3 pointer-events-none">
          <span className="px-2.5 py-1 rounded-md text-[10px] font-mono uppercase bg-black/80 border border-white/10 text-neutral-300 backdrop-blur-md">
            {activeOverlay === 'original'
              ? 'Mode: High-Resolution Fundus'
              : activeOverlay === 'gradcam'
              ? 'Mode: Grad-CAM Saliency Map'
              : 'Mode: Lesion Mask Segmentation'}
          </span>
        </div>
      </div>
    </div>
  );
};
