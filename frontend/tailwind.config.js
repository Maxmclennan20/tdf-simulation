/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{ts,tsx}'],
  theme: {
    extend: {
      colors: {
        surface: '#f4f6fa',
        panel: '#ffffff',
        card: '#eef1f6',
        border: '#dde3ed',
      },
    },
  },
  plugins: [],
}
