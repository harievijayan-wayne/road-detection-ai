import React, { useEffect, useState } from 'react';
import { FileText, Download, Filter, Search, Calendar, MapPin, CheckCircle2, ShieldAlert } from 'lucide-react';
import PriorityBadge from '../components/PriorityBadge';
import { fetchInspections, generateReport } from '../services/api';

export default function ReportsPage() {
  const [inspections, setInspections] = useState([]);
  const [filterQuery, setFilterQuery] = useState('');
  const [loading, setLoading] = useState(true);
  const [generatingFmt, setGeneratingFmt] = useState(null);

  useEffect(() => {
    fetchInspections()
      .then(res => {
        setInspections(res);
        setLoading(false);
      })
      .catch(console.error);
  }, []);

  const handleDownload = async (insp, fmt) => {
    setGeneratingFmt(`${insp.id}-${fmt}`);
    try {
      const rep = await generateReport({
        inspection_id: insp.id,
        format: fmt,
        road_id: insp.road_name,
        title: `Pavement Structural Safety Audit - ${insp.road_name}`
      });
      window.open(`http://localhost:8000${rep.download_url}`, '_blank');
    } catch (err) {
      alert("Failed to export report: " + err.message);
    } finally {
      setGeneratingFmt(null);
    }
  };

  const filtered = inspections.filter(insp =>
    insp.road_name.toLowerCase().includes(filterQuery.toLowerCase()) ||
    insp.id.toLowerCase().includes(filterQuery.toLowerCase())
  );

  return (
    <div style={{ maxWidth: 1600, margin: '0 auto', padding: '24px 24px 60px' }}>
      {/* Header */}
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 24 }}>
        <div>
          <h1 style={{ fontSize: '1.6rem', color: '#f8fafc', marginBottom: 4 }}>
            Municipal Road Condition Reports & Compliance Exports
          </h1>
          <p style={{ color: '#94a3b8', fontSize: '0.88rem' }}>
            Download certified road condition audit documentation in PDF, CSV, and JSON formats
          </p>
        </div>

        {/* Search / Filter Bar */}
        <div style={{ display: 'flex', alignItems: 'center', gap: 10, background: 'rgba(15, 23, 42, 0.7)', padding: '8px 16px', borderRadius: 10, border: '1px solid var(--border-subtle)' }}>
          <Search size={16} color="#64748b" />
          <input
            type="text"
            placeholder="Filter by road name or survey ID..."
            value={filterQuery}
            onChange={e => setFilterQuery(e.target.value)}
            style={{ background: 'transparent', border: 'none', color: '#f8fafc', fontSize: '0.88rem', outline: 'none', width: 260 }}
          />
        </div>
      </div>

      {/* Reports Table Container */}
      <div className="glass-panel" style={{ padding: 24 }}>
        <div style={{ overflowX: 'auto' }}>
          <table style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'left', fontSize: '0.88rem' }}>
            <thead>
              <tr style={{ borderBottom: '1px solid var(--border-subtle)', color: 'var(--text-muted)' }}>
                <th style={{ padding: '12px 10px' }}>Survey Identifier</th>
                <th style={{ padding: '12px 10px' }}>Road Segment</th>
                <th style={{ padding: '12px 10px' }}>Survey Date</th>
                <th style={{ padding: '12px 10px' }}>Total Defects</th>
                <th style={{ padding: '12px 10px' }}>Potholes / Cracks</th>
                <th style={{ padding: '12px 10px' }}>Pavement RHI</th>
                <th style={{ padding: '12px 10px' }}>Action Priority</th>
                <th style={{ padding: '12px 10px', textAlign: 'right' }}>Export Format</th>
              </tr>
            </thead>
            <tbody>
              {filtered.map(insp => (
                <tr key={insp.id} style={{ borderBottom: '1px solid rgba(255,255,255,0.04)' }}>
                  <td style={{ padding: '14px 10px', fontFamily: 'var(--font-mono)', color: '#38bdf8', fontWeight: 600 }}>
                    {insp.id}
                  </td>
                  <td style={{ padding: '14px 10px', color: '#f8fafc', fontWeight: 600 }}>
                    {insp.road_name}
                  </td>
                  <td style={{ padding: '14px 10px', color: '#94a3b8', fontSize: '0.8rem' }}>
                    {new Date(insp.created_at).toLocaleDateString()}
                  </td>
                  <td style={{ padding: '14px 10px', color: '#f8fafc', fontWeight: 700 }}>
                    {insp.total_defects}
                  </td>
                  <td style={{ padding: '14px 10px', color: '#94a3b8' }}>
                    <span style={{ color: '#ef4444', fontWeight: 600 }}>{insp.pothole_count} Potholes</span>, {insp.crack_count} Cracks
                  </td>
                  <td style={{ padding: '14px 10px' }}>
                    <span style={{
                      fontWeight: 700,
                      color: insp.road_health_index > 75 ? '#10b981' : insp.road_health_index > 55 ? '#f59e0b' : '#ef4444'
                    }}>
                      {insp.road_health_index} / 100
                    </span>
                  </td>
                  <td style={{ padding: '14px 10px' }}>
                    <PriorityBadge priority={insp.priority_level} />
                  </td>
                  <td style={{ padding: '14px 10px', textAlign: 'right' }}>
                    <div style={{ display: 'inline-flex', gap: 6 }}>
                      <button
                        className="btn-primary"
                        style={{ padding: '6px 12px', fontSize: '0.78rem' }}
                        onClick={() => handleDownload(insp, 'PDF')}
                        disabled={generatingFmt === `${insp.id}-PDF`}
                      >
                        <Download size={13} /> {generatingFmt === `${insp.id}-PDF` ? "Building..." : "PDF"}
                      </button>
                      <button
                        className="btn-secondary"
                        style={{ padding: '6px 10px', fontSize: '0.78rem' }}
                        onClick={() => handleDownload(insp, 'CSV')}
                        disabled={generatingFmt === `${insp.id}-CSV`}
                      >
                        CSV
                      </button>
                      <button
                        className="btn-secondary"
                        style={{ padding: '6px 10px', fontSize: '0.78rem' }}
                        onClick={() => handleDownload(insp, 'JSON')}
                        disabled={generatingFmt === `${insp.id}-JSON`}
                      >
                        JSON
                      </button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
