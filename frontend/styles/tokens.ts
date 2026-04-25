export const colors = {
  navy: "#E05A00",
  blue: "#E05A00",
  orange: "#E05A00",
  green: "#1E8B5A",
  amber: "#C87F0A",
  red: "#C0392B",
  surface: "#F5F7FA",
  border: "#E0E0E0",
  textPrimary: "#1A1A1A",
  textSecondary: "#6B7280",
  white: "#FFFFFF",
} as const;

export const urgencyColors = {
  normal: { bg: "#E8F5EE", text: "#1E8B5A", border: "#1E8B5A" },
  watch: { bg: "#FEF9E7", text: "#C87F0A", border: "#C87F0A" },
  urgent: { bg: "#FDEDEC", text: "#C0392B", border: "#C0392B" },
} as const;
