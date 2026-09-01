import axios, { AxiosError, AxiosInstance } from 'axios';
import {
  UploadResponse,
  ProcessResponse,
  StatusResponse,
  ScreeningResult,
  ApiError,
} from '@/types/api';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

const apiClient: AxiosInstance = axios.create({
  baseURL: API_BASE_URL,
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Response interceptor for error handling
apiClient.interceptors.response.use(
  response => response,
  (error: AxiosError<ApiError>) => {
    console.error('API Error:', error.response?.data || error.message);
    return Promise.reject(error);
  }
);

/**
 * Upload a fundus image
 */
export async function uploadImage(file: File): Promise<UploadResponse> {
  const formData = new FormData();
  formData.append('file', file);

  const response = await apiClient.post<UploadResponse>('/api/upload', formData, {
    headers: {
      'Content-Type': 'multipart/form-data',
    },
  });

  return response.data;
}

/**
 * Start processing pipeline for uploaded image
 */
export async function processImage(
  uploadId: string,
  runSegmentation: boolean = true
): Promise<ProcessResponse> {
  const response = await apiClient.post<ProcessResponse>('/api/process', {
    upload_id: uploadId,
    run_segmentation: runSegmentation,
  });

  return response.data;
}

/**
 * Poll job status
 */
export async function getStatus(jobId: string): Promise<StatusResponse> {
  const response = await apiClient.get<StatusResponse>('/api/status', {
    params: { job_id: jobId },
  });

  return response.data;
}

/**
 * Get completed results
 */
export async function getResults(jobId: string): Promise<ScreeningResult> {
  const response = await apiClient.get<ScreeningResult>('/api/results', {
    params: { job_id: jobId },
  });

  return response.data;
}

/**
 * Health check
 */
export async function healthCheck(): Promise<{ status: string; backend: string }> {
  const response = await apiClient.get('/api/health');
  return response.data;
}

export default apiClient;
