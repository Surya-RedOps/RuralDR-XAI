/**
 * Data formatting utilities
 */

export function formatPercent(value: number, decimals = 1): string {
  return `${(value * 100).toFixed(decimals)}%`;
}

export function formatConfidence(value: number): string {
  return formatPercent(value, 1);
}

export function formatTime(milliseconds: number): string {
  if (milliseconds < 1000) {
    return `${milliseconds}ms`;
  }
  return `${(milliseconds / 1000).toFixed(2)}s`;
}

export function formatFileSize(bytes: number): string {
  if (bytes === 0) return '0 Bytes';
  const k = 1024;
  const sizes = ['Bytes', 'KB', 'MB', 'GB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return Math.round((bytes / Math.pow(k, i)) * 100) / 100 + ' ' + sizes[i];
}

export function formatDRGrade(grade: number): string {
  const names = [
    'No DR',
    'Mild NPDR',
    'Moderate NPDR',
    'Severe NPDR',
    'PDR',
  ];
  return names[grade] || 'Unknown';
}

export function formatLesionType(type: string): string {
  return type
    .split('_')
    .map(word => word.charAt(0).toUpperCase() + word.slice(1))
    .join(' ');
}

export function formatCaseId(caseId: string): string {
  return caseId.substring(0, 8).toUpperCase();
}
