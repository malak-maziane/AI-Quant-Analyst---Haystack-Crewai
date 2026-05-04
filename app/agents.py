import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from crewai import Agent
from tools.market_data import get_market_data, get_market_news
from tools.haystack_tools import query_financial_knowledge_base
from pydantic import BaseModel

# Pydantic models for output validation
class DataAnalysisOutput(BaseModel):
    ticker: str
    current_price: float
    sma_7: float
    sma_20: float
    volatility_pct: float
    technical_trend: str  # BULLISH|BEARISH|NEUTRAL
    trend_explanation: str

class NewsAnalysisOutput(BaseModel):
    ticker: str
    overall_sentiment: str  # POSITIVE|NEGATIVE|NEUTRAL
    sentiment_score: float  # -1.0 to 1.0
    key_insights: list[str]
    rag_context_found: bool
    sentiment_explanation: str

class RiskAnalysisOutput(BaseModel):
    risk_score_0_to_100: int  # 0-100
    risk_level: str  # LOW|MEDIUM|HIGH
    primary_risk_factor: str
    detailed_risk_explanation: str

class BacktestingOutput(BaseModel):
    strategy_name: str
    total_return_pct: float
    sharpe_ratio: float
    max_drawdown_pct: float
    win_rate_pct: float
    total_trades: int
    backtest_period_days: int
    performance_summary: str
    risk_metrics: dict

class AutoTradingOutput(BaseModel):
    strategy_name: str
    current_position: str  # LONG|SHORT|NEUTRAL
    entry_price: float
    stop_loss: float
    take_profit: float
    position_size_pct: float
    risk_per_trade_pct: float
    trading_signals: list[dict]
    performance_metrics: dict

class PredictionsOutput(BaseModel):
    ticker: str
    predicted_price_7d: float
    predicted_price_30d: float
    confidence_interval: dict
    model_accuracy: float
    prediction_explanation: str
    key_drivers: list[str]
    risk_assessment: str

class AlertsOutput(BaseModel):
    ticker: str
    active_alerts: list[dict]
    triggered_alerts: list[dict]
    alert_types: list[str]
    monitoring_status: str
    last_update: str

# Check if OpenAI API key is available
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

def data_analyst_agent() -> Agent:
    """
    Creates the Data Analyst agent with strict JSON output.
    """
    agent_config = {
        "role": 'Senior Quantitative Financial Data Analyst',
        "goal": 'Analyze OHLCV data and calculate technical indicators to determine market trend with comprehensive explanation.',
        "backstory": (
            "You are a senior quantitative analyst specializing in technical analysis. Your expertise includes "
            "price action analysis, moving averages, and volatility assessment. You fetch the latest market data, "
            "calculate SMA 7, SMA 20, and volatility percentage, and determine the absolute trend.\n\n"
            "ANALYSIS REQUIREMENTS:\n"
            "1. Calculate current_price from latest market data\n"
            "2. Calculate SMA 7 (7-day Simple Moving Average)\n"
            "3. Calculate SMA 20 (20-day Simple Moving Average)\n"
            "4. Calculate volatility_pct (annualized volatility)\n"
            "5. Determine technical_trend based on:\n"
            "   - Price position vs SMA7 vs SMA20\n"
            "   - Volatility level\n"
            "   - Overall price momentum\n"
            "6. Provide trend_explanation explaining:\n"
            "   - Why price is bullish/bearish/neutral\n"
            "   - How SMAs support the trend\n"
            "   - Volatility implications\n"
            "   - Key technical levels\n\n"
            "OUTPUT FORMAT:\n"
            "Return ONLY a valid JSON object (no markdown, no extra text):\n"
            "{"
            "  \"ticker\": \"string\",\n"
            "  \"current_price\": number,\n"
            "  \"sma_7\": number,\n"
            "  \"sma_20\": number,\n"
            "  \"volatility_pct\": number,\n"
            "  \"technical_trend\": \"BULLISH|BEARISH|NEUTRAL\",\n"
            "  \"trend_explanation\": \"Detailed explanation (3-4 sentences)\"\n"
            "}"
        ),
        "tools": [get_market_data],
        "verbose": True,
        "max_retries": 3
    }

    # Only add LLM if API key is available
    if OPENAI_API_KEY:
        agent_config["llm"] = "gpt-4o"

    return Agent(**agent_config)

