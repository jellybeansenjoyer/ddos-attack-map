"""
API Routes Package
Imports all routers for easy access
"""
from . import health, attacks, statistics, websocket, honeypot

__all__ = ['health', 'attacks', 'statistics', 'websocket', 'honeypot']