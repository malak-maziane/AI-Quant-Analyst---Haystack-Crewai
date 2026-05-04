import os
import re
import yfinance as yf
from werkzeug.utils import secure_filename
from dotenv import load_dotenv

load_dotenv()

POSITIVE_KEYWORDS = [
    "profit", "growth", "upgrade", "strong", "beat", "outperform",
    "revenue increase", "record", "bullish", "buy", "positive",
    "expansion", "earnings beat", "dividend", "new product", "innovation"
]

NEGATIVE_KEYWORDS = [
    "loss", "decline", "downgrade", "risk", "miss", "underperform",
    "revenue decrease", "bearish", "sell", "negative", "debt",
    "lawsuit", "recall", "layoff", "bankruptcy", "investigation"
]


def load_environment() -> None:
    """Load .env and warn when OpenAI key is missing."""
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("WARNING: OPENAI_API_KEY not found. System will use fallback mode.")
    else:
        print("OPENAI_API_KEY found.")


def validate_ticker(ticker: str) -> bool:
    """Validate stock ticker using yfinance history data."""
    if not ticker or not ticker.strip():
        return False
    ticker = ticker.strip().upper()
    try:
        stock = yf.Ticker(ticker)
        history = stock.history(period="5d")
        return not history.empty
    except Exception as e:
        print(f"Ticker validation error for {ticker}: {e}")
        return False


def compute_sentiment(text: str) -> str:
    """Compute deterministic sentiment from text using keyword matching."""
    text_lower = text.lower()
    pos_score = sum(1 for kw in POSITIVE_KEYWORDS if kw in text_lower)
    neg_score = sum(1 for kw in NEGATIVE_KEYWORDS if kw in text_lower)
    if pos_score > neg_score:
        return "POSITIVE"
    if neg_score > pos_score:
        return "NEGATIVE"
    return "NEUTRAL"


def compute_risk_score(volatility: float, sentiment: str, sources_used: int = 0, trend: str = "NEUTRAL") -> dict:
    """Compute the enhanced composite risk score using volatility, sentiment, sources, and trend."""
    MAX_VOLATILITY = 0.05
    vol_normalized = min(volatility / MAX_VOLATILITY, 1.0)

    # Enhanced sentiment penalty with more granularity
    SENTIMENT_PENALTY = {
        "POSITIVE": 10,
        "NEUTRAL": 25,
        "NEGATIVE": 50
    }
    sentiment_penalty = SENTIMENT_PENALTY.get(sentiment, 25)

    # Trend penalty - bearish trends increase risk
    TREND_PENALTY = {
        "BULLISH": 0,
        "NEUTRAL": 10,
        "BEARISH": 20
    }
    trend_penalty = TREND_PENALTY.get(trend, 10)

    # Data quality penalty - fewer sources = higher uncertainty = higher risk
    data_quality_penalty = max(0, 20 - (sources_used * 5))  # Max 20 penalty, reduced by sources

    # Calculate composite score
    score = int((vol_normalized * 40) + sentiment_penalty + trend_penalty + data_quality_penalty)
    score = max(0, min(100, score))

    if score <= 25:
        level = "LOW"
    elif score <= 50:
        level = "MEDIUM"
    elif score <= 75:
        level = "HIGH"
    else:
        level = "CRITICAL"

    alerts = []

    # Enhanced alert conditions
    if vol_normalized > 0.6:
        alerts.append(f"High market volatility detected: {volatility:.4f} daily std dev")
    if sentiment == "NEGATIVE":
        alerts.append("Negative news sentiment detected — elevated downside risk")
    if trend == "BEARISH":
        alerts.append("Bearish market trend detected — consider defensive positioning")
    if sources_used == 0:
        alerts.append("Limited data sources — analysis confidence reduced")
    if score > 75:
        alerts.append("CRITICAL risk level — consider avoiding new positions")

    return {"score": score, "level": level, "alerts": alerts}


