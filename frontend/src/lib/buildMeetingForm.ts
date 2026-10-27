import type { MeetingFormData } from "@/features/meetings/types";
import {type CategoryId } from "@/features/meetings/filters/categories";
function toDatetimeLocal(iso: string): string {
  const d = new Date(iso);
  d.setMinutes(d.getMinutes() - d.getTimezoneOffset());
  return d.toISOString().slice(0, 16);
}

export function buildMeetingForm(
  mode: "create" | "edit",
  initialData?: Partial<MeetingFormData>
): MeetingFormData {
  const base: MeetingFormData = {
    title: "",
    categoryId: "" as CategoryId,
    description: "",
    date: "",
    maxSeats: 10,
    address: "",
  };

  if (mode === "edit" && initialData) {
    return {
      ...base,
      ...initialData,
      date: initialData.date ? toDatetimeLocal(initialData.date) : "",
    };
  }

  return base;
}