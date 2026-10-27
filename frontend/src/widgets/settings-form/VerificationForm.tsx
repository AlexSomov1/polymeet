import { GraduationCap, CheckCircle, Upload } from "lucide-react";
import type { UserProfile } from "@/features/user/types";

interface VerificationFormProps {
  user: UserProfile;
}

export function VerificationForm({ user }: VerificationFormProps) {
  const isVerified = user.isStudentVerified;

  return (
    <div className="space-y-6">
      <h2 className="text-lg font-semibold text-white">Верификация студента</h2>

      {/* Status card */}
      <div className="rounded-xl border border-white/10 bg-[#131a30] p-5">
        <div className="flex items-center gap-3">
          <div className="grid h-10 w-10 place-items-center rounded-full bg-emerald-500/10">
            {isVerified ? (
              <CheckCircle size={20} className="text-emerald-400" />
            ) : (
              <GraduationCap size={20} className="text-amber-400" />
            )}
          </div>
          <div>
            <p className="text-sm font-medium text-white">
              {isVerified ? "Студент подтверждён" : "Верификация не пройдена"}
            </p>
            <p className="text-xs text-slate-500">
              {isVerified
                ? `Ваш аккаунт подтверждён в ${user.university}`
                : "Загрузите студенческий билет для подтверждения"}
            </p>
          </div>
          {isVerified && (
            <span className="ml-auto rounded-md bg-emerald-500/10 px-2 py-1 text-xs text-emerald-400">
              Подтверждено
            </span>
          )}
        </div>
      </div>
          <p>Чтобы пройти проверку, отправьте свой студенческий билет на адрес polymeet@info.ru </p>
      {/* University info (read-only) */}
      <div className="space-y-4">
        <h3 className="text-sm font-medium text-slate-300">Данные университета</h3>
        <div className="grid gap-4 sm:grid-cols-2">
          <div className="space-y-2">
            <label className="text-xs text-slate-500">Университет</label>
            <input
              type="text"
              value={user.university}
              readOnly
              className="w-full rounded-lg border border-white/10 bg-white/5 px-4 py-3 text-sm text-slate-400"
            />
          </div>
          <div className="space-y-2">
            <label className="text-xs text-slate-500">Факультет</label>
            <input
              type="text"
              value={user.faculty}
              readOnly
              className="w-full rounded-lg border border-white/10 bg-white/5 px-4 py-3 text-sm text-slate-400"
            />
          </div>
        </div>
      </div>

      {/* Upload area — only shown if not verified */}
      {!isVerified && (
        <div className="space-y-3">
          <h3 className="text-sm font-medium text-slate-300">Загрузить документ</h3>
          <button className="flex w-full flex-col items-center gap-2 rounded-xl border-2 border-dashed border-white/10 bg-white/5 py-10 text-slate-500 transition-colors hover:border-blue-500/50 hover:bg-white/[0.03]">
            <Upload size={24} />
            <span className="text-sm">Перетащите студенческий билет сюда</span>
            <span className="text-xs text-slate-600">или нажмите для выбора файла</span>
          </button>
        </div>
      )}
    </div>
  );
}