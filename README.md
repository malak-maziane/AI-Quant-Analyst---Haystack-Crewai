# AI Quant Analyst - Haystack + CrewAI
### Enterprise-Grade Financial Analysis Platform Powered by Multi-Agent AI and RAG

<div align="center">

![Python](https://img.shields.io/badge/Python-3.10+-blue.svg?style=flat-square&logo=python)
![CrewAI](https://img.shields.io/badge/CrewAI-0.28.0+-orange.svg?style=flat-square)
![Haystack](https://img.shields.io/badge/Haystack-2.3.0+-green.svg?style=flat-square)
![Flask](https://img.shields.io/badge/Flask-3.0.3-black.svg?style=flat-square&logo=flask)
![Streamlit](https://img.shields.io/badge/Streamlit-1.35.0-red.svg?style=flat-square&logo=streamlit)
![License](https://img.shields.io/badge/License-MIT-green.svg?style=flat-square)

Revolutionary AI-powered financial analysis combining Multi-Agent AI, Retrieval Augmented Generation (RAG), and real-time market data to deliver institutional-grade investment recommendations.

[Features](#features) • [Quick Start](#quick-start) • [Architecture](#architecture) • [API](#api-endpoints) • [Contributing](#contributing)

</div>

---

## What is AI Quant Analyst?

AI Quant Analyst is a next-generation financial intelligence platform that deploys a team of autonomous AI specialists who collaborate in real-time to analyze markets, evaluate risks, and generate data-driven investment recommendations. Unlike traditional financial analysis tools, our system combines:

- Multi-Agent AI (4 specialized agents working together)
- Retrieval Augmented Generation (RAG with financial document understanding)
- Real-Time Market Data (yfinance, Finnhub, NewsAPI)
- Institutional-Grade Analysis (Technical, Sentiment, Risk, Advisory)
- Dual Interfaces (Flask API + Streamlit Dashboard)

**Perfect for:** Quantitative traders, Finance students, Portfolio managers, Investment analysts, AI/ML practitioners, FinTech developers

---

## Features

### Comprehensive Financial Analysis
- Technical Analysis - SMA, RSI, MACD, Bollinger Bands, trend detection
- Sentiment Analysis - News aggregation, market psychology, catalyst identification
- Risk Modeling - VaR, max drawdown, volatility forecasting, stress testing
- Price Prediction - Trend extrapolation, support/resistance levels

### Intelligent Agents
- Data Analyst - Quantitative analysis, technical indicators, price patterns
- News Analyst - Sentiment extraction, market intelligence, catalysts
- Risk Analyst - Portfolio risk assessment, scenario analysis, alerts
- Investment Advisor - Recommendations synthesis, position sizing, entry/exit

### Production Interfaces
- Streamlit Dashboard - Interactive real-time charts, document upload
- Flask Web App - RESTful API, form-based UI, batch processing
- Both share same core - CrewAI analysis pipeline

### Enterprise Features
- RESTful API with validation
- Error handling and graceful fallbacks
- Multi-ticker parallel processing
- Data caching and optimization
- Complete audit logging
- Security best practices

---

## Key Highlights

### 4 Autonomous AI Agents
```
Data Analyst       → Technical analysis, trend detection, momentum
News Analyst       → Sentiment analysis, market intelligence, catalysts
Risk Analyst       → Portfolio risk, VaR, stress testing, scenarios
Investment Advisor → Synthesis, recommendations, position sizing
```

### Advanced RAG Pipeline
- Haystack integration for document processing
- Vector embeddings for semantic search
- ChromaDB vector database
- Multi-document analysis (earnings reports, prospectuses, risk disclosures)

### Multi-Source Data Integration
- yfinance - OHLCV, technical indicators
- Finnhub - Institutional news, earnings calendar
- NewsAPI - Global news sentiment
- Real-time market data with automatic caching

### Two Production-Ready Interfaces
| Interface | Best For | Features |
|-----------|----------|----------|
| Streamlit Dashboard | Data Scientists, Analysts | Interactive charts, real-time updates, document upload |
| Flask API | Developers, Integrations | RESTful endpoints, programmatic access, batch processing |

### Intelligent Fallback System
Continues operating even without API keys using deterministic analysis pipeline.

---

## System Architecture

```
┌────────────────────────────────────────────────────────────────────────┐
│                        USER INTERFACES                                 │
│  ┌──────────────────────────┐         ┌──────────────────────────┐   │
│  │   Flask Web App          │         │  Streamlit Dashboard     │   │
│  │  http://localhost:5000   │         │ http://localhost:8501    │   │
│  └──────────────┬───────────┘         └──────────┬───────────────┘   │
└─────────────────┼──────────────────────────────────┼─────────────────┘
                  │                                  │
                  └──────────────────┬───────────────┘
                                     │
┌────────────────────────────────────────────────────────────────────────┐
│                   CREWAI ORCHESTRATION LAYER                           │
│                                                                        │
│  ┌────────────────────────────────────────────────────────────────┐  │
│  │  Crew Manager (app/crew.py)                                    │  │
│  │  - 4 Specialized AI Agents                                     │  │
│  │  - Task Pipeline Management                                    │  │
│  │  - Output Validation & Formatting                              │  │
│  │  - Error Handling & Fallbacks                                  │  │
│  └────────────────────────────────────────────────────────────────┘  │
│                                                                        │
│  Data Analyst │  News Analyst │  Risk Analyst │  Investment Advisor  │
│                                                                        │
└────────────┬─────────────────────────────────────────────┬────────────┘
             │                                             │
┌────────────┴─────────────────────────────────────────────┴────────────┐
│                      TOOLS & DATA LAYER                               │
│                                                                        │
│  Market Data Tools                Document Processing               │
│  - yfinance                       - Haystack RAG                    │
│  - Finnhub API                    - Vector Embeddings              │
│  - NewsAPI                        - ChromaDB Storage               │
│  - Technical Calculation          - PDF Processing                 │
│                                                                        │
└─────────────────────┬─────────────────────────────────────────────────┘
                      │
                      ↓
┌────────────────────────────────────────────────────────────────────────┐
│           STRUCTURED OUTPUT: JSON Recommendation                       │
│                                                                        │
│  - Market Analysis (Price, SMA, Volatility, Trend)                   │
│  - Sentiment Analysis (Score, Insights, Drivers)                     │
│  - Risk Assessment (Score 0-100, Risk Level, Scenarios)              │
│  - Investment Decision (BUY/HOLD/SELL + Confidence + Rationale)      │
│                                                                        │
└────────────────────────────────────────────────────────────────────────┘
```

---

## Quick Start (5 Minutes)

### Prerequisites
- Python 3.10+
- Git
- API Keys (optional - system works with fallback):
  - OpenAI (https://platform.openai.com/api-keys)
  - Finnhub (https://finnhub.io/)
  - NewsAPI (https://newsapi.org/)

### Installation

```bash
# 1. Clone repository
git clone https://github.com/malak-maziane/AI-Quant-Analyst---Haystack-Crewai.git
cd AI-Quant-Analyst---Haystack-Crewai

# 2. Create virtual environment
python -m venv .venv
.venv\Scripts\activate  # Windows
# source .venv/bin/activate  # macOS/Linux

# 3. Install dependencies
pip install -r requirements.txt

# 4. Configure environment
cp .env.example .env
# Edit .env and add OPENAI_API_KEY if available
```

### Launch

Streamlit Dashboard (Recommended):
```bash
streamlit run app.py
# Opens at http://localhost:8501
```

Flask Web Application:
```bash
python app/main.py
# Opens at http://localhost:5000
```

---

## Features

### Comprehensive Financial Analysis
- Technical Analysis - SMA, RSI, MACD, Bollinger Bands, trend detection
- Sentiment Analysis - News aggregation, market psychology, catalyst identification
- Risk Modeling - VaR, max drawdown, volatility forecasting, stress testing
- Price Prediction - Trend extrapolation, support/resistance levels

### Intelligent Agents
- Data Analyst - Quantitative analysis, technical indicators, price patterns
- News Analyst - Sentiment extraction, market intelligence, catalysts
- Risk Analyst - Portfolio risk assessment, scenario analysis, alerts
- Investment Advisor - Recommendations synthesis, position sizing, entry/exit

### Production Interfaces
- Streamlit Dashboard - Interactive real-time charts, document upload
- Flask Web App - RESTful API, form-based UI, batch processing
- Both share same core - CrewAI analysis pipeline

### Enterprise Features
- RESTful API with validation
- Error handling and graceful fallbacks
- Multi-ticker parallel processing
- Data caching and optimization
- Complete audit logging
- Security best practices

---

## AI Agents Overview

| Agent | Role | Tools | Output |
|-------|------|-------|--------|
| Data Analyst | Quantitative Data Analyst | MarketDataTool | Trend analysis, technical indicators |
| News Analyst | Financial NLP Analyst | DocumentReaderTool | Sentiment analysis, key insights |
| Risk Analyst | Risk Management Specialist | None | Risk score, alerts |
| Investment Advisor | Senior Investment Advisor | None | BUY/HOLD/SELL recommendation |

---

## API Endpoints (Flask)

| Method | Route | Description |
|--------|-------|-------------|
| GET | / | Landing page with analysis form |
| POST | /analyze | Process analysis request |
| GET | /result | Display analysis results |
| GET/POST | /api/analyze | JSON API for analysis |
| GET | /health | Health check endpoint |

---

## Tech Stack

| Tool | Version | Purpose |
|------|---------|---------|
| crewai | 0.28.0 | Multi-agent orchestration |
| haystack-ai | 2.3.0 | Document RAG pipeline |
| yfinance | 0.2.38 | Financial data fetching |
| flask | 3.0.3 | Web application framework |
| streamlit | 1.35.0 | Interactive dashboard |
| pandas | 2.2.0 | Data manipulation |
| plotly | 5.22.0 | Data visualization |

---

## Project Structure

```
AI-Quant-Analyst---Haystack-Crewai/
│
├── app/                          # Flask + CrewAI core
│   ├── __init__.py               # Flask app factory
│   ├── main.py                   # Flask entry point
│   ├── agents.py                 # 4 AI agent definitions
│   ├── tasks.py                  # Task definitions
│   ├── crew.py                   # CrewAI orchestration
│   ├── utils.py                  # Helper functions
│   ├── routes.py                 # Flask routes & API
│   └── forms.py                  # WTForms validation
│
├── tools/                        # Data & NLP tools
│   ├── __init__.py
│   ├── market_data.py            # yfinance + indicators
│   └── document_reader.py        # Haystack RAG pipeline
│
├── templates/                    # Flask HTML templates
│   ├── base.html                 # Layout template
│   ├── index.html                # Landing page
│   ├── result.html               # Results dashboard
│   ├── loading.html              # Loading screen
│   └── error.html                # Error page
│
├── static/                       # Flask assets
│   ├── css/style.css             # Dark finance theme
│   ├── js/main.js                # Form handling
│   ├── js/charts.js              # Chart.js integration
│   └── img/logo.png              # Project logo
│
├── data/                         # Sample data
│   └── sample_news.txt           # Sample financial text
│
├── uploads/                      # User file uploads
│
├── app.py                        # Streamlit entry point
├── config.py                     # Global configuration
├── requirements.txt              # Python dependencies
├── .env.example                  # Environment template
├── .gitignore                    # Git ignore rules
└── README.md                     # This file
```

---

## Configuration

### Environment Variables (.env)

```bash
# OpenAI API Configuration
OPENAI_API_KEY=sk-your-key-here
OPENAI_MODEL=gpt-4-turbo-preview

# Financial Data APIs
FINNHUB_API_KEY=your_finnhub_key
NEWS_API_KEY=your_newsapi_key

# Flask Configuration
SECRET_KEY=your-super-secret-key
DEBUG=False
FLASK_ENV=production

# Application Settings
UPLOAD_FOLDER=uploads
MAX_CONTENT_LENGTH=104857600
CACHE_ENABLED=true
```

---

## Security Best Practices

### API Key Management
```bash
# Don't commit real keys
git add .env  # WRONG

# Use environment-specific .env
.env.local (for development - gitignored)
.env.production (for production - gitignored)

# Use .env.example for template
.env.example (committed to repo - no sensitive data)
```

---

## Use Cases

### Day Trader Analysis
```python
from app.crew import QuantAnalystCrew

crew = QuantAnalystCrew(ticker="TSLA")
results = crew.run()

entry_price = results['advisor_recommendation']['entry_points'][0]['price']
stop_loss = results['advisor_recommendation']['stop_loss']
print(f"Buy TSLA at ${entry_price}, stop at ${stop_loss}")
```

### Portfolio Risk Assessment
```python
portfolio_tickers = ["AAPL", "MSFT", "JPM", "JNJ", "XOM"]

for ticker in portfolio_tickers:
    crew = QuantAnalystCrew(ticker=ticker)
    results = crew.run()
    risk_score = results['risk_analyst']['risk_score_0_to_100']
    print(f"{ticker}: Risk Score = {risk_score}/100")
```

### Event-Driven Analysis
```python
crew = QuantAnalystCrew(
    ticker="NVDA",
    question="What is the market impact of the Q4 earnings beat?",
    document_path="NVDA_Q4_Earnings.pdf"
)
results = crew.run()
```

---

## Troubleshooting

### OPENAI_API_KEY not found
```bash
# Verify .env file exists
ls -la .env

# Ensure key is set correctly
echo $OPENAI_API_KEY

# Restart application after adding key
```

### yfinance data not available
```python
import yfinance as yf
data = yf.download("AAPL", period="1y")
print(data.head())
```

### CrewAI timeout
```python
os.environ["FORCE_FALLBACK"] = "true"
# Application will use deterministic pipeline
```

### Streamlit app not starting
```bash
streamlit cache clear
streamlit run app.py --logger.level=debug
```

---

## Performance Metrics

Typical analysis runtime on standard hardware:

| Component | Time | Notes |
|-----------|------|-------|
| Market data fetch | 2-3s | yfinance + Finnhub |
| Technical analysis | 1-2s | Indicator calculation |
| Sentiment analysis | 5-10s | News fetching + NLP |
| Risk assessment | 3-5s | Historical volatility |
| Agent synthesis | 10-20s | CrewAI orchestration |
| Total end-to-end | 25-45s | With LLM enabled |
| Fallback mode | 5-10s | Deterministic pipeline |

---

## Data Sources & APIs

| Source | Purpose | Free Tier | Rate Limit |
|--------|---------|-----------|-----------|
| yfinance | Historical OHLCV data, technical indicators | Yes | None |
| Finnhub | Institutional news, earnings calendar | Yes | 60 req/min |
| NewsAPI | Global news aggregation, sentiment data | Yes | 100 req/day |
| OpenAI | CrewAI LLM backbone | Paid | Varies |
| ChromaDB | Vector database for embeddings | Yes | None |

---

## Contributing

Contributions are welcome! Please follow these guidelines:

1. Fork the repository
2. Create a feature branch (git checkout -b feature/amazing-feature)
3. Commit your changes (git commit -m 'Add amazing feature')
4. Push to the branch (git push origin feature/amazing-feature)
5. Open a Pull Request

### Contribution Areas
- Bug fixes and error handling
- New agents or analysis types
- Additional data sources
- UI/UX improvements
- Documentation and examples
- Test coverage

---

## License

This project is licensed under the MIT License - see the LICENSE file for details.

You are free to:
- Use commercially
- Modify the source code
- Distribute copies
- Use for private projects

You must:
- Include license and copyright notice
- State significant changes made

---

## Support & Contact

- Email: malakmaziane2@gmail.com
- GitHub Issues: https://github.com/malak-maziane/AI-Quant-Analyst---Haystack-Crewai/issues
- GitHub Discussions: https://github.com/malak-maziane/AI-Quant-Analyst---Haystack-Crewai/discussions

---

## Roadmap

### Phase 1: Complete (v1.0)
- [x] Multi-agent AI framework
- [x] Technical analysis module
- [x] Sentiment analysis
- [x] Risk assessment
- [x] Streamlit dashboard
- [x] Flask API

### Phase 2: In Progress (v1.5)
- [ ] Backtesting engine
- [ ] Portfolio optimization
- [ ] Options pricing (Black-Scholes)
- [ ] Machine learning predictions
- [ ] Email alerts and notifications

### Phase 3: Planned (v2.0)
- [ ] Real-time WebSocket API
- [ ] Docker containerization
- [ ] Cloud deployment (AWS/GCP)
- [ ] Mobile app
- [ ] Premium features (paid tier)

---

## Author

Malak Maziane - malakmaziane2@gmail.com

---

Made with care for the quantitative finance community