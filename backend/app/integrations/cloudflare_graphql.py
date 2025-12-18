"""
Cloudflare GraphQL Analytics Client
Free tier optimized with efficient queries
"""

import os
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from gql import gql, Client
from gql.transport.aiohttp import AIOHTTPTransport
import asyncio

logger = logging.getLogger(__name__)


class CloudflareGraphQLClient:
    """
    Cloudflare GraphQL Analytics API client
    Optimized for free tier usage
    """
    
    GRAPHQL_ENDPOINT = "https://api.cloudflare.com/client/v4/graphql"
    
    # GraphQL query for firewall events
    FIREWALL_EVENTS_QUERY = gql("""
        query FirewallEvents(
            $zoneTag: string!
            $filter: ZoneFirewallEventsAdaptiveFilter_InputObject
            $limit: int = 100
        ) {
            viewer {
                zones(filter: {zoneTag: $zoneTag}) {
                    firewallEventsAdaptive(
                        filter: $filter
                        limit: $limit
                        orderBy: [datetime_DESC]
                    ) {
                        datetime
                        rayName
                        action
                        source
                        clientIP
                        clientAsn
                        clientCountryName
                        clientRequestHTTPHost
                        clientRequestHTTPMethodName
                        clientRequestHTTPProtocol
                        clientRequestPath
                        edgeResponseStatus
                        matchIndex
                        originResponseStatus
                        originatorRayName
                        ruleId
                        userAgent
                    }
                }
            }
        }
    """)
    
    # GraphQL query for HTTP analytics
    HTTP_ANALYTICS_QUERY = gql("""
        query HTTPAnalytics(
            $zoneTag: string!
            $filter: ZoneHttpRequestsFilter_InputObject
        ) {
            viewer {
                zones(filter: {zoneTag: $zoneTag}) {
                    httpRequests1hGroups(
                        filter: $filter
                        limit: 1000
                    ) {
                        dimensions {
                            datetime
                        }
                        sum {
                            requests
                            bytes
                            threats
                        }
                        uniq {
                            uniques
                        }
                    }
                }
            }
        }
    """)
    
    def __init__(self, api_token: str, zone_id: str, demo_mode: bool = False):
        """
        Initialize Cloudflare GraphQL client
        
        Args:
            api_token: Cloudflare API token
            zone_id: Zone ID
            demo_mode: Use demo data instead of real API
        """
        self.zone_id = zone_id
        self.demo_mode = demo_mode
        self.api_token = api_token
        
        if not demo_mode:
            # Store config but don't create client yet
            # We'll create a new session for each request to avoid connection reuse issues
            self.endpoint = self.GRAPHQL_ENDPOINT
        else:
            logger.info("Running in DEMO mode - using simulated data")
    
    async def fetch_firewall_events(
        self,
        since: datetime = None,
        limit: int = 100
    ) -> List[Dict]:
        """
        Fetch firewall events using GraphQL
        
        Args:
            since: Fetch events since this time (default: last 5 minutes)
            limit: Maximum number of events (default: 100, max: 10000)
            
        Returns:
            List of firewall events
        """
        if self.demo_mode:
            return self._generate_demo_events(limit)
        
        # Default to last 5 minutes
        if since is None:
            since = datetime.utcnow() - timedelta(minutes=5)
        
        # Build filter
        filter_obj = {
            "datetime_geq": since.isoformat() + "Z",
            "datetime_leq": datetime.utcnow().isoformat() + "Z"
        }
        
        variables = {
            "zoneTag": self.zone_id,
            "filter": filter_obj,
            "limit": min(limit, 10000)  # Cloudflare max
        }
        
        try:
            # Create new transport and client for this request
            transport = AIOHTTPTransport(
                url=self.endpoint,
                headers={
                    "Authorization": f"Bearer {self.api_token}",
                    "Content-Type": "application/json"
                }
            )
            
            client = Client(
                transport=transport,
                fetch_schema_from_transport=False,
                execute_timeout=30
            )
            
            async with client as session:
                result = await session.execute(
                    self.FIREWALL_EVENTS_QUERY,
                    variable_values=variables
                )
                
                # Extract events from GraphQL response
                zones = result.get("viewer", {}).get("zones", [])
                if not zones:
                    logger.warning("No zones found in GraphQL response")
                    return []
                
                events = zones[0].get("firewallEventsAdaptive", [])
                logger.info(f"Fetched {len(events)} firewall events via GraphQL")
                
                return events
                
        except Exception as e:
            logger.error(f"Error fetching firewall events: {e}")
            return []
    
    async def fetch_http_analytics(
        self,
        since: datetime = None,
        limit: int = 1000
    ) -> Dict:
        """
        Fetch HTTP analytics using GraphQL
        
        Args:
            since: Fetch analytics since this time (default: last hour)
            limit: Maximum number of data points
            
        Returns:
            Analytics data
        """
        if self.demo_mode:
            return self._generate_demo_analytics()
        
        if since is None:
            since = datetime.utcnow() - timedelta(hours=1)
        
        filter_obj = {
            "datetime_geq": since.isoformat() + "Z",
            "datetime_leq": datetime.utcnow().isoformat() + "Z"
        }
        
        variables = {
            "zoneTag": self.zone_id,
            "filter": filter_obj
        }
        
        try:
            # Create new transport and client for this request
            transport = AIOHTTPTransport(
                url=self.endpoint,
                headers={
                    "Authorization": f"Bearer {self.api_token}",
                    "Content-Type": "application/json"
                }
            )
            
            client = Client(
                transport=transport,
                fetch_schema_from_transport=False,
                execute_timeout=30
            )
            
            async with client as session:
                result = await session.execute(
                    self.HTTP_ANALYTICS_QUERY,
                    variable_values=variables
                )
                
                zones = result.get("viewer", {}).get("zones", [])
                if not zones:
                    return {}
                
                analytics = zones[0].get("httpRequests1hGroups", [])
                logger.info(f"Fetched {len(analytics)} analytics data points")
                
                return self._process_analytics(analytics)
                
        except Exception as e:
            logger.error(f"Error fetching HTTP analytics: {e}")
            return {}
    
    async def fetch_all_data(
        self,
        since: datetime = None,
        events_limit: int = 100
    ) -> Dict:
        """
        Fetch all data in parallel (efficient!)
        Uses asyncio to make concurrent GraphQL queries
        
        Args:
            since: Fetch data since this time
            events_limit: Max firewall events to fetch
            
        Returns:
            Dictionary with events and analytics
        """
        # Run queries in parallel
        results = await asyncio.gather(
            self.fetch_firewall_events(since, events_limit),
            self.fetch_http_analytics(since),
            return_exceptions=True
        )
        
        return {
            "events": results[0] if not isinstance(results[0], Exception) else [],
            "analytics": results[1] if not isinstance(results[1], Exception) else {}
        }
    
    def _process_analytics(self, analytics: List[Dict]) -> Dict:
        """Process analytics data into summary"""
        total_requests = sum(group.get("sum", {}).get("requests", 0) for group in analytics)
        total_threats = sum(group.get("sum", {}).get("threats", 0) for group in analytics)
        
        # Group by country
        by_country = {}
        for group in analytics:
            country = group.get("dimensions", {}).get("clientCountryName", "Unknown")
            requests = group.get("sum", {}).get("requests", 0)
            by_country[country] = by_country.get(country, 0) + requests
        
        return {
            "total_requests": total_requests,
            "total_threats": total_threats,
            "by_country": by_country,
            "threat_percentage": (total_threats / total_requests * 100) if total_requests > 0 else 0
        }
    
    def _generate_demo_events(self, count: int) -> List[Dict]:
        """Generate demo firewall events"""
        import random
        
        actions = ["block", "challenge", "jschallenge", "allow"]
        countries = ["United States", "China", "Russia", "Brazil", "India", 
                    "Germany", "United Kingdom", "France", "Japan", "South Korea"]
        sources = ["firewallrules", "ratelimit", "waf", "asn"]
        methods = ["GET", "POST", "PUT", "DELETE"]
        
        events = []
        base_time = datetime.utcnow()
        
        for i in range(count):
            timestamp = base_time - timedelta(seconds=random.randint(0, 300))
            
            event = {
                "datetime": timestamp.isoformat() + "Z",
                "rayName": f"{random.randint(100000000, 999999999)}",
                "action": random.choice(actions),
                "source": random.choice(sources),
                "clientIP": f"{random.randint(1,255)}.{random.randint(0,255)}.{random.randint(0,255)}.{random.randint(1,255)}",
                "clientAsn": str(random.randint(1000, 99999)),
                "clientCountryName": random.choice(countries),
                "clientRequestHTTPHost": "example.com",
                "clientRequestHTTPMethodName": random.choice(methods),
                "clientRequestHTTPProtocol": "HTTP/1.1",
                "clientRequestPath": f"/api/endpoint{random.randint(1,10)}",
                "edgeResponseStatus": random.choice([200, 403, 503, 429]),
                "matchIndex": random.randint(1, 5),
                "metadata": f'{{"rule": "DDoS Protection", "score": {random.randint(1,100)}}}',
                "userAgent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
            }
            events.append(event)
        
        logger.info(f"Generated {count} demo firewall events")
        return events
    
    def _generate_demo_analytics(self) -> Dict:
        """Generate demo analytics"""
        import random
        return {
            "total_requests": random.randint(10000, 100000),
            "total_threats": random.randint(100, 1000),
            "by_country": {
                "United States": random.randint(1000, 5000),
                "China": random.randint(500, 3000),
                "Russia": random.randint(300, 2000)
            },
            "threat_percentage": random.uniform(1.0, 5.0)
        }


# Singleton instance
_graphql_client: Optional[CloudflareGraphQLClient] = None


def get_cloudflare_graphql_client() -> CloudflareGraphQLClient:
    """Get or create Cloudflare GraphQL client"""
    global _graphql_client
    
    if _graphql_client is None:
        api_token = os.getenv("CLOUDFLARE_API_TOKEN", "demo_token")
        zone_id = os.getenv("CLOUDFLARE_ZONE_ID", "demo_zone")
        demo_mode = os.getenv("CLOUDFLARE_DEMO_MODE", "true").lower() == "true"
        
        _graphql_client = CloudflareGraphQLClient(
            api_token=api_token,
            zone_id=zone_id,
            demo_mode=demo_mode
        )
        
        logger.info(f"Cloudflare GraphQL client initialized (demo_mode={demo_mode})")
    
    return _graphql_client
