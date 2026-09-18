import React from 'react';
import { Clock, AlertOctagon, CheckCircle2, Zap } from 'lucide-react';

export default function PriorityBadge({ priority }) {
  const norm = (priority || 'MEDIUM PRIORITY').toUpperCase();

  if (norm.includes('URGENT')) {
    return (
      <span className="badge badge-urgent">
        <Zap size={13} />
        URGENT (24-48h SLA)
      </span>
    );
  }

  if (norm.includes('HIGH')) {
    return (
      <span className="badge badge-high">
        <AlertOctagon size={13} />
        HIGH PRIORITY (7d)
      </span>
    );
  }

  if (norm.includes('MEDIUM')) {
    return (
      <span className="badge badge-moderate">
        <Clock size={13} />
        MEDIUM PRIORITY (30d)
      </span>
    );
  }

  return (
    <span className="badge badge-low">
      <CheckCircle2 size={13} />
      LOW PRIORITY (Routine)
    </span>
  );
}
