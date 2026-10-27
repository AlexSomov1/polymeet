import { useState } from "react";
import { cn } from "@/lib/utils";
import { MapPin, Eye, EyeOff } from "lucide-react";
import type { UserProfile } from "@/features/user/types";

interface PrivacyFormProps {
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

export function PrivacyForm({ settings, onChange }: PrivacyFormProps) {
  const [draft, setDraft] = useState(settings);

  const update = (patch: Partial<UserProfile["settings"]>) => {
    const next = { ...draft, ...patch };
    setDraft(next);
    onChange(next);
  };

  return (
    <div className="space-y-6">
      <h2 className="text-lg font-semibold text-white">Приватность и Геолокация</h2>

      {/* Geolocation card */}
      <div className="rounded-xl border border-white/10 bg-[#131a30] p-5">
        <div className="flex items-center gap-3 pb-4">
          <MapPin size={18} className="text-blue-400" />
          <h3 className="text-sm font-semibold text-white">Геолокация</h3>
        </div>

        <ToggleRow
          label="Показывать моё местоположение"
          checked={draft.showLocation}
          onChange={(v) => update({ showLocation: v })}
        />

        {draft.showLocation && (
          <div className="space-y-2 pt-2">
            <div className="flex items-center justify-between">
              <label className="text-xs text-slate-400">Радиус уведомлений</label>
              <span className="text-xs font-medium text-white">
                {draft.notificationRadiusKm} км
              </span>
            </div>
            <input
              type="range"
              min={1}
              max={50}
              value={draft.notificationRadiusKm}
              onChange={(e) => update({ notificationRadiusKm: Number(e.target.value) })}
              className="h-1.5 w-full cursor-pointer appearance-none rounded-full bg-white/10 accent-blue-500"
            />
            <div className="flex justify-between text-[10px] text-slate-600">
              <span>1 км</span>
              <span>50 км</span>
            </div>
          </div>
        )}
      </div>

      {/* Privacy card */}
      <div className="rounded-xl border border-white/10 bg-[#131a30] p-5">
        <div className="flex items-center gap-3 pb-4">
          {draft.contactsVisibleToApprovedOnly ? (
            <EyeOff size={18} className="text-blue-400" />
          ) : (
            <Eye size={18} className="text-blue-400" />
          )}
          <h3 className="text-sm font-semibold text-white">Контакты</h3>
        </div>

        <ToggleRow
          label="Показывать контакты только одобренным участникам"
          checked={draft.contactsVisibleToApprovedOnly}
          onChange={(v) => update({ contactsVisibleToApprovedOnly: v })}
        />
      </div>
    </div>
  );
}