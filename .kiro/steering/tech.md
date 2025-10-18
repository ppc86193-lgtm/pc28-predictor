# Technology Stack

## Core Technologies

- **Python 3.11+**: Primary development language
- **FastAPI**: Web framework for API endpoints
- **Pydantic**: Data validation and serialization
- **Redis**: Caching and session storage
- **NumPy/SciPy**: Statistical computations and analysis

## Key Dependencies

```
fastapi>=0.100.0
uvicorn>=0.20.0
requests>=2.28.0
redis>=4.0.0
numpy>=1.24.0
scipy>=1.10.0
pydantic>=2.0.0
httpx>=0.24.0
```

## Development Commands

### Environment Setup
```bash
# Create and activate virtual environment
python -m venv venv
source venv/bin/activate  # macOS/Linux
# venv\Scripts\activate   # Windows

# Install dependencies
pip install -r requirements.txt
```

### Running the Application
```bash
# Start Redis server (required)
redis-server

# Run development server
python main.py

# Alternative with uvicorn
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

### Testing
```bash
# Run specific test files
python -m pytest test_data_models.py -v
python -m pytest test_error_handling.py -v

# Health check endpoints
curl http://localhost:8000/health
curl http://localhost:8000/
```

## Configuration Management

- **config.json**: API keys, endpoints, Redis settings
- **config.py**: Configuration loader and Redis client initialization
- Environment-specific settings loaded at runtime

## API Architecture

- **RESTful endpoints** with FastAPI
- **Pydantic models** for request/response validation
- **Structured error handling** with custom exception classes
- **Health monitoring** with comprehensive system checks