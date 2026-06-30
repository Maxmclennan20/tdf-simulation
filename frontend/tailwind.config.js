/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{ts,tsx}'],
  theme: {
    extend: {
      colors: {
        surface: '#0d0f17',
        panel: '#13161f',
        card: '#1c2030',
        border: '#272c3d',
      },
    },
  },
  plugins: [],
}
