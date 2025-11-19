import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { api } from '../services/api';

function parseNotes(notes) {
  const result = { major: null, category: null };
  if (!notes) return result;
  const parts = notes.split(';').map(p => p.trim());
  parts.forEach(p => {
    if (p.startsWith('Major:')) result.major = p.replace('Major:', '').trim();
    if (p.startsWith('Category:')) result.category = p.replace('Category:', '').trim();
  });
  return result;
}

export default function EnrollSelect() {
  const [offerings, setOfferings] = useState([]);
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [showDebug, setShowDebug] = useState(false);
  const [confirmOffering, setConfirmOffering] = useState(null);
  const [actionMessage, setActionMessage] = useState(null);
  const navigate = useNavigate();

  useEffect(() => {
    const load = async () => {
      try {
        const [uResp, offResp] = await Promise.all([
          api.get('/users/me/'),
          api.get('/api/academic/offerings/?page_size=1000'),
        ]);
        setUser(uResp.data);
        const offs = offResp.data.results || offResp.data || [];
        setOfferings(offs);
      } catch (err) {
        console.error(err);
        setError('Failed to load offerings or user');
      } finally {
        setLoading(false);
      }
    };
    load();
  }, []);

  const handleEnroll = (off) => {
    setConfirmOffering(off);
  };

  const doEnroll = async (offeringId) => {
    setActionMessage(null);
    try {
      await api.post('/api/enrollment/enrollments/', { offering: offeringId });
      setActionMessage({ type: 'success', text: 'Enrollment request submitted.' });
      setConfirmOffering(null);
      // navigate to calendar to show results
      navigate('/calendar');
    } catch (err) {
      console.error(err);
      const msg = err.response?.data || (err.message || 'Enrollment failed');
      setActionMessage({ type: 'error', text: JSON.stringify(msg) });
      setConfirmOffering(null);
    }
  };

  if (loading) return <div>Loading available units...</div>;
  if (error) return <div>{error}</div>;

  const studentMajor = user?.department || null;

  const grouped = { core: [], major: [], electives: [] };

  // mapping majors to unit code prefixes that should be considered core
  const majorPrefixMap = {
    'Computer Science': ['COS', 'SWE', 'TNE'],
    'Business': ['BUS', 'FIN', 'MKT', 'ACC', 'INB', 'MGT'],
    'Media & Communications': ['MDA', 'DCO', 'COM', 'PUB'],
  };

  const isCodeStartingWith1 = (code) => {
    return typeof code === 'string' && /^1\d{4}/.test(code);
  };

  offerings.forEach(off => {
    const notes = off.notes || '';
    const meta = parseNotes(notes);
    const unit = off.unit || {};
    const unitMajor = unit.department || meta.major || null;
    const category = meta.category || null;
  const code = unit.code || '';
  const numericMatch = (code.match(/\d+/) || [null])[0];
  const levelDigit = numericMatch ? numericMatch.charAt(0) : null;
  const isLevel2 = levelDigit === '2';
  const isLevel34 = levelDigit === '3' || levelDigit === '4';

    // If we don't know the student's major yet, treat everything as electives except explicit core
    if (!studentMajor) {
      if (category === 'core') grouped.core.push(off);
      else if (unitMajor) grouped.major.push(off);
      else grouped.electives.push(off);
      return;
    }
    // If a unit is level-2 (2xxxx) treat it as elective by default
    if (isLevel2) {
      grouped.electives.push(off);
      return;
    }
    // Only show core and major units that belong to the student's major
    const prefixes = majorPrefixMap[studentMajor] || [];
    let consideredCore = false;
    if (category === 'core') consideredCore = true;
    // For Computer Science, also treat codes starting with 1xxxx as core
    if (!consideredCore && studentMajor === 'Computer Science' && isCodeStartingWith1(code)) consideredCore = true;
    // treat code prefixes as core if they match the major
    if (!consideredCore && prefixes.length) {
      for (const p of prefixes) {
        if (code.startsWith(p)) {
          consideredCore = true;
          break;
        }
      }
    }

    if (consideredCore && unitMajor === studentMajor) {
      grouped.core.push(off);
      return;
    }

    // major column: unit's major must match student's major and be level-3/4 or match major prefixes
    if (unitMajor === studentMajor && (isLevel34 || prefixes.some(p => code.startsWith(p)))) {
      grouped.major.push(off);
      return;
    }

    // everything else is elective
    grouped.electives.push(off);
  });

  // Helper to extract unit level (first digit of numeric part)
  const getUnitLevel = (code) => {
    const match = (code || '').match(/(\d{5})/);
    if (match) return match[1][0];
    return null;
  };

  const renderList = (items) => (
    <ul>
      {items.map(it => {
        const code = it.unit?.code || '';
        const level = getUnitLevel(code);
        return (
          <li key={it.id} style={{ marginBottom: 8 }}>
            <strong>{code}</strong> — {it.unit?.name}
            {level && (
              <span style={{ marginLeft: 8, fontSize: 12, color: '#888', background: '#f3f3f3', borderRadius: 4, padding: '2px 6px' }}>Level {level}</span>
            )}
            <br />
            <small>{it.notes}</small><br />
            <button onClick={() => handleEnroll(it.id)}>Enroll</button>
          </li>
        );
      })}
    </ul>
  );

  return (
    <div style={{ position: 'relative' }}>
      <div style={{ display: 'flex', gap: 24 }}>
        <div style={{ flex: 1 }}>
          <h3>Core</h3>
          <div style={{ color: '#666', marginBottom: 8 }}>Core units for your major</div>
          {grouped.core.length ? renderList(grouped.core) : <div>No core units found.</div>}
        </div>
        <div style={{ flex: 1 }}>
          <h3>Major ({studentMajor || 'Unknown'})</h3>
          <div style={{ color: '#666', marginBottom: 8 }}>Major units for your program</div>
          {grouped.major.length ? renderList(grouped.major) : <div>No major units found.</div>}
        </div>
        <div style={{ flex: 1 }}>
          <h3>Electives</h3>
          <div style={{ color: '#666', marginBottom: 8 }}>Elective options</div>
          {grouped.electives.length ? renderList(grouped.electives) : <div>No electives found.</div>}
        </div>
      </div>

      <div style={{ position: 'absolute', right: 16, top: 84 }}>
        <button onClick={() => setShowDebug(d => !d)} style={{ marginBottom: 8 }}>{showDebug ? 'Hide debug' : 'Show debug'}</button>
        {showDebug && (
          <div style={{ padding: 8, background: '#fff', border: '1px solid #eee', borderRadius: 4, maxWidth: 360 }}>
            <strong>Debug: current user</strong>
            <pre style={{ fontSize: 11, maxHeight: 200, overflow: 'auto' }}>{JSON.stringify(user, null, 2)}</pre>
          </div>
        )}
      </div>

      {/* action message */}
      {actionMessage && (
        <div style={{ position: 'fixed', left: 20, bottom: 20, padding: 12, borderRadius: 6, background: actionMessage.type === 'success' ? '#e6ffed' : '#fff1f0', border: '1px solid #ccc' }}>
          <strong>{actionMessage.type === 'success' ? 'Success' : 'Error'}:</strong> {actionMessage.text}
        </div>
      )}

      {/* confirmation modal */}
      {confirmOffering && (
        <div style={{ position: 'fixed', left: 0, top: 0, right: 0, bottom: 0, background: 'rgba(0,0,0,0.4)', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
          <div style={{ background: '#fff', padding: 20, borderRadius: 6, width: 480 }}>
            <h4>Confirm enrollment</h4>
            <p><strong>{confirmOffering.unit?.code}</strong> — {confirmOffering.unit?.name}</p>
            <p style={{ color: '#666' }}>{confirmOffering.notes}</p>
            <div style={{ display: 'flex', gap: 8, justifyContent: 'flex-end', marginTop: 12 }}>
              <button onClick={() => setConfirmOffering(null)}>Cancel</button>
              <button onClick={() => doEnroll(confirmOffering.id)} style={{ background: '#1976d2', color: '#fff', border: 'none', padding: '6px 12px', borderRadius: 4 }}>Confirm Enroll</button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
