import { useState } from "react";
import { SettingsSidebar, type SettingsTab } from "@/widgets/settings-sidebar/SettingsSidebar";
import { ProfileForm } from "@/widgets/settings-form/ProfileForm";
import { NotificationsForm } from "@/widgets/settings-form/NotificationsForm";
import { MOCK_USER } from "@/features/user/mocks";
import type { UserProfile } from "@/features/user/types";
import { VerificationForm } from "@/widgets/settings-form/VerificationForm";
import { PrivacyForm } from "@/widgets/settings-form/PrivacyForm";
import { SecurityForm } from "@/widgets/settings-form/SecurityForm";

export function ModerationPage() {
  const [activeTab, setActiveTab] = useState<SettingsTab>("profile");
  const [draftUser, setDraftUser] = useState<UserProfile>(MOCK_USER);
  const [isDirty, setIsDirty] = useState(false);

  const handleUserChange = (user: UserProfile) => {
    setDraftUser(user);
    setIsDirty(true);
  };

  const handleSettingsChange = (settings: UserProfile["settings"]) => {
    setDraftUser((prev) => ({ ...prev, settings }));
    setIsDirty(true);
  };

  const handleSave = () => {
    // TODO: API call
    console.log("Saving user:", draftUser);
    setIsDirty(false);
  };

  const handleCancel = () => {
    setDraftUser(MOCK_USER);
    setIsDirty(false);
  };

  return (
    <div className="flex flex-col gap-6 lg:flex-row">
      {/* Left sidebar */}
      <SettingsSidebar
        activeTab={activeTab}
        onTabChange={setActiveTab}
        onLogout={() => console.log("logout")}
      />

      {/* Right content */}
      <div className="min-w-0 flex-1 space-y-6">
        <div className="rounded-xl border border-white/10 bg-[#131a30] p-6">
          {activeTab === "profile" && (
            <ProfileForm user={draftUser} onChange={handleUserChange} />
          )}

          {activeTab === "notifications" && (
            <NotificationsForm
              settings={draftUser.settings}
              onChange={handleSettingsChange}
            />
          )}

          {activeTab === "verification" && (
            <VerificationForm user={draftUser} />
          )}

          {activeTab === "privacy" && (
            <PrivacyForm
              settings={draftUser.settings}
              onChange={handleSettingsChange}
            />
          )}

          {activeTab === "security" && (
            <SecurityForm />
          )}
        </div>

        {/* Save / Cancel bar */}
        {isDirty && (
          <div className="flex items-center justify-end gap-3">
            <button
              onClick={handleCancel}
              className="rounded-lg px-5 py-2 text-sm font-medium text-slate-400 transition-colors hover:text-white"
            >
              Отмена
            </button>
            <button
              onClick={handleSave}
              className="rounded-lg bg-blue-600 px-5 py-2 text-sm font-medium text-white transition-colors hover:bg-blue-500"
            >
              Сохранить изменения
            </button>
          </div>
        )}
      </div>
    </div>
  );
}

