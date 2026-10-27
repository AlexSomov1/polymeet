import type { UserProfile } from "./types";

export const MOCK_USER: UserProfile = {
  id: "u1",
  firstName: "Алексей",
  lastName: "Смирнов",
  university: "СПбПУ",
  faculty: "ИКНК",
  telegramUsername: "@alex_poly",
  bio: "Увлекаюсь веб-разработкой, настолками и бегом по утрам.",
  avatarUrl: "/avatar.jpg",
  reliabilityScore: 96,
  isStudentVerified: true,
  settings: {
    telegramBotNotifications: true,
    nearbyMeetingsNotifications: true,
    contactsVisibleToApprovedOnly: true,
    showLocation: true,
    notificationRadiusKm: 10,
  },
};