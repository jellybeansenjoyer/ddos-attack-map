import React, { useState, useEffect, Suspense } from 'react'
import { Canvas } from '@react-three/fiber'
import { OrbitControls, PerspectiveCamera } from '@react-three/drei'
import { Earth, Stars, AttackArc, AttackMarker } from './components/Globe'
import { StatsPanel, AttackFeed, Header } from './components/Components'
import './App.css'

function App() {
  // State
  const [attacks, setAttacks] = useState([])
  const [isPaused, setIsPaused] = useState(false)
  const [rotationSpeed, setRotationSpeed] = useState(0.001)
  const [maxAttacks, setMaxAttacks] = useState(50)
  const [isConnected, setIsConnected] = useState(false)
  const [stats, setStats] = useState(null)
  const [wsError, setWsError] = useState(null)
  
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
      
      // Auto-reconnect after 3 seconds
      setTimeout(() => {
        console.log('Attempting to reconnect...')
        // Component will remount and reconnect
      }, 3000)
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
      } catch (err) {
        console.error('Error fetching stats:', err)
      }
    }
    
    fetchStats()
    
    // Refresh stats every 5 seconds
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
          return age < 5000 // Keep for 5 seconds
        })
      )
    }, 1000)
    
    return () => clearInterval(interval)
  }, [])
  
  // Recent attacks for feed (last 10)
  const recentAttacks = attacks.slice(0, 10)
  
  return (
    <div className="app">
      {/* Header */}
      <Header 
        isConnected={isConnected}
        totalAttacks={stats?.total_attacks || 0}
      />
      
      <div className="main-container">
        {/* 3D Globe */}
        <div className="globe-container">
          <Suspense fallback={
            <div className="globe-loading">
              <h2>🌍 Loading Earth...</h2>
              <p>Downloading textures...</p>
            </div>
          }>
            <Canvas>
              {/* Camera */}
              <PerspectiveCamera
                makeDefault
                position={[0, 0, 2.5]}
                fov={45}
              />
              
              {/* Lights */}
              <ambientLight intensity={0.3} />
              <pointLight position={[10, 10, 10]} intensity={1} />
              <pointLight position={[-10, -10, -10]} intensity={0.5} />
              
              {/* Stars background */}
              <Stars count={5000} />
              
              {/* Earth */}
              <Earth rotationSpeed={isPaused ? 0 : rotationSpeed} />
              
              {/* Attack arcs */}
              {attacks.map(attack => (
                <AttackArc
                  key={attack.id}
                  attack={attack}
                  duration={3000}
                />
              ))}
              
              {/* Attack markers on recent attacks */}
              {recentAttacks.map(attack => (
                <AttackMarker
                  key={`marker-${attack.id}`}
                  attack={attack}
                />
              ))}
              
              {/* Controls */}
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
              {isPaused ? '▶️ Play' : '⏸️ Pause'}
            </button>
            
            <div className="speed-control">
              <label>Speed:</label>
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
              Active: {attacks.length}/{maxAttacks}
            </div>
          </div>
        </div>
        
        {/* Sidebar */}
        <div className="sidebar">
          {/* Statistics Panel */}
          <StatsPanel stats={stats} loading={!stats} />
          
          {/* Live Attack Feed */}
          <AttackFeed attacks={recentAttacks} />
          
          {/* Connection Status */}
          <div className="connection-status">
            <div className={`status-indicator ${isConnected ? 'connected' : 'disconnected'}`}>
              <span className="status-dot"></span>
              {isConnected ? 'WebSocket Connected' : 'WebSocket Disconnected'}
            </div>
            {wsError && (
              <div className="error-message">{wsError}</div>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}

export default App
