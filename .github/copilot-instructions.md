# Copilot & Coding Agent Instructions — RuralDR-XAI

## 1. Core Principles
- **No Fake Data**: Never generate synthetic patient names, fake predictions, unmeasured benchmarks, or mock doctor reviews.
- **Evidence Consistency**: Maintain the multi-stage evidence chain (Quality Gate $\rightarrow$ CLAHE $\rightarrow$ Retinal Anatomy $\rightarrow$ Lesion Inventory $\rightarrow$ DR Model $\rightarrow$ Grad-CAM $\rightarrow$ Consistency Engine $\rightarrow$ Calibration $\rightarrow$ Sub-30s Report).
- **Dual Compatibility**: Ensure MATLAB `.m` scripts and Python `src/` modules have matching functional contracts.

## 2. Directory Layout
- `src/`: Core Python modules (quality, preprocess, anatomy, lesions, models, xai, engine, reporting, edge, api).
- `matlab/`: Native MATLAB functions for Image Processing, Deep Learning, and Computer Vision toolboxes.
- `simulink/`: Telemedicine district queuing models.
- `tests/`: PyTest automated unit and integration tests.
- `docs/`: Clinical requirements, architecture, dataset registry, and research literature.
