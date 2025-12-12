# 🌍 DOS Attack Map - Real-Time Visualization Platform

A real-time DOS attack visualization system featuring a 3D interactive globe, powered by machine learning classification and live data from Cloudflare and AbuseIPDB.

![License](https://img.shields.io/badge/license-MIT-blue.svg)
![Python](https://img.shields.io/badge/python-3.11+-blue.svg)
![React](https://img.shields.io/badge/react-18.2+-blue.svg)
![FastAPI](https://img.shields.io/badge/fastapi-0.108+-green.svg)

## ✨ Features

- 🌐 **Interactive 3D Globe** - Real-time attack visualization using React Three Fiber
- 🤖 **ML Classification** - Intelligent DOS attack detection using Random Forest/XGBoost
- 📊 **Live Dashboard** - Real-time statistics and attack analytics
- 🔄 **WebSocket Streaming** - Sub-second attack event updates
- 🗺️ **Geolocation** - Accurate IP-to-coordinate mapping with MaxMind GeoLite2
- 📈 **Historical Analysis** - Timeline slider for attack pattern review
- 🎯 **Heatmap Overlay** - Geographic attack distribution visualization
- 🔔 **Real-time Alerts** - Configurable threat notifications

## 🏗️ Architecture

```
Data Sources → Pipeline → ML Classifier → Geolocation → FastAPI → WebSocket → 3D Globe
     ↓                                                       ↓
Cloudflare                                             PostgreSQL
AbuseIPDB                                              Redis Cache
```

## 📋 Prerequisites

- **Python 3.11+**
- **Node.js 18+**
- **PostgreSQL 14+**
- **Redis 7+** (optional but recommended)
- **Docker & Docker Compose** (for containerized deployment)

### API Keys Required

1. **Cloudflare API Token** ([Get here](https://dash.cloudflare.com/profile/api-tokens))
2. **AbuseIPDB API Key** ([Get here](https://www.abuseipdb.com/api))
3. **MaxMind GeoLite2** ([Download](https://dev.maxmind.com/geoip/geolite2-free-geolocation-data))

## 🚀 Quick Start

### Option 1: Docker Compose (Recommended)

```bash
# 1. Clone the repository
git clone https://github.com/yourusername/dos-attack-map.git
cd dos-attack-map

# 2. Create environment file
cp .env.example .env
# Edit .env and add your API keys

# 3. Download GeoLite2 database
# Place GeoLite2-City.mmdb in project root

# 4. Start all services
docker-compose up -d

# 5. Initialize database
docker-compose exec backend alembic upgrade head

# 6. (Optional) Train ML model with sample data
docker-compose exec backend python -m app.ml.train_model

# 7. Access the application
# Frontend: http://localhost:5173
# Backend API: http://localhost:8000/docs
# Grafana: http://localhost:3001 (if monitoring enabled)
```

### Option 2: Manual Setup

#### Backend Setup

```bash
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Setup database
export DATABASE_URL="postgresql://user:pass@localhost/dos_attacks"
alembic upgrade head

# Download and place GeoLite2-City.mmdb in backend/

# Run development server
uvicorn app.main:app --reload --port 8000
```

#### Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Create .env file
echo "VITE_API_URL=http://localhost:8000" > .env
echo "VITE_WS_URL=ws://localhost:8000" >> .env

# Run development server
npm run dev
```

## 📁 Project Structure

```
dos-attack-map/
├── backend/
│   ├── app/
│   │   ├── main.py              # FastAPI application
│   │   ├── config.py            # Configuration
│   │   ├── database.py          # DB connection
│   │   ├── models.py            # SQLAlchemy models
│   │   ├── api/
│   │   │   ├── attacks.py       # Attack endpoints
│   │   │   ├── stats.py         # Statistics endpoints
│   │   │   └── websocket.py     # WebSocket handlers
│   │   ├── services/
│   │   │   ├── cloudflare.py    # Cloudflare API client
│   │   │   ├── abuseipdb.py     # AbuseIPDB client
│   │   │   ├── classifier.py    # ML classification
│   │   │   └── geolocation.py   # IP → coordinates
│   │   └── ml/
│   │       ├── train_model.py   # Model training
│   │       └── models/          # Saved models
│   ├── requirements.txt
│   └── Dockerfile
├── frontend/
│   ├── src/
│   │   ├── App.jsx
│   │   ├── components/
│   │   │   ├── Globe/
│   │   │   │   ├── AttackGlobe.jsx
│   │   │   │   └── AttackArc.jsx
│   │   │   └── Dashboard/
│   │   │       ├── StatsPanel.jsx
│   │   │       └── Timeline.jsx
│   │   └── hooks/
│   │       └── useWebSocket.js
│   ├── package.json
│   └── Dockerfile
├── notebooks/
│   ├── data_exploration.ipynb
│   └── model_training.ipynb
├── docker-compose.yml
├── .env.example
└── README.md
```

## 🔧 Configuration

### Environment Variables

Key configurations in `.env`:

```env
# API Keys
CLOUDFLARE_API_TOKEN=your_token_here
CLOUDFLARE_ZONE_ID=your_zone_id
ABUSEIPDB_API_KEY=your_key_here

# Database
DATABASE_URL=postgresql://user:pass@localhost/dos_attacks

# ML Settings
ML_CONFIDENCE_THRESHOLD=0.75
THREAT_SCORE_THRESHOLD=15

# Data Collection
CLOUDFLARE_FETCH_INTERVAL=5  # minutes
ABUSEIPDB_FETCH_INTERVAL=10  # minutes
```

### Attack Classification Thresholds

Customize in `.env`:

```env
THREAT_SCORE_THRESHOLD=15           # Cloudflare threat score
CONFIDENCE_SCORE_THRESHOLD=70       # AbuseIPDB confidence
REQUEST_PER_MINUTE_THRESHOLD=100    # RPM spike detection
BURST_FACTOR_THRESHOLD=3.0          # Request burst multiplier
```

## 🤖 Machine Learning

### Training the Model

```bash
cd backend

# With sample data
python -m app.ml.train_model --data data/sample_attacks.csv

# With real data from database
python -m app.ml.train_model --from-db --days 30
```

### Model Features

The classifier uses these features:

- `requests_per_minute` - Request rate
- `cloudflare_threat_score` - CF threat assessment
- `abuseipdb_confidence` - AbuseIPDB confidence score
- `unique_paths_requested` - URL diversity
- `burst_factor` - Traffic spike intensity
- `request_method_entropy` - HTTP method distribution
- `country_code` - Geographic origin

### Model Performance

Target metrics:
- **Accuracy**: >90%
- **Precision**: >85%
- **Recall**: >80%
- **F1 Score**: >85%

## 📊 API Endpoints

### REST API

```
GET  /api/attacks/recent          # Last 100 attacks
GET  /api/attacks/live             # Current attack rate
GET  /api/stats/summary            # Dashboard stats
GET  /api/stats/by-country         # Geographic distribution
GET  /api/heatmap/data             # Heatmap data
POST /api/classify/ip              # Classify single IP
```

### WebSocket

```
WS   /ws/attacks                   # Real-time attack stream
```

Example WebSocket message:

```json
{
  "ip": "192.168.1.1",
  "timestamp": "2024-12-12T10:30:00Z",
  "threat_score": 18,
  "confidence": 85,
  "classification": "dos_attack",
  "latitude": 55.751244,
  "longitude": 37.618423,
  "country": "RU",
  "attack_type": "HTTP Flood"
}
```

## 🎨 UI Components

### Globe Visualization

Features:
- Auto-rotating Earth with country borders
- Attack arcs from source to target
- Color-coded threat levels (green → yellow → red)
- Particle effects for active attacks
- Interactive camera controls

### Dashboard Panels

- **Real-time Stats**: Active attacks, total requests, threat level
- **Geographic Heatmap**: Attack density by region
- **Top Attackers**: Most active source IPs
- **Attack Timeline**: Historical attack patterns
- **Threat Categories**: DOS type distribution

## 🔍 Monitoring

### Grafana Dashboards

Access at `http://localhost:3001` (default: admin/admin)

Dashboards include:
- Attack rate over time
- Geographic distribution
- Top attacking countries
- Classification accuracy
- System performance metrics

### Prometheus Metrics

Access at `http://localhost:9090`

Metrics:
- `dos_attacks_total` - Total attack count
- `dos_classification_latency` - ML inference time
- `dos_api_requests_total` - API usage
- `dos_websocket_connections` - Active connections

## 🚢 Deployment

### Production Checklist

- [ ] Set strong `SECRET_KEY` in `.env`
- [ ] Use production database credentials
- [ ] Enable SSL/TLS for API endpoints
- [ ] Configure firewall rules
- [ ] Set up log rotation
- [ ] Enable rate limiting
- [ ] Configure backup strategy
- [ ] Set up monitoring alerts
- [ ] Use environment-specific configs
- [ ] Enable HTTPS for frontend

### Cloud Platforms

**Railway** (Recommended for MVP):
```bash
railway up
```

**Render**:
```bash
render deploy
```

**Docker on VPS**:
```bash
docker-compose -f docker-compose.prod.yml up -d
```

## 📚 Development

### Running Tests

```bash
# Backend
cd backend
pytest

# Frontend
cd frontend
npm test
```

### Code Quality

```bash
# Backend linting
black app/
flake8 app/

# Frontend linting
npm run lint
```

### Database Migrations

```bash
# Create migration
alembic revision --autogenerate -m "description"

# Apply migration
alembic upgrade head

# Rollback
alembic downgrade -1
```

## 🐛 Troubleshooting

### Common Issues

**Database connection fails:**
```bash
# Check PostgreSQL is running
docker-compose ps postgres

# Check connection
psql $DATABASE_URL
```

**WebSocket not connecting:**
- Verify backend is running: `curl http://localhost:8000/health`
- Check CORS settings in backend config
- Ensure firewall allows WebSocket connections

**GeoIP lookups failing:**
- Download latest GeoLite2-City.mmdb
- Verify file path in `.env`
- Check file permissions

**ML model not loading:**
```bash
# Retrain model
python -m app.ml.train_model

# Verify model file exists
ls backend/app/ml/models/attack_classifier.pkl
```

## 🤝 Contributing

Contributions welcome! Please:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- [Cloudflare](https://www.cloudflare.com/) for threat intelligence API
- [AbuseIPDB](https://www.abuseipdb.com/) for IP reputation data
- [MaxMind](https://www.maxmind.com/) for GeoLite2 database
- [FastAPI](https://fastapi.tiangolo.com/) framework
- [React Three Fiber](https://docs.pmnd.rs/react-three-fiber) for 3D rendering
- [Aceternity UI](https://ui.aceternity.com/) for beautiful components

## 📞 Support

- Documentation: [docs.example.com](https://docs.example.com)
- Issues: [GitHub Issues](https://github.com/yourusername/dos-attack-map/issues)
- Discord: [Join our server](https://discord.gg/example)

## 🗺️ Roadmap

- [x] MVP with basic globe visualization
- [x] ML-based attack classification
- [x] Real-time WebSocket streaming
- [ ] Mobile responsive design
- [ ] Advanced anomaly detection
- [ ] Custom alert rules
- [ ] Export attack reports
- [ ] Multi-tenant support
- [ ] API rate limiting dashboard
- [ ] Blockchain-based attack verification

---

**Built with ❤️ using 100% free and open-source tools**
