import React, { useState } from "react";

export default function Login() {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");

  const handleSubmit = (e) => {
    e.preventDefault();
    alert(`Logged in as ${email}`);
    // you could navigate or call API here
  };

  return (
    <section className="stack center" style={{ maxWidth: 400, margin: "60px auto" }}>
      <h2 className="section-title">Login</h2>

      <form className="query-form" onSubmit={handleSubmit}>
        <div className="form-field">
          <label>Email</label>
          <input
            type="email"
            required
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            placeholder="you@example.com"
          />
        </div>

        <div className="form-field">
          <label>Password</label>
          <input
            type="password"
            required
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            placeholder="••••••••"
          />
        </div>

        <div className="center">
          <button className="btn btn-primary" type="submit">
            Log In
          </button>
        </div>
      </form>
    </section>
  );
}
