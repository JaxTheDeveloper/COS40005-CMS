
import React, { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { Link } from "react-router-dom";
import DashboardRoundedIcon from "@mui/icons-material/DashboardRounded";
import CalendarMonthRoundedIcon from "@mui/icons-material/CalendarMonthRounded";
import SchoolRoundedIcon from "@mui/icons-material/SchoolRounded";
import NotificationsRoundedIcon from "@mui/icons-material/NotificationsRounded";
import PersonRoundedIcon from "@mui/icons-material/PersonRounded";
import MenuBookRoundedIcon from "@mui/icons-material/MenuBookRounded";
import EventNoteRoundedIcon from "@mui/icons-material/EventNoteRounded";
import LogoutRoundedIcon from "@mui/icons-material/LogoutRounded";

export default function Sidebar({ user, onLogout }) {
  const [menu, setMenu] = useState([
    { to: "/dashboard/compsci", label: "Dashboard", icon: <DashboardRoundedIcon fontSize="small" /> },
    { to: "/calendar", label: "Calendar", icon: <CalendarMonthRoundedIcon fontSize="small" /> },
    { to: "/enrol/select", label: "Enrolment", icon: <SchoolRoundedIcon fontSize="small" /> },
    { to: "/notifications", label: "Notifications", icon: <NotificationsRoundedIcon fontSize="small" /> },
    { to: "/profile", label: "Profile", icon: <PersonRoundedIcon fontSize="small" /> },
  ]);

  useEffect(() => {
    if (!user) return;
    const isTeachingRole = user.is_staff || ['staff', 'unit_convenor', 'admin'].includes(user.user_type);
    if (isTeachingRole) {
      setMenu((m) => [
        m[0], // dashboard
        m[1], // calendar
        m[2], // enrol
        m[3], // notifications
        { to: "/teaching", label: "Teaching", icon: <MenuBookRoundedIcon fontSize="small" /> },
        { to: "/staff/events", label: "Staff Events", icon: <EventNoteRoundedIcon fontSize="small" /> },
        m[4], // profile
      ]);
    }
  }, [user]);

  const navigate = useNavigate();

  const handleLogout = (e) => {
    e.preventDefault();
    if (onLogout) onLogout();
    navigate('/login');
  };

  return (
    <nav className="sidebar">
      <div className="sidebar-top">
        <div className="sidebar-avatar">
          <div className="avatar-placeholder" />
        </div>

        <div className="sidebar-menu">
          {menu.map((item) => (
            <Link to={item.to} className="sidebar-btn" key={item.to}>
              <div className="sidebar-icon">{item.icon}</div>
              <div className="sidebar-label">{item.label}</div>
            </Link>
          ))}
        </div>
      </div>

      <div className="sidebar-bottom">
        <a href="#logout" onClick={handleLogout} className="sidebar-logout">
          <div className="sidebar-icon"><LogoutRoundedIcon fontSize="small" /></div>
          <div className="sidebar-label">Logout</div>
        </a>
      </div>
    </nav>
  );
}
