import type { Config } from "tailwindcss";

const config: Config = {
  content: ["./app/**/*.{ts,tsx}", "./components/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        bg:      "#0e0b1e",
        card:    "#16122a",
        border:  "#2d2060",
        primary: "#7c3aed",
        accent:  "#06b6d4",
        muted:   "#a89ec9",
        text:    "#f0eeff",
      },
    },
  },
  plugins: [],
};
export default config;
