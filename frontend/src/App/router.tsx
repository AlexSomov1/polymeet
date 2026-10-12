import { createBrowserRouter, RouterProvider } from "react-router-dom";
import { AppLayout } from "./AppLayout";
import { FeedPage } from "@/pages/feed/FeedPage";
import { MyEventsPage } from "@/pages/my/MyEventsPage";
import { ModerationPage } from "@/pages/moderation/ModerationPage";

const router = createBrowserRouter([
  {
    element: <AppLayout />,
    children: [
      { path: "/", element: <FeedPage /> },
      { path: "/my", element: <MyEventsPage /> },
      { path: "/moderation", element: <ModerationPage /> },
    ],
  },
]);

export function AppRouter() {
  return <RouterProvider router={router} />;
}