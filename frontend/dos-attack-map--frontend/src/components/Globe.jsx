import React, { useRef, useMemo } from 'react'
import { useFrame, useLoader } from '@react-three/fiber'
import { TextureLoader } from 'three'
import * as THREE from 'three'

/**
 * Earth Component
 * Renders the 3D Earth sphere with realistic textures
 */
export function Earth({ rotationSpeed = 0.001 }) {
  const earthRef = useRef()
  
  // Load Earth textures
  // Note: Place these textures in public/textures/
  const [dayTexture, nightTexture, cloudsTexture] = useLoader(TextureLoader, [
    '/textures/earth-day.jpg',
    '/textures/earth-night.jpg',
    '/textures/earth-clouds.jpg'
  ])
  
  // Rotate Earth
  useFrame(() => {
    if (earthRef.current) {
      earthRef.current.rotation.y += rotationSpeed
    }
  })
  
  return (
    <group ref={earthRef}>
      {/* Main Earth sphere */}
      <mesh>
        <sphereGeometry args={[1, 64, 64]} />
        <meshPhongMaterial
          map={dayTexture}
          emissiveMap={nightTexture}
          emissive={0x112244}
          emissiveIntensity={0.3}
          shininess={10}
        />
      </mesh>
      
      {/* Cloud layer */}
      <mesh>
        <sphereGeometry args={[1.01, 64, 64]} />
        <meshPhongMaterial
          map={cloudsTexture}
          transparent={true}
          opacity={0.4}
          depthWrite={false}
        />
      </mesh>
    </group>
  )
}

/**
 * Stars Component
 * Creates a starfield background
 */
export function Stars({ count = 5000 }) {
  const points = useMemo(() => {
    const p = new Array(count).fill(0).map(() => ({
      position: [
        (Math.random() - 0.5) * 50,
        (Math.random() - 0.5) * 50,
        (Math.random() - 0.5) * 50
      ]
    }))
    return p
  }, [count])
  
  return (
    <group>
      {points.map((point, i) => (
        <mesh key={i} position={point.position}>
          <sphereGeometry args={[0.01, 4, 4]} />
          <meshBasicMaterial color="#ffffff" />
        </mesh>
      ))}
    </group>
  )
}

/**
 * AttackArc Component
 * Animates an arc from source to target
 */
export function AttackArc({ attack, duration = 2000 }) {
  const arcRef = useRef()
  const startTime = useRef(Date.now())
  
  // Convert lat/lon to 3D coordinates
  const sourcePos = latLonToVector3(
    attack.latitude || 0,
    attack.longitude || 0,
    1.05
  )
  
  // Target is always center (simplified)
  const targetPos = new THREE.Vector3(0, 0, 0)
  
  // Calculate arc control point (higher arc)
  const controlPos = sourcePos.clone().multiplyScalar(1.5)
  
  // Create curve
  const curve = useMemo(() => {
    return new THREE.QuadraticBezierCurve3(
      sourcePos,
      controlPos,
      targetPos
    )
  }, [])
  
  // Get color based on classification
  const color = getAttackColor(attack.classification)
  
  // Animate along curve
  useFrame(() => {
    const elapsed = Date.now() - startTime.current
    const progress = Math.min(elapsed / duration, 1)
    
    if (arcRef.current) {
      // Update position along curve
      const position = curve.getPoint(progress)
      arcRef.current.position.copy(position)
      
      // Fade out as it approaches target
      arcRef.current.material.opacity = 1 - progress
      
      // Scale up slightly as it travels
      const scale = 1 + progress * 0.5
      arcRef.current.scale.set(scale, scale, scale)
    }
  })
  
  return (
    <mesh ref={arcRef}>
      <sphereGeometry args={[0.02, 8, 8]} />
      <meshBasicMaterial
        color={color}
        transparent
        opacity={1}
      />
    </mesh>
  )
}

/**
 * AttackMarker Component
 * Places a marker on the globe at attack location
 */
export function AttackMarker({ attack }) {
  const markerRef = useRef()
  const pulsePhase = useRef(0)
  
  // Convert lat/lon to 3D position
  const position = latLonToVector3(
    attack.latitude || 0,
    attack.longitude || 0,
    1.02
  )
  
  const color = getAttackColor(attack.classification)
  
  // Pulse animation
  useFrame((state, delta) => {
    if (markerRef.current) {
      pulsePhase.current += delta * 2
      const scale = 1 + Math.sin(pulsePhase.current) * 0.3
      markerRef.current.scale.set(scale, scale, scale)
    }
  })
  
  return (
    <mesh ref={markerRef} position={position}>
      <sphereGeometry args={[0.01, 8, 8]} />
      <meshBasicMaterial color={color} />
    </mesh>
  )
}

/**
 * Utility Functions
 */

// Convert latitude/longitude to 3D vector
function latLonToVector3(lat, lon, radius) {
  const phi = (90 - lat) * (Math.PI / 180)
  const theta = (lon + 180) * (Math.PI / 180)
  
  const x = -(radius * Math.sin(phi) * Math.cos(theta))
  const y = radius * Math.cos(phi)
  const z = radius * Math.sin(phi) * Math.sin(theta)
  
  return new THREE.Vector3(x, y, z)
}

// Get color based on attack classification
function getAttackColor(classification) {
  const colors = {
    dos: '#ef4444',           // Red
    brute_force: '#f59e0b',   // Orange
    scan: '#3b82f6',          // Blue
    legitimate: '#4ade80'     // Green
  }
  return colors[classification] || '#ffffff'
}

export default Earth
