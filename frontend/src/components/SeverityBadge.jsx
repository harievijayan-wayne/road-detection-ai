import React from 'react';
import { AlertCircle, AlertTriangle, ShieldCheck, Flame } from 'lucide-react';

export default function SeverityBadge({ level, score }) {
  const normLevel = (level || 'Moderate').toLowerCase();

  let badgeClass = 'badge-moderate';
  let Icon = AlertTriangle;

  if (normLevel === 'low') {
    badgeClass = 'badge-low';
    Icon = ShieldCheck;
  } else if (normLevel === 'moderate') {
    badgeClass = 'badge-moderate';
    Icon = AlertTriangle;
  } else if (normLevel === 'high') {
    badgeClass = 'badge-high';
    Icon = AlertCircle;
  } else if (normLevel === 'critical') {
    badgeClass = 'badge-critical';
    Icon = Flame;
  }

  return (
    <span className={`badge ${badgeClass}`}>
      <Icon size={12} />
      {level || 'Moderate'} {score !== undefined ? `(${Math.round(score)})` : ''}
    </span>
  );
}
