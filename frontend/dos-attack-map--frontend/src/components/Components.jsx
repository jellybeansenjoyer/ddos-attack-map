import React from 'react'

/**
 * StatsPanel Component
 * Displays live statistics
 */
export function StatsPanel({ stats, loading }) {
  if (loading) {
    return (
      <div className="stats-panel">
        <h2>Statistics</h2>
        <div className="loading">Loading...</div>
      </div>
    )
  }
  
  if (!stats) {
    return (
      <div className="stats-panel">
        <h2>Statistics</h2>
        <div className="error">Failed to load stats</div>
      </div>
    )
  }
  
  return (
    <div className="stats-panel">
      <h2>📊 Live Statistics</h2>
      
      <div className="stats-grid">
        <StatCard
          label="Total Attacks"
          value={stats.total_attacks?.toLocaleString() || '0'}
          icon="🚨"
        />
        
        <StatCard
          label="Last 24 Hours"
          value={stats.attacks_24h?.toLocaleString() || '0'}
          icon="⏰"
        />
        
        <StatCard
          label="Last Hour"
          value={stats.attacks_1h?.toLocaleString() || '0'}
          icon="⚡"
        />
        
        <StatCard
          label="Unique IPs"
          value={stats.unique_ips?.toLocaleString() || '0'}
          icon="🌐"
        />
        
        <StatCard
          label="Avg Threat Score"
          value={stats.average_threat_score?.toFixed(1) || '0'}
          icon="⚠️"
        />
        
        <StatCard
          label="Top Type"
          value={stats.top_classification || 'N/A'}
          icon="🎯"
        />
      </div>
    </div>
  )
}

/**
 * StatCard Component
 * Individual stat card
 */
function StatCard({ label, value, icon }) {
  return (
    <div className="stat-card">
      <div className="stat-icon">{icon}</div>
      <div className="stat-content">
        <div className="stat-value">{value}</div>
        <div className="stat-label">{label}</div>
      </div>
    </div>
  )
}

/**
 * AttackFeed Component
 * Shows recent attacks in a list
 */
export function AttackFeed({ attacks }) {
  if (!attacks || attacks.length === 0) {
    return (
      <div className="attack-feed">
        <h2>🔴 Live Attacks</h2>
        <div className="no-attacks">
          Waiting for attacks...
        </div>
      </div>
    )
  }
  
  return (
    <div className="attack-feed">
      <h2>🔴 Live Attacks</h2>
      <div className="attack-list">
        {attacks.map((attack) => (
          <AttackItem key={attack.id} attack={attack} />
        ))}
      </div>
    </div>
  )
}

/**
 * AttackItem Component
 * Single attack in the feed
 */
function AttackItem({ attack }) {
  const getClassificationColor = (classification) => {
    const colors = {
      dos: '#ef4444',
      brute_force: '#f59e0b',
      scan: '#3b82f6',
      legitimate: '#4ade80'
    }
    return colors[classification] || '#9ca3af'
  }
  
  const getClassificationIcon = (classification) => {
    const icons = {
      dos: '💥',
      brute_force: '🔓',
      scan: '🔍',
      legitimate: '✅'
    }
    return icons[classification] || '⚠️'
  }
  
  const timeAgo = (timestamp) => {
    const seconds = Math.floor((new Date() - new Date(timestamp)) / 1000)
    if (seconds < 60) return `${seconds}s ago`
    if (seconds < 3600) return `${Math.floor(seconds / 60)}m ago`
    return `${Math.floor(seconds / 3600)}h ago`
  }
  
  return (
    <div className="attack-item">
      <div className="attack-icon" style={{ color: getClassificationColor(attack.classification) }}>
        {getClassificationIcon(attack.classification)}
      </div>
      <div className="attack-details">
        <div className="attack-header">
          <span className="attack-ip">{attack.ip_address}</span>
          <span className="attack-time">{timeAgo(attack.timestamp)}</span>
        </div>
        <div className="attack-info">
          <span className="attack-country">
            {attack.country_name || 'Unknown'}
          </span>
          <span 
            className="attack-classification"
            style={{ color: getClassificationColor(attack.classification) }}
          >
            {attack.classification || 'unknown'}
          </span>
        </div>
        <div className="attack-meta">
          <span className="threat-score">
            Threat: {attack.threat_score || 0}
          </span>
        </div>
      </div>
    </div>
  )
}

/**
 * Header Component
 * Top header with status
 */
export function Header({ isConnected, totalAttacks }) {
  return (
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
          {totalAttacks.toLocaleString()} Total Attacks
        </div>
      </div>
    </header>
  )
}

export default StatsPanel
