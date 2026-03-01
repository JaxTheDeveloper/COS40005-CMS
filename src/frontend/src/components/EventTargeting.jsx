import React, { useEffect, useState } from 'react';
import { api } from '../services/api';

/**
 * EventTargeting component allows staff to granularly select who receives an event:
 * - All students
 * - Specific students
 * - Class/offering
 * - Intake (cohort)
 */
export default function EventTargeting({ eventId, onSave }) {
  const [event, setEvent] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  // Targeting controls
  const [targetAllStudents, setTargetAllStudents] = useState(false);
  const [targetStudents, setTargetStudents] = useState([]);
  const [targetOfferings, setTargetOfferings] = useState([]);
  const [targetIntakes, setTargetIntakes] = useState([]);

  const [availableStudents, setAvailableStudents] = useState([]);
  const [availableOfferings, setAvailableOfferings] = useState([]);
  const [availableIntakes, setAvailableIntakes] = useState([]);

  // Load event and dropdowns on mount
  useEffect(() => {
    (async () => {
      try {
        setLoading(true);
        // Load event details
        const eventResp = await api.get(`/api/core/events/${eventId}/`);
        setEvent(eventResp.data);
        setTargetAllStudents(eventResp.data.target_all_students || false);
        setTargetStudents(eventResp.data.target_students || []);
        setTargetOfferings(eventResp.data.target_offerings || []);
        setTargetIntakes(eventResp.data.target_intakes || []);

        // Load available options
        const studentsResp = await api.get('/api/users/?user_type=student');
        setAvailableStudents(studentsResp.data.results || studentsResp.data);

        const offeringsResp = await api.get('/api/academic/semester-offerings/');
        setAvailableOfferings(offeringsResp.data.results || offeringsResp.data);

        const intakesResp = await api.get('/api/academic/intakes/');
        setAvailableIntakes(intakesResp.data.results || intakesResp.data);
      } catch (err) {
        console.error('Failed to load targeting data', err);
        setError('Failed to load targeting options');
      } finally {
        setLoading(false);
      }
    })();
  }, [eventId]);

  const handleSave = async () => {
    try {
      const payload = {
        target_all_students: targetAllStudents,
        target_students: targetStudents,
        target_offerings: targetOfferings,
        target_intakes: targetIntakes,
      };
      const resp = await api.patch(`/api/core/events/${eventId}/`, payload);
      setEvent(resp.data);
      if (onSave) onSave(resp.data);
    } catch (err) {
      console.error('Failed to save targeting', err);
      setError('Failed to save. Check console for details.');
    }
  };

  if (loading) return <div className="alert alert-info">Loading targeting options...</div>;
  if (error) return <div className="alert alert-error">{error}</div>;
  if (!event) return <div className="alert alert-error">Event not found</div>;

  return (
    <div className="card stack">
      <h2>Event Targeting: {event.title}</h2>

      <div className="form-group">
        <label>
          <input
            type="checkbox"
            checked={targetAllStudents}
            onChange={(e) => setTargetAllStudents(e.target.checked)}
          />
          Send to all students
        </label>
        <p className="form-help">If checked, targets all active students regardless of other selections.</p>
      </div>

      {!targetAllStudents && (
        <>
          <fieldset>
            <legend>Or select specific targets:</legend>

            {/* Specific students */}
            <div className="form-group">
              <label htmlFor="target-students">Specific Students</label>
              <select
                id="target-students"
                multiple
                value={targetStudents}
                onChange={(e) => setTargetStudents(Array.from(e.target.selectedOptions, opt => parseInt(opt.value)))}
                style={{ height: '150px' }}
              >
                {availableStudents.map(student => (
                  <option key={student.id} value={student.id}>
                    {student.email} ({student.first_name} {student.last_name})
                  </option>
                ))}
              </select>
              <p className="form-help">Hold Ctrl/Cmd to select multiple. Leave empty to skip this filter.</p>
            </div>

            {/* Class offerings */}
            <div className="form-group">
              <label htmlFor="target-offerings">Class/Offering</label>
              <select
                id="target-offerings"
                multiple
                value={targetOfferings}
                onChange={(e) => setTargetOfferings(Array.from(e.target.selectedOptions, opt => parseInt(opt.value)))}
                style={{ height: '150px' }}
              >
                {availableOfferings.map(offering => (
                  <option key={offering.id} value={offering.id}>
                    {offering.unit__code || offering.unit_code} - {offering.semester} {offering.year}
                  </option>
                ))}
              </select>
              <p className="form-help">Selects all enrolled students in chosen offerings.</p>
            </div>

            {/* Intakes (cohorts) */}
            <div className="form-group">
              <label htmlFor="target-intakes">Intake (Cohort)</label>
              <select
                id="target-intakes"
                multiple
                value={targetIntakes}
                onChange={(e) => setTargetIntakes(Array.from(e.target.selectedOptions, opt => parseInt(opt.value)))}
                style={{ height: '100px' }}
              >
                {availableIntakes.map(intake => (
                  <option key={intake.id} value={intake.id}>
                    {intake.semester} {intake.year}
                  </option>
                ))}
              </select>
              <p className="form-help">Selects all students in chosen intake(s), e.g. SPRING 2025.</p>
            </div>
          </fieldset>
        </>
      )}

      <div className="form-actions">
        <button className="btn btn-primary" onClick={handleSave}>
          Save Targeting
        </button>
      </div>

      {/* Preview of targeted students */}
      <details>
        <summary>Preview Targeted Students</summary>
        <div style={{ marginTop: '1rem', padding: '1rem', backgroundColor: '#f5f5f5', borderRadius: '4px' }}>
          <p>Loading preview...</p>
        </div>
      </details>
    </div>
  );
}
