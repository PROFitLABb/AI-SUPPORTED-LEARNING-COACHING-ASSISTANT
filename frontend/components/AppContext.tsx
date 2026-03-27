"use client";
import { createContext, useContext, type ReactNode } from "react";

interface AppCtx {
  apiUrl: string;
  userId: string;
}

const defaultApi =
  typeof window === "undefined"
    ? process.env.NEXT_PUBLIC_API_URL ?? ""
    : (window as any).__NEXT_PUBLIC_API_URL__ ?? process.env.NEXT_PUBLIC_API_URL ?? "";

const Ctx = createContext<AppCtx>({ apiUrl: "", userId: "" });

export function AppProvider({ children }: { children: ReactNode }) {
  const apiUrl = process.env.NEXT_PUBLIC_API_URL ?? "";
  return (
    <Ctx.Provider value={{ apiUrl, userId: "" }}>
      {children}
    </Ctx.Provider>
  );
}

export const useApp = () => useContext(Ctx);
