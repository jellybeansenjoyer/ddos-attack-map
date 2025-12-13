import { useState, useEffect, useRef, useCallback } from 'react'

/**
 * useWebSocket Hook
 * Manages WebSocket connection with auto-reconnect
 */
export function useWebSocket(url) {
  const [isConnected, setIsConnected] = useState(false)
  const [lastMessage, setLastMessage] = useState(null)
  const [error, setError] = useState(null)
  const wsRef = useRef(null)
  const reconnectTimeoutRef = useRef(null)
  const reconnectAttemptsRef = useRef(0)
  
  const MAX_RECONNECT_ATTEMPTS = 5
  const RECONNECT_DELAY = 3000
  
  const connect = useCallback(() => {
    try {
      // Close existing connection
      if (wsRef.current) {
        wsRef.current.close()
      }
      
      // Create new WebSocket
      const ws = new WebSocket(url)
      
      ws.onopen = () => {
        console.log('WebSocket connected:', url)
        setIsConnected(true)
        setError(null)
        reconnectAttemptsRef.current = 0
      }
      
      ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data)
          setLastMessage(data)
        } catch (err) {
          console.error('Failed to parse WebSocket message:', err)
        }
      }
      
      ws.onerror = (event) => {
        console.error('WebSocket error:', event)
        setError('Connection error')
      }
      
      ws.onclose = () => {
        console.log('WebSocket disconnected')
        setIsConnected(false)
        
        // Auto-reconnect
        if (reconnectAttemptsRef.current < MAX_RECONNECT_ATTEMPTS) {
          reconnectAttemptsRef.current++
          console.log(`Reconnecting... (attempt ${reconnectAttemptsRef.current})`)
          
          reconnectTimeoutRef.current = setTimeout(() => {
            connect()
          }, RECONNECT_DELAY)
        } else {
          setError('Failed to connect after multiple attempts')
        }
      }
      
      wsRef.current = ws
    } catch (err) {
      console.error('Failed to create WebSocket:', err)
      setError(err.message)
    }
  }, [url])
  
  // Connect on mount
  useEffect(() => {
    connect()
    
    // Cleanup on unmount
    return () => {
      if (reconnectTimeoutRef.current) {
        clearTimeout(reconnectTimeoutRef.current)
      }
      if (wsRef.current) {
        wsRef.current.close()
      }
    }
  }, [connect])
  
  // Send message
  const sendMessage = useCallback((message) => {
    if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify(message))
    }
  }, [])
  
  return {
    isConnected,
    lastMessage,
    lastAttack: lastMessage,
    error,
    sendMessage,
    reconnect: connect
  }
}

/**
 * useStats Hook
 * Fetches statistics from API
 */
export function useStats(refreshInterval = 5000) {
  const [stats, setStats] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  
  const fetchStats = useCallback(async () => {
    try {
      const response = await fetch('http://localhost:8000/api/stats/summary')
      if (!response.ok) {
        throw new Error('Failed to fetch stats')
      }
      const data = await response.json()
      setStats(data)
      setError(null)
    } catch (err) {
      console.error('Error fetching stats:', err)
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }, [])
  
  useEffect(() => {
    fetchStats()
    
    // Refresh stats periodically
    const interval = setInterval(fetchStats, refreshInterval)
    
    return () => clearInterval(interval)
  }, [fetchStats, refreshInterval])
  
  return { stats, loading, error, refetch: fetchStats }
}

export { useWebSocket, useStats }
export default useWebSocket
