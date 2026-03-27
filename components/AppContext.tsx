"use client";
import { createContext, useContext, type ReactNode } from "react";

interface AppCtx {
  apiUrl: string;
  userId: string;
}

const Ctx = createContext<AppCtx>({ apiUrl: "/api", userId: "" });

export function AppProvider({ children }: { children: ReactNode }) {
  return (
    <Ctx.Provider value={{ apiUrl: "/api", userId: "" }}>
      {children}
    </Ctx.Provider>
  );
}

export const useApp = () => useContext(Ctx);
