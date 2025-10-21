import React from "react";

export default function IconCard({ title, subtitle, icon = "💡" }) {
  return (
    <div className="icon-card">
      <div className="icon">{icon}</div>
      <div className="icon-card-body">
        <div className="icon-card-title">{title}</div>
        <div className="icon-card-sub">{subtitle}</div>
      </div>
    </div>
  );
}