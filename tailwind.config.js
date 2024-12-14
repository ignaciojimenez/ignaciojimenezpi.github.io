/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./index.html",
    "./photography/**/*.{html,js}",
    "./music/**/*.{html,js}"
  ],
  theme: {
    extend: {
      fontFamily: {
        sans: ['Inter', 'sans-serif'],
      },
    }
  },
  plugins: [],
}
