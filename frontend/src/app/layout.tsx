import "./globals.css";
import type { Metadata } from "next";
import AppShell from "@/components/layout/AppShell";

export const metadata: Metadata = {
  title: "ExpiryOS — Pharmacy Expiry & Distributor Return Automation",
  description:
    "Multi-tenant SaaS for retail pharmacies that manages near-expiry stock, automates return-to-distributor workflows and tracks credit note reconciliation.",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" className="dark">
      <head>
        <link rel="preconnect" href="https://fonts.googleapis.com" />
        <link rel="preconnect" href="https://fonts.gstatic.com" crossOrigin="anonymous" />
      </head>
      <body className="bg-[#090D16] text-slate-100 antialiased selection:bg-emerald-500 selection:text-slate-950">
        <AppShell>{children}</AppShell>
      </body>
    </html>
  );
}
