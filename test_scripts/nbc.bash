CLOUDFLARE_API_TOKEN=""
ZONE_ID=""

# Correct query with proper filter syntax
curl -X POST https://api.cloudflare.com/client/v4/graphql \
  -H "Authorization: Bearer $CLOUDFLARE_API_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "query($zoneTag: string!, $filter: ZoneFirewallEventsAdaptiveFilter_InputObject) { viewer { zones(filter: {zoneTag: $zoneTag}) { firewallEventsAdaptive(filter: $filter, limit: 5, orderBy: [datetime_DESC]) { datetime rayName action source clientIP clientCountryName clientRequestHTTPMethodName clientRequestPath edgeResponseStatus userAgent } } } }",
    "variables": {
      "zoneTag": "'$ZONE_ID'",
      "filter": {
        "datetime_geq": "'$(date -u -v-1H +%Y-%m-%dT%H:%M:%SZ)'",
        "datetime_leq": "'$(date -u +%Y-%m-%dT%H:%M:%SZ)'"
      }
    }
  }' | jq