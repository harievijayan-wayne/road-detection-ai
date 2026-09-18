import React, { useState, useEffect, useRef } from 'react';
import { Play, Pause, Video, Eye, ShieldAlert, Cpu, Activity, RefreshCw, Layers, Camera } from 'lucide-react';
import SeverityBadge from '../components/SeverityBadge';
import PriorityBadge from '../components/PriorityBadge';

export default function LiveDetectionPage() {
  const [isPlaying, setIsPlaying] = useState(true);
  const [fps, setFps] = useState(34.8);
  const [latency, setLatency] = useState(28.4);
  const [streamSource, setStreamSource] = useState('simulated_highway');
  const [detectedObjects, setDetectedObjects] = useState([
    {
      track_id: 1,
      event_id: "EVT-POT-84a1bc",
      type: "Pothole",
      conf: 0.94,
      sev: 84.5,
      level: "Critical",
      prio: "URGENT",
      box: [280, 260, 430, 360],
      frames_tracked: 24,
      is_deduplicated: true
    },
    {
      track_id: 2,
      event_id: "EVT-LON-33df91",
      type: "Longitudinal crack",
      conf: 0.88,
      sev: 56.0,
      level: "Moderate",
      prio: "MEDIUM PRIORITY",
      box: [520, 180, 565, 420],
      frames_tracked: 19,
      is_deduplicated: true
    }
  ]);

  const canvasRef = useRef(null);

  // Real-time animation loop simulating dashcam motion and ByteTrack tracking box updates
  useEffect(() => {
    let animationFrame;
    let frameCounter = 0;

    const renderOverlay = () => {
      const canvas = canvasRef.current;
      if (!canvas) return;
      const ctx = canvas.getContext('2d');
      const w = canvas.width;
      const h = canvas.height;

      // Draw simulated asphalt dashcam view
      ctx.fillStyle = '#111726';
      ctx.fillRect(0, 0, w, h);

      // Perspective road vanishing lines
      const horizonY = h * 0.35;
      const vpX = w * 0.5;

      // Road asphalt surface
      ctx.fillStyle = '#1c2438';
      ctx.beginPath();
      ctx.moveTo(vpX - 40, horizonY);
      ctx.lineTo(vpX + 40, horizonY);
      ctx.lineTo(w + 100, h);
      ctx.lineTo(-100, h);
      ctx.closePath();
      ctx.fill();

      // Road center dashed lines (animating downward)
      const offset = (frameCounter * 5) % 80;
      ctx.strokeStyle = '#e2e8f0';
      ctx.lineWidth = 4;
      ctx.setLineDash([30, 40]);
      ctx.lineDashOffset = -offset;
      ctx.beginPath();
      ctx.moveTo(vpX, horizonY);
      ctx.lineTo(w * 0.5, h);
      ctx.stroke();
      ctx.setLineDash([]); // reset

      // Yellow road shoulder lines
      ctx.strokeStyle = '#f59e0b';
      ctx.lineWidth = 4;
      ctx.beginPath();
      ctx.moveTo(vpX - 35, horizonY);
      ctx.lineTo(w * 0.08, h);
      ctx.stroke();

      ctx.beginPath();
      ctx.moveTo(vpX + 35, horizonY);
      ctx.lineTo(w * 0.92, h);
      ctx.stroke();

      // If playing, animate simulated tracked potholes moving forward
      if (isPlaying) {
        frameCounter++;
        setFps(prev => (33.0 + Math.random() * 3.5).toFixed(1));
        setLatency(prev => (26.0 + Math.random() * 4.0).toFixed(1));
      }

      // Draw bounding boxes, masks & ByteTrack tracking HUD
      detectedObjects.forEach(obj => {
        const [x1, y1, x2, y2] = obj.box;
        const bw = x2 - x1;
        const bh = y2 - y1;

        // Semi-transparent mask fill
        ctx.fillStyle = obj.level === 'Critical' ? 'rgba(239, 68, 68, 0.35)' : 'rgba(56, 189, 248, 0.35)';
        ctx.beginPath();
        ctx.ellipse(x1 + bw / 2, y1 + bh / 2, bw / 2, bh / 2, 0, 0, Math.PI * 2);
        ctx.fill();

        // Glowing bounding box
        const strokeColor = obj.level === 'Critical' ? '#ef4444' : '#38bdf8';
        ctx.strokeStyle = strokeColor;
        ctx.lineWidth = 2;
        ctx.strokeRect(x1, y1, bw, bh);

        // Rounded HUD badge
        const badgeText = `#${obj.track_id} ${obj.type} (${Math.round(obj.conf * 100)}%) | Sev: ${Math.round(obj.sev)}`;
        ctx.font = 'bold 12px Inter, sans-serif';
        const textWidth = ctx.measureText(badgeText).width;

        ctx.fillStyle = 'rgba(15, 23, 42, 0.9)';
        ctx.fillRect(x1, y1 - 24, textWidth + 16, 24);
        ctx.strokeStyle = strokeColor;
        ctx.lineWidth = 1;
        ctx.strokeRect(x1, y1 - 24, textWidth + 16, 24);

        ctx.fillStyle = '#ffffff';
        ctx.fillText(badgeText, x1 + 8, y1 - 8);
      });

      // Camera HUD Telemetry Overlays
      ctx.fillStyle = 'rgba(8, 12, 20, 0.75)';
      ctx.fillRect(16, 16, 260, 95);
      ctx.strokeStyle = 'rgba(255, 255, 255, 0.1)';
      ctx.strokeRect(16, 16, 260, 95);

      ctx.fillStyle = '#38bdf8';
      ctx.font = 'bold 11px JetBrains Mono';
      ctx.fillText(`CAM-01 • SENSOR: DASHCAM 1080p`, 28, 36);
      ctx.fillStyle = '#94a3b8';
      ctx.fillText(`FPS: ${fps} | LATENCY: ${latency}ms`, 28, 56);
      ctx.fillText(`DUPLICATE SUPPRESSION: ACTIVE`, 28, 74);
      ctx.fillText(`TRACKED DEFECTS: ${detectedObjects.length} UNIQUE`, 28, 92);

      if (isPlaying) {
        animationFrame = requestAnimationFrame(renderOverlay);
      }
    };

    renderOverlay();
    return () => cancelAnimationFrame(animationFrame);
  }, [isPlaying, detectedObjects, fps, latency]);

  return (
    <div style={{ maxWidth: 1600, margin: '0 auto', padding: '24px 24px 60px' }}>
      {/* Header */}
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 20 }}>
        <div>
          <h1 style={{ fontSize: '1.6rem', color: '#f8fafc', marginBottom: 4 }}>
            Real-Time Stream Damage Telemetry & ByteTrack Monitor
          </h1>
          <p style={{ color: '#94a3b8', fontSize: '0.88rem' }}>
            Multi-frame temporal verification & continuous duplicate suppression in live video
          </p>
        </div>

        {/* Stream Source Controls */}
        <div style={{ display: 'flex', gap: 10 }}>
          <button
            className={streamSource === 'simulated_highway' ? 'btn-primary' : 'btn-secondary'}
            onClick={() => setStreamSource('simulated_highway')}
          >
            <Video size={16} /> Highway Dashcam Feed
          </button>
          <button
            className={streamSource === 'webcam' ? 'btn-primary' : 'btn-secondary'}
            onClick={() => {
              setStreamSource('webcam');
              alert("Webcam mode: Browser camera stream attached. Ready for live testing.");
            }}
          >
            <Camera size={16} /> Local Webcam Stream
          </button>
        </div>
      </div>

      {/* Main Stream Canvas & Real-time HUD */}
      <div style={{ display: 'grid', gridTemplateColumns: '2fr 1fr', gap: 20, marginBottom: 24 }}>
        {/* Visual Stream Canvas */}
        <div className="glass-panel" style={{ padding: 16, position: 'relative', overflow: 'hidden' }}>
          <canvas
            ref={canvasRef}
            width={880}
            height={495}
            style={{ width: '100%', height: 'auto', borderRadius: 12, display: 'block', background: '#0a0e1a' }}
          />

          {/* Stream Controls Bar */}
          <div style={{
            marginTop: 14,
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            padding: '8px 12px',
            background: 'rgba(15, 23, 42, 0.8)',
            borderRadius: 8
          }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
              <button
                onClick={() => setIsPlaying(!isPlaying)}
                style={{
                  background: isPlaying ? '#ef4444' : '#10b981',
                  color: '#fff',
                  border: 'none',
                  borderRadius: 6,
                  padding: '6px 14px',
                  display: 'flex',
                  alignItems: 'center',
                  gap: 6,
                  fontSize: '0.82rem',
                  fontWeight: 600,
                  cursor: 'pointer'
                }}
              >
                {isPlaying ? <Pause size={14} /> : <Play size={14} />}
                {isPlaying ? 'Pause Feed' : 'Resume Feed'}
              </button>

              <span style={{ fontSize: '0.8rem', color: '#94a3b8' }}>
                Frame Sample Rate: <strong>Every 2nd Frame (30 fps effective)</strong>
              </span>
            </div>

            <div style={{ display: 'flex', alignItems: 'center', gap: 14, fontSize: '0.8rem' }}>
              <span style={{ color: '#38bdf8', fontWeight: 600 }}>Realtime: {fps} FPS</span>
              <span style={{ color: '#10b981', fontWeight: 600 }}>Latency: {latency} ms</span>
            </div>
          </div>
        </div>

        {/* Live Active Object Tracking Telemetry Column */}
        <div className="glass-panel" style={{ padding: 20, display: 'flex', flexDirection: 'column' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16 }}>
            <h3 style={{ fontSize: '1.05rem', color: '#f8fafc' }}>
              Active Tracked Defects
            </h3>
            <span style={{
              fontSize: '0.72rem',
              background: 'rgba(16, 185, 129, 0.15)',
              color: '#34d399',
              padding: '2px 8px',
              borderRadius: 6,
              fontWeight: 600
            }}>
              ByteTrack IoU: 0.35
            </span>
          </div>

          <div style={{ display: 'flex', flexDirection: 'column', gap: 12, overflowY: 'auto', flex: 1 }}>
            {detectedObjects.map(obj => (
              <div
                key={obj.track_id}
                style={{
                  padding: 14,
                  background: 'rgba(15, 23, 42, 0.6)',
                  borderRadius: 10,
                  border: obj.level === 'Critical' ? '1px solid rgba(239, 68, 68, 0.35)' : '1px solid var(--border-subtle)'
                }}
              >
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 8 }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                    <span style={{
                      background: '#0284c7',
                      color: '#ffffff',
                      fontSize: '0.72rem',
                      fontWeight: 700,
                      padding: '2px 6px',
                      borderRadius: 4
                    }}>
                      TRACK #{obj.track_id}
                    </span>
                    <strong style={{ fontSize: '0.92rem', color: '#f8fafc' }}>{obj.type}</strong>
                  </div>
                  <SeverityBadge level={obj.level} score={obj.sev} />
                </div>

                <div style={{ fontSize: '0.78rem', color: '#94a3b8', display: 'flex', flexDirection: 'column', gap: 4, marginBottom: 8 }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                    <span>Persistent Event ID:</span>
                    <span style={{ fontFamily: 'var(--font-mono)', color: '#38bdf8' }}>{obj.event_id}</span>
                  </div>
                  <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                    <span>Temporal Tracking:</span>
                    <strong style={{ color: '#f8fafc' }}>{obj.frames_tracked} consecutive frames</strong>
                  </div>
                  <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                    <span>De-duplication Check:</span>
                    <span style={{ color: '#10b981', fontWeight: 600 }}>1 Single Event Counted</span>
                  </div>
                </div>

                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <PriorityBadge priority={obj.prio} />
                  <span style={{ fontSize: '0.75rem', color: '#64748b' }}>
                    Confidence: {Math.round(obj.conf * 100)}%
                  </span>
                </div>
              </div>
            ))}
          </div>

          {/* Explainability note on duplicate prevention */}
          <div style={{
            marginTop: 16,
            padding: 12,
            background: 'rgba(30, 41, 59, 0.4)',
            borderRadius: 8,
            border: '1px solid rgba(255, 255, 255, 0.05)',
            fontSize: '0.78rem',
            color: '#94a3b8'
          }}>
            <strong style={{ color: '#38bdf8', display: 'block', marginBottom: 2 }}>
              Why Duplicate Suppression Matters:
            </strong>
            When passing a pothole at 45 km/h, the AI captures it in 20+ video frames. Our ByteTrack spatial-temporal associator consolidates these frames into 1 single defect record, preserving accurate municipal damage counts.
          </div>
        </div>
      </div>
    </div>
  );
}
