/** @type {import('tailwindcss').Config} */
export default {
  content: ['./src/**/*.{astro,html,js,jsx,md,mdx,svelte,ts,tsx,vue}'],
  theme: {
    extend: {
      colors: {
        cream: {
          50: '#FFFDF7',
          100: '#FDF6E3',
          200: '#FAF3E0',
          300: '#E8DCC8',
          400: '#D4A574',
          500: '#C4956A',
        },
        text: {
          primary: '#3D3D3D',
          secondary: '#6B6B6B',
        }
      },
      fontFamily: {
        heading: ['Crimson Pro', 'serif'],
        body: ['Source Sans 3', 'sans-serif'],
      },
      boxShadow: {
        card: '0 2px 8px rgba(0,0,0,0.08)',
      },
      borderRadius: {
        card: '8px',
      }
    },
  },
  plugins: [],
};
