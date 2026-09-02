import React from 'react';

interface SpinnerProps {
  size?: 'sm' | 'md' | 'lg';
  variant?: 'primary' | 'secondary';
}

export const Spinner: React.FC<SpinnerProps> = ({ size = 'md' }) => {
  const dim = { sm: 16, md: 32, lg: 48 }[size];
  return (
    <svg
      width={dim} height={dim}
      viewBox="0 0 32 32"
      fill="none"
      className="animate-spin"
      aria-label="Loading"
    >
      <circle cx="16" cy="16" r="13" stroke="rgba(255,255,255,0.08)" strokeWidth="2" />
      <path
        d="M16 3 A13 13 0 0 1 29 16"
        stroke="rgba(255,255,255,0.7)"
        strokeWidth="2"
        strokeLinecap="round"
      />
    </svg>
  );
};

interface LoadingOverlayProps {
  isVisible: boolean;
  message?: string;
}

export const LoadingOverlay: React.FC<LoadingOverlayProps> = ({ isVisible, message = 'Processing…' }) => {
  if (!isVisible) return null;
  return (
    <div className="fixed inset-0 bg-black/70 backdrop-blur-sm flex items-center justify-center z-50">
      <div className="glass-2 rounded-xl p-10 text-center max-w-xs mx-4 flex flex-col items-center gap-4">
        {/* Pulse rings */}
        <div className="relative w-16 h-16 flex items-center justify-center">
          <span className="absolute inset-0 rounded-full border border-white/10 animate-pulse-ring" />
          <span className="absolute inset-2 rounded-full border border-white/10 animate-pulse-ring" style={{ animationDelay: '0.4s' }} />
          <Spinner size="md" />
        </div>
        <p className="t-small text-text-2">{message}</p>
      </div>
    </div>
  );
};
