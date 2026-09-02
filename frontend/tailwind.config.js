/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,ts,jsx,tsx}'],
  theme: {
    extend: {
      colors: {
        'bg-0': '#000000', 'bg-1': '#060606', 'bg-2': '#0e0e0e', 'bg-3': '#161616', 'bg-4': '#222222',
        'surface-1': 'rgba(255,255,255,0.03)', 'surface-2': 'rgba(255,255,255,0.06)', 'surface-3': 'rgba(255,255,255,0.10)',
        'text-0': '#ffffff', 'text-1': '#e8e8e8', 'text-2': '#a0a0a0', 'text-3': '#505050',
        'border-1': 'rgba(255,255,255,0.05)', 'border-2': 'rgba(255,255,255,0.10)', 'border-3': 'rgba(255,255,255,0.18)',
        'c-success': '#22c55e', 'c-warning': '#f59e0b', 'c-error': '#ef4444', 'c-processing': '#06b6d4',
        'c-medical': '#dc2626', 'c-retina': '#b91c1c',
        // legacy aliases
        'bg-primary': '#000000', 'bg-secondary': '#0e0e0e', 'bg-tertiary': '#161616',
        'text-primary': '#e8e8e8', 'text-secondary': '#a0a0a0', 'text-tertiary': '#505050',
        'accent-primary': '#06b6d4', 'accent-secondary': '#818cf8',
        'accent-medical': '#ef4444', 'accent-warning': '#f59e0b', 'accent-success': '#22c55e',
      },
      fontFamily: {
        sans:    ['Inter', 'system-ui', 'sans-serif'],
        display: ['Syne', 'sans-serif'],
        mono:    ['IBM Plex Mono', 'monospace'],
      },
      borderRadius: { sm: '4px', base: '8px', lg: '14px', xl: '22px', pill: '9999px' },
      keyframes: {
        float:      { '0%,100%': { transform: 'translateY(0)' }, '50%': { transform: 'translateY(-12px)' } },
        breathe:    { '0%,100%': { opacity: '0.35', transform: 'scale(1)' }, '50%': { opacity: '0.65', transform: 'scale(1.04)' } },
        'pulse-ring':{ '0%': { transform: 'scale(0.85)', opacity: '0.9' }, '100%': { transform: 'scale(2.6)', opacity: '0' } },
        'spin-slow': { from: { transform: 'rotate(0deg)' }, to: { transform: 'rotate(360deg)' } },
        flicker:    { '0%,100%': { opacity: '1' }, '92%': { opacity: '1' }, '93%': { opacity: '0.4' }, '94%': { opacity: '1' }, '96%': { opacity: '0.6' }, '97%': { opacity: '1' } },
        shimmer:    { '0%': { backgroundPosition: '-200% 0' }, '100%': { backgroundPosition: '200% 0' } },
        drawLine:   { from: { strokeDashoffset: '1000' }, to: { strokeDashoffset: '0' } },
        scan:       { '0%': { top: '-2px', opacity: '0' }, '5%': { opacity: '1' }, '95%': { opacity: '1' }, '100%': { top: '100%', opacity: '0' } },
        revealUp:   { from: { opacity: '0', transform: 'translateY(32px)' }, to: { opacity: '1', transform: 'translateY(0)' } },
        revealBlur: { from: { opacity: '0', filter: 'blur(12px)', transform: 'translateY(16px)' }, to: { opacity: '1', filter: 'blur(0)', transform: 'translateY(0)' } },
      },
      animation: {
        'float':      'float 5s ease-in-out infinite',
        'breathe':    'breathe 4s ease-in-out infinite',
        'pulse-ring': 'pulse-ring 2.8s ease-out infinite',
        'spin-slow':  'spin-slow 20s linear infinite',
        'flicker':    'flicker 8s ease-in-out infinite',
        'shimmer':    'shimmer 1.6s infinite',
        'reveal-up':  'revealUp 0.5s cubic-bezier(0.16,1,0.3,1) both',
        'reveal-blur':'revealBlur 0.5s cubic-bezier(0.16,1,0.3,1) both',
      },
    },
  },
  plugins: [],
};
