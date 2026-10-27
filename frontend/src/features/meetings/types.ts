import type { CategoryId } from "./filters/categories";

export interface MeetingFormData {
  title: string;
  categoryId: CategoryId;
  description: string;
  date: string; // datetime-local: YYYY-MM-DDTHH:MM
  maxSeats: number;
  address: string;
}