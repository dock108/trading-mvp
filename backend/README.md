# Trading MVP Backend

FastAPI-based REST API server providing trading strategy execution, backtesting, and investment recommendations.

## 🏗️ Architecture

The backend follows a clean architecture pattern with clear separation of concerns:

```
backend/
├── app/
│   ├── api.py              # Main FastAPI application
│   └── routes/             # API route handlers
│       ├── __init__.py
│       ├── config.py       # Configuration management
│       ├── strategies.py   # Strategy execution endpoints
│       ├── recommendations.py # AI recommendation endpoints
│       └── files.py        # File operation endpoints
├── data/                   # Data processing and caching
├── main.py                # Server entry point
└── trades.csv             # Trade execution logs
```

## 🚀 API Endpoints

### Configuration Management
- `GET /api/config` - Load current configuration
- `PUT /api/config` - Update configuration settings

### Strategy Execution
- `POST /api/run` - Execute trading strategies
- `GET /api/trades` - Retrieve trade history
- `GET /api/summary` - Get execution summary

### Investment Recommendations
- `POST /api/recommendations/analyze` - Generate AI recommendations
- `GET /api/recommendations/current-positions` - Get portfolio positions
- `GET /api/recommendations/market-alerts` - Get market alerts

### File Operations
- `POST /api/upload-config` - Upload configuration file
- `GET /api/download-config` - Download current configuration
- `GET /api/download-trades` - Download trade history

### Health & Monitoring
- `GET /api/health` - API health check

## 🔧 Configuration

### Environment Variables
```bash
# API Configuration
PORT=8001
HOST=127.0.0.1
DEBUG=true

# CORS Settings
FRONTEND_URL=http://localhost:5174

# Logging
LOG_LEVEL=INFO
LOG_FILE=backend.log
```

### Dependencies
```bash
pip install fastapi uvicorn pydantic python-multipart aiofiles
```

## 🛠️ Development

### Start Development Server
```bash
# From project root
python backend/main.py

# Or with uvicorn directly
uvicorn backend.app.api:app --reload --host 127.0.0.1 --port 8001
```

### API Documentation
Once running, access interactive documentation at:
- **Swagger UI**: `http://127.0.0.1:8001/docs`
- **ReDoc**: `http://127.0.0.1:8001/redoc`

## 📊 Request/Response Examples

### Execute Strategies
```bash
POST /api/run
{
  "strategies": ["wheel", "rotator"],
  "config_overrides": {
    "data_mode": "live"
  },
  "backtest": true
}
```

### Generate Recommendations
```bash
POST /api/recommendations/analyze
{
  "start_date": "2023-01-01",
  "end_date": "2023-12-31", 
  "initial_capital": 100000,
  "strategies": ["wheel", "rotator"],
  "risk_tolerance": "MEDIUM"
}
```

## 🔒 Security Features

- **CORS middleware** for cross-origin requests
- **Request validation** with Pydantic models
- **Error handling** with proper HTTP status codes
- **Input sanitization** for file uploads

## 📈 Performance

- **Async/await** patterns for non-blocking operations
- **Efficient JSON serialization** with Pydantic
- **Connection pooling** for database operations
- **Caching** for frequently accessed data

## 🧪 Testing

```bash
# Run API tests
python -m pytest backend/tests/

# Test specific endpoint
curl -X GET http://127.0.0.1:8001/api/health
```

## 📚 Integration

The backend integrates with:
- **Frontend Dashboard** via REST API
- **Trading Strategies** in `/strategies` directory
- **Market Data APIs** through `/data` module
- **Configuration** via YAML files in `/config`

---

This backend provides a robust, scalable foundation for the Trading MVP platform with comprehensive API documentation and development tools.