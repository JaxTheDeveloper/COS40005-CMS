import React from "react";
import { Routes, Route, Navigate } from "react-router-dom";
import Navbar from "./components/Navbar.jsx";
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

export default function App() {
  return (
    <div className="app">
      <Navbar />

      <div className="hero-image" role="img" aria-label="Campus">
        <div className="hero-overlay">
          <div className="hero-title">SWINBURNE VN</div>
        </div>
      </div>

      <main className="container">
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
        </Routes>
      </main>

      <footer className="footer">
        © {new Date().getFullYear()} Swinburne VN (demo)
      </footer>
    </div>
  );
}
