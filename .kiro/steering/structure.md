# Project Structure

## Root Directory Layout

```
pc28_predictor/
├── main.py              # FastAPI application entry point
├── config.py            # Configuration management and Redis client
├── config.json          # API keys, endpoints, Redis settings
├── requirements.txt     # Python dependencies
├── api_client.py        # External API integrations and data models
├── markov_model.py      # Second-order Markov chain implementation
├── tail_analyzer.py     # Tail frequency analysis and chi-square testing
├── test_*.py           # Test files for specific modules
└── README.md           # Project documentation
```

## Code Organization Patterns

### Data Models (api_client.py)
- **PC28Data**: Core lottery data with validation
- **PredictionResult**: Prediction outputs with confidence scores
- **TailFrequencyResult**: Statistical analysis results
- **ModelInfo**: AI/ML model metadata
- **ErrorResponse**: Standardized error handling
- **SystemHealth**: Health check responses

### Module Responsibilities
- **main.py**: FastAPI app, health endpoints, system info
- **config.py**: Configuration loading, Redis initialization
- **api_client.py**: External APIs, data models, validation, error handling
- **markov_model.py**: Statistical prediction algorithms
- **tail_analyzer.py**: Frequency analysis and probability adjustments

### Error Handling Convention
- Custom exception classes with error codes and details
- Centralized error logging with `log_error()` function
- Error counters for monitoring and debugging
- Structured ErrorResponse model for API consistency

### Testing Structure
- **test_data_models.py**: Pydantic model validation tests
- **test_error_handling.py**: Exception and error response tests
- Module-specific test files following `test_*.py` pattern

### Configuration Management
- Sensitive data in `config.json` (not committed to git)
- Configuration constants loaded in `config.py`
- Environment-specific settings support

## Development Phase Structure

The codebase follows a 9-phase development approach with placeholder implementations that get replaced in later phases. Current implementations include logging and basic structure for future development.