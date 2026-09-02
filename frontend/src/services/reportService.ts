/**
 * Clinical Diagnostic Report Service for RuralDR-XAI
 * Compiles structured reports ready for clinical documentation and export.
 */

import { ScreeningCase } from '@/types/api';

export interface ClinicalReportDocument {
  reportId: string;
  generatedAt: string;
  caseData: ScreeningCase;
  disclaimer: string;
  verificationBadge: string;
}

export const reportService = {
  generateReport(screeningCase: ScreeningCase): ClinicalReportDocument {
    return {
      reportId: `REP-${screeningCase.id}-${Date.now().toString().slice(-4)}`,
      generatedAt: new Date().toLocaleString('en-IN', {
        timeZone: 'Asia/Kolkata',
        dateStyle: 'medium',
        timeStyle: 'short',
      }),
      caseData: screeningCase,
      disclaimer:
        'NOTICE: AI-generated screening information is intended to assist clinical review and does not replace professional medical judgment. All automated assessments are subject to review by registered ophthalmologists.',
      verificationBadge: 'Verified Clinical Report · SIH26038 Protocol',
    };
  },

  printReport(): void {
    window.print();
  },
};
