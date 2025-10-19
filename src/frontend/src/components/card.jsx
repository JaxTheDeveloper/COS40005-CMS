export default function Card({ title, children, icon, footer, onClick }) {
  return (
    <div className="card" onClick={onClick}>
      <div className="card__head">
        {icon && <span className="card__icon">{icon}</span>}
        <h4>{title}</h4>
      </div>
      <div className="card__body">{children}</div>
      {footer && <div className="card__footer">{footer}</div>}
    </div>
  );
}
