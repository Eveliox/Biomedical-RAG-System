import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Biomedical Literature Assistant",
  description: "Search PubMed and ask grounded questions with citations.",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body className="min-h-screen font-sans">
        <header className="border-b border-slate-200 bg-white">
          <div className="mx-auto max-w-4xl px-6 py-5">
            <h1 className="text-xl font-semibold tracking-tight text-ink">
              Biomedical Literature Assistant
            </h1>
            <p className="text-sm text-slate-500">
              Search PubMed &middot; ingest papers &middot; ask grounded questions
            </p>
          </div>
        </header>
        <main className="mx-auto max-w-4xl px-6 py-8">{children}</main>
      </body>
    </html>
  );
}
