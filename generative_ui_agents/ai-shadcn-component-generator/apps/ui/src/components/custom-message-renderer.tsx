import type { RenderMessageProps } from "@copilotkit/react-ui";
import type { AssistantMessage } from "@ag-ui/core";
import { useChatKit } from "./chat/chat-kit";
import { useJsonParser } from "@hashbrownai/react";
import { memo, useState } from "react";
import { Squircle } from "./squircle";
import { ExportPanel } from "./export-panel";
import { CodeIcon } from "lucide-react";

function normalizeContent(content: unknown) {
  if (typeof content === "string") return content;
  try {
    return JSON.stringify(content, null, 2);
  } catch {
    return String(content);
  }
}

const AssistantMessageRenderer = memo(function AssistantMessageRenderer({
  message,
}: {
  message: AssistantMessage;
}) {
  const kit = useChatKit();
  const { value, parserState } = useJsonParser(message.content ?? "", kit.schema);
  const [exportOpen, setExportOpen] = useState(false);

  if (!value) return null;

  // Check if the tree contains non-markdown components
  const tree = (value as Record<string, unknown>).ui;
  const hasComponents =
    Array.isArray(tree) &&
    tree.some((node) => {
      if (!node || typeof node !== "object") return false;
      const keys = Object.keys(node as Record<string, unknown>);
      return keys.length > 0 && keys[0] !== "markdown";
    });

  return (
    <div className="group/msg mt-2 flex w-full justify-start">
      <div className="magic-text-output w-full px-1 py-1">
        {kit.render(value)}
        {hasComponents && parserState.isComplete && (
          <>
            <button
              onClick={() => setExportOpen(true)}
              className="mt-2 inline-flex items-center gap-1.5 rounded-md border border-[var(--border)] bg-[var(--surface)] px-2.5 py-1.5 text-xs font-medium text-[var(--gray)] transition-colors hover:bg-[var(--surface-elevated)] hover:text-[var(--foreground)]"
            >
              <CodeIcon className="size-3.5" />
              Export Code
            </button>
            <ExportPanel open={exportOpen} onOpenChange={setExportOpen} tree={tree as unknown[]} />
          </>
        )}
      </div>
    </div>
  );
});

export function CustomMessageRenderer({ message }: RenderMessageProps) {
  if (message.role === "assistant") {
    return <AssistantMessageRenderer message={message} />;
  }
  return (
    <div className="flex w-full justify-end">
      <Squircle
        squircle="22"
        borderWidth={0}
        className="w-full max-w-[64ch] bg-[var(--sky-blue-light)] px-4 py-3 text-sm text-[var(--gray-dark)] shadow-[0_12px_26px_-20px_rgba(100,175,181,0.52)]"
      >
        <pre className="whitespace-pre-wrap text-[15px] leading-6 text-[var(--gray-dark)]">
          {normalizeContent(message.content)}
        </pre>
      </Squircle>
    </div>
  );
}
