# PC28 Prediction System

## Overview
AI/ML API Model Extraction and PC28 Prediction System with optimized second-order Markov chain analysis.

**Current Phase: 1 - Project Setup**

## Features (Planned)
- Second-order Markov chain with 5 states (大单, 小双, 小单, 大双, 极值)
- Dynamic EMA (3-7 periods)
- Tail frequency analysis with chi-square testing
- Redis caching for <2s response time
- FastAPI web service
- Real-time PC28 data integration
- AI/ML model catalog extraction

## Installation

### Prerequisites
- Python 3.11+
- Redis server
- Virtual environment (recommended)

### Setup
```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Start Redis (if not running)
redis-server

# Run the application
python main.py
```

## API Endpoints

### Phase 1 (Current)
- `GET /` - System information
- `GET /health` - Health check (Redis connection, system status)

### Planned (Phase 5+)
- `POST /predict` - Generate PC28 predictions
- `GET /models` - Fetch AI/ML model catalog
- `GET /stats` - Statistical analysis and tail frequency data

## Configuration

Configuration is managed through `config.json`:
- API keys for AI/ML API and PC28 data services
- Redis connection settings
- External API endpoints

## Development Phases

1. **Phase 1** (Current): Project setup and configuration ✅
2. **Phase 2**: Data models and validation
3. **Phase 3**: API client implementation
4. **Phase 4**: Statistical engines (Markov chain, tail analysis)
5. **Phase 5**: Prediction system integration
6. **Phase 6**: Web service endpoints
7. **Phase 7**: Monitoring and metrics
8. **Phase 8**: Algorithm optimization
9. **Phase 9**: Deployment and verification

## Accuracy Targets
- Sum range (10-17): 65-70%
- Combination prediction: 56-61%
- Big odd/small even: 61-66%

## Performance Goals
- Response time: <2 seconds
- System uptime: 99.9%
- Statistical significance: p<0.05

## Testing

### Phase 1 Testing
```bash
# Test system health
curl http://localhost:8000/health

# Test system info
curl http://localhost:8000/
```

## License
Private development project

## Contact
Development team: DEV1 (Backend), DEV2 (AI), DA2 (Data Science), Ops1 (Operations)