"use client";
import React from "react";
import { Markdown as CpkMarkdown } from "@copilotkit/react-ui";

export function Markdown({ content }: { content: string }) {
  return (
    <div className="prose dark:prose-invert max-w-none text-sm leading-relaxed">
      <div className="word-wrap-normal break-words hyphens-auto">
        <CpkMarkdown content={content} />
      </div>
    </div>
  );
}
