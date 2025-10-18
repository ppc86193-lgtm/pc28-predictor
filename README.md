# PC28 Prediction System

## Overview
AI/ML API Model Extraction and PC28 Prediction System with optimized second-order Markov chain analysis.

**Current Phase: 2 - Data Models Implementation**

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

## Data Models

### PC28Data
Core lottery data model with validation:
- `sum`: Integer (0-27) - Sum of three numbers
- `tail`: Integer (0-9) - Last digit of sum  
- `combination`: Enum ["大单", "小双", "小单", "大双", "极值"] - Combination type
- `period`: Optional string - Period identifier
- `timestamp`: Optional datetime - Draw timestamp
- `numbers`: Optional list - Original three numbers

### PredictionResult
Prediction output model:
- `sum_range`: String - Predicted sum range
- `combination`: String - Predicted combination
- `probabilities`: Dict - Probability distribution
- `confidence`: Float (0-1) - Prediction confidence

### TailFrequencyResult
Statistical analysis result:
- `frequencies`: Dict - Tail frequency distribution
- `chi_square_statistic`: Float - Chi-square test statistic
- `p_value`: Float (0-1) - Statistical p-value
- `is_significant`: Boolean - Statistical significance

### ModelInfo
AI/ML model information:
- `id`: String - Model identifier
- `name`: String - Model name
- `developer`: String - Model developer
- `type`: String - Model type
- `context_length`: Optional int - Context length

## Development Phases

1. **Phase 1**: Project setup and configuration ✅
2. **Phase 2** (Current): Data models and validation ✅
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

### Phase 2 Testing
```bash
# Run data model tests
source venv/bin/activate
python -m pytest test_data_models.py -v

# Test system health
curl http://localhost:8000/health

# Test system info
curl http://localhost:8000/
```

### Test Coverage
- ✅ PC28Data validation (sum, tail, combination)
- ✅ PredictionResult model
- ✅ TailFrequencyResult model  
- ✅ ModelInfo model
- ✅ extract_features function
- ✅ validate_pc28_data function
- ✅ categorize_models function

## License
Private development project

## Contact
Development team: DEV1 (Backend), DEV2 (AI), DA2 (Data Science), Ops1 (Operations)