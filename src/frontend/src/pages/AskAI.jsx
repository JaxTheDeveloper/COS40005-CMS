import { useState } from "react";
import { askSuggestions } from "../data";

export default function AskAI() {
  const [q, setQ] = useState("");
  const [answers, setAnswers] = useState([]);

  const ask = () => {
    if (!q.trim()) return;
    // Fake answer (replace with API call if desired)
    setAnswers(a => [{ q, a: "Thanks! (This is a placeholder response.)" }, ...a]);
    setQ("");
  };

  return (
    <main className="page page--wide">
      <div className="askai">
        <div className="askai__bar">
          <input
            value={q}
            onChange={(e) => setQ(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && ask()}
            placeholder="Enter text here"
          />
          <button className="askai__go" onClick={ask}>▶</button>
        </div>

        <div className="askai__suggestions">
          <div className="muted">Suggestion</div>
          <ul>
            {askSuggestions.map((s, i) => <li key={i} onClick={()=>setQ(s)}>{s}</li>)}
          </ul>
        </div>

        {answers.length > 0 && (
          <div className="askai__answers">
            {answers.map((x, i) => (
              <div className="qa" key={i}>
                <div className="qa__q"><strong>Q:</strong> {x.q}</div>
                <div className="qa__a"><strong>A:</strong> {x.a}</div>
              </div>
            ))}
          </div>
        )}
      </div>
    </main>
  );
}
