"use client";

import { CopilotKitCSSProperties } from "@copilotkit/react-ui";
import { Chat } from "@/components/chat/chat";
import { MobileChat } from "@/components/chat/mobile-chat";
import { MainLayout } from "@/components/dashboard/dashboard";
import { useIsMobile } from "@/lib/isMobile";

export default function CopilotKitPage() {
  const isMobile = useIsMobile();

  return (
    <main
      style={
        { "--copilot-kit-primary-color": "#6366f1" } as CopilotKitCSSProperties
      }
      className="min-h-screen bg-background text-foreground antialiased grid grid-cols-3 md:grid-cols-3 grid-cols-1 lg:gap-10"
    >
      {isMobile ? <MobileChat /> : <Chat className="h-full max-h-screen" />}
      <div className="col-span-3 lg:col-span-2 overflow-y-auto max-h-screen">
        <MainLayout className="w-full" />
      </div>
    </main>
  );
}
