import { Verdict } from "@/lib/types";
import { urgencyColors } from "@/styles/tokens";

interface VerdictBannerProps {
  verdict: Verdict;
}

export function VerdictBanner({ verdict }: VerdictBannerProps) {
  const palette = urgencyColors[verdict.level];

  return (
    <div
      className="rounded-lg px-4 py-3 mb-5 flex items-center gap-3"
      style={{ backgroundColor: palette.bg, borderLeft: `3px solid ${palette.border}` }}
    >
      <div>
        <div
          className="text-xs font-bold uppercase tracking-widest mb-0.5"
          style={{ color: palette.text }}
        >
          {verdict.level}
        </div>
        <div className="text-sm" style={{ color: "#0F172A" }}>
          {verdict.summary}
        </div>
      </div>
    </div>
  );
}
