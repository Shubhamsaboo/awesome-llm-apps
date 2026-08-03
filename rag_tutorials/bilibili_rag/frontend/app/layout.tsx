import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "BiliMind - 收藏夹知识库",
  description: "将你的 B站收藏夹变成可对话的知识库",
  icons: {
    icon: "/favicon.ico",
  },
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="zh-CN">
      <body className="antialiased">
        {children}
      </body>
    </html>
  );
}
