interface QuestionListProps {
  questions: string[];
}

export function QuestionList({ questions }: QuestionListProps) {
  return (
    <div>
      <h3 className="text-base font-semibold mb-4" style={{ color: "#0F172A" }}>
        Questions to ask your doctor
      </h3>
      <ol className="space-y-3">
        {questions.map((q, i) => (
          <li
            key={i}
            className="flex gap-3 text-sm leading-relaxed"
            style={{ color: "#0F172A" }}
          >
            <span
              className="flex-shrink-0 w-6 h-6 rounded-full flex items-center justify-center text-xs font-bold text-white"
              style={{ backgroundColor: "#2563EB" }}
            >
              {i + 1}
            </span>
            {q}
          </li>
        ))}
      </ol>
    </div>
  );
}
