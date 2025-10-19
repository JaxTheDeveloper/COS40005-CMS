import Card from "/components/Card";
import { shortCards, news, gallery } from "../data";

export default function Dashboard() {
  return (
    <main className="page">
      <section className="intro">
        <div className="intro__left">
          <h2>Bachelor of Computer Science</h2>
          <p>
            Crack the code for a rewarding career at the heart of the digital revolution.
            With a robust theoretical core, this course trains you to become the best
            computer mind in the room. Majors in AI, Cybersecurity & Networks, Games
            Development, Data Science, Software Engineering and the Internet of Things.
          </p>
          <button className="btn">Add Major</button>
        </div>

        <div className="intro__right">
          <div className="grid grid--2">
            {shortCards.map((c) => (
              <Card key={c.title} title={c.title} icon={c.icon}>
                <p className="muted">{c.text}</p>
              </Card>
            ))}
          </div>
        </div>
      </section>

      <section className="two-col">
        <div className="news">
          {news.map((n) => (
            <article key={n.id} className="news__row">
              <img src={n.img} alt="" />
              <div className="news__meta">
                <h4>{n.title}</h4>
                <p className="muted">{n.tag}</p>
              </div>
              <div className="news__date">{n.date}</div>
              <button className="news__arrow" aria-label="open">→</button>
            </article>
          ))}
        </div>

        <div className="events">
          {news.map((n) => (
            <div className="event" key={`ev-${n.id}`}>
              <div className="event__badge">🛡️</div>
              <div className="event__body">
                <h4>{n.title}</h4>
                <p className="muted">{n.date}</p>
              </div>
              <button className="news__arrow" aria-label="open">→</button>
            </div>
          ))}
        </div>
      </section>

      <section className="gallery">
        <div className="gallery__head">
          <h3>Gallery</h3>
          <button className="btn btn--ghost">Show more</button>
        </div>
        <div className="grid grid--3">
          {gallery.map((src, i) => (
            <img className="gallery__img" src={src} key={i} alt={`Gallery ${i+1}`} />
          ))}
        </div>
      </section>
    </main>
  );
}
