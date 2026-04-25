import { Finding } from "@/lib/types";
import { FindingCard } from "./FindingCard";

interface FindingsListProps {
  findings: Finding[];
  filterUrgency?: boolean;
}

export function FindingsList({ findings, filterUrgency = false }: FindingsListProps) {
  const displayed = filterUrgency
    ? findings.filter((f) => f.urgency !== "normal")
    : findings;

  if (displayed.length === 0) {
    return (
      <p className="text-sm text-center py-8" style={{ color: "#6B7280" }}>
        {filterUrgency ? "No flagged findings." : "No findings to display."}
      </p>
    );
  }

  return (
    <div>
      {displayed.map((f) => (
        <FindingCard key={f.name} finding={f} />
      ))}
    </div>
  );
}
