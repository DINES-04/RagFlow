const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1";

export interface ChatEvent {
  type: "token" | "citations" | "done" | "error";
  content?: string;
  citations?: Array<{ document_id: string; filename: string; page: number | null; score: number | null }>;
  message?: string;
}

/**
 * Streams a chat response from POST /chat/stream (Server-Sent Events).
 * Usage: for await (const event of streamChat(payload)) { ... }
 */
export async function* streamChat(payload: {
  workspace_id: string;
  conversation_id?: string;
  question: string;
  filters?: Record<string, unknown>;
}): AsyncGenerator<ChatEvent> {
  const res = await fetch(`${API_URL}/chat/stream`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });

  if (!res.body) throw new Error("No response body from chat stream");

  const reader = res.body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";

  while (true) {
    const { done, value } = await reader.read();
    if (done) break;
    buffer += decoder.decode(value, { stream: true });

    const lines = buffer.split("\n\n");
    buffer = lines.pop() || "";

    for (const line of lines) {
      if (!line.startsWith("data: ")) continue;
      yield JSON.parse(line.slice(6)) as ChatEvent;
    }
  }
}

export async function uploadDocument(workspaceId: string, file: File, collectionId?: string) {
  const form = new FormData();
  form.append("workspace_id", workspaceId);
  form.append("file", file);
  if (collectionId) form.append("collection_id", collectionId);

  const res = await fetch(`${API_URL}/documents/upload`, { method: "POST", body: form });
  if (!res.ok) throw new Error(`Upload failed: ${res.statusText}`);
  return res.json();
}
