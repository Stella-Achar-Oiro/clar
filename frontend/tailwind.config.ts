import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./pages/**/*.{js,ts,jsx,tsx}",
    "./components/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      fontFamily: {
        sans: ["IBM Plex Sans", "sans-serif"],
      },
      colors: {
        navy: "#1B2A4A",
        cblue: "#2563EB",
        cgreen: "#1E8B5A",
        amber: "#C87F0A",
        danger: "#C0392B",
      },
    },
  },
  plugins: [require("@tailwindcss/typography")],
};

export default config;
