/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        clinical: {
          canvas: '#F8FAFC',
          card: '#FFFFFF',
          border: '#E2E8F0',
          darkBorder: '#CBD5E1',
          primary: '#0D9488', // Muted clinical teal
          primaryHover: '#0F766E',
          primaryLight: '#F0FDFA',
          accent: '#0284C7', // Slate cyan
          accentLight: '#F0F9FF',
          textMain: '#0F172A',
          textMuted: '#475569',
          textDim: '#94A3B8',
          success: '#10B981',
          danger: '#EF4444',
          warning: '#F59E0B',
        }
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', '-apple-system', 'Segoe UI', 'Roboto', 'sans-serif'],
      },
      animation: {
        'highlight-booked': 'highlightBooked 2.5s ease-out forwards',
        'highlight-cancelled': 'highlightCancelled 2.5s ease-out forwards',
        'pulse-subtle': 'pulseSubtle 2s cubic-bezier(0.4, 0, 0.6, 1) infinite',
      },
      keyframes: {
        highlightBooked: {
          '0%': { backgroundColor: '#CCFBF1', borderColor: '#14B8A6' },
          '100%': { backgroundColor: '#FFFFFF', borderColor: '#E2E8F0' },
        },
        highlightCancelled: {
          '0%': { backgroundColor: '#FEE2E2', borderColor: '#F87171' },
          '100%': { backgroundColor: '#FFFFFF', borderColor: '#E2E8F0' },
        },
        pulseSubtle: {
          '0%, 100%': { opacity: '1' },
          '50%': { opacity: '0.4' },
        }
      }
    },
  },
  plugins: [],
}
