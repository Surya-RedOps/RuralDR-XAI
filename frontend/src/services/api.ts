import axios, { AxiosError, AxiosInstance, InternalAxiosRequestConfig } from 'axios';
import {
  UploadResponse,
  ProcessResponse,
  StatusResponse,
  ScreeningResult,
} from '@/types/api';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

export const apiClient: AxiosInstance = axios.create({
  baseURL: API_BASE_URL,
  timeout: 45000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor to attach JWT authorization token
apiClient.interceptors.request.use(
  (config: InternalAxiosRequestConfig) => {
    const token = localStorage.getItem('ruraldr_jwt_token');
    if (token && config.headers) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => Promise.reject(error)
);

// Response interceptor for error handling & session expiration
apiClient.interceptors.response.use(
  (response) => response,
  (error: AxiosError<{ detail?: string }>) => {
    if (error.response?.status === 401) {
      const url = error.config?.url || '';
      if (!url.includes('/auth/login')) {
        localStorage.removeItem('ruraldr_jwt_token');
        localStorage.removeItem('ruraldr_auth_user');
      }
    }
    const errorMessage = error.response?.data?.detail || error.message || 'An unexpected error occurred';
    return Promise.reject(new Error(errorMessage));
  }
);

export async function uploadImage(file: File): Promise<UploadResponse> {
  const formData = new FormData();
  formData.append('file', file);
  const response = await apiClient.post<any>('/api/v1/screenings/ANON/image', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  });
  return {
    upload_id: response.data.case_id || 'ANON',
    filename: file.name,
    size_bytes: file.size,
    message: 'Upload successful',
  };
}

export async function processImage(uploadId: string, _runSegmentation: boolean = true): Promise<ProcessResponse> {
  const response = await apiClient.post<any>(`/api/v1/screenings/${uploadId}/analyze`);
  return {
    job_id: uploadId,
    status: response.data.status,
    message: 'Processing started',
  };
}

export async function getStatus(jobId: string): Promise<StatusResponse> {
  return {
    job_id: jobId,
    status: 'completed',
    progress_pct: 100,
    current_step: 'Analysis completed',
  };
}

export async function getResults(jobId: string): Promise<ScreeningResult> {
  const response = await apiClient.get<any>(`/api/v1/screenings/${jobId}`);
  return response.data;
}

export default apiClient;
