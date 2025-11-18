import React, { useEffect, useState } from 'react';
import { Box, Typography, Avatar, Button, TextField } from '@mui/material';
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

  if (loading) return <Box p={3}>Loading...</Box>;

  return (
    <Box sx={{ p: 3 }}>
      <Typography variant="h4" gutterBottom>Profile</Typography>
      <Box display="flex" alignItems="center" mb={3}>
        <Avatar src={user?.profile_image} alt={user?.email} sx={{ width: 72, height: 72, mr: 2 }} />
        <Box>
          <Typography variant="h6">{user?.first_name} {user?.last_name}</Typography>
          <Typography color="textSecondary">{user?.email}</Typography>
        </Box>
      </Box>

      {editing ? (
        <Box sx={{ maxWidth: 480 }}>
          <TextField fullWidth label="First name" name="first_name" value={form.first_name} onChange={handleChange} margin="normal" />
          <TextField fullWidth label="Last name" name="last_name" value={form.last_name} onChange={handleChange} margin="normal" />
          <Box mt={2}>
            <Button variant="contained" color="primary" onClick={handleSave} sx={{ mr: 1 }}>Save</Button>
            <Button variant="outlined" onClick={() => setEditing(false)}>Cancel</Button>
          </Box>
        </Box>
      ) : (
        <Box>
          <Button variant="contained" onClick={() => setEditing(true)}>Edit profile</Button>
        </Box>
      )}
    </Box>
  );
}
