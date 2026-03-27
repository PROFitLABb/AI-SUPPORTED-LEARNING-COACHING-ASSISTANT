"use client";
import "./globals.css";
import Sidebar from "@/components/Sidebar";
import { AppProvider } from "@/components/AppContext";

function Shell({ children }: { children: React.ReactNode }) {
  return (
    <div className="flex min-h-screen bg-bg">
      <Sidebar />
      <main className="flex-1 md:ml-72 p-6 min-h-screen">{children}</main>
    </div>
  );
}

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="tr">
      <head>
        <title>AI Learning Coach</title>
        <meta name="description" content="Groq LLM destekli kişiselleştirilmiş öğrenme koçu" />
      </head>
      <body>
        <AppProvider>
          <Shell>{children}</Shell>
        </AppProvider>
      </body>
    </html>
  );
}
