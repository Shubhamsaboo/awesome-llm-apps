"use client";

import { ExampleLayout } from "@/components/example-layout";
import { PasteArea } from "@/components/paste-area";
import { useGenerativeUIExamples, useExampleSuggestions } from "@/hooks";

import { CopilotChat } from "@copilotkit/react-core/v2";

export default function HomePage() {
  useGenerativeUIExamples();
  useExampleSuggestions();

  return (
    <ExampleLayout
      chatContent={
        <CopilotChat input={{ disclaimer: () => null, className: "pb-6" }} />
      }
      appContent={<PasteArea />}
    />
  );
}
