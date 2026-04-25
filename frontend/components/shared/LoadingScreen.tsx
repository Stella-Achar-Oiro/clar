const AGENT_STEPS = [
  "Extracting report text...",
  "Removing personal information...",
  "Analysing findings...",
  "Flagging urgency levels...",
  "Generating doctor questions...",
];

interface LoadingScreenProps {
  currentStep?: number;
}

export function LoadingScreen({ currentStep = 0 }: LoadingScreenProps) {
  return (
    <div className="flex flex-col items-center justify-center min-h-64 px-6">
      <div className="mb-6">
        <div
          className="w-12 h-12 rounded-full border-4 border-t-transparent animate-spin"
          style={{ borderColor: "#E05A00", borderTopColor: "transparent" }}
        />
      </div>
      <h3 className="text-lg font-semibold mb-4" style={{ color: "#0F172A" }}>
        Analysing your report
      </h3>
      <div className="w-full max-w-xs space-y-2">
        {AGENT_STEPS.map((step, i) => (
          <div key={step} className="flex items-center gap-3">
            <div
              className="w-5 h-5 rounded-full flex-shrink-0 flex items-center justify-center"
              style={{
                backgroundColor: i < currentStep ? "#1E8B5A" : i === currentStep ? "#E05A00" : "#E0E0E0",
              }}
            >
              {i < currentStep && (
                <svg width="10" height="10" viewBox="0 0 24 24" fill="none" stroke="white" strokeWidth="3">
                  <polyline points="20 6 9 17 4 12" />
                </svg>
              )}
            </div>
            <span
              className="text-sm"
              style={{
                color: i <= currentStep ? "#0F172A" : "#6B7280",
                fontWeight: i === currentStep ? 600 : 400,
              }}
            >
              {step}
            </span>
          </div>
        ))}
      </div>
    </div>
  );
}
