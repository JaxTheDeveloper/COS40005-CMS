import React, { useEffect } from "react";

const TEAM_MEMBERS = [
  { name: "Member 1", role: "Project Lead", emoji: "👨‍💼" },
  { name: "Member 2", role: "Backend Developer", emoji: "⚙️" },
  { name: "Member 3", role: "Frontend Developer", emoji: "🎨" },
  { name: "Member 4", role: "Full-Stack Developer", emoji: "💻" },
  { name: "Member 5", role: "QA & Testing", emoji: "🔍" },
];

const FEATURES = [
  { icon: "📚", title: "Course Management", desc: "Browse, enrol, and manage your academic units seamlessly." },
  { icon: "📅", title: "Events & Calendar", desc: "Stay updated with university events and manage your schedule." },
  { icon: "🤖", title: "AI Study Assistant", desc: "Get instant answers to academic questions powered by Gemini AI." },
  { icon: "🔔", title: "Notifications", desc: "Receive real-time alerts for important announcements and deadlines." },
  { icon: "🏆", title: "Social Gold", desc: "Track achievements and engage with the university community." },
  { icon: "📝", title: "Queries & Support", desc: "Submit and track academic queries with staff support." },
];

export default function About() {
  useEffect(() => {
    window.scrollTo(0, 0);
  }, []);

  return (
    <section className="about-wrapper">
      {/* Hero Section */}
      <div className="about-hero">
        <div className="about-hero-badge">COS40005 Capstone Project</div>
        <h1 className="about-hero-title">Swinburne CMS</h1>
        <p className="about-hero-subtitle">
          A modern Course Management System built for Swinburne University
          of Technology — Da Nang City Campus.
        </p>
      </div>

      {/* About Section */}
      <div className="about-section">
        <h2 className="about-section-title">About the Project</h2>
        <div className="about-card">
          <div className="about-mission-vision">
            <div className="about-mission-card">
              <h3>Our Mission</h3>
              <p>To empower the Swinburne Vietnam community with an integrated, efficient, and user-centric course management platform that simplifies academic administration and enhances student engagement.</p>
            </div>
            <div className="about-vision-card">
              <h3>Our Vision</h3>
              <p>To be the premier digital gateway for academic excellence at Swinburne HCM, setting new standards for educational management systems through innovation and accessibility.</p>
            </div>
          </div>
          <p>
            The <strong>Swinburne CMS</strong> is a flagship capstone project developed
            as part of the <strong>COS40005 Computing Technology Project</strong>.
            Our team has worked tirelessly to build a solution that addresses the unique
            needs of both students and faculty in a modern academic environment.
          </p>
          <p>
            From real-time notifications to an AI-powered study assistant, every feature
            has been crafted with the goal of making academic life more organised, 
            connected, and productive.
          </p>
        </div>
      </div>

      {/* Features Section */}
      <div className="about-section">
        <h2 className="about-section-title">Key Features</h2>
        <div className="about-features-grid">
          {FEATURES.map((f, idx) => (
            <div key={idx} className="about-feature-card">
              <span className="about-feature-icon">{f.icon}</span>
              <h3 className="about-feature-title">{f.title}</h3>
              <p className="about-feature-desc">{f.desc}</p>
            </div>
          ))}
        </div>
      </div>

      {/* Tech Stack Section */}
      <div className="about-section">
        <h2 className="about-section-title">Technology Stack</h2>
        <div className="about-tech-row">
          {[
            { label: "React", color: "#61dafb" },
            { label: "Django", color: "#0c4b33" },
            { label: "PostgreSQL", color: "#336791" },
            { label: "REST API", color: "#e53935" },
            { label: "Gemini AI", color: "#4285f4" },
            { label: "JWT Auth", color: "#f5a623" },
          ].map((tech, idx) => (
            <span
              key={idx}
              className="about-tech-badge"
              style={{ borderColor: tech.color, color: tech.color }}
            >
              {tech.label}
            </span>
          ))}
        </div>
      </div>

      {/* Team Section */}
      <div className="about-section">
        <h2 className="about-section-title">Our Team</h2>
        <div className="about-team-grid">
          {TEAM_MEMBERS.map((m, idx) => (
            <div key={idx} className="about-team-card">
              <span className="about-team-emoji">{m.emoji}</span>
              <strong className="about-team-name">{m.name}</strong>
              <span className="about-team-role">{m.role}</span>
            </div>
          ))}
        </div>
      </div>

      {/* Footer Info */}
      <div className="about-footer-info">
        <p>
          Swinburne University of Technology — Da Nang City Campus
        </p>
        <p className="about-footer-sub">
          COS40005 Computing Technology Project &middot; Semester 1, 2026
        </p>
      </div>
    </section>
  );
}
