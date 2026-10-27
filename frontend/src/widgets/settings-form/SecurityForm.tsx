import { useState } from "react";
import {Lock, Smartphone } from "lucide-react";

export function SecurityForm() {
  const [currentPassword, setCurrentPassword] = useState("");
  const [newPassword, setNewPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");

  const canSubmit =
    currentPassword.length > 0 &&
    newPassword.length >= 8 &&
    newPassword === confirmPassword;

  return (
    <div className="space-y-6">
      <h2 className="text-lg font-semibold text-white">Безопасность</h2>

      {/* Password change */}
      <div className="rounded-xl border border-white/10 bg-[#131a30] p-5">
        <div className="flex items-center gap-3 pb-4">
          <Lock size={18} className="text-blue-400" />
          <h3 className="text-sm font-semibold text-white">Смена пароля</h3>
        </div>

        <div className="space-y-4">
          <div className="space-y-2">
            <label className="text-xs text-slate-500">Текущий пароль</label>
            <input
              type="password"
              value={currentPassword}
              onChange={(e) => setCurrentPassword(e.target.value)}
              className="w-full rounded-lg border border-white/10 bg-white/5 px-4 py-3 text-sm text-white focus:border-blue-500 focus:outline-none"
            />
          </div>

          <div className="space-y-2">
            <label className="text-xs text-slate-500">Новый пароль</label>
            <input
              type="password"
              value={newPassword}
              onChange={(e) => setNewPassword(e.target.value)}
              className="w-full rounded-lg border border-white/10 bg-white/5 px-4 py-3 text-sm text-white focus:border-blue-500 focus:outline-none"
            />
            {newPassword.length > 0 && newPassword.length < 8 && (
              <p className="text-xs text-red-400">Минимум 8 символов</p>
            )}
          </div>

          <div className="space-y-2">
            <label className="text-xs text-slate-500">Подтвердите пароль</label>
            <input
              type="password"
              value={confirmPassword}
              onChange={(e) => setConfirmPassword(e.target.value)}
              className="w-full rounded-lg border border-white/10 bg-white/5 px-4 py-3 text-sm text-white focus:border-blue-500 focus:outline-none"
            />
            {confirmPassword.length > 0 && confirmPassword !== newPassword && (
              <p className="text-xs text-red-400">Пароли не совпадают</p>
            )}
          </div>

          <button
            disabled={!canSubmit}
            className="mt-2 rounded-lg bg-blue-600 px-5 py-2.5 text-sm font-medium text-white transition-colors hover:bg-blue-500 disabled:opacity-40 disabled:hover:bg-blue-600"
          >
            Обновить пароль
          </button>
        </div>
      </div>

      {/* Sessions */}
      <div className="rounded-xl border border-white/10 bg-[#131a30] p-5">
        <div className="flex items-center gap-3 pb-4">
          <Smartphone size={18} className="text-blue-400" />
          <h3 className="text-sm font-semibold text-white">Активные сессии</h3>
        </div>

        <div className="space-y-3">
          <SessionRow
            device="Chrome · Windows"
            location="Санкт-Петербург, Россия"
            isCurrent
          />
          <SessionRow
            device="Safari · iPhone"
            location="Санкт-Петербург, Россия"
          />
        </div>
      </div>
    </div>
  );
}

function SessionRow({
  device,
  location,
  isCurrent,
}: {
  device: string;
  location: string;
  isCurrent?: boolean;
}) {
  return (
    <div className="flex items-center justify-between rounded-lg bg-white/5 px-4 py-3">
      <div>
        <p className="text-sm text-white">{device}</p>
        <p className="text-xs text-slate-500">{location}</p>
      </div>
      <div className="flex items-center gap-3">
        {isCurrent && (
          <span className="rounded-md bg-emerald-500/10 px-2 py-0.5 text-[10px] text-emerald-400">
            Текущая
          </span>
        )}
        {!isCurrent && (
          <button className="text-xs text-red-400 transition-colors hover:text-red-300">
            Завершить
          </button>
        )}
      </div>
    </div>
  );
}