/** @type {import('tailwindcss').Config} */
export default {
  darkMode: "class",

  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],

  theme: {
    extend: {
      colors: {
        brand: {
          50: "#fff6f1",
          100: "#ffe9dc",
          500: "#d96b3f",
          600: "#c45a32",
          700: "#9f4529",
        },
      },

      boxShadow: {
        "soft-panel":
          "0 12px 36px rgba(39, 25, 30, 0.06)",
        "dark-panel":
          "0 20px 55px rgba(0, 0, 0, 0.24)",
      },
    },
  },

  plugins: [],
};
