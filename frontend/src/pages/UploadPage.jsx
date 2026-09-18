import React, { useState, useEffect } from 'react';
import { UploadCloud, FileImage, Sparkles, CheckCircle2, AlertTriangle, Cpu, Download, ArrowRight, Eye, ShieldCheck, RefreshCw } from 'lucide-react';
import SeverityBadge from '../components/SeverityBadge';
import PriorityBadge from '../components/PriorityBadge';
import DamageModal from '../components/DamageModal';
import { detectImageUpload, fetchDemoSamples, generateReport, getMediaUrl } from '../services/api';

export default function UploadPage({ onNavigate }) {
  const [selectedFile, setSelectedFile] = useState(null);
  const [previewUrl, setPreviewUrl] = useState(null);
  const [roadName, setRoadName] = useState('South Ring Expressway (KM 14.2)');
  const [demoSamples, setDemoSamples] = useState([]);
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [selectedDamage, setSelectedDamage] = useState(null);
  const [downloadingReport, setDownloadingReport] = useState(false);

  useEffect(() => {
    fetchDemoSamples().then(res => setDemoSamples(res.samples || [])).catch(console.error);
  }, []);

  const handleFileChange = (e) => {
    const file = e.target.files[0];
    if (file) {
      setSelectedFile(file);
      setPreviewUrl(URL.createObjectURL(file));
      setResult(null);
    }
  };

  const handleSelectDemoSample = async (sample) => {
    setLoading(true);
    setResult(null);
    try {
      // Fetch sample as blob to run live through detector
      const response = await fetch(`http://localhost:8000${sample.url}`);
      const blob = await response.blob();
      const file = new File([blob], sample.filename, { type: 'image/jpeg' });
      
      setSelectedFile(file);
      setPreviewUrl(URL.createObjectURL(file));

      const formData = new FormData();
      formData.append('file', file);
      formData.append('road_name', `Sample: ${sample.title}`);

      const data = await detectImageUpload(formData);
      setResult(data);
    } catch (err) {
      alert("Analysis failed: " + err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleRunAnalysis = async () => {
    if (!selectedFile) return;
    setLoading(true);
    try {
      const formData = new FormData();
      formData.append('file', selectedFile);
      formData.append('road_name', roadName);

      const data = await detectImageUpload(formData);
      setResult(data);
    } catch (err) {
      alert("Analysis failed: " + err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleDownloadReport = async (fmt) => {
    if (!result) return;
    setDownloadingReport(true);
    try {
      const rep = await generateReport({
        inspection_id: result.inspection_id,
        format: fmt,
        road_id: roadName
      });
      window.open(`http://localhost:8000${rep.download_url}`, '_blank');
    } catch (err) {
      alert("Failed to download report: " + err.message);
    } finally {
      setDownloadingReport(false);
    }
  };

  const lighting = result?.lighting_assessment || {};
  const initMetrics = lighting.initial_metrics || {};

  return (
    <div style={{ maxWidth: 1600, margin: '0 auto', padding: '24px 24px 60px' }}>
      {/* Header */}
      <div style={{ marginBottom: 24 }}>
        <h1 style={{ fontSize: '1.6rem', color: '#f8fafc', marginBottom: 4 }}>
          Upload Road Imagery & Automated Defect Audit
        </h1>
        <p style={{ color: '#94a3b8', fontSize: '0.88rem' }}>
          Applies adaptive CLAHE lighting normalization, YOLO segmentation, and multi-factor mathematical severity
        </p>
      </div>

      {/* Demo 1-Click Samples Bar (Super convenient for hackathon presentation!) */}
      <div className="glass-panel" style={{ padding: 18, marginBottom: 24 }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 12 }}>
          <Sparkles size={18} color="#38bdf8" />
          <span style={{ fontSize: '0.9rem', fontWeight: 600, color: '#f8fafc' }}>
            Instant Hackathon Demo: Click a Sample Road Scenario to Analyze
          </span>
        </div>

        <div style={{ display: 'flex', gap: 12, overflowX: 'auto', paddingBottom: 6 }}>
          {demoSamples.map((s, idx) => (
            <button
              key={idx}
              onClick={() => handleSelectDemoSample(s)}
              disabled={loading}
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: 10,
                padding: '8px 14px',
                background: 'rgba(15, 23, 42, 0.7)',
                border: '1px solid var(--border-subtle)',
                borderRadius: 8,
                color: '#f8fafc',
                cursor: 'pointer',
                fontSize: '0.82rem',
                whiteSpace: 'nowrap',
                transition: 'all 0.2s ease'
              }}
              onMouseEnter={e => e.currentTarget.style.borderColor = '#38bdf8'}
              onMouseLeave={e => e.currentTarget.style.borderColor = 'var(--border-subtle)'}
            >
              <FileImage size={16} color="#38bdf8" />
              <span>{s.title}</span>
            </button>
          ))}
        </div>
      </div>

      {/* Main Upload / Analysis Workspace */}
      <div style={{ display: 'grid', gridTemplateColumns: '1.1fr 1fr', gap: 24 }}>
        {/* Left Column: Upload Dropzone & Settings */}
        <div>
          <div className="glass-panel" style={{ padding: 24, marginBottom: 20 }}>
            <h3 style={{ fontSize: '1.05rem', color: '#f8fafc', marginBottom: 16 }}>
              Select Road Image / Video File
            </h3>

            <div
              style={{
                border: '2px dashed var(--border-subtle)',
                borderRadius: 14,
                padding: '36px 20px',
                textAlign: 'center',
                background: 'rgba(15, 23, 42, 0.5)',
                cursor: 'pointer',
                transition: 'border-color 0.2s'
              }}
              onClick={() => document.getElementById('file-upload-input').click()}
            >
              <input
                id="file-upload-input"
                type="file"
                accept="image/*,video/*"
                style={{ display: 'none' }}
                onChange={handleFileChange}
              />
              <UploadCloud size={44} color="#38bdf8" style={{ margin: '0 auto 12px' }} />
              <p style={{ fontSize: '0.95rem', fontWeight: 600, color: '#f8fafc', marginBottom: 4 }}>
                {selectedFile ? selectedFile.name : "Click to select or drag road inspection file"}
              </p>
              <p style={{ fontSize: '0.78rem', color: '#64748b' }}>
                Supports JPG, PNG, WEBP, and MP4 dashcam recordings (up to 100MB)
              </p>
            </div>

            <div style={{ marginTop: 18 }}>
              <label style={{ fontSize: '0.82rem', color: '#94a3b8', display: 'block', marginBottom: 6 }}>
                Road / Survey Identifier
              </label>
              <input
                type="text"
                value={roadName}
                onChange={e => setRoadName(e.target.value)}
                style={{
                  width: '100%',
                  background: '#0f172a',
                  border: '1px solid #334155',
                  color: '#f8fafc',
                  padding: '10px 14px',
                  borderRadius: 8,
                  fontSize: '0.88rem'
                }}
              />
            </div>

            <div style={{ marginTop: 18 }}>
              <button
                className="btn-primary"
                style={{ width: '100%', justifyContent: 'center', padding: '12px 20px' }}
                onClick={handleRunAnalysis}
                disabled={!selectedFile || loading}
              >
                {loading ? (
                  <>
                    <RefreshCw className="animate-spin" size={18} /> Processing AI Pipeline...
                  </>
                ) : (
                  <>
                    <Sparkles size={18} /> Run Segmentation & Severity Telemetry
                  </>
                )}
              </button>
            </div>
          </div>

          {/* Raw Image Preview */}
          {previewUrl && (
            <div className="glass-panel" style={{ padding: 20 }}>
              <h4 style={{ fontSize: '0.88rem', color: '#94a3b8', marginBottom: 10 }}>
                Original Input File
              </h4>
              <img
                src={previewUrl}
                alt="Input Preview"
                style={{ width: '100%', maxHeight: 280, objectFit: 'cover', borderRadius: 8 }}
              />
            </div>
          )}
        </div>

        {/* Right Column: AI Output Results */}
        <div>
          {result ? (
            <div style={{ display: 'flex', flexDirection: 'column', gap: 20 }}>
              {/* Annotated Result Viewer */}
              <div className="glass-panel" style={{ padding: 20 }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 12 }}>
                  <h3 style={{ fontSize: '1.05rem', color: '#f8fafc' }}>
                    AI Segmented Telemetry Output
                  </h3>
                  <span style={{ fontSize: '0.78rem', color: '#10b981', fontWeight: 600 }}>
                    Inference: {result.processing_time_ms} ms
                  </span>
                </div>

                <div style={{ borderRadius: 10, overflow: 'hidden', border: '1px solid var(--border-subtle)', background: '#070a12' }}>
                  <img
                    src={getMediaUrl(result.annotated_image_url)}
                    alt="AI Annotated"
                    style={{ width: '100%', height: 'auto', display: 'block' }}
                  />
                </div>

                {/* Score Strip */}
                <div style={{
                  marginTop: 14,
                  display: 'grid',
                  gridTemplateColumns: '1fr 1fr 1fr',
                  gap: 12,
                  padding: 12,
                  background: 'rgba(15, 23, 42, 0.7)',
                  borderRadius: 8
                }}>
                  <div>
                    <span style={{ fontSize: '0.75rem', color: '#94a3b8', display: 'block' }}>Road Health Index</span>
                    <strong style={{ fontSize: '1.2rem', color: result.road_health_index > 75 ? '#10b981' : '#f59e0b' }}>
                      {result.road_health_index} / 100
                    </strong>
                  </div>

                  <div>
                    <span style={{ fontSize: '0.75rem', color: '#94a3b8', display: 'block' }}>Defects Detected</span>
                    <strong style={{ fontSize: '1.2rem', color: '#38bdf8' }}>
                      {result.total_damages}
                    </strong>
                  </div>

                  <div>
                    <span style={{ fontSize: '0.75rem', color: '#94a3b8', display: 'block' }}>Action Priority</span>
                    <PriorityBadge priority={result.priority_recommendation} />
                  </div>
                </div>
              </div>

              {/* Lighting & Preprocessing Diagnostic Card */}
              <div className="glass-panel" style={{ padding: 20 }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 12 }}>
                  <Cpu size={18} color="#38bdf8" />
                  <h4 style={{ fontSize: '0.92rem', color: '#f8fafc' }}>
                    Adaptive Lighting Robustness Diagnosis
                  </h4>
                </div>

                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: 10, fontSize: '0.78rem', marginBottom: 12 }}>
                  <div style={{ background: 'rgba(15, 23, 42, 0.6)', padding: 8, borderRadius: 6 }}>
                    <span style={{ color: '#94a3b8', display: 'block' }}>Sharpness</span>
                    <strong style={{ color: '#f8fafc' }}>{initMetrics.sharpness}</strong>
                  </div>
                  <div style={{ background: 'rgba(15, 23, 42, 0.6)', padding: 8, borderRadius: 6 }}>
                    <span style={{ color: '#94a3b8', display: 'block' }}>Brightness</span>
                    <strong style={{ color: '#f8fafc' }}>{initMetrics.brightness}</strong>
                  </div>
                  <div style={{ background: 'rgba(15, 23, 42, 0.6)', padding: 8, borderRadius: 6 }}>
                    <span style={{ color: '#94a3b8', display: 'block' }}>Contrast</span>
                    <strong style={{ color: '#f8fafc' }}>{initMetrics.contrast}</strong>
                  </div>
                  <div style={{ background: 'rgba(15, 23, 42, 0.6)', padding: 8, borderRadius: 6 }}>
                    <span style={{ color: '#94a3b8', display: 'block' }}>Exposure State</span>
                    <strong style={{ color: '#38bdf8', textTransform: 'capitalize' }}>{initMetrics.exposure_state || 'Normal'}</strong>
                  </div>
                </div>

                <div style={{ fontSize: '0.8rem', color: '#94a3b8' }}>
                  Applied Ops: {lighting.applied_operations?.length > 0 ? (
                    lighting.applied_operations.map((op, i) => (
                      <span key={i} style={{ background: 'rgba(56, 189, 248, 0.15)', color: '#38bdf8', padding: '2px 6px', borderRadius: 4, marginRight: 6, fontFamily: 'var(--font-mono)' }}>
                        {op}
                      </span>
                    ))
                  ) : (
                    <span style={{ color: '#10b981' }}>Standard exposure verified; no distortion detected.</span>
                  )}
                </div>
              </div>

              {/* Detected Defects List */}
              <div className="glass-panel" style={{ padding: 20 }}>
                <h4 style={{ fontSize: '0.92rem', color: '#f8fafc', marginBottom: 12 }}>
                  Detected Defect Instances
                </h4>

                <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
                  {result.detections.map((d, i) => (
                    <div
                      key={i}
                      onClick={() => setSelectedDamage(d)}
                      style={{
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'space-between',
                        padding: '10px 14px',
                        background: 'rgba(15, 23, 42, 0.6)',
                        borderRadius: 8,
                        border: '1px solid var(--border-subtle)',
                        cursor: 'pointer'
                      }}
                    >
                      <div>
                        <strong style={{ fontSize: '0.88rem', color: '#f8fafc', display: 'block' }}>{d.damage_type}</strong>
                        <span style={{ fontSize: '0.75rem', color: '#94a3b8' }}>
                          Confidence: {Math.round(d.confidence * 100)}% • Area: {Math.round(d.area_pixels)} px²
                        </span>
                      </div>
                      <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                        <SeverityBadge level={d.severity_level} score={d.severity_score} />
                        <PriorityBadge priority={d.priority} />
                      </div>
                    </div>
                  ))}
                </div>

                {/* Report Generation Actions */}
                <div style={{ display: 'flex', gap: 10, marginTop: 18 }}>
                  <button
                    className="btn-primary"
                    style={{ flex: 1, justifyContent: 'center' }}
                    onClick={() => handleDownloadReport('PDF')}
                    disabled={downloadingReport}
                  >
                    <Download size={16} /> Download PDF Audit Report
                  </button>
                  <button
                    className="btn-secondary"
                    onClick={() => handleDownloadReport('CSV')}
                    disabled={downloadingReport}
                  >
                    CSV
                  </button>
                  <button
                    className="btn-secondary"
                    onClick={() => handleDownloadReport('JSON')}
                    disabled={downloadingReport}
                  >
                    JSON
                  </button>
                </div>
              </div>
            </div>
          ) : (
            <div className="glass-panel" style={{
              height: '100%',
              minHeight: 450,
              display: 'flex',
              flexDirection: 'column',
              alignItems: 'center',
              justifyContent: 'center',
              padding: 40,
              textAlign: 'center',
              color: '#64748b'
            }}>
              <Eye size={48} style={{ marginBottom: 16, opacity: 0.4 }} />
              <h3 style={{ fontSize: '1.1rem', color: '#cbd5e1', marginBottom: 6 }}>
                Awaiting Inspection Telemetry
              </h3>
              <p style={{ fontSize: '0.85rem', maxWidth: 360 }}>
                Upload a road image or click one of the preset sample scenarios above to run automated segmentation and priority modeling.
              </p>
            </div>
          )}
        </div>
      </div>

      {/* Modal for explainability calibration */}
      {selectedDamage && (
        <DamageModal
          damage={selectedDamage}
          onClose={() => setSelectedDamage(null)}
        />
      )}
    </div>
  );
}
