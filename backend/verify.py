import geoip2.database

reader = geoip2.database.Reader('GeoLite2-City.mmdb')
response = reader.city('8.8.8.8')

print(f"IP: 8.8.8.8")
print(f"City: {response.city.name}")
print(f"Country: {response.country.name}")
print(f"Location: {response.location.latitude}, {response.location.longitude}")

reader.close()

