import type { Config } from "tailwindcss";

const config: Config = {
  content: ["./app/**/*.{ts,tsx}", "./components/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        ink: "#0f172a",
        paper: "#f5f7ff",
        accent: "#6366f1",       // indigo-500
        accentSoft: "#eef2ff",   // indigo-50 for pills
        sidebar: "#eef1ff",      // lavender-tinted sidebar bg
      },
      fontFamily: {
        sans: ["ui-sans-serif", "system-ui", "-apple-system", "Segoe UI", "sans-serif"],
      },
      boxShadow: {
        soft: "0 1px 2px rgba(15,23,42,0.04), 0 8px 24px rgba(15,23,42,0.04)",
      },
    },
  },
  plugins: [],
};

export default config;
