# Security, Privacy & Clinical Safety Policy
## RuralDR-XAI: Ethical & Secure Medical AI System

---

## 1. Medical Privacy & De-Identification

1. **Zero Personally Identifiable Information (PII)**:
   - The application does not store, log, or transmit patient names, national identity numbers (Aadhaar/SSN), or contact addresses.
   - All screening sessions utilize temporary, locally generated anonymous session tokens (e.g., `ANON-SESSION-2026-X84B`).
2. **Local Storage & Edge-First Architecture**:
   - Fundus images processed locally on Primary Health Center (PHC) devices are kept in ephemeral RAM/scratch disk cache and purged according to local clinic retention rules.
   - No diagnostic images or metadata are uploaded to unverified third-party cloud endpoints.

---

## 2. Input Validation & File Sanitization

1. **Supported Medical Image Formats**:
   - Only validated raster image formats are accepted (`image/jpeg`, `image/png`, `image/tiff`).
   - All uploaded files are checked for MIME-type magic numbers and maximum file size limits (50 MB).
2. **Path Traversal Protection**:
   - Filenames are sanitized and normalized using secure path join operations to strictly prevent directory traversal attacks (`../` or `..\`).
3. **No Code Execution via Data**:
   - Image decoding is isolated and utilizes standard C/Python libraries (Pillow / OpenCV) with safety checks for corrupted headers or buffer overflow vulnerabilities.

---

## 3. Clinical Safety & Medical Disclaimers

1. **Decision Support Only**:
   - RuralDR-XAI is a clinical decision-support and screening triage system. It is not an autonomous diagnostic device.
   - All generated screening reports prominently include the certified medical disclaimer:
     > *"RuralDR-XAI is an investigational decision-support tool for rural screening triage. Findings must be validated by a registered ophthalmologist before any medical, laser, or surgical intervention is administered."*
2. **Ungradable Image Safety Interlock**:
   - The system strictly forbids running automated DR diagnosis on images flagged as `UNGRADABLE` by the Quality Gate, preventing erroneous false negatives due to image degradation.
3. **Traceability & Version Auditing**:
   - Every report and screening record embeds the model version hash, preprocessing pipeline version, calibration timestamp, and Git commit hash for full clinical auditability.
