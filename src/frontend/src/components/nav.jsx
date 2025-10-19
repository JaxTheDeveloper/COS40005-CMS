import { NavLink } from "react-router-dom";

export default function Nav() {
  return (
    <header className="hero">
      <div className="hero__overlay" />
      <div className="hero__content">
        <nav className="nav">
          <div className="nav__brand">SWINBURNE VN</div>
          <div className="nav__links">
            <NavLink to="/dashboard">Dashboard</NavLink>
            <NavLink to="/queries">Queries</NavLink>
            <NavLink to="/ask-ai">Ask AI</NavLink>
            <a href="#!" onClick={(e)=>e.preventDefault()}>Courses</a>
            <a href="#!" onClick={(e)=>e.preventDefault()}>Clubs</a>
            <a href="#!" onClick={(e)=>e.preventDefault()}>Lectures/Faculties</a>
            <NavLink to="/login" className="btn btn--ghost">Log in</NavLink>
          </div>
        </nav>
        <h1 className="hero__title">SWINBURNE VN</h1>
      </div>
    </header>
  );
}
