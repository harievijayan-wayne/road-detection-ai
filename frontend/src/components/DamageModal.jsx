import React, { useState } from 'react';
import { X, Check, AlertTriangle, Sliders, ShieldCheck, MapPin, Eye } from 'lucide-react';
import SeverityBadge from './SeverityBadge';
import PriorityBadge from './PriorityBadge';
import { reviewDamageEvent, getMediaUrl } from '../services/api';

export default function DamageModal({ damage, onClose, onUpdated }) {
  if (!damage) return null;

  const [damageType, setDamageType] = useState(damage.damage_type);
  const [severityScore, setSeverityScore] = useState(damage.severity_score || 50);
  const [status, setStatus] = useState(damage.status || 'confirmed');
  const [notes, setNotes] = useState(damage.human_notes || '');
  const [saving, setSaving] = useState(false);
  const [saveSuccess, setSaveSuccess] = useState(false);

  const factors = damage.factors || {};

  const handleSave = async () => {
    setSaving(true);
    try {
      await reviewDamageEvent(damage.id, {
        verified_damage_type: damageType,
        verified_severity_score: parseFloat(severityScore),
        status,
        notes
      });
      setSaveSuccess(true);
      setTimeout(() => {
        if (onUpdated) onUpdated();
        onClose();
      }, 700);
    } catch (err) {
      alert("Failed to save review: " + err.message);
    } finally {
      setSaving(false);
    }
  };

  return (
    <div style={{
      position: 'fixed',
      inset: 0,
      zIndex: 100,
      background: 'rgba(4, 7, 13, 0.8)',
      backdropFilter: 'blur(10px)',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      padding: 20
    }}>
      <div className="glass-panel" style={{
        maxWidth: 720,
        width: '100%',
        maxHeight: '90vh',
        overflowY: 'auto',
        background: '#0d1322',
        border: '1px solid rgba(255, 255, 255, 0.15)',
        padding: 28,
        position: 'relative'
      }}>
        {/* Header */}
        <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', marginBottom: 20 }}>
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 6 }}>
              <span style={{ fontSize: '0.8rem', color: 'var(--primary)', fontFamily: 'var(--font-mono)' }}>
                {damage.id}
              </span>
              <SeverityBadge level={damage.severity_level} score={damage.severity_score} />
              <PriorityBadge priority={damage.priority} />
            </div>
            <h2 style={{ fontSize: '1.4rem', color: '#f8fafc' }}>
              {damage.damage_type}
            </h2>
          </div>
          <button
            onClick={onClose}
            style={{
              background: 'rgba(255, 255, 255, 0.05)',
              border: 'none',
              color: '#94a3b8',
              cursor: 'pointer',
              padding: 8,
              borderRadius: 8
            }}
          >
            <X size={20} />
          </button>
        </div>

        {/* Modal Content Grid */}
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 20, marginBottom: 24 }}>
          {/* Visual Thumbnail & BBox info */}
          <div>
            <div style={{
              borderRadius: 12,
              overflow: 'hidden',
              background: '#070a12',
              border: '1px solid var(--border-subtle)',
              height: 200,
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              position: 'relative'
            }}>
              {damage.annotated_image_path || damage.image_path ? (
                <img
                  src={getMediaUrl(damage.annotated_image_path || damage.image_path)}
                  alt={damage.damage_type}
                  style={{ width: '100%', height: '100%', objectFit: 'cover' }}
                />
              ) : (
                <div style={{ textAlign: 'center', color: '#64748b' }}>
                  <Eye size={36} style={{ margin: '0 auto 8px', opacity: 0.5 }} />
                  <p style={{ fontSize: '0.8rem' }}>Telemetry Frame Capture</p>
                </div>
              )}
            </div>

            <div style={{ marginTop: 12, display: 'flex', flexDirection: 'column', gap: 6, fontSize: '0.82rem', color: '#94a3b8' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                <span>Detection Confidence:</span>
                <strong style={{ color: '#38bdf8' }}>{Math.round((damage.confidence || 0.88) * 100)}%</strong>
              </div>
              <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                <span>GPS Location:</span>
                <span style={{ fontFamily: 'var(--font-mono)', color: '#f8fafc' }}>
                  {damage.latitude ? `${damage.latitude.toFixed(4)}°N, ${damage.longitude.toFixed(4)}°E` : "Location unavailable"}
                </span>
              </div>
              <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                <span>Verification State:</span>
                <span style={{ color: damage.human_verified ? '#10b981' : '#f59e0b', fontWeight: 600 }}>
                  {damage.human_verified ? "Verified by Engineer" : "Automated AI Detection"}
                </span>
              </div>
            </div>
          </div>

          {/* Model Explainability: Multi-factor breakdown */}
          <div style={{
            background: 'rgba(15, 23, 42, 0.7)',
            borderRadius: 12,
            padding: 16,
            border: '1px solid var(--border-subtle)'
          }}>
            <h4 style={{ fontSize: '0.85rem', color: '#cbd5e1', marginBottom: 12, textTransform: 'uppercase', letterSpacing: '0.04em' }}>
              Severity Factor Explainability
            </h4>

            <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
              {[
                { label: 'Surface Area Impact (30%)', val: factors.area_score || 65, color: '#38bdf8' },
                { label: 'Dimension / Aspect Ratio (20%)', val: factors.dimension_score || 55, color: '#818cf8' },
                { label: 'Damage Type Base Hazard (20%)', val: factors.type_risk_score || 85, color: '#f59e0b' },
                { label: 'Model Confidence (15%)', val: factors.confidence_score || 92, color: '#10b981' },
                { label: 'Temporal Video Persistence (15%)', val: factors.persistence_score || 60, color: '#ec4899' },
              ].map((f, i) => (
                <div key={i}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.78rem', marginBottom: 4 }}>
                    <span style={{ color: '#94a3b8' }}>{f.label}</span>
                    <span style={{ color: '#f8fafc', fontWeight: 600 }}>{Math.round(f.val)}%</span>
                  </div>
                  <div style={{ height: 6, background: '#1e293b', borderRadius: 3, overflow: 'hidden' }}>
                    <div style={{ width: `${Math.min(100, f.val)}%`, height: '100%', background: f.color, borderRadius: 3 }} />
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* Human In The Loop Active Review Form */}
        <div style={{
          background: 'rgba(30, 41, 59, 0.4)',
          borderRadius: 12,
          padding: 18,
          border: '1px solid rgba(56, 189, 248, 0.2)'
        }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 14 }}>
            <Sliders size={18} color="#38bdf8" />
            <h4 style={{ fontSize: '0.92rem', color: '#f8fafc' }}>
              Human-in-the-Loop Engineer Calibration
            </h4>
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: 14, marginBottom: 14 }}>
            <div>
              <label style={{ fontSize: '0.78rem', color: '#94a3b8', display: 'block', marginBottom: 4 }}>
                Damage Classification
              </label>
              <select
                value={damageType}
                onChange={e => setDamageType(e.target.value)}
                style={{
                  width: '100%',
                  background: '#0f172a',
                  border: '1px solid #334155',
                  color: '#f8fafc',
                  padding: '8px 10px',
                  borderRadius: 6,
                  fontSize: '0.85rem'
                }}
              >
                {[
                  "Pothole", "Longitudinal crack", "Transverse crack", "Alligator crack",
                  "Edge crack", "Surface deformation", "Rutting", "Patch damage",
                  "Manhole/road-surface defect", "Other road damage"
                ].map(c => (
                  <option key={c} value={c}>{c}</option>
                ))}
              </select>
            </div>

            <div>
              <label style={{ fontSize: '0.78rem', color: '#94a3b8', display: 'block', marginBottom: 4 }}>
                Calibrated Severity Score: <strong>{severityScore}</strong>
              </label>
              <input
                type="range"
                min="0"
                max="100"
                value={severityScore}
                onChange={e => setSeverityScore(e.target.value)}
                style={{ width: '100%', accentColor: '#38bdf8', marginTop: 8 }}
              />
            </div>

            <div>
              <label style={{ fontSize: '0.78rem', color: '#94a3b8', display: 'block', marginBottom: 4 }}>
                Maintenance Status
              </label>
              <select
                value={status}
                onChange={e => setStatus(e.target.value)}
                style={{
                  width: '100%',
                  background: '#0f172a',
                  border: '1px solid #334155',
                  color: '#f8fafc',
                  padding: '8px 10px',
                  borderRadius: 6,
                  fontSize: '0.85rem'
                }}
              >
                <option value="confirmed">Confirmed</option>
                <option value="in_review">In Engineering Review</option>
                <option value="dispatched">Maintenance Dispatched</option>
                <option value="repaired">Repaired & Closed</option>
              </select>
            </div>
          </div>

          <div style={{ marginBottom: 14 }}>
            <label style={{ fontSize: '0.78rem', color: '#94a3b8', display: 'block', marginBottom: 4 }}>
              Civil Engineer Field Notes
            </label>
            <input
              type="text"
              placeholder="e.g. Sub-base moisture detected, prioritize asphalt cold-mix patching."
              value={notes}
              onChange={e => setNotes(e.target.value)}
              style={{
                width: '100%',
                background: '#0f172a',
                border: '1px solid #334155',
                color: '#f8fafc',
                padding: '8px 12px',
                borderRadius: 6,
                fontSize: '0.85rem'
              }}
            />
          </div>

          <div style={{ display: 'flex', justifyContent: 'flex-end', gap: 10 }}>
            <button className="btn-secondary" onClick={onClose}>
              Cancel
            </button>
            <button
              className="btn-primary"
              onClick={handleSave}
              disabled={saving}
              style={{ background: saveSuccess ? '#10b981' : undefined }}
            >
              {saveSuccess ? <Check size={16} /> : <ShieldCheck size={16} />}
              {saveSuccess ? "Calibration Saved!" : saving ? "Saving..." : "Verify & Save Decision"}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
