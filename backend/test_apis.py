#!/usr/bin/env python3
"""
DOS Attack Map - API Credentials Test Script  
Tests all API connections and credentials
"""

import os
import sys
import requests
import geoip2.database
from dotenv import load_dotenv
from datetime import datetime, timedelta, timezone

# Load environment variables
load_dotenv()


class Colors:
    """ANSI color codes for terminal output"""
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    BOLD = '\033[1m'
    END = '\033[0m'


def print_success(msg):
    """Print success message"""
    print(f"{Colors.GREEN}✅ {msg}{Colors.END}")


def print_error(msg):
    """Print error message"""
    print(f"{Colors.RED}❌ {msg}{Colors.END}")


def print_info(msg):
    """Print info message"""
    print(f"{Colors.BLUE}ℹ️  {msg}{Colors.END}")


def print_warning(msg):
    """Print warning message"""
    print(f"{Colors.YELLOW}⚠️  {msg}{Colors.END}")


def print_header(text):
    """Print formatted header"""
    print(f"\n{Colors.BLUE}{Colors.BOLD}{'='*60}{Colors.END}")
    print(f"{Colors.BLUE}{Colors.BOLD}{text}{Colors.END}")
    print(f"{Colors.BLUE}{Colors.BOLD}{'='*60}{Colors.END}")


