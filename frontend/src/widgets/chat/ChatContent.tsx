import { useChatMessages } from "@/features/meetings/chat/useChatMessages";
import { MessageList } from "@/features/meetings/chat/MessageList";
import { MessageInput } from "@/features/meetings/chat/MessageInput";

interface ChatContentProps {
  meetingId: string;
}

export function ChatContent({ meetingId }: ChatContentProps) {
  const { messages, sendMessage } = useChatMessages(meetingId);

  return (
    <div className="flex h-full flex-col">
      <MessageList messages={messages} />
      <MessageInput onSend={sendMessage} />
    </div>
  );
}