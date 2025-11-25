import React, { useEffect, useState } from 'react';
import {
  Box,
  Card,
  CardContent,
  Typography,
  Grid,
  Alert,
  CircularProgress,
  Chip,
  LinearProgress,
  Stack,
} from '@mui/material';
import { api } from '../services/api';

const statusColorMap = {
  PENDING: 'warning',
  ENROLLED: 'success',
  WITHDRAWN: 'default',
  COMPLETED: 'info',
  FAILED: 'error',
};

export default function TeachingDashboard() {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    const load = async () => {
      try {
        setLoading(true);
        const response = await api.get('/enrollment/enrollments/teaching/');
        setData(response.data);
        setError(null);
      } catch (err) {
        console.error(err);
        if (err.response?.status === 403) {
          setError('You do not have access to the teaching dashboard.');
        } else {
          setError('Failed to load teaching dashboard.');
        }
      } finally {
        setLoading(false);
      }
    };
    load();
  }, []);

  const formatUpcoming = (session) => {
    if (!session) return 'No upcoming session scheduled';
    const date = new Date(session.date);
    const options = { weekday: 'short', month: 'short', day: 'numeric' };
    return `${date.toLocaleDateString(undefined, options)} • ${session.start_time?.slice(0, 5) ?? '??'} @ ${session.location || 'TBA'}`;
  };

  if (loading) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" minHeight="400px">
        <CircularProgress />
      </Box>
    );
  }

  if (error) {
    return (
      <Box p={3}>
        <Alert severity="warning">{error}</Alert>
      </Box>
    );
  }

  if (!data) {
    return null;
  }

  const summary = data.summary || {};
  const classes = data.classes || [];

  return (
    <Box sx={{ width: '100%', p: 3 }}>
      <Typography variant="h5" gutterBottom>
        Teaching Overview
      </Typography>

      <Grid container spacing={2} sx={{ mb: 3 }}>
        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Typography color="textSecondary">Active Classes</Typography>
              <Typography variant="h4">{summary.total_classes ?? 0}</Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Typography color="textSecondary">Students</Typography>
              <Typography variant="h4">{summary.total_students ?? 0}</Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Typography color="textSecondary">Pending Approvals</Typography>
              <Typography variant="h4">{summary.pending_approvals ?? 0}</Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Typography color="textSecondary">Avg Attendance</Typography>
              <Typography variant="h4">
                {summary.average_attendance != null ? `${summary.average_attendance}%` : '—'}
              </Typography>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {classes.length === 0 ? (
        <Alert severity="info">No teaching assignments found.</Alert>
      ) : (
        <Grid container spacing={2}>
          {classes.map((cls) => {
            const unit = cls.offering?.unit || {};
            const attendanceRate = cls.attendance?.attendance_rate;
            return (
              <Grid item xs={12} md={6} key={`${cls.offering?.id}`}>
                <Card>
                  <CardContent>
                    <Typography variant="h6">{unit.code}</Typography>
                    <Typography variant="subtitle2" color="textSecondary">
                      {unit.name}
                    </Typography>
                    <Typography variant="body2" color="textSecondary" sx={{ mt: 0.5 }}>
                      {cls.offering?.semester} {cls.offering?.year} • {unit.credit_points || 0} CP
                    </Typography>
                    <Typography variant="body2" sx={{ mt: 1 }}>
                      {formatUpcoming(cls.upcoming_session)}
                    </Typography>

                    <Stack direction="row" spacing={1} sx={{ mt: 2 }} flexWrap="wrap">
                      {Object.entries(cls.status_breakdown || {}).map(([status, count]) => (
                        <Chip
                          key={status}
                          label={`${status}: ${count}`}
                          color={statusColorMap[status] || 'default'}
                          size="small"
                        />
                      ))}
                    </Stack>

                    {attendanceRate != null && (
                      <Box sx={{ mt: 2 }}>
                        <Typography variant="caption" color="textSecondary">
                          Attendance {attendanceRate}%
                        </Typography>
                        <LinearProgress
                          variant="determinate"
                          value={Math.min(attendanceRate, 100)}
                          sx={{ height: 6, borderRadius: 3, mt: 0.5 }}
                        />
                        <Typography variant="caption" color="textSecondary">
                          Present {cls.attendance.present || 0} • Late {cls.attendance.late || 0} • Absent{' '}
                          {cls.attendance.absent || 0}
                        </Typography>
                      </Box>
                    )}
                  </CardContent>
                </Card>
              </Grid>
            );
          })}
        </Grid>
      )}
    </Box>
  );
}

