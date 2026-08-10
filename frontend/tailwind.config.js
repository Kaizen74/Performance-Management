/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        // Score tiers. Teal / amber / rose reads in grayscale and avoids a
        // red-green pairing; every use is paired with a text or symbol cue
        // so status never depends on hue alone.
        tier: {
          high: '#0D9488',      // high alignment (>=80)
          moderate: '#F59E0B',  // moderate (50-79)
          low: '#E11D48',       // low (<50)
        },
        // Brand. `primary` is the interactive blue used for buttons, links,
        // and selected states; `deep` anchors headers and the wordmark.
        brand: {
          primary: '#2563EB',
          hover: '#1D4ED8',
          deep: '#1E40AF',
          subtle: '#EFF6FF',
        },
      },
      fontFamily: {
        // One family, actually loaded in index.html. A second display face was
        // previously declared here but never loaded or referenced, so every
        // `font-display` class silently fell back to the system stack.
        sans: ['DM Sans', 'Inter', 'system-ui', 'sans-serif'],
      },
    },
  },
  plugins: [],
}
