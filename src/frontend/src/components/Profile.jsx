import React, { useEffect, useState } from 'react';
import { authService } from '../services/auth';

export default function Profile() {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);
  const [editing, setEditing] = useState(false);
  const [form, setForm] = useState({ first_name: '', last_name: '' });

  useEffect(() => {
    (async () => {
      try {
        const u = await authService.getCurrentUser();
        setUser(u);
        setForm({ first_name: u.first_name || '', last_name: u.last_name || '' });
      } catch (err) {
        console.error('Failed to load profile', err);
      } finally {
        setLoading(false);
      }
    })();
  }, []);

  const handleChange = (e) => setForm({ ...form, [e.target.name]: e.target.value });

  const handleSave = async () => {
    try {
      const updated = await authService.updateProfile(form);
      setUser(updated);
      setEditing(false);
    } catch (err) {
      console.error('Failed to update profile', err);
    }
  };

  if (loading) {
    return (
      <section className="stack">
        <p className="lead">Loading...</p>
      </section>
    );
  }

  return (
    <section className="stack">
      <div className="breadcrumb">Home / <strong>Profile</strong></div>
      <h1 className="page-h1">Profile</h1>

      <div className="profile-header">
        {user?.profile_image ? (
          <img className="profile-avatar" src={user.profile_image} alt={user?.email} />
        ) : (
          <div className="profile-avatar-placeholder">👤</div>
        )}
        <div className="profile-info">
          <div className="profile-name">{user?.first_name} {user?.last_name}</div>
          <div className="profile-email">{user?.email}</div>
        </div>
      </div>

      {editing ? (
        <div className="query-form" style={{ maxWidth: 480 }}>
          <div className="form-field">
            <label htmlFor="first_name">First name</label>
            <input
              type="text"
              id="first_name"
              name="first_name"
              value={form.first_name}
              onChange={handleChange}
            />
          </div>
          <div className="form-field">
            <label htmlFor="last_name">Last name</label>
            <input
              type="text"
              id="last_name"
              name="last_name"
              value={form.last_name}
              onChange={handleChange}
            />
          </div>
          <div style={{ display: 'flex', gap: '0.75rem', marginTop: '1rem' }}>
            <button className="btn btn-primary" onClick={handleSave}>Save</button>
            <button className="btn" onClick={() => setEditing(false)}>Cancel</button>
          </div>
        </div>
      ) : (
        <div>
          <button className="btn btn-primary" onClick={() => setEditing(true)}>Edit profile</button>
        </div>
      )}
    </section>
  );
}
