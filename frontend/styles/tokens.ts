export const colors = {
  navy: "#1B2A4A",
  blue: "#2563EB",
  green: "#1E8B5A",
  amber: "#C87F0A",
  red: "#C0392B",
  surface: "#F5F7FA",
  border: "#E0E0E0",
  textPrimary: "#0F172A",
  textSecondary: "#6B7280",
  white: "#FFFFFF",
} as const;

export const urgencyColors = {
  normal: { bg: "#E8F5EE", text: "#1E8B5A", border: "#1E8B5A" },
  watch: { bg: "#FEF9E7", text: "#C87F0A", border: "#C87F0A" },
  urgent: { bg: "#FDEDEC", text: "#C0392B", border: "#C0392B" },
} as const;
