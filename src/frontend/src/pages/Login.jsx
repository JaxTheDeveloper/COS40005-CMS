import React from 'react';
import { useNavigate } from 'react-router-dom';
import { useFormik } from 'formik';
import * as Yup from 'yup';
import { Box, Container, TextField, Button, Typography, Paper } from '@mui/material';
import { authService } from '../services/auth';

const validationSchema = Yup.object({
  email: Yup.string()
    .trim()
    .transform((value) => (value ? value.toLowerCase() : value))
    .email('Enter a valid email')
    .matches(/^[\w.%+-]+@swin\.edu\.au$/i, 'Please use your Swinburne email (@swin.edu.au)')
    .required('Email is required'),
  password: Yup.string()
    .min(8, 'Password should be of minimum 8 characters length')
    .required('Password is required'),
});

export default function Login({ onLogin }) {
  const navigate = useNavigate();

  const formik = useFormik({
    initialValues: {
      email: '',
      password: '',
    },
    validationSchema: validationSchema,
    onSubmit: async (values, { setSubmitting, setErrors }) => {
      try {
        const user = await authService.login(values.email, values.password);
        // Notify App.jsx that we have a logged-in user
        if (onLogin) onLogin(user);
        navigate('/dashboard/compsci');
      } catch (error) {
        setErrors({
          submit: error.response?.data?.detail || 'Login failed. Please try again.'
        });
      } finally {
        setSubmitting(false);
      }
    },
  });

  return (
    <Container component="main" maxWidth="xs">
      <Paper 
        elevation={3} 
        sx={{ 
          mt: 8, 
          p: 4, 
          display: 'flex', 
          flexDirection: 'column', 
          alignItems: 'center' 
        }}
      >
        <Typography component="h1" variant="h5">
          Sign in
        </Typography>
        <Box component="form" onSubmit={formik.handleSubmit} noValidate sx={{ mt: 1 }}>
          <TextField
            margin="normal"
            required
            fullWidth
            id="email"
            label="Email Address"
            name="email"
            autoComplete="email"
            autoFocus
            value={formik.values.email}
            onChange={formik.handleChange}
            onBlur={formik.handleBlur}
            error={(formik.touched.email || formik.submitCount > 0) && Boolean(formik.errors.email)}
            helperText={(formik.touched.email || formik.submitCount > 0) && formik.errors.email}
          />
          <TextField
            margin="normal"
            required
            fullWidth
            name="password"
            label="Password"
            type="password"
            id="password"
            autoComplete="current-password"
            value={formik.values.password}
            onChange={formik.handleChange}
            onBlur={formik.handleBlur}
            error={(formik.touched.password || formik.submitCount > 0) && Boolean(formik.errors.password)}
            helperText={(formik.touched.password || formik.submitCount > 0) && formik.errors.password}
          />
          {formik.errors.submit && (
            <Typography color="error" variant="body2" sx={{ mt: 2 }}>
              {formik.errors.submit}
            </Typography>
          )}
          <Button
            type="submit"
            fullWidth
            variant="contained"
            sx={{ mt: 3, mb: 2 }}
            disabled={formik.isSubmitting}
          >
            Sign In
          </Button>
        </Box>
      </Paper>
    </Container>
  );
}
