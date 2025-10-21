import React from "react";
import { Routes, Route, Navigate } from "react-router-dom";
import Navbar from "./components/Navbar.jsx";
import AskAI from "./pages/AskAI.jsx";
import Queries from "./pages/Queries.jsx";
import CSDashboard from "./pages/CS_Dashboard.jsx";
import Login from "./pages/Login.jsx";          // ← new import

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
          <Route path="/login" element={<Login />} />     {/* ← new route */}
        </Routes>
      </main>

      <footer className="footer">
        © {new Date().getFullYear()} Swinburne VN (demo)
      </footer>
    </div>
  );
}
