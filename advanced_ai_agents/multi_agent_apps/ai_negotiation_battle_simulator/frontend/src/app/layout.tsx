import type { Metadata } from "next";
import { CopilotKit } from "@copilotkit/react-core";
import "@copilotkit/react-ui/styles.css";
import "./globals.css";

export const metadata: Metadata = {
  title: "🎮 AI Negotiation Battle Simulator",
  description: "Watch AI agents battle it out in epic negotiations!",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body className="antialiased">
        <CopilotKit 
          runtimeUrl="/api/copilotkit" 
          agent="negotiation_agent"
        >
          {children}
        </CopilotKit>
      </body>
    </html>
  );
}