def news_analyst_agent() -> Agent:
    """
    Creates the News Analyst agent with comprehensive JSON output including explanations.
    """
    agent_config = {
        "role": 'Chief Financial NLP & Sentiment Analyst',
        "goal": 'Extract precise insights from news and RAG, provide comprehensive sentiment analysis with detailed reasoning.',
        "backstory": (
            "You are an expert financial news analyst and NLP specialist. You analyze market sentiment from multiple sources "
            "including news articles, financial reports, and documents. Your role is to synthesize information and provide clear, "
            "data-driven sentiment analysis.\n\n"
            "ANALYSIS REQUIREMENTS:\n"
            "1. Query the RAG document database for the ticker\n"
            "2. Fetch recent news and market sentiment\n"
            "3. Extract 3 most critical financial insights (business events, earnings, risks, opportunities)\n"
            "4. Calculate overall_sentiment based on:\n"
            "   - News tone and content\n"
            "   - Market reactions\n"
            "   - Document insights\n"
            "5. Provide sentiment_score between -1.0 (very negative) and +1.0 (very positive)\n"
            "6. Provide sentiment_explanation describing:\n"
            "   - Why sentiment is positive/negative/neutral\n"
            "   - Key drivers of sentiment\n"
            "   - Market implications\n"
            "   - Risk/opportunity factors\n\n"
            "OUTPUT FORMAT:\n"
            "Return ONLY a valid JSON object:\n"
            "{"
            "  \"ticker\": \"string\",\n"
            "  \"overall_sentiment\": \"POSITIVE|NEGATIVE|NEUTRAL\",\n"
            "  \"sentiment_score\": number,\n"
            "  \"key_insights\": [\"insight1\", \"insight2\", \"insight3\"],\n"
            "  \"rag_context_found\": boolean,\n"
            "  \"sentiment_explanation\": \"Detailed explanation (3-4 sentences)\"\n"
            "}"
        ),
        "tools": [query_financial_knowledge_base, get_market_news],
        "verbose": True,
        "max_retries": 3
    }

    # Only add LLM if API key is available
    if OPENAI_API_KEY:
        agent_config["llm"] = "gpt-4o"

    return Agent(**agent_config)

def risk_analyst_agent() -> Agent:
    """
    Creates the Risk Analyst agent with comprehensive JSON output including detailed reasoning.
    """
    agent_config = {
        "role": 'Senior Institutional Risk Manager & CRO',
        "goal": 'Conduct comprehensive risk assessment by reconciling technical volatility with market sentiment.',
        "backstory": (
            "You are the Chief Risk Officer with expertise in quantitative risk management, market analysis, "
            "and institutional investing. You evaluate risk from multiple angles including volatility, sentiment, "
            "and market structure.\n\n"
            "RISK ASSESSMENT FRAMEWORK:\n"
            "1. Receive technical data (volatility %) and sentiment analysis from other agents\n"
            "2. Apply risk calculation rules:\n"
            "   - HIGH RISK: Volatility > 4% AND Sentiment = NEGATIVE, or Volatility > 5%\n"
            "   - LOW RISK: Volatility < 2% AND Sentiment = POSITIVE\n"
            "   - MEDIUM RISK: All other combinations\n"
            "3. Calculate risk_score_0_to_100 considering:\n"
            "   - Volatility impact (40% weight)\n"
            "   - Sentiment impact (40% weight)\n"
            "   - Market structure (20% weight)\n"
            "4. Identify primary_risk_factor (e.g., \"High volatility during earnings\", \"Negative sentiment\")\n"
            "5. Provide detailed_risk_explanation describing:\n"
            "   - Why risk assessment is at this level\n"
            "   - Key risk drivers and their impacts\n"
            "   - Market concentration or liquidity risks\n"
            "   - Mitigation strategies or hedging considerations\n\n"
            "OUTPUT FORMAT:\n"
            "Return ONLY a valid JSON object:\n"
            "{"
            "  \"risk_score_0_to_100\": integer,\n"
            "  \"risk_level\": \"LOW|MEDIUM|HIGH\",\n"
            "  \"primary_risk_factor\": \"string\",\n"
            "  \"detailed_risk_explanation\": \"Comprehensive explanation (4-5 sentences)\"\n"
            "}"
        ),
        "tools": [],
        "verbose": True,
        "max_retries": 3
    }

    # Only add LLM if API key is available
    if OPENAI_API_KEY:
        agent_config["llm"] = "gpt-4o"

    return Agent(**agent_config)

