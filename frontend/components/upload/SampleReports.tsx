const SAMPLES: { label: string; filename: string; content: string }[] = [
  {
    label: "Lab report",
    filename: "sample_lab.txt",
    content: `CBC Blood Panel Report
Date: [DATE]
Report Type: Laboratory

Haemoglobin: 10.2 g/dL (Reference: 12.0-16.0 g/dL)
MCV: 72 fL (Reference: 80-100 fL)
MCH: 24 pg (Reference: 27-33 pg)
WBC: 6.2 x10^3/uL (Reference: 4.5-11.0 x10^3/uL)
Platelets: 210 x10^3/uL (Reference: 150-400 x10^3/uL)
Neutrophils: 65% (Reference: 40-75%)
`,
  },
  {
    label: "Radiology report",
    filename: "sample_radiology.txt",
    content: `Radiology Report
Date: [DATE]

PROCEDURE: Chest X-Ray PA and Lateral

FINDINGS:
Mild consolidation in the right lower lobe. Cardiac silhouette within normal limits.
No pleural effusion identified. Costophrenic angles are clear.
Mediastinal contour is normal. No pneumothorax.

IMPRESSION:
Findings consistent with early community-acquired pneumonia, right lower lobe.
Follow-up chest X-ray recommended in 6 weeks to confirm resolution.
`,
  },
  {
    label: "Discharge summary",
    filename: "sample_discharge.txt",
    content: `Discharge Summary
Date: [DATE]

PRINCIPAL DIAGNOSIS: Community-acquired pneumonia, right lower lobe

SECONDARY DIAGNOSES:
- Type 2 diabetes mellitus
- Hypertension

DISCHARGE MEDICATIONS:
- Amoxicillin 500mg PO TID x 7 days
- Metformin 500mg PO BID (continue home dose)
- Lisinopril 10mg PO OD (continue home dose)

INVESTIGATIONS:
WBC: 14.2 x10^3/uL (Reference: 4.5-11.0 x10^3/uL) — elevated, consistent with infection
CRP: 85 mg/L (Reference: 0-5 mg/L) — markedly elevated
Haemoglobin: 11.8 g/dL (Reference: 12.0-16.0 g/dL) — mildly low

CLINICAL COURSE:
Patient presented with 3 days of productive cough, fever, and shortness of breath.
Treated with IV antibiotics for 48 hours, then stepped down to oral.
Oxygen requirements resolved by day 2. Clinically improved for discharge.

FOLLOW-UP:
- GP review in 1 week
- Repeat chest X-ray in 6 weeks to confirm resolution
- Diabetic nurse review for glucose optimisation
`,
  },
  {
    label: "Pathology report",
    filename: "sample_pathology.txt",
    content: `Histopathology Report
Date: [DATE]
Specimen ID: PATH-2026-0042

CLINICAL INFORMATION:
Right breast lump, query carcinoma. Core needle biopsy.

MICROSCOPIC DESCRIPTION:
Sections show invasive ductal carcinoma, no special type (NST).
Nuclear pleomorphism is moderate. Mitotic count: 8 per 10 high-power fields.
No lymphovascular invasion identified.

IMMUNOHISTOCHEMISTRY:
ER (Oestrogen Receptor): POSITIVE (Allred score 7/8, 90% of cells)
PR (Progesterone Receptor): POSITIVE (Allred score 6/8, 70% of cells)
HER2: NEGATIVE (IHC 1+)
Ki-67 Proliferation Index: 22%

TUMOUR GRADE (Nottingham): Grade 2 (Intermediate) — 7/9

SURGICAL MARGINS:
Margins clear. Minimum clearance: 3.2mm (posterior margin).

CONCLUSION:
Invasive ductal carcinoma, Grade 2. ER positive, PR positive, HER2 negative.
Margins clear (>3mm).
`,
  },
];

interface SampleReportsProps {
  onLoad: (file: File) => void;
}

export function SampleReports({ onLoad }: SampleReportsProps) {
  function loadSample(sample: typeof SAMPLES[0]) {
    const blob = new Blob([sample.content], { type: "text/plain" });
    const file = new File([blob], sample.filename, { type: "text/plain" });
    onLoad(file);
  }

  return (
    <div className="mt-5">
      <p className="text-xs text-center mb-3" style={{ color: "#9CA3AF" }}>
        Or try a sample report
      </p>
      <div className="flex flex-wrap justify-center gap-2">
        {SAMPLES.map((s) => (
          <button
            key={s.filename}
            onClick={() => loadSample(s)}
            className="px-3 py-1.5 rounded-full text-xs font-medium border transition-colors hover:opacity-80"
            style={{
              borderColor: "#E05A00",
              color: "#E05A00",
              backgroundColor: "#FFF3ED",
            }}
          >
            {s.label}
          </button>
        ))}
      </div>
    </div>
  );
}