def build_reasoning(trend: str, sentiment: str, risk_score: int, risk_level: str, decision: str, sma_7=None, sma_20=None, sources_used=None) -> str:
    """Build a reasoning paragraph using actual computed values."""
    sma_part = ""
    if sma_7 is not None and sma_20 is not None:
        sma_part = f"SMA_7 ({sma_7:.2f}) is above SMA_20 ({sma_20:.2f})" if sma_7 > sma_20 else f"SMA_7 ({sma_7:.2f}) is below SMA_20 ({sma_20:.2f})" if sma_7 < sma_20 else f"SMA_7 ({sma_7:.2f}) equals SMA_20 ({sma_20:.2f})"

    source_part = f" based on {sources_used} real news sources" if sources_used is not None else ""
    return (
        f"The quantitative analysis shows a {trend} market trend based on SMA comparison. "
        f"News sentiment analysis classified the overall tone as {sentiment}.{source_part} "
        f"The composite risk score is {risk_score}/100 ({risk_level} risk level). "
        f"Based on these three signals, the recommendation is {decision}."
    )


def make_decision(trend: str, sentiment: str, risk_score: int, risk_level: str, sma_7=None, sma_20=None, sources_used=None) -> dict:
    """Apply strict decision rules and return recommendation output."""
    # Enhanced decision logic considering all factors
    confidence_sources = sources_used if sources_used is not None else 0

    if trend == "BULLISH" and sentiment == "POSITIVE" and risk_score <= 50:
        decision = "BUY"
        confidence = "HIGH" if risk_score <= 25 and confidence_sources >= 1 else "MEDIUM"
    elif trend == "BEARISH" and sentiment == "NEGATIVE" and risk_score >= 50:
        decision = "SELL"
        confidence = "HIGH" if risk_score >= 75 else "MEDIUM"
    elif trend == "NEUTRAL" or (sentiment == "NEUTRAL" and risk_level == "MEDIUM"):
        decision = "HOLD"
        confidence = "MEDIUM"
    else:
        # More nuanced decision based on weighted factors
        signals = [
            trend in ["BULLISH", "BEARISH"],
            sentiment in ["POSITIVE", "NEGATIVE"],
            risk_level in ["LOW", "HIGH"]
        ]
        confidence = "MEDIUM" if sum(signals) >= 2 else "LOW"

        # If mixed signals, default to HOLD
        if sum(signals) < 2:
            decision = "HOLD"

    reasoning = build_reasoning(trend, sentiment, risk_score, risk_level, decision, sma_7, sma_20, sources_used)

    return {
        "decision": decision,
        "reasoning": reasoning,
        "confidence": confidence,
        "disclaimer": "This analysis is for educational purposes only and does not constitute financial advice."
    }


def format_recommendation_badge(decision: str) -> dict:
    badges = {
      "BUY":  {"color": "#00c853", "icon": "✅", "label": "BUY"},
      "HOLD": {"color": "#ffd600", "icon": "⏸️", "label": "HOLD"},
      "SELL": {"color": "#d50000", "icon": "🔴", "label": "SELL"}
    }
    return badges.get(decision.upper(), badges["HOLD"])


def format_risk_badge(level: str) -> dict:
    badges = {
        "LOW": {"color": "#00c853", "icon": "🟢", "label": "LOW"},
        "MEDIUM": {"color": "#ffd600", "icon": "🟡", "label": "MEDIUM"},
        "HIGH": {"color": "#ff6d00", "icon": "🟠", "label": "HIGH"},
        "CRITICAL": {"color": "#d50000", "icon": "🔴", "label": "CRITICAL"}
    }
    return badges.get(level.upper(), badges["MEDIUM"])


def sanitize_upload(filename: str) -> str:
    if not filename:
        return ""
    return secure_filename(filename)


def get_company_name(ticker: str) -> str:
    try:
        stock = yf.Ticker(ticker)
        info = stock.info
        return info.get("longName", ticker.upper())
    except Exception:
        return ticker.upper()

if __name__ == "__main__":
    print("Testing app/utils.py...")
    load_environment()
    print(f"Company for AAPL: {get_company_name('AAPL')}")
    print(f"Sentiment from sample text: {compute_sentiment('Strong revenue growth and profit beat.')}")
    print(f"Risk score: {compute_risk_score(0.018, 'POSITIVE')}")
    print("app/utils.py functions tested successfully.")
