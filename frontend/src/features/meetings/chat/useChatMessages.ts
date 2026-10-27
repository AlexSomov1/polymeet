import { useState, useCallback } from "react";
import { MOCK_MESSAGES } from "../mock";
import type { ChatMessage } from "../mock";

export function useChatMessages(meetingId: string) {
  const [messages, setMessages] = useState<ChatMessage[]>(() => {
    return MOCK_MESSAGES[meetingId] ?? [];
  });

  const sendMessage = useCallback(
    (text: string) => {
      const newMsg: ChatMessage = {
        id: `msg-${Date.now()}`,
        meetingId,
        authorId: "me",
        authorName: "GR",
        text: text.trim(),
        sentAt: new Date().toISOString(),
      };

      setMessages((prev) => [...prev, newMsg]);
    },
    [meetingId]
  );

  return { messages, sendMessage };
}