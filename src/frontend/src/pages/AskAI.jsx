import React, { useState } from "react";

const SUGGESTIONS = [
  "How do I write a strong introduction for my essay?",
  "What’s a good way to manage my time for homework?",
  "What are the major differences between democracy and monarchy?",
  "Why are we still here?",
  "What’s the best way to handle group projects?",
  "How to not piss off my team leader",
  "Why are these questions the suggestion for students to ask AI?",
];

export default function AskAI() {
  const [query, setQuery] = useState("");
  const handleSend = (e) => {
    e.preventDefault();
    if (!query.trim()) return;
    console.log("AskAI prompt:", query);
  };
  return (
    <section className="askai-wrapper">
      <h2 className="askai-title">Ask AI</h2>
      <div className="askai-box">
        <div className="askai-input-row">
          <input
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Enter text here"
            className="askai-input"
          />
          <button
            className="askai-send"
            aria-label="Send"
            onClick={handleSend}
            disabled={!query.trim()}
            title={!query.trim() ? "Enter a prompt" : "Send"}
          >
            ➤
          </button>
        </div>

        <div className="askai-suggest-title">Suggestion</div>
        <ul className="askai-suggest-list">
          {SUGGESTIONS.map((s, idx) => (
            <li
              key={idx}
              className="askai-suggest-item"
              onClick={() => setQuery(s)}
            >
              {s}
            </li>
          ))}
        </ul>
      </div>
    </section>
  );
}