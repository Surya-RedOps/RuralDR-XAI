import { useState, useCallback } from 'react';
import * as api from '@/services/api';
import { ScreeningResult } from '@/types/api';

export interface ProcessingState {
  status: 'idle' | 'uploading' | 'processing' | 'completed' | 'failed';
  progress: number;
  currentStep: string;
  uploadId?: string;
  jobId?: string;
  error?: string;
  results?: ScreeningResult;
}

const initialState: ProcessingState = {
  status: 'idle',
  progress: 0,
  currentStep: '',
};

export function useProcessing() {
  const [state, setState] = useState<ProcessingState>(initialState);

  /**
   * Upload an image file
   */
  const uploadImage = useCallback(async (file: File): Promise<string> => {
    setState(prev => ({ ...prev, status: 'uploading', progress: 0 }));

    try {
      const result = await api.uploadImage(file);
      setState(prev => ({ ...prev, uploadId: result.upload_id }));
      return result.upload_id;
    } catch (error) {
      const errorMsg = error instanceof Error ? error.message : 'Upload failed';
      setState(prev => ({
        ...prev,
        status: 'failed',
        error: errorMsg,
      }));
      throw error;
    }
  }, []);

  /**
   * Process an uploaded image
   */
  const processImage = useCallback(
    async (uploadId: string, runSegmentation = true): Promise<ScreeningResult> => {
      setState(prev => ({ ...prev, status: 'processing', progress: 0 }));

      try {
        // Start processing
        const jobData = await api.processImage(uploadId, runSegmentation);
        const jobId = jobData.job_id;

        setState(prev => ({ ...prev, jobId }));

        // Poll for completion
        let completed = false;
        while (!completed) {
          const statusData = await api.getStatus(jobId);

          setState(prev => ({
            ...prev,
            progress: statusData.progress_pct,
            currentStep: statusData.current_step,
          }));

          if (statusData.status === 'completed') {
            completed = true;
            // Fetch full results
            const results = await api.getResults(jobId);
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
              error: statusData.error || 'Processing failed',
            }));
            throw new Error(statusData.error || 'Processing failed');
          }

          // Wait before next poll
          await new Promise(resolve => setTimeout(resolve, 1000));
        }

        throw new Error('Unexpected processing state');
      } catch (error) {
        const errorMsg = error instanceof Error ? error.message : 'Processing failed';
        setState(prev => ({
          ...prev,
          status: 'failed',
          error: errorMsg,
        }));
        throw error;
      }
    },
    []
  );

  /**
   * Reset processing state
   */
  const reset = useCallback(() => {
    setState(initialState);
  }, []);

  return {
    state,
    uploadImage,
    processImage,
    reset,
  };
}
