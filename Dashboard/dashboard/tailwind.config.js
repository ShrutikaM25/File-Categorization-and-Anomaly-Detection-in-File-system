/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./src/**/*.{js,jsx,ts,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        darkPurple: "#2A004E",   // Dark Purple
        deepViolet: "#500073", // Deep Violet
        strongRed: "#C62300",    // Strong Red
        brightOrange: "#F14A00", // Bright Orange
      },
    },
  },
  plugins: [],
};
