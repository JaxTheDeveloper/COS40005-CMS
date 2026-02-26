
import React from "react";
import { Link, useNavigate } from "react-router-dom";

export default function PublicNavbar({ user, onLogout }) {
  const navigate = useNavigate();

  const handleLogout = (e) => {
    e.preventDefault();
    if (onLogout) onLogout();
    navigate("/login");
  };

  return (
    <nav className="public-navbar">
      <Link to="/">Home</Link>
      <Link to="/events">Events</Link>
      <Link to="/social-gold">Social Gold</Link>
      <Link to="/ask-ai">Ask AI</Link>
      <Link to="/queries">Queries</Link>
      {user ? (
        <a href="#logout" onClick={handleLogout}>Logout</a>
      ) : (
        <Link to="/login">Login</Link>
      )}
      <Link to="/about">About</Link>
    </nav>
  );
}
