import React, { useState } from 'react';
import Navbar from './components/Navbar';
import OverviewPage from './pages/OverviewPage';
import LiveDetectionPage from './pages/LiveDetectionPage';
import UploadPage from './pages/UploadPage';
import DamageMapPage from './pages/DamageMapPage';
import ReportsPage from './pages/ReportsPage';
import AnalyticsPage from './pages/AnalyticsPage';
import LoginPage from './pages/LoginPage';

export default function App() {
  const [isLoggedIn, setIsLoggedIn] = useState(false);
  const [activeTab, setActiveTab] = useState('overview');

  if (!isLoggedIn) {
    return <LoginPage onLogin={() => setIsLoggedIn(true)} />;
  }

  return (
    <div style={{ minHeight: '100vh', display: 'flex', flexDirection: 'column' }}>
      <Navbar activeTab={activeTab} setActiveTab={setActiveTab} />

      <main style={{ flex: 1 }}>
        {activeTab === 'overview' && <OverviewPage onNavigate={setActiveTab} />}
        {activeTab === 'live' && <LiveDetectionPage />}
        {activeTab === 'upload' && <UploadPage onNavigate={setActiveTab} />}
        {activeTab === 'map' && <DamageMapPage />}
        {activeTab === 'reports' && <ReportsPage />}
        {activeTab === 'analytics' && <AnalyticsPage />}
      </main>

      <footer style={{
        borderTop: '1px solid var(--border-subtle)',
        padding: '20px 24px',
        textAlign: 'center',
        fontSize: '0.8rem',
        color: '#64748b',
        background: 'rgba(8, 12, 20, 0.9)'
      }}>
        <div style={{ maxWidth: 1600, margin: '0 auto', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <span>
            <strong>RoadDamageAI</strong> • Hackathon Solution for Problem M15 – Intelligent Road Damage Detection
          </span>
          <span>
            Ultralytics YOLO Segmentation • ByteTrack Tracking • CLAHE Preprocessing • Leaflet GIS
          </span>
        </div>
      </footer>
    </div>
  );
}
