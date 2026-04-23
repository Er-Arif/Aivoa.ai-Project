/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      fontFamily: {
        sans: ["Inter", "sans-serif"],
      },
      colors: {
        crm: {
          ink: "#182033",
          line: "#dfe3ea",
          muted: "#667085",
          panel: "#ffffff",
          bg: "#f5f6f8",
          blue: "#406de7",
        },
      },
      keyframes: {
        flash: {
          "0%": { backgroundColor: "#fef08a" },
          "100%": { backgroundColor: "#ffffff" },
        },
      },
      animation: {
        flash: "flash 1.2s ease-out",
      },
    },
  },
  plugins: [],
};
