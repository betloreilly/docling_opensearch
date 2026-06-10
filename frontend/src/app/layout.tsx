import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "NexValue Financial Enterprise Search",
  description: "Turn complex internal documents into searchable business knowledge with Docling and OpenSearch",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
