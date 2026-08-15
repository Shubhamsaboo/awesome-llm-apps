import type { Metadata } from "next";

import { CopilotKit } from "@copilotkit/react-core";
import "./globals.css";
import "@copilotkit/react-ui/styles.css";

export const metadata: Metadata = {
  title: "Deep Research Assistant | CopilotKit Deep Agents Demo",
  description:
    "A research assistant powered by Deep Agents and CopilotKit - demonstrating planning, memory, subagents, and generative UI",
  openGraph: {
    title: "Deep Research Assistant",
    description: "A research assistant powered by Deep Agents and CopilotKit",
    images: ["/og-image.png"],
  },
  twitter: {
    card: "summary_large_image",
    title: "Deep Research Assistant",
    description: "A research assistant powered by Deep Agents and CopilotKit",
    images: ["/og-image.png"],
  },
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body className="antialiased">
        <CopilotKit runtimeUrl="/api/copilotkit" agent="research_assistant">
          {children}
        </CopilotKit>
      </body>
    </html>
  );
}
