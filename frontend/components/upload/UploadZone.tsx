import { useRef, useState, DragEvent, ChangeEvent } from "react";

interface UploadZoneProps {
  onFile: (file: File) => void;
  disabled?: boolean;
}

export function UploadZone({ onFile, disabled = false }: UploadZoneProps) {
  const [dragging, setDragging] = useState(false);
  const inputRef = useRef<HTMLInputElement>(null);

  function handleDrop(e: DragEvent<HTMLDivElement>) {
    e.preventDefault();
    setDragging(false);
    const file = e.dataTransfer.files[0];
    if (file) onFile(file);
  }

  function handleChange(e: ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0];
    if (file) onFile(file);
  }

  return (
    <div
      onDragOver={(e) => { e.preventDefault(); setDragging(true); }}
      onDragLeave={() => setDragging(false)}
      onDrop={handleDrop}
      onClick={() => !disabled && inputRef.current?.click()}
      className="border-2 border-dashed rounded-xl p-12 flex flex-col items-center justify-center cursor-pointer transition-colors"
      style={{
        borderColor: dragging ? "#2563EB" : "#CBD5E1",
        backgroundColor: dragging ? "#EFF6FF" : "#FFFFFF",
        opacity: disabled ? 0.6 : 1,
        cursor: disabled ? "not-allowed" : "pointer",
      }}
    >
      <svg width="40" height="40" viewBox="0 0 24 24" fill="none" stroke="#6B7280" strokeWidth="1.5" className="mb-4">
        <path d="M21 15v4a2 2 0 01-2 2H5a2 2 0 01-2-2v-4" />
        <polyline points="17 8 12 3 7 8" />
        <line x1="12" y1="3" x2="12" y2="15" />
      </svg>
      <p className="text-base font-semibold mb-1" style={{ color: "#0F172A" }}>
        Drop your medical report here
      </p>
      <p className="text-sm" style={{ color: "#6B7280" }}>
        PDF or plain text · max 10 MB
      </p>
      <input
        ref={inputRef}
        type="file"
        accept=".pdf,.txt"
        className="hidden"
        onChange={handleChange}
        disabled={disabled}
      />
    </div>
  );
}
