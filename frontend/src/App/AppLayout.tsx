import { useState } from "react";
import { Outlet } from "react-router-dom";
import { Navbar } from "@/widgets/navbar/Navbar";
import { CreateMeetingModal } from "@/widgets/create-meeting/CreateMeetingModal";
import type { MeetingFormData } from "@/features/meetings/types";

export function AppLayout() {
  const [isCreateOpen, setIsCreateOpen] = useState(false);

  const handleCreate = (data: MeetingFormData) => {
    console.log("Create meeting:", data);
    // TODO: API call
  };

  return (
    <div className="min-h-screen bg-background text-foreground">
      <Navbar onCreateClick={() => setIsCreateOpen(true)} />

      <div className="mx-auto max-w-350 px-4 py-6">
        <Outlet />
      </div>

      <CreateMeetingModal
        key={`create-${isCreateOpen}`}
        isOpen={isCreateOpen}
        onClose={() => setIsCreateOpen(false)}
        onSubmit={handleCreate}
        mode="create"
      />
    </div>
  );
}