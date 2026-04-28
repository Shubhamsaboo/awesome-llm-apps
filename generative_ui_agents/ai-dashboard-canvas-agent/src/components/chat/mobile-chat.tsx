"use client";

import { CopilotSidebar } from "@copilotkit/react-ui";
import { SidebarInput } from "@/components/chat/layout/input";
import { AssistantBubble } from "@/components/chat/layout/assistant-message";
import { UserBubble } from "@/components/chat/layout/user-message";
import { Suggestions } from "@/components/chat/layout/suggestion";

export function MobileChat() {
  return (
    <CopilotSidebar
      labels={{
        title: "🪁 ADK Dashboard Agent",
        initial: "👋 Hi! Describe a dashboard and I'll build it.",
      }}
      suggestions={[
        {
          title: "Pizza sales",
          message:
            "Please update the dashboard to help me keep track of the current trends in the Pizza industry.",
        },
        {
          title: "AI growth",
          message:
            "Please update the dashbaord to help me keep track of the current trends in the AI industry.",
        },
        {
          title: "Music trends",
          message:
            "Please update the dashbaord to help me keep track of the current trends in the Music industry.",
        },
      ]}
      Input={SidebarInput}
      AssistantMessage={AssistantBubble}
      UserMessage={UserBubble}
      RenderSuggestionsList={Suggestions}
    />
  );
}
