"use client";

import { useRouter } from "next/navigation";
import { useState } from "react";

export default function Home() {
  const router = useRouter();
  const [workspaceId, setWorkspaceId] = useState("default");

  const enterWorkspace = () => {
    if (workspaceId.trim()) {
      router.push(`/workspace/${encodeURIComponent(workspaceId.trim())}/chat`);
    }
  };

  return (
    <main className="flex min-h-screen flex-col items-center justify-center bg-gradient-to-br from-gray-900 via-slate-900 to-indigo-950 text-white p-6">
      <div className="max-w-md w-full text-center space-y-8 bg-slate-800/40 backdrop-blur-md p-8 rounded-2xl border border-slate-700/50 shadow-2xl">
        <div className="space-y-3">
          <div className="inline-flex items-center justify-center p-3 bg-indigo-500/10 rounded-xl text-indigo-400 border border-indigo-500/20 mb-2">
            <svg xmlns="http://www.w3.org/2000/svg" className="h-10 w-10 animate-pulse" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19.428 15.428a2 2 0 00-1.022-.547l-2.387-.477a6 6 0 00-3.86.517l-.318.158a6 6 0 01-3.86.517L6.05 15.21a2 2 0 00-1.806.547M8 4h8l-1 1v5.172a2 2 0 00.586 1.414l5 5c1.26 1.26.367 3.414-1.415 3.414H4.828c-1.782 0-2.674-2.154-1.414-3.414l5-5A2 2 0 009 10.172V5L8 4z" />
            </svg>
          </div>
          <h1 className="text-4xl font-extrabold tracking-tight bg-gradient-to-r from-indigo-200 via-slate-100 to-indigo-200 bg-clip-text text-transparent">
            RAGFlow
          </h1>
          <p className="text-slate-400 text-sm">
            Enterprise AI Knowledge & Document Chat Assistant
          </p>
        </div>

        <div className="space-y-4 pt-4">
          <div className="text-left space-y-1">
            <label className="text-xs font-semibold text-slate-400 uppercase tracking-wider">
              Workspace ID
            </label>
            <input
              type="text"
              value={workspaceId}
              onChange={(e) => setWorkspaceId(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && enterWorkspace()}
              placeholder="e.g., default"
              className="w-full px-4 py-3 rounded-xl bg-slate-900/60 border border-slate-700 focus:border-indigo-500 focus:ring-2 focus:ring-indigo-500/20 text-white outline-none transition-all duration-200 placeholder:text-slate-600"
            />
          </div>

          <button
            onClick={enterWorkspace}
            className="w-full py-3 px-4 rounded-xl bg-gradient-to-r from-indigo-600 to-violet-600 hover:from-indigo-500 hover:to-violet-500 text-white font-medium shadow-lg hover:shadow-indigo-500/20 active:scale-[0.98] transition-all duration-150"
          >
            Enter Chat
          </button>
        </div>

        <div className="pt-4 border-t border-slate-700/50 flex justify-around text-xs text-slate-400">
          <div className="flex items-center gap-1.5">
            <span className="h-2 w-2 rounded-full bg-emerald-500"></span>
            System Online
          </div>
          <div>Version 0.1.0</div>
        </div>
      </div>
    </main>
  );
}
