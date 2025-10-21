import React from "react";

export default function Queries() {
  return (
    <section className="stack">
      <h2 className="section-title">Queries</h2>

      <div className="rules">
        <ul>
          <li>Be Clear — Ask one question at a time and make it easy to understand.</li>
          <li>Be Polite — Use respectful language and tone.</li>
          <li>Stay on Topic — Keep your question related to the subject or discussion.</li>
          <li>Think First — Try to find the answer before asking, if possible.</li>
          <li>Be Specific — Give enough detail so others know exactly what you mean.</li>
        </ul>
      </div>

      <form className="query-form" onSubmit={(e) => e.preventDefault()}>
        <div className="grid-2">
          <div className="form-field">
            <label>Name</label>
            <input placeholder="Jon" />
          </div>
          <div className="form-field">
            <label>Email</label>
            <input type="email" placeholder="jon@swinburne.com" />
          </div>
        </div>

        <div className="grid-2">
          <div className="form-field">
            <label>Phone</label>
            <input placeholder="+84" />
          </div>
          <div className="form-field">
            <label>Title</label>
            <input placeholder="…" />
          </div>
        </div>

        <div className="form-field">
          <label>Description</label>
          <textarea rows={8} placeholder="Text" />
        </div>

        <div className="center">
          <button className="btn" type="submit">Send</button>
        </div>
      </form>
    </section>
  );
}