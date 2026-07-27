"use client";

import { useState } from "react";
import { streamChat, uploadDocument, type ChatEvent } from "@/lib/api";

interface DisplayMessage {
  role: "user" | "assistant";
  content: string;
  citations?: ChatEvent["citations"];
}

export default function ChatPage({ params }: { params: { workspaceId: string } }) {
  const [messages, setMessages] = useState<DisplayMessage[]>([]);
  const [input, setInput] = useState("");
  const [isStreaming, setIsStreaming] = useState(false);
  
  const [uploading, setUploading] = useState(false);
  const [uploadStatus, setUploadStatus] = useState<string | null>(null);

  async function handleSend() {
    if (!input.trim() || isStreaming) return;

    const question = input;
    setInput("");
    setMessages((prev) => [...prev, { role: "user", content: question }]);
    setMessages((prev) => [...prev, { role: "assistant", content: "" }]);
    setIsStreaming(true);

    try {
      for await (const event of streamChat({ workspace_id: params.workspaceId, question })) {
        if (event.type === "token") {
          setMessages((prev) => {
            const next = [...prev];
            next[next.length - 1].content += event.content ?? "";
            return next;
          });
        } else if (event.type === "citations") {
          setMessages((prev) => {
            const next = [...prev];
            next[next.length - 1].citations = event.citations;
            return next;
          });
        } else if (event.type === "error") {
          setMessages((prev) => {
            const next = [...prev];
            next[next.length - 1].content = `⚠️ ${event.message}`;
            return next;
          });
        }
      }
    } finally {
      setIsStreaming(false);
    }
  }

  async function handleUpload(e: React.ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0];
    if (!file) return;

    setUploading(true);
    setUploadStatus("Uploading document...");
    try {
      await uploadDocument(params.workspaceId, file);
      setUploadStatus(`Successfully uploaded: ${file.name}`);
    } catch (err: any) {
      setUploadStatus(`Upload failed: ${err.message}`);
    } finally {
      setUploading(false);
      setTimeout(() => setUploadStatus(null), 5000);
    }
  }

  return (
    <div className="mx-auto flex h-screen max-w-3xl flex-col p-4">
      <h1 className="mb-4 text-xl font-semibold">RAGFlow — Workspace Chat</h1>

      {/* Upload Zone */}
      <div className="mb-4 p-6 rounded-xl border-2 border-dashed border-gray-300 dark:border-gray-700 bg-gray-50/50 dark:bg-gray-900/30 flex flex-col items-center justify-center relative hover:border-blue-500 dark:hover:border-blue-400 transition-colors duration-200">
        <input
          type="file"
          onChange={handleUpload}
          className="absolute inset-0 w-full h-full opacity-0 cursor-pointer"
          disabled={uploading}
        />
        <svg xmlns="http://www.w3.org/2000/svg" className={`h-8 w-8 text-blue-500 mb-2 ${uploading ? "animate-bounce" : ""}`} fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
        </svg>
        <span className="text-sm font-medium text-gray-700 dark:text-gray-300">
          {uploading ? "Uploading document..." : "Drag & drop or click to upload a document"}
        </span>
        <span className="text-xs text-gray-500 mt-1">
          Supports PDF, TXT, MD, DOCX
        </span>
      </div>

      {uploadStatus && (
        <div className={`mb-4 px-4 py-2 rounded-lg text-xs font-medium ${uploadStatus.includes("failed") ? "bg-red-500/10 text-red-600 dark:text-red-400 border border-red-500/20" : "bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 border border-emerald-500/20"}`}>
          {uploadStatus}
        </div>
      )}

      <div className="flex-1 space-y-4 overflow-y-auto">
        {messages.map((m, i) => (
          <div key={i} className={m.role === "user" ? "text-right" : "text-left"}>
            <div
              className={`inline-block rounded-lg px-4 py-2 ${
                m.role === "user" ? "bg-blue-600 text-white" : "bg-gray-100 dark:bg-gray-800"
              }`}
            >
              {m.content || "…"}
            </div>
            {m.citations && m.citations.length > 0 && (
              <div className="mt-1 text-xs text-gray-500">
                Sources: {m.citations.map((c) => c.filename).filter(Boolean).join(", ")}
              </div>
            )}
          </div>
        ))}
      </div>

      <div className="mt-4 flex gap-2">
        <input
          className="flex-1 rounded-lg border px-3 py-2 dark:bg-gray-900"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && handleSend()}
          placeholder="Ask something about this workspace's documents..."
        />
        <button
          onClick={handleSend}
          disabled={isStreaming}
          className="rounded-lg bg-blue-600 px-4 py-2 text-white disabled:opacity-50"
        >
          Send
        </button>
      </div>
    </div>
  );
}
