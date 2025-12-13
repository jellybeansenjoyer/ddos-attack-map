#!/usr/bin/env python3
"""
Run FastAPI Development Server
Simple script to start the API server
"""

import os
import sys

# Add backend directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def main():
    """Run the server"""
    import uvicorn
    
    host = os.getenv("API_HOST", "0.0.0.0")
    port = int(os.getenv("API_PORT", 8000))
    reload = os.getenv("DEBUG", "true").lower() == "true"
    
    print(f"""
╔════════════════════════════════════════════════════════════╗
║                                                            ║
║          DOS ATTACK MAP - API SERVER                      ║
║                                                            ║
╚════════════════════════════════════════════════════════════╝

🚀 Starting server...
   Host: {host}
   Port: {port}
   Reload: {reload}

📚 Documentation:
   Swagger UI: http://{host}:{port}/docs
   ReDoc: http://{host}:{port}/redoc

🔗 Endpoints:
   Health: http://{host}:{port}/health
   Attacks: http://{host}:{port}/api/attacks/recent
   Stats: http://{host}:{port}/api/stats/summary
   WebSocket: ws://{host}:{port}/ws/attacks

Press Ctrl+C to stop
════════════════════════════════════════════════════════════
""")
    
    uvicorn.run(
        "app.main:app",
        host=host,
        port=port,
        reload=reload,
        log_level="info"
    )


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n🛑 Server stopped by user")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Error: {e}")
        sys.exit(1)
