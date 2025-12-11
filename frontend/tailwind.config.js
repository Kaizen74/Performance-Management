/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        // Strategic scoring colors
        tier: {
          high: '#0D9488',      // Deep teal for high alignment (>80)
          moderate: '#F59E0B',  // Amber for moderate (50-79)
          low: '#E11D48',       // Rose for low (<50)
        },
        // Brand colors
        brand: {
          primary: '#1E40AF',   // Blue
          secondary: '#7C3AED', // Purple
        }
      },
      fontFamily: {
        display: ['Clash Display', 'Inter', 'sans-serif'],
        sans: ['DM Sans', 'Inter', 'sans-serif'],
      },
    },
  },
  plugins: [],
}
