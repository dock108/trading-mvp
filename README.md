# Trading MVP Platform

A comprehensive trading platform implementing options wheel and crypto rotation strategies with live market data integration, backtesting capabilities, and AI-powered investment recommendations.

## 🏗️ Platform Architecture

```
trading_mvp/
├── README.md          # Project documentation
├── main.py           # CLI entry point for strategy execution
├── requirements.txt  # Python dependencies
├── CLAUDE.md        # Development history and documentation
│
├── frontend/         # React TypeScript dashboard
│   ├── src/         # Source code
│   ├── public/      # Static assets
│   └── README.md    # Frontend documentation
│
├── backend/         # FastAPI REST API server
│   ├── app/         # Application code
│   ├── data/        # Backend data cache
│   └── README.md    # Backend API documentation
│
├── strategies/      # Trading strategy implementations
│   ├── wheel_strategy.py        # Options wheel strategy
│   └── crypto_rotator_strategy.py # Crypto rotation strategy
│
├── engines/         # Backtesting and analysis engines
│   └── backtesting_engine.py    # Performance analysis
│
├── data/           # Market data integration
│   ├── price_fetcher.py         # Live data APIs
│   └── cache/                   # Data caching
│
├── config/         # Configuration management
│   └── config.yaml             # Strategy configuration
│
├── scripts/        # Utility scripts and tools
│   ├── summary_report.py       # Performance reporting
│   └── README.md              # Scripts documentation
│
├── logs/          # Application logs and trade data
│   └── trades.csv            # Trade execution logs
│
└── venv/          # Python virtual environment
```

## 🎯 Core Features

### 📊 **Trading Strategies**
- **Options Wheel Strategy**: Cash-secured puts and covered calls on ETFs (SPY, QQQ, IWM)
- **Crypto Rotator Strategy**: Momentum-based rotation between cryptocurrencies (BTC, ETH, SOL)
- **Multi-strategy execution** with dynamic capital allocation

### 🔄 **Live Market Data Integration**
- **CoinGecko API** for real-time cryptocurrency prices
- **Alpha Vantage API** for stock/ETF data with backup fallback
- **Yahoo Finance** integration with error handling
- **Rate limiting** and **caching** for API efficiency
- **Health monitoring** and **automatic fallbacks**

### 📈 **Analysis & Backtesting**
- **Comprehensive backtesting engine** with historical performance analysis
- **AI-powered investment recommendations** with confidence scoring
- **Portfolio performance metrics** (Sharpe ratio, max drawdown, volatility)
- **Risk assessment** and **position sizing** recommendations

### 🖥️ **Modern Web Interface**
- **React TypeScript** frontend with Tailwind CSS
- **Real-time dashboard** with interactive charts and tables
- **Multi-tab interface** for different workflows
- **Responsive design** with mobile support
- **Error handling** and **loading states** throughout

## 🚀 Quick Start

### Prerequisites
```bash
# Backend dependencies
pip install -r requirements.txt

# Frontend dependencies  
cd frontend && npm install
```

### Environment Setup
```bash
# Copy environment template
cp .env.example .env

# Add your API keys to .env
COINGECKO_API_KEY=your_coingecko_key
ALPHA_VANTAGE_API_KEY=your_alpha_vantage_key
```

### Run the Platform
```bash
# Start backend API server
python backend/main.py

# Start frontend development server (in new terminal)
cd frontend && npm run dev
```

Access the dashboard at `http://localhost:5174`

## 📚 Documentation

### Module Documentation
- [Frontend Architecture](frontend/README.md) - React TypeScript dashboard
- [Backend API](backend/README.md) - FastAPI server and endpoints
- [Scripts & Tools](scripts/README.md) - Utility scripts and analysis tools
- [Development History](CLAUDE.md) - Comprehensive development documentation

### Quick References
- **Configuration**: `config/config.yaml` - Strategy and system settings
- **CLI Usage**: `python main.py --help` - Command-line interface
- **API Docs**: `http://localhost:8001/docs` - Interactive API documentation
- **Dashboard**: `http://localhost:5174` - Web interface

## 🏛️ System Architecture

