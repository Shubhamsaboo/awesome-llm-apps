import type { Metadata } from "next";

import { CopilotKit } from "@copilotkit/react-core";
import { Manrope } from "next/font/google";
import { GeistMono } from "geist/font/mono";
import "./globals.css";
import "@copilotkit/react-ui/styles.css";

const manrope = Manrope({
  subsets: ["latin"],
  display: "swap",
  variable: "--font-manrope",
});

export const metadata: Metadata = {
  title: "Gen Dashboard",
  description: "AI-powered analytics dashboard",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" className={`${manrope.variable} ${GeistMono.variable}`}>
      <body className={"subpixel-antialiased"}>
        <CopilotKit
          runtimeUrl="/api/copilotkit"
          agent="my_agent"
          showDevConsole={false}
        >
          {children}
        </CopilotKit>
      </body>
    </html>
  );
}
