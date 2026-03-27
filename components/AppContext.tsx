"use client";
import { createContext, useContext, type ReactNode } from "react";

interface AppCtx {
  apiUrl: string;
  userId: string;
}

// Vercel'de Python handler /api/index adresinde çalışır
const API_URL = "/api/index";

const Ctx = createContext<AppCtx>({ apiUrl: API_URL, userId: "" });

export function AppProvider({ children }: { children: ReactNode }) {
  return (
    <Ctx.Provider value={{ apiUrl: API_URL, userId: "" }}>
      {children}
    </Ctx.Provider>
  );
}

export const useApp = () => useContext(Ctx);