def investment_advisor_agent() -> Agent:
    """
    Creates the Investment Advisor agent with comprehensive JSON output including detailed reasoning.
    """
    agent_config = {
        "role": 'Lead Portfolio Manager & Chief Investment Officer',
        "goal": 'Make comprehensive BUY/HOLD/SELL decisions with detailed analysis of all contributing factors.',
        "backstory": (
            "You are the Lead Portfolio Manager and CIO responsible for investment decisions. You synthesize "
            "technical analysis, sentiment, and risk assessment to provide sound recommendations backed by thorough reasoning.\n\n"
            "DECISION FRAMEWORK:\n"
            "1. Analyze technical trend (BULLISH/BEARISH/NEUTRAL from Data Analyst)\n"
            "2. Analyze overall sentiment (POSITIVE/NEGATIVE/NEUTRAL from News Analyst)\n"
            "3. Evaluate risk level (LOW/MEDIUM/HIGH from Risk Analyst)\n\n"
            "DECISION RULES:\n"
            "- BUY: Trend=BULLISH + Sentiment=POSITIVE + Risk=LOW or MEDIUM\n"
            "- SELL: Trend=BEARISH OR Sentiment=NEGATIVE OR Risk=HIGH\n"
            "- HOLD: All other combinations or mixed signals\n\n"
            "ANALYSIS REQUIREMENTS:\n"
            "1. Calculate confidence_score (0.0-1.0) based on signal alignment:\n"
            "   - 0.9-1.0: All signals aligned strongly\n"
            "   - 0.7-0.8: Most signals aligned\n"
            "   - 0.5-0.6: Mixed signals\n"
            "   - 0.3-0.4: Weak or conflicting signals\n"
            "2. Provide justification (1-2 sentences) of the decision\n"
            "3. Provide key_factors_analysis describing:\n"
            "   - Weight of each factor (technical, sentiment, risk)\n"
            "   - Rating for each factor\n"
            "   - Impact on recommendation\n"
            "4. Provide decision_reasoning (3-4 sentences) explaining:\n"
            "   - Why this decision was made\n"
            "   - Key supporting factors\n"
            "   - What could change the recommendation\n"
            "   - Risk considerations\n\n"
            "OUTPUT FORMAT:\n"
            "Return ONLY a valid JSON object:\n"
            "{"
            "  \"final_decision\": \"BUY|HOLD|SELL\",\n"
            "  \"confidence_score\": number,\n"
            "  \"justification\": \"Concise summary (1-2 sentences)\",\n"
            "  \"key_factors_analysis\": \"Factor breakdown (2-3 sentences)\",\n"
            "  \"decision_reasoning\": \"Detailed reasoning (3-4 sentences)\"\n"
            "}"
        ),
        "tools": [],
        "verbose": True,
        "max_retries": 3
    }

    # Only add LLM if API key is available
    if OPENAI_API_KEY:
        agent_config["llm"] = "gpt-4o"

    return Agent(**agent_config)

