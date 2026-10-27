import { Camera } from "lucide-react";
import { useState } from "react";
import { cn } from "@/lib/utils";
import type { UserProfile } from "@/features/user/types";

interface ProfileFormProps {
  user: UserProfile;
  onChange: (user: UserProfile) => void;
}

function Field({
  label,
  value,
  onChange,
  readOnly,
}: {
  label: string;
  value: string;
  onChange?: (v: string) => void;
  readOnly?: boolean;
}) {
  return (
    <div className="space-y-2">
      <label className="text-xs font-medium text-slate-400">{label}</label>
      <input
        type="text"
        value={value}
        readOnly={readOnly}
        onChange={(e) => onChange?.(e.target.value)}
        className={cn(
          "w-full rounded-lg border border-white/10 bg-white/5 px-4 py-3 text-sm text-white focus:outline-none",
          readOnly
            ? "cursor-default text-slate-500"
            : "focus:border-blue-500"
        )}
      />
    </div>
  );
}

export function ProfileForm({ user, onChange }: ProfileFormProps) {
  const [draft, setDraft] = useState(user);

  const update = (patch: Partial<UserProfile>) => {
    const next = { ...draft, ...patch };
    setDraft(next);
    onChange(next);
  };

  return (
    <div className="space-y-6">
      <h2 className="text-lg font-semibold text-white">Основной профиль</h2>

      {/* Avatar + reliability */}
      <div className="flex items-start gap-5">
        <div className="relative">
          <img
            src={draft.avatarUrl}
            alt="avatar"
            className="h-24 w-24 rounded-full object-cover ring-2 ring-white/10"
          />
          <button className="absolute bottom-0 right-0 grid h-8 w-8 place-items-center rounded-full bg-blue-600 text-white shadow-lg transition-colors hover:bg-blue-500">
            <Camera size={14} />
          </button>
        </div>

        <div className="space-y-1 pt-2">
          <p className="text-base font-medium">
            {draft.firstName} {draft.lastName}
          </p>
          <span className="inline-flex items-center rounded-md bg-emerald-500/10 px-2 py-0.5 text-xs text-emerald-400">
            Надёжность {draft.reliabilityScore}%
          </span>
        </div>
      </div>

      {/* Fields */}
      <div className="grid gap-4 sm:grid-cols-2">
        <Field
          label="Имя и Фамилия"
          value={`${draft.firstName} ${draft.lastName}`}
          onChange={(v) => {
            const [first = "", ...rest] = v.split(" ");
            update({ firstName: first, lastName: rest.join(" ") });
          }}
        />
        <Field
          label="Университет / Факультет"
          value={`${draft.university} · ${draft.faculty}`}
          readOnly
        />
        <Field
          label="Telegram username"
          value={draft.telegramUsername}
          onChange={(v) => update({ telegramUsername: v })}
        />
      </div>

      {/* Bio */}
      <div className="space-y-2">
        <label className="text-xs font-medium text-slate-400">О себе</label>
        <textarea
          value={draft.bio}
          onChange={(e) => update({ bio: e.target.value })}
          rows={4}
          className="w-full rounded-lg border border-white/10 bg-white/5 px-4 py-3 text-sm text-white placeholder:text-slate-600 focus:border-blue-500 focus:outline-none"
        />
      </div>
    </div>
  );
}