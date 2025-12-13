import React, { useState, useEffect, Suspense } from 'react'
import { Canvas } from '@react-three/fiber'
import { OrbitControls, PerspectiveCamera } from '@react-three/drei'
import { Earth, Stars, AttackArc, AttackMarker } from './components/Globe'
import { StatsPanel, AttackFeed, Header, ThreatRadar, MatrixRain } from './components/CyberpunkComponents'
import './App-Cyberpunk.css'

function App() {
  // State
  const [attacks, setAttacks] = useState([])
  const [isPaused, setIsPaused] = useState(false)
  const [rotationSpeed, setRotationSpeed] = useState(0.001)
  const [maxAttacks, setMaxAttacks] = useState(50)
  const [isConnected, setIsConnected] = useState(false)
  const [stats, setStats] = useState(null)
  const [wsError, setWsError] = useState(null)
  const [threatLevel, setThreatLevel] = useState('HIGH')
  
  // WebSocket connection
  useEffect(() => {
    const ws = new WebSocket('ws://localhost:8000/ws/attacks')
    
    ws.onopen = () => {
      console.log('WebSocket connected')
      setIsConnected(true)
      setWsError(null)
    }
    
    ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data)
        
        if (data.type === 'attack') {
          const newAttack = {
            ...data.data,
            id: Date.now() + Math.random(),
            timestamp: new Date()
          }
          
          setAttacks(prev => {
            const updated = [newAttack, ...prev]
            return updated.slice(0, maxAttacks)
          })
        }
      } catch (err) {
        console.error('Error parsing WebSocket message:', err)
      }
    }
    
    ws.onerror = (error) => {
      console.error('WebSocket error:', error)
      setWsError('Connection error')
    }
    
    ws.onclose = () => {
      console.log('WebSocket disconnected')
      setIsConnected(false)
    }
    
    return () => {
      ws.close()
    }
  }, [maxAttacks])
  
  // Fetch statistics
  useEffect(() => {
    const fetchStats = async () => {
      try {
        const response = await fetch('http://localhost:8000/api/stats/summary')
        const data = await response.json()
        setStats(data)
        
        // Calculate threat level based on recent attacks
        if (data.attacks_1h > 100) setThreatLevel('CRITICAL')
        else if (data.attacks_1h > 50) setThreatLevel('HIGH')
        else if (data.attacks_1h > 20) setThreatLevel('MEDIUM')
        else setThreatLevel('LOW')
      } catch (err) {
        console.error('Error fetching stats:', err)
      }
    }
    
    fetchStats()
    const interval = setInterval(fetchStats, 5000)
    
    return () => clearInterval(interval)
  }, [])
  
  // Remove old attacks
  useEffect(() => {
    const interval = setInterval(() => {
      const now = Date.now()
      setAttacks(prev => 
        prev.filter(attack => {
          const age = now - new Date(attack.timestamp).getTime()
          return age < 5000
        })
      )
    }, 1000)
    
    return () => clearInterval(interval)
  }, [])
  
  const recentAttacks = attacks.slice(0, 10)
  
  return (
    <div className="app">
      {/* Matrix Rain Background */}
      <MatrixRain />
      
      {/* Header */}
      <header className="app-header">
        <div className="header-left">
          <h1 data-text="⚡ DOS ATTACK MAP">⚡ DOS ATTACK MAP</h1>
          <div className="subtitle">Real-time Global Threat Intelligence</div>
        </div>
        
        <div className="header-right">
          <div className="threat-level">
            <span className="threat-level-text">THREAT LEVEL: {threatLevel}</span>
          </div>
          
          <div className={`live-indicator ${isConnected ? 'live' : 'offline'}`}>
            <span className="pulse-dot"></span>
            {isConnected ? 'LIVE' : 'OFFLINE'}
          </div>
          
          <div className="total-count">
            {stats?.total_attacks?.toLocaleString() || '0'} ATTACKS
          </div>
        </div>
      </header>
      
      <div className="main-container">
        {/* 3D Globe */}
        <div className="globe-container">
          <Suspense fallback={
            <div className="globe-loading">
              <h2>▓▓▓ INITIALIZING GLOBE ▓▓▓</h2>
              <p>LOADING EARTH TEXTURES...</p>
            </div>
          }>
            <Canvas>
              <PerspectiveCamera
                makeDefault
                position={[0, 0, 2.5]}
                fov={45}
              />
              
              {/* Lights with neon glow */}
              <ambientLight intensity={0.2} />
              <pointLight position={[10, 10, 10]} intensity={1} color="#00FFFF" />
              <pointLight position={[-10, -10, -10]} intensity={0.5} color="#FF00FF" />
              <pointLight position={[0, 10, -10]} intensity={0.3} color="#FFFF00" />
              
              <Stars count={5000} />
              <Earth rotationSpeed={isPaused ? 0 : rotationSpeed} />
              
              {/* Attack arcs with neon glow */}
              {attacks.map(attack => (
                <AttackArc
                  key={attack.id}
                  attack={attack}
                  duration={3000}
                />
              ))}
              
              {/* Attack markers */}
              {recentAttacks.map(attack => (
                <AttackMarker
                  key={`marker-${attack.id}`}
                  attack={attack}
                />
              ))}
              
              <OrbitControls
                enableZoom={true}
                enablePan={false}
                minDistance={1.5}
                maxDistance={4}
                autoRotate={false}
              />
            </Canvas>
          </Suspense>
          
          {/* Globe controls */}
          <div className="globe-controls">
            <button 
              onClick={() => setIsPaused(!isPaused)}
              className="control-btn"
            >
              {isPaused ? '▶ PLAY' : '⏸ PAUSE'}
            </button>
            
            <div className="speed-control">
              <label>SPEED</label>
              <input
                type="range"
                min="0.0005"
                max="0.003"
                step="0.0005"
                value={rotationSpeed}
                onChange={(e) => setRotationSpeed(parseFloat(e.target.value))}
              />
              <span>{(rotationSpeed / 0.001).toFixed(1)}x</span>
            </div>
            
            <div className="attack-count">
              ACTIVE: {attacks.length}/{maxAttacks}
            </div>
          </div>
        </div>
        
        {/* Sidebar */}
        <div className="sidebar">
          {/* Threat Radar */}
          <ThreatRadar threatLevel={threatLevel} />
          
          {/* Statistics Panel */}
          <StatsPanel stats={stats} loading={!stats} />
          
          {/* Live Attack Feed */}
          <AttackFeed attacks={recentAttacks} />
          
          {/* Connection Status */}
          <div className="connection-status cyber-panel">
            <div className={`status-indicator ${isConnected ? 'connected' : 'disconnected'}`}>
              <span className="status-dot"></span>
              {isConnected ? 'SYSTEM ONLINE' : 'SYSTEM OFFLINE'}
            </div>
            {wsError && (
              <div className="error-message">⚠ {wsError}</div>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}

export default App
