import React from 'react';

export default function MetricCard({ title, value, unit, subtitle, icon: Icon, trend, color = '#38bdf8' }) {
  return (
    <div className="glass-panel" style={{ padding: '20px 24px', display: 'flex', flexDirection: 'column', gap: 10 }}>
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
        <span style={{ fontSize: '0.85rem', fontWeight: 600, color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.04em' }}>
          {title}
        </span>
        {Icon && (
          <div style={{
            width: 38,
            height: 38,
            borderRadius: 10,
            background: `rgba(${parseInt(color.slice(1,3),16)}, ${parseInt(color.slice(3,5),16)}, ${parseInt(color.slice(5,7),16)}, 0.12)`,
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            border: `1px solid rgba(${parseInt(color.slice(1,3),16)}, ${parseInt(color.slice(3,5),16)}, ${parseInt(color.slice(5,7),16)}, 0.25)`
          }}>
            <Icon size={20} color={color} />
          </div>
        )}
      </div>

      <div style={{ display: 'flex', alignItems: 'baseline', gap: 8 }}>
        <span style={{ fontSize: '2.1rem', fontWeight: 800, color: '#f8fafc', fontFamily: 'var(--font-heading)' }}>
          {value}
        </span>
        {unit && (
          <span style={{ fontSize: '0.9rem', fontWeight: 600, color: 'var(--text-dim)' }}>
            {unit}
          </span>
        )}
      </div>

      {(subtitle || trend) && (
        <div style={{ display: 'flex', alignItems: 'center', gap: 6, fontSize: '0.78rem', color: 'var(--text-muted)' }}>
          {trend && (
            <span style={{ color: trend.startsWith('+') ? '#10b981' : '#ef4444', fontWeight: 600 }}>
              {trend}
            </span>
          )}
          <span>{subtitle}</span>
        </div>
      )}
    </div>
  );
}
