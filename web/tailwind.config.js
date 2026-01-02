/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        // KDS Color Palette (fixed colors)
        kds: {
          primary: '#7823DC',
          'light-gray': '#D2D2D2',
          'medium-gray': '#A5A6A5',
          'dark-gray': '#787878',
          'light-purple': '#E0D2FA',
          'medium-light-purple': '#C8A5F0',
          'medium-purple': '#AF7DEB',
          'charcoal': '#4B4B4B',
          'kearney-black': '#1E1E1E',
          'bright-purple': '#9150E1',
          'accent-light': '#9B4DCA',
        },
        // Theme-aware colors (CSS variables)
        bg: {
          primary: 'var(--bg-primary)',
          secondary: 'var(--bg-secondary)',
          tertiary: 'var(--bg-tertiary)',
        },
        text: {
          primary: 'var(--text-primary)',
          secondary: 'var(--text-secondary)',
          tertiary: 'var(--text-tertiary)',
        },
        brand: {
          primary: 'var(--brand-primary)',
          accent: 'var(--brand-accent)',
          light: 'var(--brand-light)',
        },
        border: {
          primary: 'var(--border-primary)',
          secondary: 'var(--border-secondary)',
        },
      },
      fontFamily: {
        sans: ['Inter', '-apple-system', 'BlinkMacSystemFont', 'Segoe UI', 'Roboto', 'sans-serif'],
        mono: ['Fira Code', 'Courier New', 'monospace'],
      },
    },
  },
  plugins: [],
}
