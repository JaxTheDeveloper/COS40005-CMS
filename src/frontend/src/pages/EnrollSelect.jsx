import React, { useEffect, useMemo, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { api } from '../services/api';

const STATUS_BADGE = {
  passed: { label: 'Passed', cls: 'badge-success' },
  enrolled: { label: 'Enrolled', cls: 'badge-primary' },
  selected: { label: 'Selected', cls: 'badge-warning' },
  available: { label: 'Available', cls: 'badge-info' },
  failed: { label: 'Failed', cls: 'badge-error' },
  withdrawn: { label: 'Withdrawn', cls: 'badge-default' },
};

const ENROLLMENT_BADGE = {
  PENDING: 'badge-warning',
  ENROLLED: 'badge-success',
  WITHDRAWN: 'badge-error',
  COMPLETED: 'badge-info',
  FAILED: 'badge-error',
};

const STATUS_FILTERS = [
  { value: 'all', label: 'All' },
  { value: 'available', label: 'Available' },
  { value: 'selected', label: 'Selected' },
  { value: 'enrolled', label: 'Enrolled' },
  { value: 'passed', label: 'Passed' },
  { value: 'failed', label: 'Failed' },
];

export default function EnrollSelect() {
  const [dashboardData, setDashboardData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [tabValue, setTabValue] = useState(0);
  const [statusFilter, setStatusFilter] = useState('all');
  const [searchQuery, setSearchQuery] = useState('');
  const [confirmOffering, setConfirmOffering] = useState(null);
  const [actionMessage, setActionMessage] = useState(null);
  const navigate = useNavigate();

  const filteredCards = useMemo(() => {
    const offeringCards = dashboardData?.offering_cards || [];
    let cards = statusFilter === 'all' ? offeringCards : offeringCards.filter((card) => card.status_label === statusFilter);
    if (searchQuery.trim()) {
      const q = searchQuery.trim().toLowerCase();
      cards = cards.filter((card) => {
        const unit = card.offering?.unit || {};
        return (
          (unit.code || '').toLowerCase().includes(q) ||
          (unit.name || '').toLowerCase().includes(q)
        );
      });
    }
    return cards;
  }, [dashboardData, statusFilter, searchQuery]);

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

  if (loading) {
    return (
      <section className="stack">
        <p className="lead">Loading...</p>
      </section>
    );
  }

  if (error) {
    return (
      <section className="stack">
        <div className="alert alert-error">{error}</div>
      </section>
    );
  }

  if (!dashboardData) {
    return (
      <section className="stack">
        <div className="alert alert-info">No enrollment data available</div>
      </section>
    );
  }

  const { past_enrollments, current_enrollments, statistics } = dashboardData;

  const tabs = ['Unit Planner', 'Current Enrollments', 'Past Enrollments'];

  const renderOfferingCard = (card) => {
    const meta = STATUS_BADGE[card.status_label] || STATUS_BADGE.available;
    const attendance = card.attendance_summary || {};
    const attendanceRate = attendance.attendance_rate ?? null;
    const missingPrereqs = card.missing_prerequisites || [];
    const canEnroll = card.can_enroll;
    const offering = card.offering || {};
    const unit = offering.unit || {};

    return (
      <div className="unit-card" key={`${offering.id}-${card.status_label}`}>
        <div className="unit-card-header">
          <div>
            <div className="unit-code">{unit.code}</div>
            <div className="unit-name">{unit.name}</div>
          </div>
          <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'flex-end', gap: '0.25rem' }}>
            <span className={`badge ${meta.cls}`}>{meta.label}</span>
            {unit.is_elective && (
              <span className="badge badge-default" style={{ fontSize: '0.7rem', opacity: 0.85 }}>Elective</span>
            )}
          </div>
        </div>

        <div className="unit-detail">
          {offering.semester} {offering.year} • {unit.credit_points || 0} CP
        </div>
        {card.schedule_summary && (
          <div className="unit-detail">{card.schedule_summary}</div>
        )}
        {card.instructor && (
          <div className="unit-detail">Instructor: {card.instructor.name}</div>
        )}

        {card.grade && (
          <div className="unit-detail" style={{ fontWeight: 600 }}>
            Grade: {card.grade} {card.marks ? `(${card.marks}%)` : ''}
          </div>
        )}

        {attendanceRate !== null && (
          <div>
            <div className="unit-detail">Attendance {attendanceRate}%</div>
            <div className="progress-bar">
              <div
                className="progress-fill"
                style={{ width: `${Math.min(attendanceRate, 100)}%` }}
              />
            </div>
            <div className="unit-detail" style={{ fontSize: '0.75rem' }}>
              Present {attendance.present || 0} • Late {attendance.late || 0} • Absent{' '}
              {attendance.absent || 0}
            </div>
          </div>
        )}

        {card.status_label === 'available' && !card.prerequisites_met && missingPrereqs.length > 0 && (
          <div className="alert alert-warning" style={{ marginTop: '0.5rem' }}>
            Missing prerequisites: {missingPrereqs.map((p) => p.code).join(', ')}
          </div>
        )}

        <div className="unit-actions">
          {card.status_label === 'available' && (
            <button
              className="btn btn-primary"
              onClick={() => handleEnroll(offering)}
              disabled={!canEnroll}
            >
              Enroll
            </button>
          )}
          {card.status_label === 'selected' && (
            <span className="badge badge-warning">Pending approval</span>
          )}
          {card.status_label === 'enrolled' && (
            <button className="btn" onClick={() => navigate('/calendar')}>
              View schedule
            </button>
          )}
          {card.status_label === 'passed' && (
            <button className="btn" onClick={() => navigate('/profile')}>
              View transcript
            </button>
          )}
        </div>
      </div>
    );
  };

  const renderEnrollmentTable = (enrollments, showGrade = false) => {
    if (!enrollments || enrollments.length === 0) {
      return <p className="lead" style={{ fontSize: '0.9375rem' }}>No enrollments</p>;
    }

    return (
      <div className="table-wrapper">
        <table className="data-table">
          <thead>
            <tr>
              <th>Unit Code</th>
              <th>Unit Name</th>
              <th>Semester</th>
              <th>Year</th>
              <th>Status</th>
              {showGrade && <th>Grade</th>}
              {showGrade && <th>Marks</th>}
              <th>Credit Points</th>
            </tr>
          </thead>
          <tbody>
            {enrollments.map((enrollment) => (
              <tr key={enrollment.id}>
                <td>{enrollment.offering?.unit?.code}</td>
                <td>{enrollment.offering?.unit?.name}</td>
                <td>{enrollment.offering?.semester}</td>
                <td>{enrollment.offering?.year}</td>
                <td>
                  <span className={`badge ${ENROLLMENT_BADGE[enrollment.status] || 'badge-default'}`}>
                    {enrollment.status}
                  </span>
                </td>
                {showGrade && <td>{enrollment.grade || '-'}</td>}
                {showGrade && <td>{enrollment.marks || '-'}</td>}
                <td>{enrollment.offering?.unit?.credit_points || 0}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    );
  };

  return (
    <section className="stack">
      <div className="breadcrumb">Home / <strong>Enrolment</strong></div>
      <h1 className="page-h1">Enrolment</h1>

      {/* Statistics */}
      <div className="stat-grid">
        <div className="stat-card">
          <div className="stat-label">Completed Units</div>
          <div className="stat-value">{statistics?.total_completed || 0}</div>
        </div>
        <div className="stat-card">
          <div className="stat-label">Currently Enrolled</div>
          <div className="stat-value">{statistics?.current_enrolled || 0}</div>
        </div>
        <div className="stat-card">
          <div className="stat-label">Pending Approval</div>
          <div className="stat-value">{statistics?.pending_approval || 0}</div>
        </div>
        <div className="stat-card">
          <div className="stat-label">Available Units</div>
          <div className="stat-value">{statistics?.available_count || 0}</div>
        </div>
      </div>

      {/* Tabs */}
      <div>
        <div className="tab-bar">
          {tabs.map((label, i) => (
            <button
              key={label}
              className={`tab-btn ${tabValue === i ? 'active' : ''}`}
              onClick={() => setTabValue(i)}
            >
              {label}
            </button>
          ))}
        </div>

        {/* Unit Planner Tab */}
        {tabValue === 0 && (
          <div className="tab-panel">
            {/* Search bar */}
            <div style={{ marginBottom: '0.75rem' }}>
              <input
                type="search"
                className="search-input"
                placeholder="Search by unit code or name…"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                style={{
                  width: '100%',
                  padding: '0.5rem 0.75rem',
                  borderRadius: '6px',
                  border: '1px solid var(--border, #d1d5db)',
                  background: 'var(--surface, #fff)',
                  color: 'inherit',
                  fontSize: '0.9375rem',
                  outline: 'none',
                }}
              />
            </div>
            <div className="chip-row" style={{ marginBottom: '1rem' }}>
              {STATUS_FILTERS.map((filter) => (
                <button
                  key={filter.value}
                  className={`chip ${statusFilter === filter.value ? 'active' : ''}`}
                  onClick={() => setStatusFilter(filter.value)}
                >
                  {filter.label}
                </button>
              ))}
            </div>
            {filteredCards.length ? (
              <div className="card-grid">
                {filteredCards.map((card) => renderOfferingCard(card))}
              </div>
            ) : (
              <p className="lead" style={{ fontSize: '0.9375rem' }}>No units found for this filter.</p>
            )}
          </div>
        )}

        {/* Current Enrollments Tab */}
        {tabValue === 1 && (
          <div className="tab-panel">
            {renderEnrollmentTable(current_enrollments)}
          </div>
        )}

        {/* Past Enrollments Tab */}
        {tabValue === 2 && (
          <div className="tab-panel">
            {renderEnrollmentTable(past_enrollments, true)}
          </div>
        )}
      </div>

      {/* Action Message */}
      {actionMessage && (
        <div className={`alert alert-${actionMessage.type} alert-fixed`}>
          {actionMessage.text}
          <button className="close-btn" onClick={() => setActionMessage(null)}>✕</button>
        </div>
      )}

      {/* Confirmation Modal */}
      {confirmOffering && (
        <div className="modal-overlay" onClick={() => setConfirmOffering(null)}>
          <div className="modal" onClick={(e) => e.stopPropagation()}>
            <div className="modal-title">Confirm Enrollment</div>
            <div className="modal-body">
              <div className="unit-code">{confirmOffering.unit?.code}</div>
              <div className="unit-name">{confirmOffering.unit?.name}</div>
              <div className="unit-detail">
                <strong>Semester:</strong> {confirmOffering.semester} {confirmOffering.year}
              </div>
              <div className="unit-detail">
                <strong>Credit Points:</strong> {confirmOffering.unit?.credit_points || 0}
              </div>
              {confirmOffering.notes && (
                <div className="unit-detail">
                  <strong>Notes:</strong> {confirmOffering.notes}
                </div>
              )}
              {!confirmOffering.prerequisites_met && confirmOffering.missing_prerequisites?.length > 0 && (
                <div className="alert alert-error">
                  Cannot enroll: Missing prerequisites: {confirmOffering.missing_prerequisites.map(p => p.code).join(', ')}
                </div>
              )}
            </div>
            <div className="modal-actions">
              <button className="btn" onClick={() => setConfirmOffering(null)}>Cancel</button>
              <button
                className="btn btn-primary"
                onClick={() => doEnroll(confirmOffering?.id)}
                disabled={!confirmOffering?.prerequisites_met}
              >
                Confirm Enrollment
              </button>
            </div>
          </div>
        </div>
      )}
    </section>
  );
}
