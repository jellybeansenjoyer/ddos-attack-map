#!/usr/bin/env python3
"""
WebSocket Testing Script
Tests the WebSocket connection and streaming
"""

import asyncio
import websockets
import json
from datetime import datetime


async def test_websocket_attacks():
    """Test the attacks WebSocket endpoint"""
    uri = "ws://localhost:8000/ws/attacks"
    
    print("🔌 Connecting to WebSocket...")
    print(f"   URI: {uri}\n")
    
    try:
        async with websockets.connect(uri) as websocket:
            print("✅ Connected successfully!")
            print("📡 Listening for messages...\n")
            print("=" * 60)
            
            # Wait for messages
            message_count = 0
            timeout_seconds = 10
            
            try:
                async for message in websocket:
                    message_count += 1
                    data = json.loads(message)
                    
                    print(f"\n📨 Message #{message_count}")
                    print(f"   Type: {data.get('type', 'unknown')}")
                    print(f"   Timestamp: {data.get('timestamp', 'N/A')}")
                    
                    if data.get('type') == 'connected':
                        print(f"   Message: {data.get('message', 'N/A')}")
                        print("\n   ✅ Connection established!")
                        print(f"   ⏳ Waiting for attack messages (timeout: {timeout_seconds}s)...")
                    
                    elif data.get('type') == 'attack':
                        attack = data.get('data', {})
                        print(f"   🚨 ATTACK DETECTED!")
                        print(f"      IP: {attack.get('ip_address', 'N/A')}")
                        print(f"      Country: {attack.get('country_name', 'N/A')}")
                        print(f"      Classification: {attack.get('classification', 'N/A')}")
                        print(f"      Threat Score: {attack.get('threat_score', 'N/A')}")
                    
                    print("=" * 60)
                    
                    # Exit after receiving a few messages for testing
                    if message_count >= 5:
                        print("\n✅ Received 5 messages, test complete!")
                        break
                        
            except asyncio.TimeoutError:
                print(f"\n⏰ No new messages after {timeout_seconds} seconds")
                print("   This is normal if no new attacks are being added to database")
                
    except websockets.exceptions.WebSocketException as e:
        print(f"❌ WebSocket error: {e}")
        return False
    except ConnectionRefusedError:
        print("❌ Connection refused!")
        print("   Make sure the server is running on http://localhost:8000")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    return True


async def test_websocket_stats():
    """Test the stats WebSocket endpoint"""
    uri = "ws://localhost:8000/ws/stats"
    
    print("\n\n🔌 Testing Stats WebSocket...")
    print(f"   URI: {uri}\n")
    
    try:
        async with websockets.connect(uri) as websocket:
            print("✅ Connected successfully!")
            print("📡 Listening for stats updates...\n")
            print("=" * 60)
            
            # Receive a few messages
            for i in range(3):
                message = await asyncio.wait_for(websocket.recv(), timeout=6)
                data = json.loads(message)
                
                print(f"\n📊 Stats Update #{i+1}")
                print(f"   Type: {data.get('type', 'unknown')}")
                
                if data.get('type') == 'stats':
                    stats = data.get('data', {})
                    print(f"   Total Attacks: {stats.get('total_attacks', 'N/A')}")
                    print(f"   Timestamp: {stats.get('timestamp', 'N/A')}")
                
                print("=" * 60)
                
    except asyncio.TimeoutError:
        print("\n⏰ Timeout waiting for stats")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False
    
    return True


async def main():
    """Run all WebSocket tests"""
    print("\n" + "=" * 60)
    print("  WEBSOCKET CONNECTION TEST")
    print("=" * 60 + "\n")
    
    # Test attacks WebSocket
    success1 = await test_websocket_attacks()
    
    # Test stats WebSocket
    success2 = await test_websocket_stats()
    
    # Summary
    print("\n" + "=" * 60)
    print("  TEST SUMMARY")
    print("=" * 60)
    print(f"Attacks WebSocket: {'✅ PASS' if success1 else '❌ FAIL'}")
    print(f"Stats WebSocket:   {'✅ PASS' if success2 else '❌ FAIL'}")
    print()
    
    if success1 and success2:
        print("🎉 All WebSocket tests passed!")
        print("\nNote: If no attack messages appear, that's normal.")
        print("New attacks only stream when they're added to the database.")
        print("Try running: python3 seed_database.py --count 10")
        return 0
    else:
        print("⚠️  Some WebSocket tests failed")
        print("Check the errors above for details")
        return 1


if __name__ == "__main__":
    try:
        exit_code = asyncio.run(main())
        exit(exit_code)
    except KeyboardInterrupt:
        print("\n\n⚠️  Test cancelled by user")
        exit(1)
