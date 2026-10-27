import type { CategoryId } from "./filters/categories";

export interface Meeting {
  id: string;
  title: string;
  categoryId: CategoryId;
  address: string;
  lat: number;
  lng: number;
  distanceKm: number;
  /** ISO 8601 — comparable with string ops, filterable by prefix */
  date: string;
  freeSeats: number;
  imageUrl: string;
  isJoined: boolean;
}

export const MOCK_MEETINGS: Meeting[] = [

  {
    id: "m1",
    title: "Утренняя пробежка по парку",
    categoryId: "sport",
    address: "Центральный парк, вход №2",
    lat: 59.9520,
    lng: 30.3100,
    distanceKm: 3.5,
    date: "2026-10-26T08:00:00",
    freeSeats: 6,
    imageUrl: "/sport.jpg",
    isJoined: false,
  },
  {
    id: "m2",
    title: "Прогулка по набережной",
    categoryId: "walk",
    address: "Набережная, фонтан",
    lat: 59.9400,
    lng: 30.3400,
    distanceKm: 5.2,
    date: "2026-10-27T15:00:00",
    freeSeats: 1,
    imageUrl: "/walking.jpg",
    isJoined: false,
  },
  {
    id: "m3",
    title: "Квартирник: акустика",
    categoryId: "other",
    address: "ул. Морская 22, кв. 7",
    lat: 59.9200,
    lng: 30.3000,
    distanceKm: 12.6,
    date: "2026-11-02T19:30:00",
    freeSeats: 2,
    imageUrl: "/others.jpg",
    isJoined: false,
  },
    {
    id: "m4",
    title: "Играть в видеоигру",
    categoryId: "games",
    address: "Пушкинская 10",
    lat: 59.9343,
    lng: 30.3351,
    distanceKm: 1.3,
    date: "2026-10-27T18:30:00",
    freeSeats: 3,
    imageUrl: "/gaming.jpg",
    isJoined: true,
  },
  {
    id: "m5",
    title: "Лекция: основы TypeScript",
    categoryId: "lecture",
    address: "Главный корпус, ауд. 305",
    lat: 59.9310,
    lng: 30.3600,
    distanceKm: 0.4,
    date: "2026-10-25T17:00:00",
    freeSeats: 3,
    imageUrl: "/lecture.jpg",
    isJoined: false,
  },
  {
    id: "m6",
    title: "Вечер настольных игр",
    categoryId: "concert",
    address: "Кафе «Кубик», Ленина 5",
    lat: 59.9290,
    lng: 30.3200,
    distanceKm: 2.8,
    date: "2026-10-29T19:00:00",
    freeSeats: 0,
    imageUrl: "/concert.jpg",
    isJoined: false,
  },
];

// === My Events extensions ===

export type EventStatus = "approved" | "pending" | "confirmed" | "completed" | "cancelled";
export type UserRole = "participant" | "organizer";

export interface MyEvent extends Meeting {
  status: EventStatus;
  role: UserRole;
  unreadCount: number;
  hasRoute: boolean;
}

export const MOCK_MY_EVENTS: MyEvent[] = [
  {
    ...MOCK_MEETINGS[2], // "Вечер настольных игр" — m3
    status: "approved",
    role: "participant",
    unreadCount: 2,
    hasRoute: true,
  },
  {
    ...MOCK_MEETINGS[1], // "Лекция: основы TypeScript" — m2
    status: "pending",
    role: "participant",
    unreadCount: 0,
    hasRoute: false,
  },
  {
    ...MOCK_MEETINGS[4], // "Прогулка по набережной" — m5
    status: "approved",
    role: "participant",
    unreadCount: 0,
    hasRoute: false,
  },
  {
    ...MOCK_MEETINGS[3], // "Утренняя пробежка" — m4
    status: "approved",
    role: "participant",
    unreadCount: 0,
    hasRoute: false,
  },
  // Organizer events
  {
    id: "m8",
    title: "Хакатон по TypeScript",
    categoryId: "other",
    address: "IT-парк, этаж 3",
    lat: 59.9260,
    lng: 30.3150,
    distanceKm: 4.2,
    date: "2026-11-05T10:00:00",
    freeSeats: 15,
    imageUrl: "/lecture.jpg",
    isJoined: true,
    status: "pending",
    role: "organizer",
    unreadCount: 3,
    hasRoute: true,
  },
  {
    id: "m9",
    title: "Мастер-класс по глине",
    categoryId: "other",
    address: "Главный корп, №2 10",
    lat: 59.9380,
    lng: 30.3250,
    distanceKm: 6.6,
    date: "2026-10-30T14:00:00",
    freeSeats: 2,
    imageUrl: "/others.jpg",
    isJoined: true,
    status: "approved",
    role: "organizer",
    unreadCount: 0,
    hasRoute: false,
  },
];

export interface ChatMessage {
  id: string;
  meetingId: string;
  authorId: string;
  authorName: string;
  text: string;
  sentAt: string;
}

export const MOCK_MESSAGES: Record<string, ChatMessage[]> = {
  "m3": [
    { id: "msg1", meetingId: "m3", authorId: "u2", authorName: "Анна", text: "Привет! Какой стол забронируем?", sentAt: "2026-10-27T14:00:00" },
    { id: "msg2", meetingId: "m3", authorId: "me", authorName: "GR", text: "У окна, если свободен", sentAt: "2026-10-30T14:05:00" },
  ],
  "m8": [
    { id: "msg3", meetingId: "m8", authorId: "u5", authorName: "Дима", text: "Когда регистрация?", sentAt: "2026-10-29T09:00:00" },
    { id: "msg4", meetingId: "m8", authorId: "u6", authorName: "Маша", text: "С 9:30", sentAt: "2026-10-25T09:15:00" },
    { id: "msg5", meetingId: "m8", authorId: "u7", authorName: "Коля", text: "Буду чуть позже", sentAt: "2026-10-25T09:20:00" },
  ],
};