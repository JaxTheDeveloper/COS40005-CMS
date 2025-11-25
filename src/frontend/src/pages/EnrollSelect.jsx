import React, { useEffect, useMemo, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Box,
  Card,
  CardContent,
  Typography,
  Button,
  Chip,
  Grid,
  Tabs,
  Tab,
  Alert,
  CircularProgress,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
  LinearProgress,
  Stack,
} from '@mui/material';
import { api } from '../services/api';

const statusColors = {
  PENDING: 'warning',
  ENROLLED: 'success',
  WITHDRAWN: 'error',
  COMPLETED: 'info',
  FAILED: 'error',
};

const CARD_STATUS_META = {
  passed: { label: 'Passed', color: 'success', bg: '#E8F5E9', border: '#C8E6C9' },
  enrolled: { label: 'Enrolled', color: 'primary', bg: '#E3F2FD', border: '#BBDEFB' },
  selected: { label: 'Selected', color: 'warning', bg: '#FFF8E1', border: '#FFE082' },
  available: { label: 'Available', color: 'info', bg: '#E0F7FA', border: '#B2EBF2' },
  failed: { label: 'Failed', color: 'error', bg: '#FFEBEE', border: '#FFCDD2' },
  withdrawn: { label: 'Withdrawn', color: 'default', bg: '#F5F5F5', border: '#E0E0E0' },
};

const STATUS_FILTERS = [
  { value: 'all', label: 'All' },
  { value: 'available', label: 'Available' },
  { value: 'selected', label: 'Selected' },
  { value: 'enrolled', label: 'Enrolled' },
  { value: 'passed', label: 'Passed' },
  { value: 'failed', label: 'Failed' },
];

function TabPanel({ children, value, index }) {
  return (
    <div role="tabpanel" hidden={value !== index}>
      {value === index && <Box sx={{ p: 3 }}>{children}</Box>}
    </div>
  );
}

