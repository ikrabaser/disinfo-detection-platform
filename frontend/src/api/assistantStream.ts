import {
  apiClient,
  type AssistantMessage,
} from "./client";


const API_BASE_URL =
  import.meta.env.VITE_API_BASE_URL ??
  "/api";


export interface AssistantToolCall {
  id?: string;
  name?: string;
  status?: string;
}


interface StreamHandlers {
  onStart?: (
    userMessage: AssistantMessage
  ) => void;

  onDelta?: (
    delta: string
  ) => void;

  onToolStart?: (
    toolCall: AssistantToolCall
  ) => void;

  onToolEnd?: (
    toolCall: AssistantToolCall
  ) => void;

  onDone?: (
    userMessage: AssistantMessage,
    assistantMessage: AssistantMessage
  ) => void;
}


interface SSEPacket {
  event: string;
  data: Record<string, unknown>;
}


function streamUrl(
  conversationId: string
): string {
  const base =
    API_BASE_URL.endsWith("/")
      ? API_BASE_URL.slice(0, -1)
      : API_BASE_URL;

  return (
    `${base}/agent/conversations/` +
    `${conversationId}/messages/stream/`
  );
}


function parsePacket(
  block: string
): SSEPacket | null {
  let event = "message";

  const dataLines: string[] = [];

  for (
    const line
    of block.split("\n")
  ) {
    if (
      line.startsWith("event:")
    ) {
      event = line
        .slice("event:".length)
        .trim();

      continue;
    }

    if (
      line.startsWith("data:")
    ) {
      dataLines.push(
        line
          .slice("data:".length)
          .trimStart()
      );
    }
  }

  if (!dataLines.length) {
    return null;
  }

  const raw = dataLines.join(
    "\n"
  );

  return {
    event,
    data: JSON.parse(raw),
  };
}


async function openStream(
  conversationId: string,
  content: string,
  signal?: AbortSignal
): Promise<Response> {
  return fetch(
    streamUrl(conversationId),
    {
      method: "POST",
      credentials: "include",
      headers: {
        "Content-Type":
          "application/json",
        Accept:
          "text/event-stream",
      },
      body: JSON.stringify({
        content,
      }),
      signal,
    }
  );
}


export async function sendAssistantMessageStream(
  conversationId: string,
  content: string,
  handlers: StreamHandlers,
  signal?: AbortSignal
): Promise<void> {
  let response =
    await openStream(
      conversationId,
      content,
      signal
    );

  if (
    response.status === 401
  ) {
    await apiClient.post(
      "/auth/refresh/"
    );

    response = await openStream(
      conversationId,
      content,
      signal
    );
  }

  if (!response.ok) {
    let detail = (
      "Assistant streaming "
      + "başlatılamadı."
    );

    try {
      const payload =
        await response.json();

      if (
        typeof payload?.detail
        === "string"
      ) {
        detail =
          payload.detail;
      }
    } catch {
      // Response JSON degilse
      // varsayilan mesaj kullanilir.
    }

    throw new Error(detail);
  }

  if (!response.body) {
    throw new Error(
      "Streaming response body alınamadı."
    );
  }

  const reader =
    response.body.getReader();

  const decoder =
    new TextDecoder();

  let buffer = "";
  let streamError:
    string | null = null;

  function handlePacket(
    packet: SSEPacket
  ) {
    switch (packet.event) {
      case "start": {
        const userMessage =
          packet.data.user_message as AssistantMessage;

        handlers.onStart?.(
          userMessage
        );

        break;
      }

      case "delta": {
        const delta =
          packet.data.delta;

        if (
          typeof delta
          === "string"
        ) {
          handlers.onDelta?.(
            delta
          );
        }

        break;
      }

      case "tool_start": {
        const toolCall =
          packet.data.tool_call as AssistantToolCall;

        handlers.onToolStart?.(
          toolCall
        );

        break;
      }

      case "tool_end": {
        const toolCall =
          packet.data.tool_call as AssistantToolCall;

        handlers.onToolEnd?.(
          toolCall
        );

        break;
      }

      case "done": {
        const userMessage =
          packet.data.user_message as AssistantMessage;

        const assistantMessage =
          packet.data.assistant_message as AssistantMessage;

        handlers.onDone?.(
          userMessage,
          assistantMessage
        );

        break;
      }

      case "error": {
        const detail =
          packet.data.detail;

        streamError =
          typeof detail
          === "string"
            ? detail
            : (
              "Assistant streaming "
              + "hatası oluştu."
            );

        break;
      }
    }
  }

  while (true) {
    const {
      done,
      value,
    } = await reader.read();

    if (done) {
      buffer += decoder.decode();

      break;
    }

    buffer += decoder.decode(
      value,
      {
        stream: true,
      }
    );

    let boundary =
      buffer.indexOf("\n\n");

    while (
      boundary !== -1
    ) {
      const block =
        buffer
          .slice(0, boundary)
          .trim();

      buffer = buffer.slice(
        boundary + 2
      );

      if (block) {
        const packet =
          parsePacket(block);

        if (packet) {
          handlePacket(packet);
        }
      }

      boundary =
        buffer.indexOf("\n\n");
    }
  }

  const remaining =
    buffer.trim();

  if (remaining) {
    const packet =
      parsePacket(remaining);

    if (packet) {
      handlePacket(packet);
    }
  }

  if (streamError) {
    throw new Error(
      streamError
    );
  }
}
