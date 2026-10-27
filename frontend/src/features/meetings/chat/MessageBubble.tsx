import { cn } from "@/lib/utils";

interface MessageBubbleProps {
  text: string;
  authorName: string;
  isMine: boolean;
  sentAt: string;
}

export function MessageBubble({ text, authorName, isMine, sentAt }: MessageBubbleProps) {
  const time = new Date(sentAt).toLocaleTimeString("ru-RU", {
    hour: "2-digit",
    minute: "2-digit",
  });

  return (
    <div className={cn("flex flex-col gap-0.5", isMine ? "items-end" : "items-start")}>
      {!isMine && (
        <span className="text-[10px] text-slate-500">{authorName}</span>
      )}

      <div
        className={cn(
          "max-w-[80%] rounded-2xl px-4 py-2.5 text-sm",
          isMine
            ? "rounded-br-md bg-blue-600 text-white"
            : "rounded-bl-md bg-white/10 text-slate-200"
        )}
      >
        {text}
      </div>

      <span className="text-[10px] text-slate-600">{time}</span>
    </div>
  );
}