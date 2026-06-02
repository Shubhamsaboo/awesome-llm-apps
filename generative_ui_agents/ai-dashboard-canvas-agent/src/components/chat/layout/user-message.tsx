"use client";
import type { UserMessageProps } from "@copilotkit/react-ui";
import { Card, CardContent } from "@/components/ui/card";

// In newer CopilotKit, message.content is a union (string | content parts),
// not a plain string, so coerce it to text before rendering it as JSX.
function toText(content: unknown): string {
  if (typeof content === "string") return content;
  if (Array.isArray(content)) {
    return content
      .map((part) =>
        typeof part === "string"
          ? part
          : part && typeof part === "object" && "text" in part
            ? String((part as { text?: unknown }).text ?? "")
            : "",
      )
      .join("");
  }
  return content == null ? "" : String(content);
}

export function UserBubble({ message }: UserMessageProps) {
  const content = toText(message?.content);
  return (
    <div className="flex justify-end mb-4 mt-4">
      <Card className="max-w-[80%] bg-accent/10 text-card-foreground border border-accent/40 rounded-lg text-sm whitespace-pre-wrap p-0">
        <CardContent className="px-3 py-2">{content}</CardContent>
      </Card>
    </div>
  );
}
