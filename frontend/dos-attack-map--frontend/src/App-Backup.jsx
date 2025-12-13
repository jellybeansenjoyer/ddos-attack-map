import React, { useState, useEffect } from 'react'
import './App.css'

// Simple test component first
function App() {
  const [isConnected, setIsConnected] = useState(false)
  const [stats, setStats] = useState(null)
  const [attacks, setAttacks] = useState([])

  // Test API connection
  useEffect(() => {
    fetch('http://localhost:8000/health')
      .then(res => res.json())
      .then(data => {
        console.log('API Health:', data)
        setIsConnected(true)
      })
      .catch(err => {
        console.error('API Error:', err)
      })
  }, [])

  // Fetch stats
  useEffect(() => {
    fetch('http://localhost:8000/api/stats/summary')
      .then(res => res.json())
      .then(data => {
        console.log('Stats:', data)
        setStats(data)
      })
      .catch(err => {
        console.error('Stats Error:', err)
      })
  }, [])

  return (
    <div className="app">
      <header className="app-header">
        <div className="header-left">
          <h1>🌍 DOS Attack Map</h1>
          <div className="subtitle">Real-time Global Attack Visualization</div>
        </div>
        
        <div className="header-right">
          <div className={`live-indicator ${isConnected ? 'live' : 'offline'}`}>
            <span className="pulse-dot"></span>
            {isConnected ? 'LIVE' : 'OFFLINE'}
          </div>
          
          <div className="total-count">
            {stats?.total_attacks?.toLocaleString() || '0'} Total Attacks
          </div>
        </div>
      </header>

      <div className="main-container">
        {/* Placeholder for globe */}
        <div className="globe-container">
          <div className="globe-placeholder">
            <h2>🌍 3D Globe</h2>
            <p>Globe will appear here</p>
            <p>Connection: {isConnected ? '✅ Connected' : '❌ Disconnected'}</p>
          </div>
        </div>

        {/* Sidebar */}
        <div className="sidebar">
          {/* Stats */}
          <div className="stats-panel">
            <h2>📊 Live Statistics</h2>
            {stats ? (
              <div className="stats-grid">
                <div className="stat-card">
                  <div className="stat-icon">🚨</div>
                  <div className="stat-content">
                    <div className="stat-value">{stats.total_attacks?.toLocaleString()}</div>
                    <div className="stat-label">Total Attacks</div>
                  </div>
                </div>
                
                <div className="stat-card">
                  <div className="stat-icon">⏰</div>
                  <div className="stat-content">
                    <div className="stat-value">{stats.attacks_24h?.toLocaleString()}</div>
                    <div className="stat-label">Last 24 Hours</div>
                  </div>
                </div>
                
                <div className="stat-card">
                  <div className="stat-icon">🌐</div>
                  <div className="stat-content">
                    <div className="stat-value">{stats.unique_ips?.toLocaleString()}</div>
                    <div className="stat-label">Unique IPs</div>
                  </div>
                </div>
                
                <div className="stat-card">
                  <div className="stat-icon">⚡</div>
                  <div className="stat-content">
                    <div className="stat-value">{stats.attacks_1h?.toLocaleString()}</div>
                    <div className="stat-label">Last Hour</div>
                  </div>
                </div>
              </div>
            ) : (
              <div className="loading">Loading stats...</div>
            )}
          </div>

          {/* Connection Status */}
          <div className="connection-status">
            <div className={`status-indicator ${isConnected ? 'connected' : 'disconnected'}`}>
              <span className="status-dot"></span>
              {isConnected ? 'API Connected' : 'API Disconnected'}
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}

export default App
