import { CopilotKit } from "@copilotkit/react-core";
import { useAgentContext, CopilotChat } from "@copilotkit/react-core/v2";

import { AppHeader } from "@/components/app-header";
import { useChatKit } from "@/components/chat/chat-kit";
import { s } from "@hashbrownai/core";
import { chatTheme } from "@/lib/chat-theme";
import { useInitialSuggestions } from "./lib/suggestions";

export function App() {
  return (
    <CopilotKit
      runtimeUrl={
        import.meta.env.VITE_RUNTIME_HOST
          ? `https://${import.meta.env.VITE_RUNTIME_HOST}.onrender.com/api/copilotkit`
          : "/api/copilotkit"
      }
      showDevConsole={false}
    >
      <Page />
    </CopilotKit>
  );
}

export function Page() {
  const chatKit = useChatKit();
  useAgentContext({ description: "output_schema", value: s.toJsonSchema(chatKit.schema) });
  useInitialSuggestions();

  return <Chat />;
}

function Chat() {
  return (
    <main className="relative z-10 flex h-dvh w-full flex-col overflow-hidden text-[--foreground]">
      <AppHeader title="Shadify" />
      <div className="w-full h-[calc(100vh-60px)]">
        <CopilotChat {...chatTheme} />
      </div>
    </main>
  );
}
