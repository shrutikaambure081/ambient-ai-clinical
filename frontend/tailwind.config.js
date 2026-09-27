/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,ts,jsx,tsx}"],
  darkMode: "class",
  theme: {
    extend: {
      colors: {
        panel: "#111318",
        panel2: "#161a22",
        border: "#242833",
        accent: "#3b82f6",
        accentGreen: "#22c55e",
      },
    },
  },
  plugins: [],
};
