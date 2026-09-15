import type { Metadata } from "next";
import "./globals.css";
import { CommandPalette } from "@/components/CommandPalette";

export const metadata: Metadata = {
  title: "Biomed RAG — Ask the literature",
  description: "Search PubMed and ask grounded questions with citations.",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body className="min-h-screen font-sans antialiased">
        {children}
        <CommandPalette />
      </body>
    </html>
  );
}
