export default function Queries() {
  const onSubmit = (e) => {
    e.preventDefault();
    const form = new FormData(e.currentTarget);
    const payload = Object.fromEntries(form.entries());
    alert("Submitted!\n\n" + JSON.stringify(payload, null, 2));
  };

  return (
    <main className="page page--narrow">
      <div className="panel">
        <h3 className="panel__title">Queries</h3>
        <ul className="rules">
          <li>Be Clear — Ask one question at a time and make it easy to understand.</li>
          <li>Be Polite — Use respectful language and tone.</li>
          <li>Stay on Topic — Keep your question related to the subject or discussion.</li>
          <li>Think First — Try to find the answer before asking, if possible.</li>
          <li>Be Specific — Give enough detail so others know exactly what you mean.</li>
        </ul>
      </div>

      <form className="form" onSubmit={onSubmit}>
        <div className="grid grid--2">
          <label className="field">
            <span>Name</span>
            <input name="name" placeholder="Jan" required />
          </label>

          <label className="field">
            <span>Email</span>
            <input name="email" type="email" placeholder="you@email.com" required />
          </label>

          <label className="field">
            <span>Phone</span>
            <input name="phone" placeholder="+84" />
          </label>

          <span />{/* spacer */}
        </div>

        <label className="field">
          <span>Description</span>
          <textarea name="description" rows={8} placeholder="Text" required />
        </label>

        <div className="center">
          <button className="btn" type="submit">Send</button>
        </div>
      </form>
    </main>
  );
}