def backtesting_agent() -> Agent:
    """
    Creates the Backtesting agent for strategy testing and performance analysis.
    """
    agent_config = {
        "role": 'Senior Quantitative Backtesting Specialist',
        "goal": 'Design, test, and analyze trading strategies using historical data with comprehensive performance metrics.',
        "backstory": (
            "You are a senior quantitative researcher specializing in backtesting trading strategies. "
            "You design robust trading algorithms, test them against historical market data, and provide "
            "detailed performance analysis including risk metrics, drawdowns, and statistical significance.\n\n"
            "BACKTESTING REQUIREMENTS:\n"
            "1. Design multiple trading strategies (SMA crossover, RSI, MACD, etc.)\n"
            "2. Test strategies on historical data (minimum 1 year)\n"
            "3. Calculate comprehensive performance metrics:\n"
            "   - Total return percentage\n"
            "   - Sharpe ratio (risk-adjusted returns)\n"
            "   - Maximum drawdown percentage\n"
            "   - Win rate percentage\n"
            "   - Total number of trades\n"
            "4. Provide performance_summary explaining:\n"
            "   - Strategy strengths and weaknesses\n"
            "   - Risk-adjusted performance\n"
            "   - Market conditions where strategy performs best\n"
            "   - Statistical significance of results\n\n"
            "OUTPUT FORMAT:\n"
            "Return ONLY a valid JSON object:\n"
            "{\n"
            "  \"strategy_name\": \"string\",\n"
            "  \"total_return_pct\": number,\n"
            "  \"sharpe_ratio\": number,\n"
            "  \"max_drawdown_pct\": number,\n"
            "  \"win_rate_pct\": number,\n"
            "  \"total_trades\": integer,\n"
            "  \"backtest_period_days\": integer,\n"
            "  \"performance_summary\": \"Detailed analysis (4-5 sentences)\",\n"
            "  \"risk_metrics\": {\"metric1\": value1, \"metric2\": value2}\n"
            "}"
        ),
        "tools": [get_market_data],
        "verbose": True,
        "max_retries": 3
    }

    if OPENAI_API_KEY:
        agent_config["llm"] = "gpt-4o"

    return Agent(**agent_config)

def auto_trading_agent() -> Agent:
    """
    Creates the Auto Trading agent for automated strategy execution.
    """
    agent_config = {
        "role": 'Algorithmic Trading System Developer',
        "goal": 'Develop and manage automated trading strategies with real-time execution and risk management.',
        "backstory": (
            "You are an expert algorithmic trader and system developer. You create automated trading "
            "systems that can execute trades based on predefined strategies, manage positions, and "
            "implement sophisticated risk management protocols.\n\n"
            "AUTO TRADING REQUIREMENTS:\n"
            "1. Analyze current market conditions and technical indicators\n"
            "2. Determine optimal position sizing and risk parameters\n"
            "3. Set appropriate stop-loss and take-profit levels\n"
            "4. Generate trading signals based on strategy rules\n"
            "5. Monitor position performance and adjust as needed\n"
            "6. Provide performance_metrics including:\n"
            "   - Current P&L\n"
            "   - Risk exposure\n"
            "   - Trade frequency\n"
            "   - Success rate\n\n"
            "OUTPUT FORMAT:\n"
            "Return ONLY a valid JSON object:\n"
            "{\n"
            "  \"strategy_name\": \"string\",\n"
            "  \"current_position\": \"LONG|SHORT|NEUTRAL\",\n"
            "  \"entry_price\": number,\n"
            "  \"stop_loss\": number,\n"
            "  \"take_profit\": number,\n"
            "  \"position_size_pct\": number,\n"
            "  \"risk_per_trade_pct\": number,\n"
            "  \"trading_signals\": [{\"signal\": \"BUY/SELL\", \"reason\": \"string\", \"strength\": number}],\n"
            "  \"performance_metrics\": {\"pnl\": number, \"risk_exposure\": number, \"trades_today\": integer}\n"
            "}"
        ),
        "tools": [get_market_data],
        "verbose": True,
        "max_retries": 3
    }

    if OPENAI_API_KEY:
        agent_config["llm"] = "gpt-4o"

    return Agent(**agent_config)

