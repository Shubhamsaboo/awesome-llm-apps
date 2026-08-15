"use client";

import { useMemo } from "react";
import { useCopilotChatSuggestions } from "@copilotkit/react-core";
import { getChatStarterPrompts } from "../constants/chatStarters";

/**
 * Registers starter prompts with CopilotKit v2 so CopilotChat renders suggestion pills.
 * Configure with `NEXT_PUBLIC_CHAT_STARTER_PROMPTS` (JSON) — see `.env.example`. Defaults: three build demos + Excalidraw test.
 */
export function ChatSuggestions() {
  const suggestions = useMemo(() => getChatStarterPrompts(), []);

  useCopilotChatSuggestions(
    {
      available: "before-first-message",
      suggestions,
    },
    [suggestions],
  );

  return null;
}