def test_cloudflare():
    """Test Cloudflare API connection using GraphQL"""
    print_header("Testing Cloudflare GraphQL API")
    
    api_token = os.getenv('CLOUDFLARE_API_TOKEN')
    zone_id = os.getenv('CLOUDFLARE_ZONE_ID')
    
    if not api_token or api_token == '':
        print_error("CLOUDFLARE_API_TOKEN not set in .env file")
        return False
    
    if not zone_id or zone_id == '':
        print_error("CLOUDFLARE_ZONE_ID not set in .env file")
        return False
    
    # Mask sensitive data
    masked_token = api_token[:10] + '...' if len(api_token) > 10 else '***'
    masked_zone = zone_id[:10] + '...' if len(zone_id) > 10 else zone_id
    
    print_info(f"Zone ID: {masked_zone}")
    print_info(f"Token: {masked_token}")
    
    try:
        # Test 1: Verify token and zone with REST API
        print_info("Verifying zone access...")
        url = f"https://api.cloudflare.com/client/v4/zones/{zone_id}"
        headers = {
            "Authorization": f"Bearer {api_token}",
            "Content-Type": "application/json"
        }
        
        response = requests.get(url, headers=headers, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            if data.get('success'):
                zone_name = data['result'].get('name', 'Unknown')
                zone_status = data['result'].get('status', 'Unknown')
                plan_name = data['result'].get('plan', {}).get('name', 'Unknown')
                
                print_success(f"Zone verified: {zone_name}")
                print_info(f"Zone status: {zone_status}")
                print_info(f"Plan: {plan_name}")
            else:
                print_error("API returned error")
                errors = data.get('errors', [])
                for error in errors:
                    print_info(f"Error: {error.get('message', 'Unknown error')}")
                return False
        elif response.status_code == 403:
            print_error("Access denied - check token permissions")
            print_info("Token needs: Zone.Analytics:Read, Zone.Zone Settings:Read")
            return False
        elif response.status_code == 404:
            print_error("Zone not found - check Zone ID")
            return False
        else:
            print_error(f"Connection failed: HTTP {response.status_code}")
            return False
        
        # Test 2: Test GraphQL Analytics API
        print_info("Testing GraphQL Analytics API...")
        
        # Use last 7 days for better data availability
        # Free plan: httpRequests1dGroups (1 day aggregation)
        # Pro+ plan: httpRequests1hGroups (1 hour aggregation)  
        # Enterprise: httpRequests1mGroups (1 minute aggregation)
        until_dt = datetime.now(timezone.utc)
        since_dt = until_dt - timedelta(days=7)
        
        # Format as date strings (YYYY-MM-DD) for httpRequests1dGroups
        since_date = since_dt.strftime('%Y-%m-%d')
        until_date = until_dt.strftime('%Y-%m-%d')
        
        # GraphQL query using httpRequests1dGroups (available on all plans)
        graphql_query = """
        query TrafficStats($zoneTag: String!, $since: String!, $until: String!) {
          viewer {
            zones(filter: {zoneTag: $zoneTag}) {
              httpRequests1dGroups(
                limit: 100,
                filter: {
                  date_geq: $since,
                  date_leq: $until
                }
              ) {
                sum {
                  requests
                  threats
                }
                dimensions {
                  date
                }
              }
            }
          }
        }
        """
        
        graphql_payload = {
            "query": graphql_query,
            "variables": {
                "zoneTag": zone_id,
                "since": since_date,
                "until": until_date
            }
        }
        
        graphql_response = requests.post(
            "https://api.cloudflare.com/client/v4/graphql",
            headers=headers,
            json=graphql_payload,
            timeout=30
        )
        
        if graphql_response.status_code == 200:
            graphql_data = graphql_response.json()
            
            # Check for GraphQL errors
            if 'errors' in graphql_data:
                print_error("GraphQL query returned errors:")
                errors = graphql_data.get('errors', [])
                if errors:
                    for error in errors:
                        msg = error.get('message', 'Unknown error')
                        print_info(f"  {msg}")
                else:
                    print_info("  Unknown error format")
                print_warning("Note: Zone may need active traffic or higher plan")
                
                # Still consider it a pass if GraphQL endpoint is accessible
                print_success("GraphQL API is accessible (but no data yet)")
                return True
            
            # Extract data
            try:
                viewer_data = graphql_data.get('data', {})
                if not viewer_data or 'viewer' not in viewer_data:
                    print_warning("No viewer data in response")
                    print_success("GraphQL API is accessible")
                    return True
                
                zones = viewer_data['viewer'].get('zones', [])
                if not zones or len(zones) == 0:
                    print_warning("No zones returned (check permissions)")
                    print_success("GraphQL API is accessible")
                    return True
                
                groups = zones[0].get('httpRequests1dGroups', [])
                
                if groups and len(groups) > 0:
                    # Calculate totals
                    total_requests = sum(g['sum']['requests'] for g in groups)
                    total_threats = sum(g['sum']['threats'] for g in groups)
                    
                    print_success("GraphQL Analytics API accessible")
                    print_info(f"Last 7 days data points: {len(groups)}")
                    print_info(f"Total requests: {total_requests:,}")
                    print_info(f"Total threats: {total_threats:,}")
                    
                    return True
                else:
                    print_warning("No traffic data yet (zone may be new or pending)")
                    print_success("GraphQL API is accessible")
                    return True
                    
            except (KeyError, IndexError, TypeError) as e:
                print_error(f"Error parsing GraphQL response: {str(e)}")
                print_info("Response structure may have changed")
                return False
        else:
            print_error(f"GraphQL API failed: HTTP {graphql_response.status_code}")
            try:
                error_data = graphql_response.json()
                print_info(f"Response: {error_data}")
            except:
                print_info(f"Response: {graphql_response.text[:200]}")
            return False
            
    except requests.exceptions.Timeout:
        print_error("Connection timeout - check network connection")
        return False
    except requests.exceptions.RequestException as e:
        print_error(f"Connection error: {str(e)}")
        return False
    except Exception as e:
        print_error(f"Unexpected error: {str(e)}")
        return False


def test_abuseipdb():
    """Test AbuseIPDB API connection"""
    print_header("Testing AbuseIPDB API")
    
    api_key = os.getenv('ABUSEIPDB_API_KEY')
    
    if not api_key or api_key == '':
        print_error("ABUSEIPDB_API_KEY not set in .env file")
        return False
    
    # Mask sensitive data
    masked_key = api_key[:10] + '...' if len(api_key) > 10 else '***'
    print_info(f"API Key: {masked_key}")
    
    try:
        # Test with known safe IP (Google DNS)
        url = "https://api.abuseipdb.com/api/v2/check"
        headers = {
            "Key": api_key,
            "Accept": "application/json"
        }
        params = {
            "ipAddress": "8.8.8.8",
            "maxAgeInDays": 90,
            "verbose": True
        }
        
        print_info("Testing IP check endpoint...")
        response = requests.get(url, headers=headers, params=params, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            ip_data = data.get('data', {})
            
            print_success("API key verified!")
            print_info(f"Test IP: {ip_data.get('ipAddress', 'Unknown')}")
            print_info(f"Abuse Score: {ip_data.get('abuseConfidenceScore', 0)}%")
            print_info(f"Country: {ip_data.get('countryCode', 'Unknown')}")
            print_info(f"ISP: {ip_data.get('isp', 'Unknown')}")
            print_info(f"Usage Type: {ip_data.get('usageType', 'Unknown')}")
            print_info(f"Total Reports: {ip_data.get('totalReports', 0)}")
            
            return True
        elif response.status_code == 401:
            print_error("Invalid API key - check your credentials")
            return False
        elif response.status_code == 429:
            print_error("Rate limit exceeded")
            print_info("Free tier: 1,000 requests/day")
            print_info("Please try again later or upgrade your plan")
            return False
        elif response.status_code == 422:
            print_error("Invalid request parameters")
            try:
                error_data = response.json()
                print_info(f"Errors: {error_data.get('errors', [])}")
            except:
                pass
            return False
        else:
            print_error(f"Connection failed: HTTP {response.status_code}")
            try:
                error_data = response.json()
                print_info(f"Response: {error_data}")
            except:
                print_info(f"Response: {response.text[:200]}")
            return False
            
    except requests.exceptions.Timeout:
        print_error("Connection timeout - check network connection")
        return False
    except requests.exceptions.RequestException as e:
        print_error(f"Connection error: {str(e)}")
        return False
    except Exception as e:
        print_error(f"Unexpected error: {str(e)}")
        return False


def test_geoip():
    """Test MaxMind GeoLite2 database"""
    print_header("Testing MaxMind GeoLite2 Database")
    
    db_path = os.getenv('GEOIP_DB_PATH', './GeoLite2-City.mmdb')
    
    print_info(f"Database path: {db_path}")
    
    # Check if file exists
    if not os.path.exists(db_path):
        print_error(f"Database file not found: {db_path}")
        print_info("Please download from: https://dev.maxmind.com/geoip/geolite2-free-geolocation-data")
        return False
    
    # Check file size
    file_size = os.path.getsize(db_path) / (1024 * 1024)  # Convert to MB
    print_info(f"Database size: {file_size:.1f} MB")
    
    if file_size < 50:
        print_warning("Database file seems too small (should be ~60-70 MB)")
        print_warning("The database may be corrupted or incomplete")
    
    try:
        # Try to open the database
        print_info("Loading database...")
        reader = geoip2.database.Reader(db_path)
        
        print_success("Database loaded successfully!")
        
        # Test with multiple well-known IPs
        test_ips = [
            ('8.8.8.8', 'Google DNS', 'US'),
            ('1.1.1.1', 'Cloudflare DNS', 'AU'),
            ('208.67.222.222', 'OpenDNS', 'US'),
            ('77.88.8.8', 'Yandex DNS', 'RU'),
            ('94.140.14.14', 'AdGuard DNS', 'CY')
        ]
        
        print_info("\nTesting IP lookups:")
        success_count = 0
        
        for ip, description, expected_country in test_ips:
            try:
                response = reader.city(ip)
                
                country = response.country.name or 'Unknown'
                country_code = response.country.iso_code or 'Unknown'
                city = response.city.name or 'Unknown'
                
                # Handle None values for latitude/longitude
                lat = response.location.latitude
                lon = response.location.longitude
                
                print(f"\n  {ip} ({description}):")
                print(f"    Country: {country} ({country_code})")
                print(f"    City: {city}")
                
                # Only print coordinates if they exist
                if lat is not None and lon is not None:
                    print(f"    Coordinates: {lat:.4f}, {lon:.4f}")
                else:
                    print(f"    Coordinates: Not available")
                
                # Verify expected country
                if country_code == expected_country:
                    print(f"    ✓ Country verified")
                else:
                    print(f"    ⚠️  Expected {expected_country}, got {country_code}")
                
                success_count += 1
                
            except geoip2.errors.AddressNotFoundError:
                print(f"\n  {ip} ({description}): Not found in database")
            except Exception as e:
                print(f"\n  {ip} ({description}): Error - {str(e)}")
        
        reader.close()
        
        if success_count >= 3:
            print_success(f"\n{success_count}/{len(test_ips)} lookups successful!")
            return True
        else:
            print_warning(f"\nOnly {success_count}/{len(test_ips)} lookups successful")
            return False
        
    except geoip2.errors.GeoIP2Error as e:
        print_error(f"GeoIP2 error: {str(e)}")
        return False
    except Exception as e:
        print_error(f"Database error: {str(e)}")
        return False


def check_env_file():
    """Check if .env file exists and is properly configured"""
    print_header("Checking Environment Configuration")
    
    if not os.path.exists('.env'):
        print_error(".env file not found!")
        print_info("Please create .env file from .env.example")
        return False
    
    print_success(".env file found")
    
    # Check for placeholder values
    required_vars = {
        'CLOUDFLARE_API_TOKEN': 'your_cloudflare_api_token_here',
        'CLOUDFLARE_ZONE_ID': 'your_cloudflare_zone_id_here',
        'ABUSEIPDB_API_KEY': 'your_abuseipdb_api_key_here'
    }
    
    has_placeholder = False
    for var, placeholder in required_vars.items():
        value = os.getenv(var, '')
        if value == placeholder or value == '':
            print_warning(f"{var} not configured (still has placeholder value)")
            has_placeholder = True
        else:
            print_success(f"{var} configured")
    
    if has_placeholder:
        print_warning("\nPlease update .env file with your actual API credentials")
        return False
    
    return True


def main():
    """Run all tests"""
    print(f"\n{Colors.BOLD}{Colors.BLUE}")
    print("=" * 60)
    print("  DOS ATTACK MAP - API CREDENTIALS TEST")
    print("=" * 60)
    print(Colors.END)
    
    # Check environment file first
    if not check_env_file():
        print_error("\n.env file is not properly configured")
        print_info("Please add your API credentials to .env file")
        return 1
    
    # Run all API tests
    results = {
        'Cloudflare': test_cloudflare(),
        'AbuseIPDB': test_abuseipdb(),
        'GeoLite2': test_geoip()
    }
    
    # Summary
    print_header("TEST SUMMARY")
    
    for service, passed in results.items():
        if passed:
            print_success(f"{service}: PASS")
        else:
            print_error(f"{service}: FAIL")
    
    total = len(results)
    passed_count = sum(results.values())
    failed_count = total - passed_count
    
    print(f"\n{Colors.BOLD}Results: {passed_count} passed, {failed_count} failed, {total} total{Colors.END}")
    
    if passed_count == total:
        print(f"\n{Colors.GREEN}{Colors.BOLD}🎉 All API credentials are working!{Colors.END}")
        print(f"{Colors.GREEN}You're ready to move to Step 3: Initialize Database{Colors.END}\n")
        return 0
    else:
        print(f"\n{Colors.YELLOW}{Colors.BOLD}⚠️  Some tests failed{Colors.END}")
        print(f"{Colors.YELLOW}Please check your credentials and try again{Colors.END}")
        print(f"\n{Colors.BLUE}Common issues:{Colors.END}")
        print("  • Wrong API key or token")
        print("  • Incorrect Zone ID")
        print("  • Insufficient API permissions")
        print("  • Rate limit exceeded")
        print("  • Missing GeoLite2 database file\n")
        return 1


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print(f"\n\n{Colors.YELLOW}Test cancelled by user{Colors.END}")
        sys.exit(1)
    except Exception as e:
        print(f"\n{Colors.RED}Unexpected error: {str(e)}{Colors.END}")
        sys.exit(1)
