import React, { useState } from 'react';
import { ArrowRight, LockKeyhole, ShieldCheck, UserRound } from 'lucide-react';

export default function LoginPage({ onLogin }) {
  const [form, setForm] = useState({ email: '', password: '' });
  const [error, setError] = useState('');

  const handleChange = (event) => {
    const { name, value } = event.target;
    setForm((prev) => ({ ...prev, [name]: value }));
    if (error) setError('');
  };

  const handleSubmit = (event) => {
    event.preventDefault();

    if (!form.email.trim() || !form.password.trim()) {
      setError('Please enter both email and password.');
      return;
    }

    onLogin();
  };

  return (
    <div style={{
      minHeight: '100vh',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      padding: '32px 20px',
      background: 'radial-gradient(circle at top, rgba(56, 189, 248, 0.12), transparent 35%), #080c14'
    }}>
      <div style={{
        width: '100%',
        maxWidth: 460,
        background: 'rgba(15, 23, 42, 0.82)',
        border: '1px solid rgba(255,255,255,0.08)',
        borderRadius: 24,
        padding: '32px 28px',
        boxShadow: '0 24px 60px rgba(2, 6, 23, 0.7)'
      }}>
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', marginBottom: 18 }}>
          <div style={{
            width: 54,
            height: 54,
            borderRadius: 18,
            background: 'linear-gradient(135deg, #0284c7, #38bdf8)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            boxShadow: '0 0 20px rgba(56, 189, 248, 0.35)'
          }}>
            <ShieldCheck size={28} color="#fff" />
          </div>
        </div>

        <div style={{ textAlign: 'center', marginBottom: 26 }}>
          <p style={{ color: '#38bdf8', fontWeight: 700, letterSpacing: '0.12em', fontSize: '0.72rem', textTransform: 'uppercase' }}>
            RoadDamageAI
          </p>
          <h1 style={{ fontSize: '2rem', marginTop: 8, marginBottom: 8, color: '#f8fafc' }}>
            Sign in
          </h1>
          <p style={{ color: '#94a3b8', fontSize: '0.92rem' }}>
            Access the municipal road intelligence dashboard
          </p>
        </div>

        <form onSubmit={handleSubmit} style={{ display: 'flex', flexDirection: 'column', gap: 18 }}>
          <label style={{ display: 'flex', flexDirection: 'column', gap: 8, color: '#cbd5e1', fontSize: '0.9rem' }}>
            <span style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
              <UserRound size={16} color="#38bdf8" />
              Email
            </span>
            <input
              type="email"
              name="email"
              value={form.email}
              onChange={handleChange}
              placeholder="engineer@roaddamage.ai"
              style={{
                background: 'rgba(15, 23, 42, 0.9)',
                border: '1px solid rgba(148, 163, 184, 0.3)',
                borderRadius: 12,
                padding: '12px 14px',
                fontSize: '0.96rem',
                color: '#f8fafc',
                outline: 'none'
              }}
            />
          </label>

          <label style={{ display: 'flex', flexDirection: 'column', gap: 8, color: '#cbd5e1', fontSize: '0.9rem' }}>
            <span style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
              <LockKeyhole size={16} color="#38bdf8" />
              Password
            </span>
            <input
              type="password"
              name="password"
              value={form.password}
              onChange={handleChange}
              placeholder="Enter password"
              style={{
                background: 'rgba(15, 23, 42, 0.9)',
                border: '1px solid rgba(148, 163, 184, 0.3)',
                borderRadius: 12,
                padding: '12px 14px',
                fontSize: '0.96rem',
                color: '#f8fafc',
                outline: 'none'
              }}
            />
          </label>

          {error && (
            <div style={{
              background: 'rgba(239, 68, 68, 0.12)',
              border: '1px solid rgba(239, 68, 68, 0.35)',
              color: '#fca5a5',
              borderRadius: 10,
              padding: '10px 12px',
              fontSize: '0.85rem'
            }}>
              {error}
            </div>
          )}

          <button
            type="submit"
            className="btn-primary"
            style={{ width: '100%', justifyContent: 'center', marginTop: 8 }}
          >
            Sign in <ArrowRight size={18} />
          </button>
        </form>

        <div style={{
          marginTop: 22,
          textAlign: 'center',
          color: '#94a3b8',
          fontSize: '0.82rem',
          borderTop: '1px solid rgba(148,163,184,0.15)',
          paddingTop: 18
        }}>
          Demo access: use any email and password to continue
        </div>
      </div>
    </div>
  );
}
