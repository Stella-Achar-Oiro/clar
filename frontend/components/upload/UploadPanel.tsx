import { UploadZone } from "./UploadZone";
import { SampleReports } from "./SampleReports";
import { TrustBadges } from "./TrustBadges";

interface UploadPanelProps {
  onFile: (file: File) => void;
}

export function UploadPanel({ onFile }: UploadPanelProps) {
  return (
    <div className="max-w-xl mx-auto px-6 py-16">
      <div className="text-center mb-8">
        <h1 className="text-2xl font-bold mb-2" style={{ color: "#E05A00" }}>
          Understand your medical report
        </h1>
        <p className="text-sm" style={{ color: "#6B7280" }}>
          Upload a lab result, radiology report, or discharge summary.
          CLAR explains it in plain English.
        </p>
      </div>
      <UploadZone onFile={onFile} />
      <SampleReports onLoad={onFile} />
      <TrustBadges />
    </div>
  );
}