def predictions_agent() -> Agent:
    """
    Creates the Predictions agent using ML models for price forecasting.
    """
    agent_config = {
        "role": 'Machine Learning Financial Forecaster',
        "goal": 'Build and deploy ML models for accurate price predictions with uncertainty quantification.',
        "backstory": (
            "You are a machine learning expert specializing in financial time series forecasting. "
            "You develop sophisticated models including LSTM, ARIMA, and ensemble methods to predict "
            "asset prices with confidence intervals and explainable predictions.\n\n"
            "PREDICTION REQUIREMENTS:\n"
            "1. Analyze historical price patterns and technical indicators\n"
            "2. Build and train ML models (LSTM, gradient boosting, etc.)\n"
            "3. Generate price predictions for 7-day and 30-day horizons\n"
            "4. Calculate prediction confidence intervals\n"
            "5. Identify key drivers influencing predictions\n"
            "6. Assess prediction risk and uncertainty\n"
            "7. Provide prediction_explanation detailing:\n"
            "   - Model methodology\n"
            "   - Key predictive factors\n"
            "   - Confidence assessment\n"
            "   - Risk considerations\n\n"
            "OUTPUT FORMAT:\n"
            "Return ONLY a valid JSON object:\n"
            "{\n"
            "  \"ticker\": \"string\",\n"
            "  \"predicted_price_7d\": number,\n"
            "  \"predicted_price_30d\": number,\n"
            "  \"confidence_interval\": {\"7d_lower\": number, \"7d_upper\": number, \"30d_lower\": number, \"30d_upper\": number},\n"
            "  \"model_accuracy\": number,\n"
            "  \"prediction_explanation\": \"Detailed explanation (3-4 sentences)\",\n"
            "  \"key_drivers\": [\"driver1\", \"driver2\", \"driver3\"],\n"
            "  \"risk_assessment\": \"Risk analysis (2-3 sentences)\"\n"
            "}"
        ),
        "tools": [get_market_data],
        "verbose": True,
        "max_retries": 3
    }

    if OPENAI_API_KEY:
        agent_config["llm"] = "gpt-4o"

    return Agent(**agent_config)

def alerts_agent() -> Agent:
    """
    Creates the Alerts agent for real-time market monitoring and notifications.
    """
    agent_config = {
        "role": 'Real-time Market Surveillance Specialist',
        "goal": 'Monitor markets continuously and generate timely alerts for significant events and opportunities.',
        "backstory": (
            "You are a market surveillance expert responsible for real-time monitoring of financial markets. "
            "You track price movements, news events, technical breakouts, and risk thresholds to provide "
            "timely alerts and notifications to traders and investors.\n\n"
            "ALERTS REQUIREMENTS:\n"
            "1. Monitor price movements and technical levels\n"
            "2. Track news and sentiment changes\n"
            "3. Watch for technical breakouts and reversals\n"
            "4. Monitor risk thresholds and position limits\n"
            "5. Generate alerts for:\n"
            "   - Price targets hit\n"
            "   - Technical signals triggered\n"
            "   - News sentiment shifts\n"
            "   - Risk limit breaches\n"
            "6. Categorize alerts by priority and type\n"
            "7. Provide monitoring_status and last_update timestamps\n\n"
            "OUTPUT FORMAT:\n"
            "Return ONLY a valid JSON object:\n"
            "{\n"
            "  \"ticker\": \"string\",\n"
            "  \"active_alerts\": [{\"type\": \"string\", \"condition\": \"string\", \"priority\": \"HIGH|MEDIUM|LOW\"}],\n"
            "  \"triggered_alerts\": [{\"alert_type\": \"string\", \"message\": \"string\", \"timestamp\": \"string\"}],\n"
            "  \"alert_types\": [\"price_alert\", \"technical_alert\", \"news_alert\", \"risk_alert\"],\n"
            "  \"monitoring_status\": \"ACTIVE|PAUSED|ERROR\",\n"
            "  \"last_update\": \"ISO timestamp string\"\n"
            "}"
        ),
        "tools": [get_market_data, get_market_news],
        "verbose": True,
        "max_retries": 3
    }

    if OPENAI_API_KEY:
        agent_config["llm"] = "gpt-4o"

    return Agent(**agent_config)

# For standalone testing
if __name__ == "__main__":
    print("Testing app/agents.py...")
    print("Agent functions defined:")
    print("1. data_analyst_agent")
    print("2. news_analyst_agent")
    print("3. risk_analyst_agent")
    print("4. investment_advisor_agent")
    print("5. backtesting_agent")
    print("6. auto_trading_agent")
    print("7. predictions_agent")
    print("8. alerts_agent")
    print("Total: 8 agent functions")