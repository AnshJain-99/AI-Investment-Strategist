# 📈 InvestIQ - AI Investment Strategist & Quantitative Research Platform

InvestIQ is an institutional-grade, web-based financial research and portfolio management platform designed to simplify Indian stock market analysis and empower investors with deterministic quantitative scoring and AI-powered insights.

The platform provides real-time market data, detailed fundamental and technical analysis, interactive price charts, stock comparison engines, FIFO portfolio accounting, and multi-model AI synthesis through a clean, high-performance web interface.

---

## 🏛️ System Architecture

### 🎨 Frontend Architecture
- **Framework & Templating**: **Flask + Jinja2** server-rendered templates
- **Markup & Styling**: Semantic **HTML5**, Modern **CSS3** (Custom design system + CSS variables + Dark Mode support)
- **UI Components & Icons**: **Bootstrap 5.3**, **Bootstrap Icons**
- **Client-Side Scripting**: **Vanilla ES6+ JavaScript** (No heavyweight frontend build chains required)
- **Interactive Visualizations**: **Chart.js** (Multi-timeframe candlestick & line price charts, portfolio allocation donuts, financial metric comparisons)

### ⚙️ Backend Architecture
- **Language & Runtime**: **Python 3.12+**
- **Core Framework**: **Flask** microframework
- **ORM & Data Layer**: **Flask-SQLAlchemy**
- **Authentication & Security**: **Flask-Login** (Session security, user isolation), **Flask-Bcrypt** (Password hashing), Google Identity Services (GIS OAuth)
- **Caching & Stampede Protection**: Thread-safe in-memory cache with stale-while-revalidate TTL and dogpile lock protection

### 🗄️ Database Architecture
- **Primary Database**: **SQLite 3** (`instance/database.db`) with relational integrity
- **Models**:
  - `User`: Account credentials, profile preferences, Google OAuth mappings
  - `Portfolio`: User-isolated investment portfolios with health metrics
  - `Holding`: Realized/unrealized FIFO positions, weighted cost basis, real-time allocation %
  - `Transaction`: Complete audit ledger for buy/sell order execution
  - `Watchlist`: User-scoped tracked equities
  - `Notification`: User price alerts and portfolio health advisories

### 📡 External Market Data Providers
- **Equity Prices & Fundamentals**: **Yahoo Finance** via [`yfinance`](https://github.com/ranaroussi/yfinance) (Real-time prices, 52-week ranges, PE, ROE, debt ratios, earnings history)
- **News Sentiment Feeds**: **Google News RSS** with topic-filtered ticker parsing

### 🤖 AI & Quantitative Scoring Engine
- **Deterministic 7-Pillar Quantitative Engine**:
  - Fundamentals (25%), Technical Structure (20%), Valuation Multiples (15%), Price Momentum (15%), News Sentiment (10%), Risk Resilience (10%), Liquidity (5%)
  - ATR-derived structural target prices and trailing stop-loss calculations
- **Multi-Model LLM Gateway (`LLMService`)**:
  - Primary Model: `openai/gpt-4o-mini`
  - Configurable Fallback Chain: `anthropic/claude-3.5-haiku` $\to$ `google/gemini-2.5-flash` $\to$ `openai/gpt-4o`
  - Features: Fast-path immediate return on success, transient error retries (429/5xx/Timeout) with bounded jitter backoff, permanent error fast-fail (401/403/400), prompt-injection defenses, and graceful deterministic qualitative fallbacks.

---

## ✨ Key Features

- 📊 **Real-Time Market Tracking**: Live Nifty 50, Sensex, and individual stock telemetry.
- 🔍 **Dynamic Stock Search**: Instant symbol and company lookup across Indian equities (`.NS` / `.BO`).
- 📈 **Quantitative Stock Analysis**: Multi-factor scoring with signal categorization (`STRONG BUY`, `BUY`, `HOLD`, `REDUCE`, `AVOID`).
- 🤖 **Conversational AI Research Assistant**: Interactive grounding in verified financial metrics with anti-hallucination guardrails.
- ⚖️ **Multi-Stock Comparison**: Side-by-side comparative financial and technical analysis of up to 3 stocks.
- 💼 **Portfolio Tracker**: FIFO cost basis calculation, unrealized/realized P&L, sector allocation, and AI portfolio health analysis.
- 📉 **Interactive Charts**: Dynamic historical filters (1M, 6M, 1Y, 3Y, 5Y).
- 📰 **Sentiment Analysis**: Aggregated market news and sentiment classification.
- 🔐 **Enterprise Security**: User data isolation, CSRF protection, and OAuth integration.

---

## 🚀 Getting Started

### 1. Clone & Install Dependencies
```bash
git clone https://github.com/AnshJain-99/AI-Investment-Strategist.git
cd AI-Investment-Strategist
python -m venv venv
# On Windows:
venv\Scripts\activate
# On Linux/macOS:
source venv/bin/activate
pip install -r requirements.txt
```

### 2. Configure Environment Variables
Create a `.env` file in the project root:
```env
SECRET_KEY=your-secure-random-secret
OPENROUTER_API_KEY=your-openrouter-api-key
LLM_PRIMARY_MODEL=openai/gpt-4o-mini
LLM_FALLBACK_MODELS=anthropic/claude-3.5-haiku,google/gemini-2.5-flash,openai/gpt-4o
LLM_TIMEOUT=12
LLM_MAX_RETRIES=1
```

### 3. Run Application
```bash
python app.py
```
Open [http://localhost:5000](http://localhost:5000) in your browser.

---

## 🧪 Testing

Run the full automated test suite:
```bash
python -m unittest discover -s tests -v
```

---

## ⚠️ Disclaimer

This application is developed for educational and quantitative research purposes only. Numerical calculations and qualitative research summaries do not constitute financial advice. Conduct independent due diligence before making capital investment decisions.
