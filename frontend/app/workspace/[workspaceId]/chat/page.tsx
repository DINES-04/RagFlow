"use client";

import { useState } from "react";
import { streamChat, type ChatEvent } from "@/lib/api";

interface DisplayMessage {
  role: "user" | "assistant";
  content: string;
  citations?: ChatEvent["citations"];
}

export default function ChatPage({ params }: { params: { workspaceId: string } }) {
  const [messages, setMessages] = useState<DisplayMessage[]>([]);
  const [input, setInput] = useState("");
  const [isStreaming, setIsStreaming] = useState(false);

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

  return (
    <div className="mx-auto flex h-screen max-w-3xl flex-col p-4">
      <h1 className="mb-4 text-xl font-semibold">RAGFlow — Workspace Chat</h1>

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
