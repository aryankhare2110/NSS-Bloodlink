import { createBrowserRouter, RouterProvider } from "react-router-dom"
import { Layout } from "@/components/layout/Layout"
import Dashboard from "@/pages/Dashboard"
import Requests from "@/pages/Requests"
import Donors from "@/pages/Donors"
import Camps from "@/pages/Camps"
import Assistant from "@/pages/Assistant"
import Settings from "@/pages/Settings"

const router = createBrowserRouter([
  {
    path: "/",
    element: <Layout />,
    children: [
      {
        index: true,
        element: <Dashboard />,
      },
      {
        path: "requests",
        element: <Requests />,
      },
      {
        path: "donors",
        element: <Donors />,
      },
      {
        path: "camps",
        element: <Camps />,
      },
      {
        path: "assistant",
        element: <Assistant />,
      },
      {
        path: "settings",
        element: <Settings />,
      },
    ],
  },
])

export function AppRouter() {
  return <RouterProvider router={router} />
}