### Backend (FastAPI)
```python
backend/
├── app/
│   ├── api.py              # Main FastAPI application
│   └── routes/             # API route handlers
│       ├── config.py       # Configuration management
│       ├── strategies.py   # Strategy execution
│       ├── recommendations.py # AI recommendations
│       └── files.py        # File operations
├── data/                   # Data processing and caching
└── main.py                # Server entry point
```

### Frontend (React + TypeScript)
```typescript
frontend/src/
├── components/             # React components
│   ├── common/            # Reusable UI components
│   └── [Feature]Panel.tsx # Feature-specific panels
├── hooks/                 # Custom React hooks
├── services/              # API integration
├── utils/                 # Utility functions
├── types/                 # TypeScript definitions
└── App.tsx               # Main application
```

### Trading Engine
```python
strategies/
├── wheel_strategy.py      # Options wheel implementation
├── crypto_rotator_strategy.py # Crypto rotation strategy
└── __init__.py           # Strategy registry

engines/
└── backtesting_engine.py # Performance analysis engine
```

## 🔧 Configuration

### Strategy Configuration (`config/config.yaml`)
```yaml
initial_capital: 100000
data_mode: "live"  # "live" | "mock"

strategies:
  wheel: true
  rotator: true

allocation:
  wheel: 0.5
  rotator: 0.5

wheel_symbols: ['SPY', 'QQQ', 'IWM']
rotator_symbols: ['BTC', 'ETH', 'SOL']

simulation:
  weeks_to_simulate: 8
  enable_deterministic_mode: true
```

### API Configuration (`.env`)
```bash
# Market Data APIs
COINGECKO_API_KEY=your_key_here
ALPHA_VANTAGE_API_KEY=your_key_here

# Rate Limiting
CRYPTO_RATE_LIMIT_PER_MIN=10
ETF_RATE_LIMIT_PER_MIN=5

# Caching
ENABLE_CACHE=true
CACHE_EXPIRY_MINUTES=60
```

## 📊 Performance Metrics

The platform provides comprehensive performance analysis:

### Strategy Metrics
- **Total Return**: Overall portfolio performance
- **Sharpe Ratio**: Risk-adjusted returns
- **Maximum Drawdown**: Largest loss from peak
- **Win Rate**: Percentage of profitable trades
- **Volatility**: Price movement variability

### Real-time Monitoring
- **API Health Checks**: Monitor data source availability
- **Execution Tracking**: Real-time trade logging
- **Error Monitoring**: Comprehensive error tracking
- **Performance Dashboards**: Visual performance metrics

## 🛡️ Security & Best Practices

### API Security
- **Environment-based configuration** for sensitive data
- **API key masking** in logs for security
- **Request rate limiting** to prevent abuse
- **Input validation** and **sanitization**

### Code Quality
- **TypeScript** for type safety and developer experience
- **ESLint** and **Prettier** for code consistency
- **Comprehensive error handling** throughout the stack
- **Logging** with appropriate levels and filtering

## 🔄 Development Workflow

### Code Organization
- **Single Responsibility Principle** applied throughout
- **Separation of concerns** between modules
- **Reusable components** and utility functions
- **Type-safe interfaces** between modules

### Testing Strategy
- **Unit tests** for core business logic
- **Integration tests** for API endpoints
- **Component tests** for React components
- **End-to-end tests** for critical user workflows

## 📈 Future Roadmap

### Near-term Enhancements
1. **Advanced Options Strategies** (Iron Condors, Straddles)
2. **Machine Learning Models** for price prediction
3. **Portfolio Optimization** algorithms
4. **Real-time Alerts** and notifications

### Long-term Goals
1. **Multi-asset Support** (Forex, Commodities, Bonds)
2. **Social Trading** features and strategy sharing
3. **Mobile Application** for iOS and Android
4. **Institutional Features** for larger portfolios

## 🤝 Contributing

We welcome contributions! Please see our [Contributing Guide](docs/contributing.md) for:
- Development setup instructions
- Code style guidelines
- Pull request process
- Issue reporting templates

## 📄 License

This project is licensed under the MIT License. See [LICENSE](LICENSE) for details.

## 🆘 Support

- **Documentation**: Comprehensive guides in `/docs`
- **Issues**: Report bugs via GitHub Issues
- **Discussions**: Feature requests and general questions
- **Email**: Support contact for urgent issues

---

**Trading MVP Platform** - A comprehensive, production-ready trading system built with modern technologies and best practices for reliable, scalable investment management.