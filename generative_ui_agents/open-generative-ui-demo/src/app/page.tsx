"use client";

import { CopilotChat } from "@copilotkit/react-core/v2";
import { useExampleSuggestions } from "@/hooks";

export default function HomePage() {
  useExampleSuggestions();

  return (
    <div className="h-full flex flex-col pb-6 max-w-3xl mx-auto w-full">
      <header className="shrink-0 pt-6 px-6 pb-2 flex gap-1.5 items-center">
        <span className="font-extrabold text-2xl pb-1.5">CopilotKit</span>
        <img
          src="/copilotkit-logo-mark.svg"
          alt="CopilotKit"
          className="h-7"
        />
        <span className="text-sm text-stone-500 ml-2">Open Generative UI</span>
      </header>
      <div className="flex-1 min-h-0 overflow-y-auto px-2">
        <CopilotChat
          attachments={{ enabled: true }}
          input={{ disclaimer: () => null, className: "pb-6" }}
        />
      </div>
    </div>
  );
}
