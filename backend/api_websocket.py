"""
WebSocket Router
Real-time attack streaming via WebSocket
"""

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from typing import List
import asyncio
import json
from datetime import datetime, timezone

from app_database import get_session
from app_models import Attack

router = APIRouter()


class ConnectionManager:
    """Manages WebSocket connections"""
    
    def __init__(self):
        self.active_connections: List[WebSocket] = []
    
    async def connect(self, websocket: WebSocket):
        """Accept new connection"""
        await websocket.accept()
        self.active_connections.append(websocket)
        print(f"✅ WebSocket connected. Total connections: {len(self.active_connections)}")
    
    def disconnect(self, websocket: WebSocket):
        """Remove connection"""
        self.active_connections.remove(websocket)
        print(f"❌ WebSocket disconnected. Total connections: {len(self.active_connections)}")
    
    async def broadcast(self, message: dict):
        """Broadcast message to all connections"""
        disconnected = []
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except Exception as e:
                print(f"Error sending to connection: {e}")
                disconnected.append(connection)
        
        # Remove disconnected clients
        for conn in disconnected:
            if conn in self.active_connections:
                self.active_connections.remove(conn)
    
    async def send_personal(self, message: dict, websocket: WebSocket):
        """Send message to specific connection"""
        try:
            await websocket.send_json(message)
        except Exception as e:
            print(f"Error sending personal message: {e}")


manager = ConnectionManager()


async def stream_attacks(websocket: WebSocket):
    """
    Stream attacks to WebSocket client
    Sends new attacks as they appear in database
    """
    last_id = 0
    
    while True:
        try:
            # Get session
            session = get_session()
            
            # Query new attacks
            new_attacks = session.query(Attack).filter(
                Attack.id > last_id
            ).order_by(Attack.id).limit(10).all()
            
            # Send new attacks
            for attack in new_attacks:
                attack_data = attack.to_dict()
                await websocket.send_json({
                    "type": "attack",
                    "data": attack_data,
                    "timestamp": datetime.now(timezone.utc).isoformat()
                })
                last_id = attack.id
            
            session.close()
            
            # Wait before next check (1 second)
            await asyncio.sleep(1)
            
        except WebSocketDisconnect:
            print("Client disconnected from stream")
            break
        except Exception as e:
            print(f"Error in stream: {e}")
            await asyncio.sleep(5)


@router.websocket("/attacks")
async def websocket_attacks(websocket: WebSocket):
    """
    WebSocket endpoint for real-time attack streaming
    
    Client connection:
    ws://localhost:8000/ws/attacks
    
    Message format:
    {
        "type": "attack",
        "data": {
            "id": 123,
            "ip_address": "192.0.2.1",
            "timestamp": "2025-12-13T10:30:00Z",
            "latitude": 40.7128,
            "longitude": -74.0060,
            "country_code": "US",
            "country_name": "United States",
            "classification": "dos",
            "threat_score": 85
        },
        "timestamp": "2025-12-13T10:30:01Z"
    }
    """
    await manager.connect(websocket)
    
    try:
        # Send welcome message
        await websocket.send_json({
            "type": "connected",
            "message": "Connected to DOS Attack Map stream",
            "timestamp": datetime.now(timezone.utc).isoformat()
        })
        
        # Start streaming attacks
        await stream_attacks(websocket)
        
    except WebSocketDisconnect:
        manager.disconnect(websocket)
        print("WebSocket disconnected")
    except Exception as e:
        print(f"WebSocket error: {e}")
        manager.disconnect(websocket)


@router.websocket("/stats")
async def websocket_stats(websocket: WebSocket):
    """
    WebSocket endpoint for real-time statistics
    Sends updated stats every 5 seconds
    """
    await manager.connect(websocket)
    
    try:
        await websocket.send_json({
            "type": "connected",
            "message": "Connected to statistics stream"
        })
        
        while True:
            # Get stats from database
            session = get_session()
            
            from sqlalchemy import func
            total_attacks = session.query(func.count(Attack.id)).scalar()
            
            # Send stats
            await websocket.send_json({
                "type": "stats",
                "data": {
                    "total_attacks": total_attacks or 0,
                    "timestamp": datetime.now(timezone.utc).isoformat()
                }
            })
            
            session.close()
            
            # Wait 5 seconds
            await asyncio.sleep(5)
            
    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception as e:
        print(f"Stats WebSocket error: {e}")
        manager.disconnect(websocket)
