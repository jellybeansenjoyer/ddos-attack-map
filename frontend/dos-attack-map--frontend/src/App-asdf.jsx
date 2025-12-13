import React, { useState, useEffect } from 'react'
import { Canvas } from '@react-three/fiber'
import { OrbitControls, PerspectiveCamera } from '@react-three/drei'
import { Earth, Stars, AttackArc, AttackMarker } from './components/Globe'
import { StatsPanel, AttackFeed, Header } from './components/Components'
import { useWebSocket, useStats } from './hooks/useWebSocket'
import './App.css'

function App() {
  // State
  const [attacks, setAttacks] = useState([])
  const [isPaused, setIsPaused] = useState(false)
  const [rotationSpeed, setRotationSpeed] = useState(0.001)
  const [maxAttacks, setMaxAttacks] = useState(50)
  
  // WebSocket connection
  const { 
    isConnected, 
    lastAttack, 
    error 
  } = useWebSocket('ws://localhost:8000/ws/attacks')
  
  // Statistics
  const { stats, loading: statsLoading } = useStats()
  
  // Add new attack from WebSocket
  useEffect(() => {
    if (lastAttack && lastAttack.type === 'attack') {
      const newAttack = {
        ...lastAttack.data,
        id: Date.now(),
        timestamp: new Date()
      }
      
      setAttacks(prev => {
        const updated = [newAttack, ...prev]
        // Limit number of active attacks for performance
        return updated.slice(0, maxAttacks)
      })
    }
  }, [lastAttack, maxAttacks])
  
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
  
  // Calculate recent attacks (last 5 minutes)
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
          </div>
        </div>
        
        {/* Sidebar */}
        <div className="sidebar">
          {/* Statistics Panel */}
          <StatsPanel stats={stats} loading={statsLoading} />
          
          {/* Live Attack Feed */}
          <AttackFeed attacks={recentAttacks} />
          
          {/* Connection Status */}
          <div className="connection-status">
            <div className={`status-indicator ${isConnected ? 'connected' : 'disconnected'}`}>
              <span className="status-dot"></span>
              {isConnected ? 'Connected' : 'Disconnected'}
            </div>
            {error && (
              <div className="error-message">{error}</div>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}

export default App
