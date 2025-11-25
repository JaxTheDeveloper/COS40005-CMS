
import React, { useEffect, useState } from "react";
import { authService } from "../services/auth";
import { useNavigate } from "react-router-dom";
import { Link } from "react-router-dom";

export default function Sidebar() {
  const [menu, setMenu] = useState([
    { to: "/dashboard/compsci", label: "Dashboard" },
    { to: "/calendar", label: "Calendar" },
    { to: "/enrol/select", label: "Enrolment" },
    { to: "/notifications", label: "Notifications" },
    // Teaching and Staff Events will be conditionally shown for staff/convenors
    { to: "/profile", label: "Profile" },
  ]);

  useEffect(() => {
    let mounted = true;
    (async () => {
      try {
        const user = await authService.getCurrentUser();
        const isTeachingRole = user?.is_staff || ['staff', 'unit_convenor', 'admin'].includes(user?.user_type);
        if (mounted && isTeachingRole) {
          setMenu((m) => [
            m[0], // dashboard
            m[1], // calendar
            m[2], // enrol
            m[3], // notifications
            { to: "/teaching", label: "Teaching" },
            { to: "/staff/events", label: "Staff Events" },
            m[4], // profile
          ]);
        }
      } catch (e) {
        // ignore; user may not be authenticated
      }
    })();
    return () => { mounted = false; };
  }, []);

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
