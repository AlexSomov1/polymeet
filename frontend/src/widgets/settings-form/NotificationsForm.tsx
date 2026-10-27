import { useState } from "react";
import { cn } from "@/lib/utils";
import type { UserProfile } from "@/features/user/types";

interface NotificationsFormProps {
  settings: UserProfile["settings"];
  onChange: (settings: UserProfile["settings"]) => void;
}

function ToggleRow({
  label,
  checked,
  onChange,
}: {
  label: string;
  checked: boolean;
  onChange: (v: boolean) => void;
}) {
  return (
    <div className="flex items-center justify-between py-3">
      <span className="text-sm text-slate-300">{label}</span>
      <button
        onClick={() => onChange(!checked)}
        className={cn(
          "relative h-6 w-11 rounded-full transition-colors",
          checked ? "bg-blue-600" : "bg-white/10"
        )}
      >
        <span
          className={cn(
            "absolute top-0.5 h-5 w-5 rounded-full bg-white shadow-sm transition-transform",
            checked ? "left-6" : "left-0.5"
          )}
        />
      </button>
    </div>
  );
}

export function NotificationsForm({ settings, onChange }: NotificationsFormProps) {
  const [draft, setDraft] = useState(settings);

  const update = (patch: Partial<UserProfile["settings"]>) => {
    const next = { ...draft, ...patch };
    setDraft(next);
    onChange(next);
  };

  return (
    <div className="space-y-6">
      <div className="rounded-xl border border-white/10 bg-[#131a30] p-5">
        <h3 className="text-white font-semibold">
          Уведомления и Приватность
        </h3>
        <div className="mt-2 divide-y divide-white/5">
          <ToggleRow
            label="Уведомления в Telegram-бот"
            checked={draft.telegramBotNotifications}
            onChange={(v) => update({ telegramBotNotifications: v })}
          />
          <ToggleRow
            label="Уведомлять о встречах рядом (радиус 10 км)"
            checked={draft.nearbyMeetingsNotifications}
            onChange={(v) => update({ nearbyMeetingsNotifications: v })}
          />
          <ToggleRow
            label="Показывать мои контакты только одобренным участникам"
            checked={draft.contactsVisibleToApprovedOnly}
            onChange={(v) => update({ contactsVisibleToApprovedOnly: v })}
          />
        </div>
      </div>
    </div>
  );
}