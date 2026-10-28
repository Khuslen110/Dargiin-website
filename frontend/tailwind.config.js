/** @type {import('tailwindcss').Config} */
export default {
  darkMode: "class",
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        fg: "rgb(var(--fg) / <alpha-value>)",
        night: {
          950: "rgb(var(--night-950) / <alpha-value>)",
          900: "rgb(var(--night-900) / <alpha-value>)",
          850: "rgb(var(--night-850) / <alpha-value>)",
          800: "rgb(var(--night-800) / <alpha-value>)",
          700: "rgb(var(--night-700) / <alpha-value>)",
          600: "rgb(var(--night-600) / <alpha-value>)",
          500: "rgb(var(--night-500) / <alpha-value>)",
        },
        acid: {
          200: "rgb(var(--acid-200) / <alpha-value>)",
          300: "rgb(var(--acid-300) / <alpha-value>)",
          400: "rgb(var(--acid-400) / <alpha-value>)",
          500: "rgb(var(--acid-500) / <alpha-value>)",
          600: "rgb(var(--acid-600) / <alpha-value>)",
        },
        clay: "#2dd4bf",
        brass: "#fbbf24",
      },
      fontFamily: {
        sans: [
          "ui-sans-serif",
          "system-ui",
          "-apple-system",
          "Segoe UI",
          "Roboto",
          "Helvetica Neue",
          "Arial",
          "Noto Sans",
          "sans-serif",
        ],
        mono: ["ui-monospace", "SFMono-Regular", "Menlo", "monospace"],
      },
      boxShadow: {
        card: "var(--shadow-card)",
        pop: "var(--shadow-pop)",
        glass: "var(--shadow-card)",
      },
      keyframes: {
        "fade-in": {
          from: { opacity: "0", transform: "translateY(4px)" },
          to: { opacity: "1", transform: "translateY(0)" },
        },
      },
      animation: {
        "fade-in": "fade-in 180ms ease-out",
      },
    },
  },
  plugins: [],
};
