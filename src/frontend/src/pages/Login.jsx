import React from 'react';
import { useNavigate } from 'react-router-dom';
import { useFormik } from 'formik';
import * as Yup from 'yup';
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
    <div className="login-wrapper">
      <div className="login-card">
        <h1>Sign in</h1>
        <form onSubmit={formik.handleSubmit} noValidate>
          <div className="form-field">
            <label htmlFor="email">Email Address *</label>
            <input
              type="email"
              id="email"
              name="email"
              autoComplete="email"
              autoFocus
              placeholder="you@swin.edu.au"
              value={formik.values.email}
              onChange={formik.handleChange}
              onBlur={formik.handleBlur}
              style={(formik.touched.email || formik.submitCount > 0) && formik.errors.email ? { borderColor: '#c62828' } : {}}
            />
            {(formik.touched.email || formik.submitCount > 0) && formik.errors.email && (
              <span className="form-error">{formik.errors.email}</span>
            )}
          </div>
          <div className="form-field">
            <label htmlFor="password">Password *</label>
            <input
              type="password"
              id="password"
              name="password"
              autoComplete="current-password"
              placeholder="••••••••"
              value={formik.values.password}
              onChange={formik.handleChange}
              onBlur={formik.handleBlur}
              style={(formik.touched.password || formik.submitCount > 0) && formik.errors.password ? { borderColor: '#c62828' } : {}}
            />
            {(formik.touched.password || formik.submitCount > 0) && formik.errors.password && (
              <span className="form-error">{formik.errors.password}</span>
            )}
          </div>
          {formik.errors.submit && (
            <div className="alert alert-error" style={{ marginTop: '1rem' }}>
              {formik.errors.submit}
            </div>
          )}
          <div className="form-actions">
            <button
              type="submit"
              className="btn btn-primary"
              disabled={formik.isSubmitting}
              style={{ width: '100%' }}
            >
              {formik.isSubmitting ? 'Signing in…' : 'Sign In'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
