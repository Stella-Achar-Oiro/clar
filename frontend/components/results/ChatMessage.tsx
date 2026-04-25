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
          <div className="prose prose-sm max-w-none prose-p:my-1 prose-ul:my-1 prose-li:my-0 prose-headings:text-gray-900" style={{ color: colors.textPrimary }}>
            <ReactMarkdown>{text || " "}</ReactMarkdown>
          </div>
        ) : text}
      </div>
    </div>
  );
}
