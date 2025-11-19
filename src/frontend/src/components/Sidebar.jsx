
import React from "react";
import { authService } from "../services/auth";
import { useNavigate } from "react-router-dom";
import { Link } from "react-router-dom";

export default function Sidebar() {
  const menu = [
    { to: "/dashboard/compsci", label: "Dashboard" },
    { to: "/calendar", label: "Calendar" },
    { to: "/enrol/select", label: "Enrolment" },
    { to: "/profile", label: "Profile" },
  ];

  const navigate = useNavigate();

  const handleLogout = (e) => {
    e.preventDefault();
    authService.logout();
    navigate('/login');
  };

  return (
    <nav className="sidebar">
      <div className="sidebar-top">
        <div className="sidebar-avatar">
          {/* avatar placeholder; user will provide image later */}
          <div className="avatar-placeholder" />
        </div>

        <div className="sidebar-menu">
          {menu.map((item) => (
            <Link to={item.to} className="sidebar-btn" key={item.to}>
              <div className="icon-placeholder" />
              <div className="sidebar-label">{item.label}</div>
            </Link>
          ))}
        </div>
      </div>

      <div className="sidebar-bottom">
        <a href="#logout" onClick={handleLogout} className="sidebar-logout">
          <div className="icon-placeholder" />
          <div className="sidebar-label">Logout</div>
        </a>
      </div>
    </nav>
  );
}
