import { useState, useEffect } from "react";
import { X } from "lucide-react";
import type { MeetingFormData } from "@/features/meetings/types";
import { buildMeetingForm } from "@/lib/buildMeetingForm";
import { validateMeetingForm } from "@/lib/validateMeetingForm";
import { FormField } from "./FormField";
import { FormTextarea } from "./FormTextarea";
import { CategoryChips } from "./CategoryChips";
import type { ValidationErrors } from "@/lib/validateMeetingForm";
interface CreateMeetingModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSubmit: (data: MeetingFormData) => void;
  mode: "create" | "edit";
  initialData?: Partial<MeetingFormData>;
}

export function CreateMeetingModal({
  isOpen,
  onClose,
  onSubmit,
  mode,
  initialData,
}: CreateMeetingModalProps) {
  const [form, setForm] = useState(() => buildMeetingForm(mode, initialData));
  const [errors, setErrors] = useState<ValidationErrors>({});

  // Escape to close
  useEffect(() => {
    if (!isOpen) return;
    const handleKey = (e: KeyboardEvent) => {
      if (e.key === "Escape") onClose();
    };
    window.addEventListener("keydown", handleKey);
    return () => window.removeEventListener("keydown", handleKey);
  }, [isOpen, onClose]);

  const update = (patch: Partial<MeetingFormData>) => {
    setForm((prev) => ({ ...prev, ...patch }));
    // Clear error for touched field
    const key = Object.keys(patch)[0];
    if (key) {
      setErrors((prev) => {
        // eslint-disable-next-line @typescript-eslint/no-unused-vars
        const { [key as keyof ValidationErrors]: _, ...rest } = prev;
        return rest;
      });
    }
  };

  const handleSubmit = () => {
    const validation = validateMeetingForm(form);
    if (Object.keys(validation).length > 0) {
      setErrors(validation);
      return;
    }
    onSubmit({ ...form });
    onClose();
  };

  if (!isOpen) return null;

  return (
    <>
      <div
        className="fixed inset-0 z-50 bg-black/70 backdrop-blur-sm"
        onClick={onClose}
      />
      <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
        <div className="max-h-[90vh] w-full max-w-lg overflow-y-auto rounded-2xl border border-white/10 bg-[#131a30] shadow-2xl">
          {/* Header */}
          <div className="flex items-center justify-between border-b border-white/10 px-6 py-4">
            <h2 className="text-lg font-semibold text-white">
              {mode === "create" ? "Создать встречу" : "Редактировать встречу"}
            </h2>
            <button onClick={onClose} className="rounded-md p-1 text-slate-400 transition-colors hover:text-white">
              <X size={20} />
            </button>
          </div>

          {/* Form */}
          <div className="space-y-5 px-6 py-5">
            <FormField
              label="Название"
              required
              value={form.title}
              onChange={(e) => update({ title: e.target.value })}
              placeholder="Напр.: Поход на лекцию по ИИ"
              error={errors.title}
            />

            <CategoryChips
              selected={form.categoryId}
              onSelect={(id) => update({ categoryId: id })}
              error={errors.categoryId}
            />

            <FormTextarea
              label="Описание"
              value={form.description}
              onChange={(e) => update({ description: e.target.value })}
              placeholder="Подробнее о встрече..."
              rows={3}
            />

            <div className="grid grid-cols-2 gap-4">
              <FormField
                label="Дата и время"
                required
                type="datetime-local"
                value={form.date}
                onChange={(e) => update({ date: e.target.value })}
                error={errors.date}
              />
              <FormField
                label="Макс. мест"
                required
                type="number"
                min={1}
                value={form.maxSeats}
                onChange={(e) => update({ maxSeats: Math.max(1, Number(e.target.value)) })}
              />
            </div>

            <FormField
              label="Место встречи"
              required
              value={form.address}
              onChange={(e) => update({ address: e.target.value })}
              placeholder="Напр.: ауд.305 СПбПУ, Политехническая"
              error={errors.address}
            />
          </div>

          {/* Footer */}
          <div className="flex items-center gap-3 border-t border-white/10 px-6 py-4">
            <button
              onClick={onClose}
              className="flex-1 rounded-lg border border-white/10 py-2.5 text-sm font-medium text-slate-300 transition-colors hover:bg-white/5 hover:text-white"
            >
              Отмена
            </button>
            <button
              onClick={handleSubmit}
              className="flex-1 rounded-lg bg-blue-600 py-2.5 text-sm font-semibold text-white transition-colors hover:bg-blue-500"
            >
              {mode === "create" ? "Создать встречу" : "Сохранить"}
            </button>
          </div>
        </div>
      </div>
    </>
  );
}