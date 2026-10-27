import type { MeetingFormData } from "@/features/meetings/types";

export interface ValidationErrors {
  title?: string;
  categoryId?: string;
  date?: string;
  address?: string;
  maxSeats?: string;
}

export function validateMeetingForm(form: MeetingFormData): ValidationErrors {
  const errors: ValidationErrors = {};

  if (!form.title.trim() || form.title.trim().length < 3) {
    errors.title = "Минимум 3 символа";
  }
  if (!form.categoryId) {
    errors.categoryId = "Выберите тематику";
  }
  if (!form.date) {
    errors.date = "Укажите дату и время";
  }
  if (!form.address.trim()) {
    errors.address = "Укажите место встречи";
  }
  if (form.maxSeats < 1) {
    errors.maxSeats = "Минимум 1 место";
  }

  return errors;
}