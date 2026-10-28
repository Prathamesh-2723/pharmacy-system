"use client";

import React from "react";
import { usePathname } from "next/navigation";
import Sidebar from "./Sidebar";
import Navbar from "./Navbar";

export default function AppShell({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const isLoginPage = pathname === "/login";

  if (isLoginPage) {
    return <main className="min-h-screen bg-[#090D16]">{children}</main>;
  }

  return (
    <div className="min-h-screen bg-[#090D16] text-slate-100 flex">
      <Sidebar />
      <div className="flex-1 ml-64 flex flex-col min-h-screen">
        <Navbar />
        <main className="flex-1 mt-16 p-8 overflow-y-auto">{children}</main>
      </div>
    </div>
  );
}
