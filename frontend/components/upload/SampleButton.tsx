interface SampleButtonProps {
  onLoad: (file: File) => void;
}

const SAMPLE_CBC = `CBC Blood Panel Report
Date: [DATE]
Report Type: Laboratory

Haemoglobin: 10.2 g/dL (Reference: 12.0-16.0 g/dL)
MCV: 72 fL (Reference: 80-100 fL)
MCH: 24 pg (Reference: 27-33 pg)
WBC: 6.2 x10^3/uL (Reference: 4.5-11.0 x10^3/uL)
Platelets: 210 x10^3/uL (Reference: 150-400 x10^3/uL)
Neutrophils: 65% (Reference: 40-75%)
`;

export function SampleButton({ onLoad }: SampleButtonProps) {
  function handleClick() {
    const blob = new Blob([SAMPLE_CBC], { type: "text/plain" });
    const file = new File([blob], "sample_cbc.txt", { type: "text/plain" });
    onLoad(file);
  }

  return (
    <button
      onClick={handleClick}
      className="mt-4 text-sm font-medium underline underline-offset-2 hover:opacity-70 transition-opacity"
      style={{ color: "#2563EB" }}
    >
      Try with a sample CBC report
    </button>
  );
}
