
import React from "react";
import { Link } from "react-router-dom";

export default function PublicNavbar() {
  return (
    <nav className="public-navbar">
      <Link to="/">Home</Link>
      <Link to="/events">Events</Link>
      <Link to="/social-gold">Social Gold</Link>
      <Link to="/ask-ai">Ask AI</Link>
      <Link to="/queries">Queries</Link>
      <Link to="/login">Login</Link>
      <Link to="/about">About</Link>
    </nav>
  );
}
