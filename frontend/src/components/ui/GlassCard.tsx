import React, { useRef } from 'react';

interface GlassCardProps extends React.HTMLAttributes<HTMLDivElement> {
  variant?: 'light' | 'dark';
  hover?: boolean;
  glow?: boolean;
  tilt?: boolean;
}

export const GlassCard = React.forwardRef<HTMLDivElement, GlassCardProps>(
  ({ variant = 'light', hover = false, glow = false, tilt = false, className = '', children, style, ...props }, ref) => {
    const innerRef = useRef<HTMLDivElement>(null);
    const combinedRef = (ref as React.RefObject<HTMLDivElement>) || innerRef;

    const handleMouseMove = (e: React.MouseEvent<HTMLDivElement>) => {
      if (!tilt) return;
      const el = combinedRef.current;
      if (!el) return;
      const rect = el.getBoundingClientRect();
      const x = (e.clientX - rect.left) / rect.width  - 0.5;
      const y = (e.clientY - rect.top)  / rect.height - 0.5;
      el.style.transform = `perspective(600px) rotateY(${x * 6}deg) rotateX(${-y * 6}deg) translateY(-2px)`;
    };

    const handleMouseLeave = () => {
      if (!tilt) return;
      const el = combinedRef.current;
      if (el) el.style.transform = '';
    };

    return (
      <div
        ref={combinedRef}
        className={`card ${glow ? 'card-glow' : ''} ${className}`}
        style={{
          transition: 'transform 0.15s ease, border-color 0.28s ease, box-shadow 0.28s ease',
          ...style,
        }}
        onMouseMove={handleMouseMove}
        onMouseLeave={handleMouseLeave}
        {...props}
      >
        {children}
      </div>
    );
  }
);
GlassCard.displayName = 'GlassCard';
