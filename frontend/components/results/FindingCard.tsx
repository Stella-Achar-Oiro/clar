import { useState } from "react";
import { Finding } from "@/lib/types";
import { urgencyColors } from "@/styles/tokens";

interface FindingCardProps {
  finding: Finding;
}

export function FindingCard({ finding }: FindingCardProps) {
  const [expanded, setExpanded] = useState(finding.urgency !== "normal");
  const palette = urgencyColors[finding.urgency];

  return (
    <div
      className="rounded-xl mb-3 overflow-hidden"
      style={{ border: `1px solid #E0E0E0`, boxShadow: "0 1px 4px rgba(0,0,0,0.06)" }}
    >
      <button
        className="w-full flex items-center gap-3 px-4 py-3.5 text-left"
        onClick={() => setExpanded((v) => !v)}
      >
        <div className="flex-1">
          <div className="font-semibold text-sm" style={{ color: "#0F172A" }}>
            {finding.name}
          </div>
          <div className="text-xs mt-0.5" style={{ color: "#6B7280" }}>
            {finding.value} &nbsp;&middot;&nbsp; Ref: {finding.reference_range}
          </div>
        </div>
        <span
          className="text-xs font-bold uppercase px-2.5 py-0.5 rounded-full tracking-wide"
          style={{ backgroundColor: palette.bg, color: palette.text }}
        >
          {finding.urgency}
        </span>
        <svg
          width="12"
          height="12"
          viewBox="0 0 24 24"
          fill="none"
          stroke="#6B7280"
          strokeWidth="2"
          style={{ transform: expanded ? "rotate(90deg)" : "none", transition: "transform 0.15s" }}
        >
          <polyline points="9 18 15 12 9 6" />
        </svg>
      </button>

      {expanded && (
        <div
          className="px-4 pb-4 text-sm leading-relaxed"
          style={{ borderTop: "1px solid #F5F7FA", paddingTop: "0.75rem", color: "#0F172A" }}
        >
          {finding.explanation}
          {finding.urgency_reason && (
            <div
              className="mt-2 text-xs px-2.5 py-1.5 rounded"
              style={{ backgroundColor: palette.bg, color: palette.text }}
            >
              {finding.urgency_reason}
            </div>
          )}
        </div>
      )}
    </div>
  );
}
