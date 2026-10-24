import type { CategoryId } from "./filters/categories";

export interface Meeting {
  id: string;
  title: string;
  categoryId: CategoryId;
  address: string;
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
    title: "Играть в видеоигру",
    categoryId: "games",
    address: "Пушкинская 10",
    distanceKm: 1.3,
    date: "2026-10-27T18:30:00",
    freeSeats: 3,
    imageUrl: "/gaming.jpg",
    isJoined: true,
  },
  {
    id: "m2",
    title: "Лекция: основы TypeScript",
    categoryId: "lecture",
    address: "Главный корпус, ауд. 305",
    distanceKm: 0.4,
    date: "2026-10-25T17:00:00",
    freeSeats: 12,
    imageUrl: "/lecture.jpg",
    isJoined: false,
  },
  {
    id: "m3",
    title: "Вечер настольных игр",
    categoryId: "games",
    address: "Кафе «Кубик», Ленина 5",
    distanceKm: 2.8,
    date: "2026-10-28T19:00:00",
    freeSeats: 0,
    imageUrl: "/gaming.jpg",
    isJoined: false,
  },
  {
    id: "m4",
    title: "Концерт студенческих групп",
    categoryId: "concert",
    address: "Актовый зал",
    distanceKm: 0.1,
    date: "2026-10-31T20:00:00",
    freeSeats: 45,
    imageUrl: "/concert.jpg",
    isJoined: false,
  },
  {
    id: "m5",
    title: "Утренняя пробежка по парку",
    categoryId: "sport",
    address: "Центральный парк, вход №2",
    distanceKm: 3.5,
    date: "2026-10-26T08:00:00",
    freeSeats: 6,
    imageUrl: "/sport.jpg",
    isJoined: false,
  },
  {
    id: "m6",
    title: "Прогулка по набережной",
    categoryId: "walk",
    address: "Набережная, фонтан",
    distanceKm: 5.2,
    date: "2026-10-27T15:00:00",
    freeSeats: 8,
    imageUrl: "/walking.jpg",
    isJoined: false,
  },
  {
    id: "m7",
    title: "Квартирник: акустика",
    categoryId: "other",
    address: "ул. Морская 22, кв. 7",
    distanceKm: 12.6,
    date: "2026-11-02T19:30:00",
    freeSeats: 2,
    imageUrl: "/others.jpg",
    isJoined: false,
  },
 {
    id: "m2",
    title: "Лекция: основы TypeScript",
    categoryId: "lecture",
    address: "Главный корпус, ауд. 305",
    distanceKm: 0.4,
    date: "2026-10-25T17:00:00",
    freeSeats: 12,
    imageUrl: "/lecture.jpg",
    isJoined: false,
  },
    {
    id: "m4",
    title: "Концерт студенческих групп",
    categoryId: "concert",
    address: "Актовый зал",
    distanceKm: 0.1,
    date: "2026-10-31T20:00:00",
    freeSeats: 45,
    imageUrl: "/concert.jpg",
    isJoined: false,
  },
];