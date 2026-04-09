import { Platform } from "react-native";

export const colors = {
  background: "#F4EFE8",
  backgroundAlt: "#FFF9F2",
  panel: "#1D3140",
  panelMuted: "#294454",
  paper: "#FFFDF8",
  paperAlt: "#F7F0E8",
  paperLine: "#E6D8C7",
  outline: "#D8CABB",
  ink: "#1B2028",
  muted: "#8B98A6",
  mutedDark: "#66727E",
  textOnDark: "#FFF7EF",
  subtleText: "#D3DFE7",
  accent: "#F46B4E",
  accentSoft: "#FFD4C7",
  deepAccent: "#2C5262",
  mint: "#A6D9C8",
  sun: "#F2C779",
  sky: "#B7D8F3",
  successBg: "#E8F5EF",
  successText: "#255440",
  errorBg: "#FFE3DA",
  errorText: "#922F1A",
};

export const fonts = {
  display: Platform.select({
    ios: "Avenir Next",
    android: "serif",
    default: "serif",
  }),
  body: Platform.select({
    ios: "Avenir Next",
    android: "sans-serif",
    default: "sans-serif",
  }),
  mono: Platform.select({
    ios: "Menlo",
    android: "monospace",
    default: "monospace",
  }),
};
