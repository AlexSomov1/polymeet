export interface UserProfile {
  id: string;
  firstName: string;
  lastName: string;
  university: string;
  faculty: string;
  telegramUsername: string;
  bio: string;
  avatarUrl: string;
  reliabilityScore: number;
  isStudentVerified: boolean;
  settings: {
    telegramBotNotifications: boolean;
    nearbyMeetingsNotifications: boolean;
    contactsVisibleToApprovedOnly: boolean;
    showLocation: boolean;
    notificationRadiusKm: number;
  };
}