"use client";

import "./globals.css";
import "@copilotkit/react-core/v2/styles.css";

import { CopilotKit } from "@copilotkit/react-core/v2";

export default function RootLayout({
  children,
}: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="en">
      <head>
        <title>AI Knowledge Explorer</title>
      </head>
      <body className="antialiased">
        <CopilotKit runtimeUrl="/api/copilotkit" useSingleEndpoint={false}>
          {children}
        </CopilotKit>
      </body>
    </html>
  );
}
