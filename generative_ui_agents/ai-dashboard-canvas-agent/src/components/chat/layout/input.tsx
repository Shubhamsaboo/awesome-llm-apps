"use client";
import { useState } from "react";
import { Textarea } from "@/components/ui/textarea";
import { Button } from "@/components/ui/button";
import type { InputProps as CpkInputProps } from "@copilotkit/react-ui";
import { ArrowUp, Square } from "lucide-react";

export function SidebarInput({
  inProgress,
  onSend,
  onStop,
  hideStopButton,
}: CpkInputProps) {
  const [text, setText] = useState("");
  const canSend = !inProgress && text.trim().length > 0;

  const submit = async () => {
    if (canSend) {
      setText("");
      await onSend(text);
    }
  };

  return (
    <div className="p-3 px-4 bg-card">
      <div className="relative mx-auto max-w-none">
        <div className="rounded-xl border bg-card shadow-sm px-3 py-2 flex items-end gap-2">
          <Textarea
            value={text}
            onChange={(e) => setText(e.target.value)}
            placeholder="Ask for anything"
            className="min-h-20 border-0 focus-visible:ring-0 px-0 resize-none shadow-none max-h-48 pb-4 px-2 bg-white"
            onKeyDown={(e) => {
              if (e.key === "Enter" && !e.shiftKey) {
                e.preventDefault();
                submit();
              }
            }}
          />
          {inProgress && !hideStopButton ? (
            <Button
              size="icon"
              variant="ghost"
              onClick={onStop}
              title="Stop generating"
              className="text-accent hover:text-white"
            >
              <Square className="size-3 animate-pulse" />
            </Button>
          ) : (
            <Button
              size="icon"
              variant="ghost"
              disabled={!canSend}
              onClick={submit}
              title="Send"
            >
              <ArrowUp className="size-4" />
            </Button>
          )}
        </div>
        <p className="mt-2 text-[11px] text-muted-foreground text-center">
          Press Enter to send • Shift+Enter for new line
        </p>
      </div>
    </div>
  );
}
