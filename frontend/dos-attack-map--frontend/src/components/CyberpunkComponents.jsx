import React, { useEffect, useRef } from 'react'

/**
 * MatrixRain Component
 * Creates falling matrix-style characters in background
 */
export function MatrixRain() {
  const canvasRef = useRef(null)
  
  useEffect(() => {
    const canvas = canvasRef.current
    if (!canvas) return
    
    const ctx = canvas.getContext('2d')
    canvas.width = window.innerWidth
    canvas.height = window.innerHeight
    
    const chars = '01アイウエオカキクケコサシスセソタチツテトナニヌネノ'
    const fontSize = 14
    const columns = canvas.width / fontSize
    const drops = []
    
    for (let i = 0; i < columns; i++) {
      drops[i] = Math.random() * -100
    }
    
    function draw() {
      ctx.fillStyle = 'rgba(13, 2, 33, 0.05)'
      ctx.fillRect(0, 0, canvas.width, canvas.height)
      
      ctx.fillStyle = '#00FFFF'
      ctx.font = fontSize + 'px monospace'
      
      for (let i = 0; i < drops.length; i++) {
        const text = chars[Math.floor(Math.random() * chars.length)]
        ctx.fillText(text, i * fontSize, drops[i] * fontSize)
        
        if (drops[i] * fontSize > canvas.height && Math.random() > 0.975) {
          drops[i] = 0
        }
        drops[i]++
      }
    }
    
    const interval = setInterval(draw, 33)
    
    const handleResize = () => {
      canvas.width = window.innerWidth
      canvas.height = window.innerHeight
    }
    
    window.addEventListener('resize', handleResize)
    
    return () => {
      clearInterval(interval)
      window.removeEventListener('resize', handleResize)
    }
  }, [])
  
  return (
    <canvas
      ref={canvasRef}
      className="matrix-bg"
      style={{
        position: 'fixed',
        top: 0,
        left: 0,
        zIndex: 0,
        opacity: 0.15
      }}
    />
  )
}

/**
 * ThreatRadar Component
 * Animated radar display
 */
export function ThreatRadar({ threatLevel }) {
  return (
    <div className="cyber-panel" style={{ textAlign: 'center' }}>
      <h3 style={{
        fontFamily: "'Orbitron', sans-serif",
        fontSize: '14px',
        color: '#39FF14',
        textShadow: '0 0 10px #39FF14',
        marginBottom: '16px',
        letterSpacing: '2px'
      }}>
        ◢◤ THREAT RADAR ◢◤
      </h3>
      <div className="threat-radar">
        {/* Radar rings */}
        {[1, 2, 3].map((ring) => (
          <div
            key={ring}
            style={{
              position: 'absolute',
              top: '50%',
              left: '50%',
              width: `${ring * 30}%`,
              height: `${ring * 30}%`,
              border: '1px solid rgba(57, 255, 20, 0.3)',
              borderRadius: '50%',
              transform: 'translate(-50%, -50%)'
            }}
          />
        ))}
      </div>
      <div style={{
        marginTop: '12px',
        fontFamily: "'Orbitron', sans-serif",
        fontSize: '12px',
        color: '#FFFF00',
        textShadow: '0 0 10px #FFFF00',
        letterSpacing: '1px'
      }}>
        STATUS: {threatLevel}
      </div>
    </div>
  )
}

/**
 * StatsPanel Component (Cyberpunk themed)
 */
export function StatsPanel({ stats, loading }) {
  if (loading) {
    return (
      <div className="stats-panel cyber-panel">
        <h2>▓▓▓ SYSTEM STATS</h2>
        <div className="loading"></div>
      </div>
    )
  }
  
  if (!stats) {
    return (
      <div className="stats-panel cyber-panel">
        <h2>▓▓▓ SYSTEM STATS</h2>
        <div style={{ textAlign: 'center', padding: '24px', color: '#FF00FF' }}>
          ERROR: DATA UNAVAILABLE
        </div>
      </div>
    )
  }
  
  return (
    <div className="stats-panel cyber-panel">
      <h2>▓▓▓ SYSTEM STATS</h2>
      
      <div className="stats-grid">
        <StatCard
          label="TOTAL ATTACKS"
          value={stats.total_attacks?.toLocaleString() || '0'}
          icon="🚨"
        />
        
        <StatCard
          label="LAST 24H"
          value={stats.attacks_24h?.toLocaleString() || '0'}
          icon="⏰"
        />
        
        <StatCard
          label="LAST HOUR"
          value={stats.attacks_1h?.toLocaleString() || '0'}
          icon="⚡"
        />
        
        <StatCard
          label="UNIQUE IPs"
          value={stats.unique_ips?.toLocaleString() || '0'}
          icon="🌐"
        />
        
        <StatCard
          label="AVG THREAT"
          value={stats.average_threat_score?.toFixed(1) || '0'}
          icon="⚠️"
        />
        
        <StatCard
          label="TOP TYPE"
          value={stats.top_classification?.toUpperCase() || 'N/A'}
          icon="🎯"
        />
      </div>
    </div>
  )
}

/**
 * StatCard Component
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
 * AttackFeed Component (Cyberpunk themed)
 */
export function AttackFeed({ attacks }) {
  if (!attacks || attacks.length === 0) {
    return (
      <div className="attack-feed cyber-panel">
        <h2>◢◤ LIVE FEED</h2>
        <div className="no-attacks">
          &gt;_ MONITORING FOR THREATS...
        </div>
      </div>
    )
  }
  
  return (
    <div className="attack-feed cyber-panel">
      <h2>◢◤ LIVE FEED</h2>
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
 */
function AttackItem({ attack }) {
  const getClassificationColor = (classification) => {
    const colors = {
      dos: '#FF00FF',           // Magenta
      brute_force: '#FF10F0',   // Pink
      scan: '#00F0FF',          // Cyan
      legitimate: '#39FF14'     // Green
    }
    return colors[classification] || '#00FFFF'
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
    if (seconds < 60) return `${seconds}s`
    if (seconds < 3600) return `${Math.floor(seconds / 60)}m`
    return `${Math.floor(seconds / 3600)}h`
  }
  
  const color = getClassificationColor(attack.classification)
  
  return (
    <div className="attack-item" style={{ borderLeftColor: color }}>
      <div className="attack-icon" style={{ color }}>
        {getClassificationIcon(attack.classification)}
      </div>
      <div className="attack-details">
        <div className="attack-header">
          <span className="attack-ip">{attack.ip_address}</span>
          <span className="attack-time">{timeAgo(attack.timestamp)}</span>
        </div>
        <div className="attack-info">
          <span className="attack-country">
            {attack.country_name || 'UNKNOWN'}
          </span>
          <span 
            className="attack-classification"
            style={{ 
              color,
              borderColor: color
            }}
          >
            {attack.classification?.toUpperCase() || 'UNKNOWN'}
          </span>
        </div>
        <div className="attack-meta">
          <span className="threat-score">
            THREAT: {attack.threat_score || 0}
          </span>
        </div>
      </div>
    </div>
  )
}

/**
 * Header Component (Cyberpunk themed)
 */
export function Header({ isConnected, totalAttacks }) {
  // Already included in main App component
  return null
}

export default StatsPanel
