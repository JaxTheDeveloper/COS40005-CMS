import React from "react";
import { Routes, Route, Navigate } from "react-router-dom";
import PublicNavbar from "./components/PublicNavbar.jsx";
import Sidebar from "./components/Sidebar.jsx";
import AskAI from "./pages/AskAI.jsx";
import Queries from "./pages/Queries.jsx";
import CSDashboard from "./pages/CS_Dashboard.jsx";
import Login from "./pages/Login.jsx";
import MyEnrollments from "./components/MyEnrollments.jsx";
import SocialGold from "./components/SocialGold.jsx";
import Profile from "./components/Profile.jsx";
import Events from "./pages/Events.jsx";
import CalendarPage from "./pages/Calendar.jsx";
import EnrollSelect from "./pages/EnrollSelect.jsx";
import TeachingDashboard from "./pages/TeachingDashboard.jsx";
import StaffEventManager from "./pages/StaffEventManager.jsx";
import StudentNotifications from "./pages/StudentNotifications.jsx";

import "./App.css";
import { authService } from "./services/auth";

export default function App() {
  // Simulate auth state (replace with real context/hook later)
  const [user, setUser] = React.useState(null);
  React.useEffect(() => {
    // Check current authenticated user via authService
    async function check() {
      try {
        const u = await authService.getCurrentUser();
        setUser(u);
      } catch (e) {
        setUser(null);
      }
    }
    check();
  }, []);

  return (
    <div className={`app-layout ${user ? "logged-in" : ""}`}>
      <PublicNavbar />
      {user && <Sidebar />}
      <main className={!user ? "main-public" : "main-private"}>
        <Routes>
          <Route path="/" element={<Navigate to="/dashboard/compsci" />} />
          <Route path="/dashboard/compsci" element={<CSDashboard />} />
          <Route path="/queries" element={<Queries />} />
          <Route path="/ask-ai" element={<AskAI />} />
          <Route path="/login" element={<Login />} />
          <Route path="/enrollments" element={<MyEnrollments />} />
          <Route path="/social-gold" element={<SocialGold />} />
          <Route path="/profile" element={<Profile />} />
          <Route path="/events" element={<Events />} />
          <Route path="/calendar" element={<CalendarPage />} />
          <Route path="/enrol/select" element={<EnrollSelect />} />
          <Route path="/teaching" element={<TeachingDashboard />} />
          <Route path="/staff/events" element={<StaffEventManager />} />
          <Route path="/notifications" element={<StudentNotifications />} />
        </Routes>
      </main>
      <footer className="footer">
        © {new Date().getFullYear()} Swinburne VN (demo)
      </footer>
    </div>
  );
}
