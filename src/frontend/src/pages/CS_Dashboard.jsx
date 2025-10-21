import React from "react";
import IconCard from "../components/IconCard.jsx";


const news = [
  {
    title: "Introduction to Quantum Computing",
    text:
      "Learn the fundamentals of qubits, superposition & algorithms.",
  },
  {
    title: "Cybersecurity in the Age of AI",
    text:
      "Secure design, threat modeling, detection, and governance.",
  },
  {
    title: "Creative Coding with AR/VR",
    text:
      "Build immersive experiences using Unity & WebXR.",
  },
];

const events = [
  { date: "09 • 18 • 2025", title: "Introduction to Quantum Computing" },
  { date: "12 • 01 • 2025", title: "Cybersecurity in the Age of AI" },
  { date: "01 • 06 • 2026", title: "Creative Coding with AR/VR" },
];

const gallery = Array.from({ length: 6 }, (_, i) => `https://picsum.photos/seed/cs${i}/600/400`);

export default function CSDashboard() {
  return (
    <section className="stack">
      <div className="breadcrumb">Home / Dashboard / <strong>Computer Science</strong></div>
      <h1 className="page-h1">Bachelor of Computer Science</h1>

      <p className="lead">
        Crack the code for a rewarding career at the core of the digital revolution.
        With a rich stream of diverse specializations, this degree prepares you for the
        most in-demand tech roles — from AI and data to security, cloud, and XR.
      </p>

      <div className="actions-row">
        <button className="btn btn-primary">Add Major</button>
        <div className="card-grid">
          <IconCard title="Overview" subtitle="General view, jobs after studying." icon="📘" />
          <IconCard title="Location" subtitle="Where you’ll learn and belong." icon="📍" />
          <IconCard title="Fee & Scholarship" subtitle="Tuition, aid & grants." icon="💸" />
          <IconCard title="Study structure" subtitle="Units and study plan." icon="🧩" />
        </div>
      </div>

      <div className="two-col">
        <div className="left-col">
          <h3 className="subheading">Articles</h3>
          <ul className="news-list">
            {news.map((n, i) => (
              <li key={i} className="news-item">
                <img
                  src={`https://picsum.photos/seed/news${i}/120/80`}
                  alt=""
                  className="news-thumb"
                />
                <div className="news-body">
                  <div className="news-title">{n.title}</div>
                  <p className="news-text">{n.text}</p>
                </div>
                <div className="news-arrow">→</div>
              </li>
            ))}
          </ul>
        </div>

        <div className="right-col">
          <h3 className="subheading">Events</h3>
          <ul className="event-list">
            {events.map((e, i) => (
              <li key={i} className="event-item">
                <div className="event-date">{e.date}</div>
                <div className="event-title">{e.title}</div>
                <div className="news-arrow">→</div>
              </li>
            ))}
          </ul>
        </div>
      </div>

      <h3 className="subheading">Gallery</h3>
      <div className="gallery">
        {gallery.map((src, idx) => (
          <img key={idx} src={src} alt="" />
        ))}
      </div>

      <div className="center">
        <button className="btn">Show more</button>
      </div>
    </section>
  );
}