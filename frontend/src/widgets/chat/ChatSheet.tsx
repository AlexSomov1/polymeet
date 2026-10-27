import { X } from "lucide-react";
import { useEffect } from "react";
import { ChatContent } from "./ChatContent";
import { MOCK_MY_EVENTS } from "@/features/meetings/mock";

interface ChatSheetProps {
  meetingId: string | null;
  isOpen: boolean;
  onClose: () => void;
}

export function ChatSheet({ meetingId, isOpen, onClose }: ChatSheetProps) {
  const meeting = meetingId
    ? MOCK_MY_EVENTS.find((e) => e.id === meetingId)
    : undefined;

  // Close on Escape key
  useEffect(() => {
    const handleKey = (e: KeyboardEvent) => {
      if (e.key === "Escape") onClose();
    };
    if (isOpen) window.addEventListener("keydown", handleKey);
    return () => window.removeEventListener("keydown", handleKey);
  }, [isOpen, onClose]);

  if (!isOpen) return null;

  return (
    <>
      {/* Backdrop */}
      <div
        className="fixed inset-0 z-40 bg-black/60 backdrop-blur-sm"
        onClick={onClose}
      />

      {/* Drawer panel */}
      <div className="fixed inset-y-0 right-0 z-50 flex w-full flex-col border-l border-white/10 bg-[#0b0f1a] sm:max-w-md">
        {/* Header */}
        <div className="flex items-center justify-between border-b border-white/10 px-5 py-4">
          <h2 className="text-sm font-semibold text-white">
            {meeting?.title ?? "Чат"}
          </h2>
          <button
            onClick={onClose}
            className="rounded-md p-1 text-slate-400 transition-colors hover:text-white"
          >
            <X size={18} />
          </button>
        </div>

        {/* Chat content */}
        {meetingId && (
          <div className="flex-1 overflow-hidden">
            <ChatContent meetingId={meetingId} />
          </div>
        )}
      </div>
    </>
  );
}