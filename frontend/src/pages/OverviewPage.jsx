import React, { useEffect, useState } from 'react';
import { Activity, AlertTriangle, ShieldAlert, Cpu, CheckCircle2, TrendingUp, ArrowUpRight, FileSpreadsheet } from 'lucide-react';
import MetricCard from '../components/MetricCard';
import SeverityBadge from '../components/SeverityBadge';
import PriorityBadge from '../components/PriorityBadge';
import DamageModal from '../components/DamageModal';
import { fetchOverviewAnalytics, fetchInspections, fetchDamages, getMediaUrl } from '../services/api';
import { ResponsiveContainer, BarChart, Bar, XAxis, YAxis, Tooltip, PieChart, Pie, Cell } from 'recharts';

export default function OverviewPage({ onNavigate }) {
  const [data, setData] = useState(null);
  const [inspections, setInspections] = useState([]);
  const [recentDamages, setRecentDamages] = useState([]);
  const [selectedDamage, setSelectedDamage] = useState(null);
  const [loading, setLoading] = useState(true);

  const loadData = async () => {
    try {
      const [analyticsRes, inspRes, damagesRes] = await Promise.all([
        fetchOverviewAnalytics(),
        fetchInspections(),
        fetchDamages({ limit: 8 })
      ]);
      setData(analyticsRes);
      setInspections(inspRes);
      setRecentDamages(damagesRes);
    } catch (err) {
      console.error("Overview load error:", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  if (loading) {
    return (
      <div style={{ padding: 40, textAlign: 'center', color: '#94a3b8' }}>
        <Activity className="animate-spin" size={32} style={{ margin: '0 auto 12px', color: '#38bdf8' }} />
        <p>Loading Infrastructure Telemetry...</p>
      </div>
    );
  }

  const kpis = data?.kpis || {};
  const damageDist = data?.damage_distribution || [];
  const priorityDist = data?.priority_distribution || [];

  const PIE_COLORS = ['#38bdf8', '#818cf8', '#f59e0b', '#ef4444', '#10b981', '#ec4899', '#06b6d4'];

  return (
    <div style={{ maxWidth: 1600, margin: '0 auto', padding: '24px 24px 60px' }}>
      {/* Top Banner / Headline */}
      <div style={{
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        marginBottom: 24,
        background: 'linear-gradient(135deg, rgba(15, 23, 42, 0.9), rgba(30, 41, 59, 0.7))',
        padding: '20px 28px',
        borderRadius: 16,
        border: '1px solid var(--border-subtle)'
      }}>
        <div>
          <h1 style={{ fontSize: '1.6rem', color: '#f8fafc', marginBottom: 4 }}>
            Municipal Road Network Health Monitor
          </h1>
          <p style={{ color: '#94a3b8', fontSize: '0.88rem' }}>
            Autonomous road surface damage segmentation, severity modeling & GIS maintenance scheduling
          </p>
        </div>
        <div style={{ display: 'flex', gap: 12 }}>
          <button className="btn-primary" onClick={() => onNavigate('upload')}>
            <ArrowUpRight size={16} /> Run New Survey
          </button>
          <button className="btn-secondary" onClick={() => onNavigate('map')}>
            View GIS Map
          </button>
        </div>
      </div>

      {/* Top KPI Cards (8 Key Metrics) */}
      <div style={{
        display: 'grid',
        gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))',
        gap: 16,
        marginBottom: 24
      }}>
        <MetricCard
          title="Total Inspections"
          value={kpis.total_inspections}
          subtitle="Surveys completed"
          icon={Activity}
          color="#38bdf8"
        />
        <MetricCard
          title="Detected Defects"
          value={kpis.total_detected_damages}
          subtitle="Physical damages"
          icon={AlertTriangle}
          color="#f59e0b"
        />
        <MetricCard
          title="Critical Hazards"
          value={kpis.critical_damages}
          subtitle="Immediate impact"
          icon={ShieldAlert}
          color="#ef4444"
          trend="Action Required"
        />
        <MetricCard
          title="High Priority"
          value={kpis.high_priority_damages}
          subtitle="SLA: <= 7 days"
          icon={TrendingUp}
          color="#f97316"
        />
        <MetricCard
          title="Average Severity"
          value={kpis.average_severity}
          unit="/100"
          subtitle="Weighted pavement index"
          icon={Activity}
          color="#818cf8"
        />
        <MetricCard
          title="Model Confidence"
          value={`${kpis.model_confidence}%`}
          subtitle="YOLO11 Segmenter"
          icon={CheckCircle2}
          color="#10b981"
        />
        <MetricCard
          title="Processing FPS"
          value={kpis.realtime_fps}
          unit="fps"
          subtitle="Edge realtime speed"
          icon={Cpu}
          color="#06b6d4"
        />
        <MetricCard
          title="Inference Latency"
          value={kpis.inference_latency_ms}
          unit="ms"
          subtitle="End-to-end pipeline"
          icon={Cpu}
          color="#ec4899"
        />
      </div>

      {/* Interactive Charts Section */}
      <div style={{
        display: 'grid',
        gridTemplateColumns: '1.4fr 1fr',
        gap: 20,
        marginBottom: 24
      }}>
        {/* Defect Class Breakdown Bar Chart */}
        <div className="glass-panel" style={{ padding: 24 }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16 }}>
            <h3 style={{ fontSize: '1.05rem', color: '#f8fafc' }}>
              Detected Defects by Classification
            </h3>
            <span style={{ fontSize: '0.78rem', color: '#94a3b8' }}>10 Core Classes</span>
          </div>

          <div style={{ height: 260 }}>
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={damageDist} margin={{ top: 10, right: 10, left: -20, bottom: 20 }}>
                <XAxis dataKey="name" stroke="#64748b" fontSize={11} angle={-25} textAnchor="end" />
                <YAxis stroke="#64748b" fontSize={11} />
                <Tooltip
                  contentStyle={{ background: '#0f172a', border: '1px solid rgba(255,255,255,0.1)', borderRadius: 8 }}
                  itemStyle={{ color: '#38bdf8' }}
                />
                <Bar dataKey="value" fill="#38bdf8" radius={[6, 6, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Maintenance Priority Distribution Pie Chart */}
        <div className="glass-panel" style={{ padding: 24 }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16 }}>
            <h3 style={{ fontSize: '1.05rem', color: '#f8fafc' }}>
              Maintenance Dispatch Priority
            </h3>
            <span style={{ fontSize: '0.78rem', color: '#94a3b8' }}>SLA Allocation</span>
          </div>

          <div style={{ height: 260, display: 'flex', alignItems: 'center' }}>
            <ResponsiveContainer width="100%" height="100%">
              <PieChart>
                <Pie
                  data={priorityDist}
                  dataKey="value"
                  nameKey="name"
                  cx="50%"
                  cy="50%"
                  innerRadius={55}
                  outerRadius={85}
                  paddingAngle={4}
                  label={({ name, percent }) => `${name.split(' ')[0]} ${(percent * 100).toFixed(0)}%`}
                >
                  {priorityDist.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={PIE_COLORS[index % PIE_COLORS.length]} />
                  ))}
                </Pie>
                <Tooltip contentStyle={{ background: '#0f172a', border: '1px solid rgba(255,255,255,0.1)', borderRadius: 8 }} />
              </PieChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>

      {/* Lower Section: Recent Inspections & Active Damaged Spots */}
      <div style={{ display: 'grid', gridTemplateColumns: '1.3fr 1fr', gap: 20 }}>
        {/* Recent Road Surveys Table */}
        <div className="glass-panel" style={{ padding: 24 }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16 }}>
            <h3 style={{ fontSize: '1.05rem', color: '#f8fafc' }}>
              Recent Infrastructure Surveys
            </h3>
            <button className="btn-secondary" style={{ padding: '4px 10px', fontSize: '0.78rem' }} onClick={() => onNavigate('reports')}>
              View All
            </button>
          </div>

          <div style={{ overflowX: 'auto' }}>
            <table style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'left', fontSize: '0.85rem' }}>
              <thead>
                <tr style={{ borderBottom: '1px solid var(--border-subtle)', color: 'var(--text-muted)' }}>
                  <th style={{ padding: '10px 8px' }}>Survey ID</th>
                  <th style={{ padding: '10px 8px' }}>Road Segment</th>
                  <th style={{ padding: '10px 8px' }}>Defects</th>
                  <th style={{ padding: '10px 8px' }}>Road Health (RHI)</th>
                  <th style={{ padding: '10px 8px' }}>Priority</th>
                </tr>
              </thead>
              <tbody>
                {inspections.map(insp => (
                  <tr key={insp.id} style={{ borderBottom: '1px solid rgba(255,255,255,0.04)' }}>
                    <td style={{ padding: '12px 8px', fontFamily: 'var(--font-mono)', color: '#38bdf8' }}>
                      {insp.id}
                    </td>
                    <td style={{ padding: '12px 8px', color: '#f8fafc', fontWeight: 500 }}>
                      {insp.road_name}
                    </td>
                    <td style={{ padding: '12px 8px', color: '#94a3b8' }}>
                      {insp.total_defects} ({insp.pothole_count} P, {insp.crack_count} C)
                    </td>
                    <td style={{ padding: '12px 8px' }}>
                      <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                        <div style={{ width: 60, height: 6, background: '#1e293b', borderRadius: 3 }}>
                          <div style={{
                            width: `${insp.road_health_index}%`,
                            height: '100%',
                            borderRadius: 3,
                            background: insp.road_health_index > 75 ? '#10b981' : insp.road_health_index > 55 ? '#f59e0b' : '#ef4444'
                          }} />
                        </div>
                        <span style={{ fontWeight: 600, fontSize: '0.8rem' }}>{Math.round(insp.road_health_index)}/100</span>
                      </div>
                    </td>
                    <td style={{ padding: '12px 8px' }}>
                      <PriorityBadge priority={insp.priority_level} />
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>

        {/* Recent Defect Spot Inspector */}
        <div className="glass-panel" style={{ padding: 24 }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16 }}>
            <h3 style={{ fontSize: '1.05rem', color: '#f8fafc' }}>
              Detected Damage Incidents
            </h3>
            <span style={{ fontSize: '0.78rem', color: '#94a3b8' }}>Click to Calibrate</span>
          </div>

          <div style={{ display: 'flex', flexDirection: 'column', gap: 10, maxHeight: 380, overflowY: 'auto' }}>
            {recentDamages.map(d => (
              <div
                key={d.id}
                onClick={() => setSelectedDamage(d)}
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'space-between',
                  padding: '10px 14px',
                  background: 'rgba(15, 23, 42, 0.6)',
                  borderRadius: 10,
                  border: '1px solid var(--border-subtle)',
                  cursor: 'pointer',
                  transition: 'all 0.2s ease'
                }}
                onMouseEnter={e => e.currentTarget.style.borderColor = 'rgba(56, 189, 248, 0.4)'}
                onMouseLeave={e => e.currentTarget.style.borderColor = 'var(--border-subtle)'}
              >
                <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
                  <div style={{
                    width: 44,
                    height: 44,
                    borderRadius: 8,
                    background: '#1e293b',
                    overflow: 'hidden',
                    flexShrink: 0
                  }}>
                    {d.annotated_image_path || d.image_path ? (
                      <img
                        src={getMediaUrl(d.annotated_image_path || d.image_path)}
                        alt={d.damage_type}
                        style={{ width: '100%', height: '100%', objectFit: 'cover' }}
                      />
                    ) : (
                      <div style={{ width: '100%', height: '100%', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                        <AlertTriangle size={16} color="#f59e0b" />
                      </div>
                    )}
                  </div>
                  <div>
                    <div style={{ fontSize: '0.88rem', fontWeight: 600, color: '#f8fafc' }}>
                      {d.damage_type}
                    </div>
                    <div style={{ fontSize: '0.75rem', color: '#64748b', fontFamily: 'var(--font-mono)' }}>
                      {d.id} • Conf: {Math.round((d.confidence || 0.88) * 100)}%
                    </div>
                  </div>
                </div>

                <div style={{ textAlign: 'right' }}>
                  <SeverityBadge level={d.severity_level} score={d.severity_score} />
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Explainability & Human Calibration Modal */}
      {selectedDamage && (
        <DamageModal
          damage={selectedDamage}
          onClose={() => setSelectedDamage(null)}
          onUpdated={loadData}
        />
      )}
    </div>
  );
}
