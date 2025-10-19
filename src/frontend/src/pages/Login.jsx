import { useState } from "react";
import { useNavigate } from "react-router-dom";

export default function Login() {
  const [showPwd, setShowPwd] = useState(false);
  const navigate = useNavigate();

  const onSubmit = (e) => {
    e.preventDefault();
    // simple demo: pretend login succeeded
    navigate("/dashboard");
  };

  return (
    <main className="page page--center">
      <form className="login" onSubmit={onSubmit}>
        <h2 className="login__title">Welcome back</h2>
        <p className="muted">Sign in to continue to Swinburne VN</p>

        <label className="field">
          <span>Email</span>
          <input name="email" type="email" placeholder="you@email.com" required />
        </label>

        <label className="field">
          <span>Password</span>
          <div className="password">
            <input name="password" type={showPwd ? "text":"password"} placeholder="••••••••" required />
            <button type="button" className="password__toggle" onClick={()=>setShowPwd(s=>!s)}>
              {showPwd ? "Hide" : "Show"}
            </button>
          </div>
        </label>

        <div className="login__row">
          <label className="checkbox">
            <input type="checkbox" /> Remember me
          </label>
          <a href="#!" onClick={(e)=>e.preventDefault()} className="muted">Forgot password?</a>
        </div>

        <button className="btn btn--full" type="submit">Log in</button>

        <div className="login__meta">
          <span className="muted">Don’t have an account?</span>{" "}
          <a href="#!" onClick={(e)=>e.preventDefault()}>Create one</a>
        </div>
      </form>
    </main>
  );
}
