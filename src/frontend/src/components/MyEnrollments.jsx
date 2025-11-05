import React, { useState, useEffect } from 'react';
import { Box, Card, CardContent, Typography, Button, Chip, Grid } from '@mui/material';
import axios from 'axios';

const statusColors = {
  'PENDING': 'warning',
  'ENROLLED': 'success',
  'WITHDRAWN': 'error',
  'COMPLETED': 'info',
  'FAILED': 'error'
};

export default function MyEnrollments() {
  const [enrollments, setEnrollments] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    loadEnrollments();
  }, []);

  const loadEnrollments = async () => {
    try {
      const response = await axios.get('/api/enrollment/enrollments/');
      setEnrollments(response.data);
      setError(null);
    } catch (err) {
      setError('Failed to load enrollments');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const handleWithdraw = async (enrollmentId) => {
    try {
      await axios.post(`/api/enrollment/enrollments/${enrollmentId}/withdraw/`);
      loadEnrollments(); // Reload after withdrawal
    } catch (err) {
      setError('Failed to withdraw from unit');
      console.error(err);
    }
  };

  if (loading) return <Box>Loading...</Box>;
  if (error) return <Box color="error.main">{error}</Box>;

  return (
    <Box sx={{ p: 3 }}>
      <Typography variant="h4" gutterBottom>My Enrollments</Typography>
      <Grid container spacing={3}>
        {enrollments.map((enrollment) => (
          <Grid item xs={12} md={6} key={enrollment.id}>
            <Card>
              <CardContent>
                <Box display="flex" justifyContent="space-between" alignItems="center" mb={2}>
                  <Typography variant="h6">
                    {enrollment.offering.unit.code} - {enrollment.offering.unit.name}
                  </Typography>
                  <Chip 
                    label={enrollment.status}
                    color={statusColors[enrollment.status]}
                  />
                </Box>
                <Typography color="textSecondary" gutterBottom>
                  Semester {enrollment.offering.semester} {enrollment.offering.year}
                </Typography>
                {enrollment.grade && (
                  <Typography>
                    Grade: {enrollment.grade} ({enrollment.marks}%)
                  </Typography>
                )}
                {enrollment.status === 'ENROLLED' && (
                  <Box mt={2}>
                    <Button
                      variant="outlined"
                      color="error"
                      onClick={() => handleWithdraw(enrollment.id)}
                    >
                      Withdraw
                    </Button>
                  </Box>
                )}
              </CardContent>
            </Card>
          </Grid>
        ))}
      </Grid>
    </Box>
  );
}