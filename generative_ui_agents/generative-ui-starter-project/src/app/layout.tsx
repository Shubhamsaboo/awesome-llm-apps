"use client";

import "./globals.css";
import "@copilotkit/react-core/v2/styles.css";

import { CopilotKit } from "@copilotkit/react-core/v2";
import { ThemeProvider } from "@/hooks/use-theme";
// A2UI catalog: definitions + renderers in ./declarative-generative-ui/
import { demonstrationCatalog } from "./declarative-generative-ui/renderers";

export default function RootLayout({
  children,
}: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="en">
      <head>
        <title>CopilotKit</title>
        <link
          rel="icon"
          type="image/svg+xml"
          href="/copilotkit-logo-mark.svg"
        />
      </head>
      <body className={`antialiased`}>
        <ThemeProvider>
          <CopilotKit
            runtimeUrl="/api/copilotkit"
            inspectorDefaultAnchor={{ horizontal: "right", vertical: "top" }}
            a2ui={{ catalog: demonstrationCatalog }}
            openGenerativeUI={{}}
            useSingleEndpoint={false}
          >
            {children}
          </CopilotKit>
        </ThemeProvider>
      </body>
    </html>
  );
}
