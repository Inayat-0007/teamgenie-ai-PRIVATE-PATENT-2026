/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    './app/**/*.{js,ts,jsx,tsx,mdx}',
    './components/**/*.{js,ts,jsx,tsx,mdx}',
    './lib/**/*.{js,ts,jsx,tsx}',
  ],
  darkMode: 'class',
  theme: {
    extend: {
      fontFamily: {
        sans: ['var(--font-inter)', 'system-ui', 'sans-serif'],
      },
      colors: {
        primary: {
          DEFAULT: '#6366f1',
          hover: '#818cf8',
          50: '#eef2ff',
          100: '#e0e7ff',
          200: '#c7d2fe',
          300: '#a5b4fc',
          400: '#818cf8',
          500: '#6366f1',
          600: '#4f46e5',
          700: '#4338ca',
          800: '#3730a3',
          900: '#312e81',
          950: '#1e1b4b',
        },
        accent: {
          DEFAULT: '#22d3ee',
          dark: '#06b6d4',
          light: '#67e8f9',
        },
        surface: {
          DEFAULT: 'rgba(255, 255, 255, 0.05)',
          hover: 'rgba(255, 255, 255, 0.08)',
          active: 'rgba(255, 255, 255, 0.12)',
        },
      },
      borderRadius: {
        '2xl': '16px',
        '3xl': '24px',
      },
      boxShadow: {
        glow: '0 0 40px rgba(99, 102, 241, 0.15), 0 0 80px rgba(34, 211, 238, 0.1)',
        'glow-lg': '0 0 60px rgba(99, 102, 241, 0.25), 0 0 120px rgba(34, 211, 238, 0.15)',
      },
      animation: {
        'pulse-glow': 'pulse-glow 2s ease-in-out infinite',
        shimmer: 'shimmer 1.5s infinite',
      },
      keyframes: {
        'pulse-glow': {
          '0%, 100%': { opacity: '1' },
          '50%': { opacity: '0.5' },
        },
        shimmer: {
          '0%': { backgroundPosition: '-200% 0' },
          '100%': { backgroundPosition: '200% 0' },
        },
      },
      backdropBlur: {
        xs: '2px',
      },
    },
  },
  plugins: [],
};
