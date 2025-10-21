import React from "react";
import { NavLink, useNavigate } from "react-router-dom";

const NavItem = ({ to, children }) => (
  <NavLink
    to={to}
    className={({ isActive }) =>
      "nav-link" + (isActive ? " nav-link--active" : "")
    }
  >
    {children}
  </NavLink>
);

export default function Navbar() {
  const navigate = useNavigate();

  return (
    <header className="nav">
      <nav className="nav-inner container">
        <div className="brand">Swinburne</div>
        <div className="spacer" />

        <NavItem to="/dashboard/compsci">Dashboard</NavItem>
        <NavItem to="/queries">Queries</NavItem>
        <NavItem to="/courses">Courses</NavItem>
        <NavItem to="/clubs">Clubs</NavItem>
        <NavItem to="/lecturers">Lecturers/Mentors</NavItem>
        <NavItem to="/ask-ai">Ask AI Assistant</NavItem>

        {/* right-aligned Login button */}
        <button
          className="btn btn-primary"
          style={{ marginLeft: "12px" }}
          onClick={() => navigate("/login")}
        >
          Login
        </button>
      </nav>
    </header>
  );
}
