/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,jsx}"],
  theme: {
    extend: {
      colors: {
        ink: "#0f172a",
        surface: "#f8fafc",
        accent: "#0f766e",
        accentSoft: "#ccfbf1",
        danger: "#dc2626",
        warning: "#d97706",
        success: "#15803d",
      },
      boxShadow: {
        panel: "0 16px 40px rgba(15, 23, 42, 0.08)",
      },
    },
  },
  plugins: [],
};
