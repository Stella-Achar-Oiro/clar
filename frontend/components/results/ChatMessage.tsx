import ReactMarkdown from "react-markdown";
import { colors } from "@/styles/tokens";

interface ChatMessageProps {
  role: "user" | "assistant";
  text: string;
}

export function ChatMessage({ role, text }: ChatMessageProps) {
  return (
    <div className={`flex ${role === "user" ? "justify-end" : "justify-start"}`}>
      <div
        className="text-sm rounded-xl px-4 py-3"
        style={
          role === "user"
            ? { backgroundColor: colors.blue, color: colors.white, maxWidth: "75%" }
            : { backgroundColor: colors.surface, color: colors.textPrimary, maxWidth: "90%" }
        }
      >
        {role === "assistant" ? (
          <ReactMarkdown
            components={{
              p: ({ children }) => <p className="mb-2 last:mb-0 leading-relaxed">{children}</p>,
              strong: ({ children }) => <strong className="font-semibold">{children}</strong>,
              em: ({ children }) => <em className="italic">{children}</em>,
              ul: ({ children }) => <ul className="list-disc pl-4 mb-2 space-y-0.5">{children}</ul>,
              ol: ({ children }) => <ol className="list-decimal pl-4 mb-2 space-y-0.5">{children}</ol>,
              li: ({ children }) => <li className="leading-relaxed">{children}</li>,
              h1: ({ children }) => <p className="font-semibold mb-1">{children}</p>,
              h2: ({ children }) => <p className="font-semibold mb-1">{children}</p>,
              h3: ({ children }) => <p className="font-semibold mb-1">{children}</p>,
            }}
          >
            {text || " "}
          </ReactMarkdown>
        ) : text}
      </div>
    </div>
  );
}
