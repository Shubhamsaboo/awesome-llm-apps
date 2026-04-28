"use client";
import type { UserMessageProps } from "@copilotkit/react-ui";
import { Card, CardContent } from "@/components/ui/card";

export function UserBubble({ message }: UserMessageProps) {
  const content = message?.content ?? "";
  return (
    <div className="flex justify-end mb-4 mt-4">
      <Card className="max-w-[80%] bg-accent/10 text-card-foreground border border-accent/40 rounded-lg text-sm whitespace-pre-wrap p-0">
        <CardContent className="px-3 py-2">{content}</CardContent>
      </Card>
    </div>
  );
}