export default function EnrollSelect() {
  const [dashboardData, setDashboardData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [tabValue, setTabValue] = useState(0);
  const [statusFilter, setStatusFilter] = useState('all');
  const [confirmOffering, setConfirmOffering] = useState(null);
  const [actionMessage, setActionMessage] = useState(null);
  const navigate = useNavigate();

  // Hooks must be called before any conditional returns (React rules)
  const filteredCards = useMemo(() => {
    const offeringCards = dashboardData?.offering_cards || [];
    if (statusFilter === 'all') return offeringCards;
    return offeringCards.filter((card) => card.status_label === statusFilter);
  }, [dashboardData, statusFilter]);

  useEffect(() => {
    loadDashboard();
  }, []);

  const loadDashboard = async () => {
    try {
      setLoading(true);
      const response = await api.get('/enrollment/enrollments/dashboard/');
      setDashboardData(response.data);
      setError(null);
      } catch (err) {
        console.error(err);
      setError('Failed to load enrollment dashboard');
      } finally {
        setLoading(false);
      }
    };

  const handleEnroll = (offering) => {
    setConfirmOffering(offering);
  };

  const doEnroll = async (offeringId) => {
    setActionMessage(null);
    try {
  await api.post('/enrollment/enrollments/', { offering: offeringId });
      setActionMessage({ type: 'success', text: 'Enrollment request submitted successfully!' });
      setConfirmOffering(null);
      await loadDashboard();
      setTimeout(() => {
      navigate('/calendar');
      }, 1500);
    } catch (err) {
      console.error(err);
      const msg =
        err.response?.data?.detail ||
        err.response?.data?.error ||
        err.message ||
        'Enrollment failed';
      setActionMessage({ type: 'error', text: typeof msg === 'string' ? msg : JSON.stringify(msg) });
      setConfirmOffering(null);
    }
  };

  const handleTabChange = (event, newValue) => {
    setTabValue(newValue);
  };

  const handleStatusFilter = (value) => {
    setStatusFilter(value);
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
        <Alert severity="error">{error}</Alert>
      </Box>
    );
  }

  if (!dashboardData) {
    return (
      <Box p={3}>
        <Alert severity="info">No enrollment data available</Alert>
      </Box>
    );
  }

  const {
    past_enrollments,
    current_enrollments,
    statistics,
  } = dashboardData;

  const renderStatusFilters = () => (
    <Stack direction="row" spacing={1} flexWrap="wrap" sx={{ mb: 2 }}>
      {STATUS_FILTERS.map((filter) => {
        const isActive = statusFilter === filter.value;
        const meta = CARD_STATUS_META[filter.value] || {};
        return (
          <Chip
            key={filter.value}
            label={filter.label}
            color={isActive && meta.color ? meta.color : 'default'}
            variant={isActive ? 'filled' : 'outlined'}
            onClick={() => handleStatusFilter(filter.value)}
            sx={{ textTransform: 'capitalize' }}
          />
        );
      })}
    </Stack>
  );

  const renderOfferingCard = (card) => {
    const meta = CARD_STATUS_META[card.status_label] || CARD_STATUS_META.available;
    const attendance = card.attendance_summary || {};
    const attendanceRate = attendance.attendance_rate ?? null;
    const missingPrereqs = card.missing_prerequisites || [];
    const canEnroll = card.can_enroll;
    const offering = card.offering || {};
    const unit = offering.unit || {};

    return (
      <Grid item xs={12} md={6} lg={4} key={`${offering.id}-${card.status_label}`}>
        <Card
          sx={{
            height: '100%',
            borderLeft: `4px solid ${meta.border}`,
            backgroundColor: meta.bg,
          }}
        >
          <CardContent>
            <Box display="flex" justifyContent="space-between" alignItems="center" mb={1}>
              <Box>
                <Typography variant="h6">{unit.code}</Typography>
                <Typography variant="body2" color="textSecondary">
                  {unit.name}
                </Typography>
              </Box>
              <Chip label={meta.label} color={meta.color} size="small" />
            </Box>

            <Typography variant="body2" color="textSecondary">
              {offering.semester} {offering.year} • {unit.credit_points || 0} CP
            </Typography>
            <Typography variant="body2" sx={{ mt: 0.5 }}>
              {card.schedule_summary}
            </Typography>
            {card.instructor && (
              <Typography variant="body2" color="textSecondary">
                Instructor: {card.instructor.name}
              </Typography>
            )}

            {card.grade && (
              <Typography variant="body2" sx={{ mt: 1 }}>
                Grade: {card.grade} {card.marks ? `(${card.marks}%)` : ''}
              </Typography>
            )}

            {attendanceRate !== null && (
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
                  Present {attendance.present || 0} • Late {attendance.late || 0} • Absent{' '}
                  {attendance.absent || 0}
                </Typography>
              </Box>
            )}

            {card.status_label === 'available' && !card.prerequisites_met && missingPrereqs.length > 0 && (
              <Alert severity="warning" sx={{ mt: 2 }}>
                Missing prerequisites: {missingPrereqs.map((p) => p.code).join(', ')}
              </Alert>
            )}

            <Box sx={{ mt: 2, display: 'flex', gap: 1, flexWrap: 'wrap' }}>
              {card.status_label === 'available' && (
                <Button
                  variant="contained"
                  size="small"
                  onClick={() => handleEnroll(offering)}
                  disabled={!canEnroll}
                >
                  Enroll
                </Button>
              )}
              {card.status_label === 'selected' && (
                <Chip label="Pending approval" color="warning" size="small" />
              )}
              {card.status_label === 'enrolled' && (
                <Button variant="outlined" size="small" onClick={() => navigate('/calendar')}>
                  View schedule
                </Button>
              )}
              {card.status_label === 'passed' && (
                <Button variant="outlined" size="small" onClick={() => navigate('/profile')}>
                  View transcript
                </Button>
              )}
            </Box>
          </CardContent>
        </Card>
      </Grid>
    );
  };

  return (
    <Box sx={{ width: '100%', p: 3 }}>
      {/* Statistics Cards */}
      <Grid container spacing={2} sx={{ mb: 3 }}>
        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Typography color="textSecondary" gutterBottom>Completed Units</Typography>
              <Typography variant="h4">{statistics?.total_completed || 0}</Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Typography color="textSecondary" gutterBottom>Currently Enrolled</Typography>
              <Typography variant="h4">{statistics?.current_enrolled || 0}</Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Typography color="textSecondary" gutterBottom>Pending Approval</Typography>
              <Typography variant="h4">{statistics?.pending_approval || 0}</Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Typography color="textSecondary" gutterBottom>Available Units</Typography>
              <Typography variant="h4">{statistics?.available_count || 0}</Typography>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* Tabs */}
      <Card>
        <Box sx={{ borderBottom: 1, borderColor: 'divider' }}>
          <Tabs value={tabValue} onChange={handleTabChange}>
            <Tab label="Unit Planner" />
            <Tab label="Current Enrollments" />
            <Tab label="Past Enrollments" />
          </Tabs>
        </Box>

        {/* Unit Planner Tab */}
        <TabPanel value={tabValue} index={0}>
          {renderStatusFilters()}
          {filteredCards.length ? (
            <Grid container spacing={2}>
              {filteredCards.map((card) => renderOfferingCard(card))}
            </Grid>
          ) : (
            <Typography color="textSecondary">No units found for this filter.</Typography>
          )}
        </TabPanel>

        {/* Current Enrollments Tab */}
        <TabPanel value={tabValue} index={1}>
          {current_enrollments && current_enrollments.length > 0 ? (
            <TableContainer component={Paper}>
              <Table>
                <TableHead>
                  <TableRow>
                    <TableCell>Unit Code</TableCell>
                    <TableCell>Unit Name</TableCell>
                    <TableCell>Semester</TableCell>
                    <TableCell>Year</TableCell>
                    <TableCell>Status</TableCell>
                    <TableCell>Credit Points</TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {current_enrollments.map(enrollment => (
                    <TableRow key={enrollment.id}>
                      <TableCell>{enrollment.offering?.unit?.code}</TableCell>
                      <TableCell>{enrollment.offering?.unit?.name}</TableCell>
                      <TableCell>{enrollment.offering?.semester}</TableCell>
                      <TableCell>{enrollment.offering?.year}</TableCell>
                      <TableCell>
                        <Chip 
                          label={enrollment.status} 
                          color={statusColors[enrollment.status] || 'default'}
                          size="small"
                        />
                      </TableCell>
                      <TableCell>{enrollment.offering?.unit?.credit_points || 0}</TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </TableContainer>
          ) : (
            <Typography color="textSecondary">No current enrollments</Typography>
          )}
        </TabPanel>

        {/* Past Enrollments Tab */}
        <TabPanel value={tabValue} index={2}>
          {past_enrollments && past_enrollments.length > 0 ? (
            <TableContainer component={Paper}>
              <Table>
                <TableHead>
                  <TableRow>
                    <TableCell>Unit Code</TableCell>
                    <TableCell>Unit Name</TableCell>
                    <TableCell>Semester</TableCell>
                    <TableCell>Year</TableCell>
                    <TableCell>Status</TableCell>
                    <TableCell>Grade</TableCell>
                    <TableCell>Marks</TableCell>
                    <TableCell>Credit Points</TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {past_enrollments.map(enrollment => (
                    <TableRow key={enrollment.id}>
                      <TableCell>{enrollment.offering?.unit?.code}</TableCell>
                      <TableCell>{enrollment.offering?.unit?.name}</TableCell>
                      <TableCell>{enrollment.offering?.semester}</TableCell>
                      <TableCell>{enrollment.offering?.year}</TableCell>
                      <TableCell>
                        <Chip 
                          label={enrollment.status} 
                          color={statusColors[enrollment.status] || 'default'}
                          size="small"
                        />
                      </TableCell>
                      <TableCell>{enrollment.grade || '-'}</TableCell>
                      <TableCell>{enrollment.marks || '-'}</TableCell>
                      <TableCell>{enrollment.offering?.unit?.credit_points || 0}</TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </TableContainer>
          ) : (
            <Typography color="textSecondary">No past enrollments</Typography>
          )}
        </TabPanel>
      </Card>

      {/* Action Message */}
      {actionMessage && (
        <Alert 
          severity={actionMessage.type} 
          sx={{ position: 'fixed', bottom: 20, left: 20, right: 20, zIndex: 9999 }}
          onClose={() => setActionMessage(null)}
        >
          {actionMessage.text}
        </Alert>
      )}

      {/* Confirmation Dialog */}
      <Dialog open={!!confirmOffering} onClose={() => setConfirmOffering(null)}>
        <DialogTitle>Confirm Enrollment</DialogTitle>
        <DialogContent>
      {confirmOffering && (
            <>
              <Typography variant="h6">{confirmOffering.unit?.code}</Typography>
              <Typography variant="body2" color="textSecondary">
                {confirmOffering.unit?.name}
              </Typography>
              <Typography variant="body2" sx={{ mt: 2 }}>
                <strong>Semester:</strong> {confirmOffering.semester} {confirmOffering.year}
              </Typography>
              <Typography variant="body2">
                <strong>Credit Points:</strong> {confirmOffering.unit?.credit_points || 0}
              </Typography>
              {confirmOffering.notes && (
                <Typography variant="body2" sx={{ mt: 1 }}>
                  <strong>Notes:</strong> {confirmOffering.notes}
                </Typography>
              )}
              {!confirmOffering.prerequisites_met && confirmOffering.missing_prerequisites?.length > 0 && (
                <Alert severity="error" sx={{ mt: 2 }}>
                  Cannot enroll: Missing prerequisites: {confirmOffering.missing_prerequisites.map(p => p.code).join(', ')}
                </Alert>
              )}
            </>
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setConfirmOffering(null)}>Cancel</Button>
          <Button 
            onClick={() => doEnroll(confirmOffering?.id)} 
            variant="contained"
            disabled={!confirmOffering?.prerequisites_met}
          >
            Confirm Enrollment
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
}
