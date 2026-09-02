import React from 'react';

interface SectionProps extends React.HTMLAttributes<HTMLElement> {
  children: React.ReactNode;
  container?: boolean;
  centered?: boolean;
}

export const Section = React.forwardRef<HTMLElement, SectionProps>(
  ({ children, container = true, centered = false, className, ...props }, ref) => {
    return (
      <section
        ref={ref}
        className={`
          py-12 md:py-20 lg:py-28
          ${centered ? 'flex items-center justify-center' : ''}
          ${className}
        `}
        {...props}
      >
        {container ? (
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
            {children}
          </div>
        ) : (
          children
        )}
      </section>
    );
  }
);

Section.displayName = 'Section';

interface ContainerProps extends React.HTMLAttributes<HTMLDivElement> {
  children: React.ReactNode;
  size?: 'sm' | 'md' | 'lg' | 'full';
}

export const Container = React.forwardRef<HTMLDivElement, ContainerProps>(
  ({ children, size = 'lg', className, ...props }, ref) => {
    const sizeClasses = {
      sm: 'max-w-2xl',
      md: 'max-w-4xl',
      lg: 'max-w-7xl',
      full: 'w-full',
    };

    return (
      <div
        ref={ref}
        className={`
          mx-auto px-4 sm:px-6 lg:px-8
          ${sizeClasses[size]}
          ${className}
        `}
        {...props}
      >
        {children}
      </div>
    );
  }
);

Container.displayName = 'Container';
