import os
import sys
import time
from typing import Dict

import pandas as pd
import numpy as np
import yfinance as yf

try:
    from crewai.tools import tool
except ImportError:
    def tool(name):
        def decorator(fn):
            return fn
        return decorator

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT_DIR not in sys.path:
    sys.path.append(ROOT_DIR)

from config import Config

def _get_market_data(ticker: str) -> Dict:
    """Fetch real OHLCV data and compute SMA and volatility deterministically."""
    ticker = ticker.strip().upper()
    if not ticker:
        raise ValueError("Ticker symbol is required.")


    import logging
    stock = yf.Ticker(ticker)
    history = None
    last_exception = None

    for attempt in range(2):
        try:
            history = stock.history(period=Config.YFINANCE_PERIOD, interval=Config.YFINANCE_INTERVAL)
            if history is not None and not history.empty:
                break
        except Exception as e:
            last_exception = e
            logging.error(f"yfinance error for ticker {ticker}: {e}")
        if attempt == 0:
            time.sleep(5)

    # Check if ticker exists by looking for info dict
    try:
        info = stock.info
        valid_ticker = info and info.get('regularMarketPrice') is not None
    except Exception as e:
        valid_ticker = False
        last_exception = e

    if history is None or history.empty:
        if not valid_ticker:
            msg = f"Ticker '{ticker}' is invalid or delisted. Please check the symbol and try again."
        else:
            msg = f"Could not retrieve data for ticker '{ticker}'. This may be due to network issues, Yahoo Finance API changes, or the ticker being delisted. Please check your internet connection or try again later."
        if last_exception:
            msg += f"\nDetails: {last_exception}"
        return {
            "current_price": None,
            "sma_7": None,
            "sma_20": None,
            "volatility": None,
            "trend": "N/A",
            "price_history": {
                "dates": [],
                "prices": [],
                "sma7": [],
                "sma20": []
            },
            "error": msg
        }

    history = history.dropna(subset=["Close"]).copy()
    if history.empty:
        raise ValueError(f"Ticker {ticker} found but no valid closing price data.")

    history = history.tail(60)
    history["daily_return"] = history["Close"].pct_change()
    history["SMA_7"] = history["Close"].rolling(window=Config.SMA_SHORT).mean()
    history["SMA_20"] = history["Close"].rolling(window=Config.SMA_LONG).mean()

    latest = history.iloc[-1]
    sma_7 = latest["SMA_7"] if not pd.isna(latest["SMA_7"]) else None
    sma_20 = latest["SMA_20"] if not pd.isna(latest["SMA_20"]) else None
    current_price = float(latest["Close"])
    volatility = float(history["daily_return"].std())
    if np.isnan(volatility):
        volatility = 0.0

    if sma_7 is None or sma_20 is None:
        trend = "NEUTRAL"
    elif sma_7 > sma_20:
        trend = "BULLISH"
    elif sma_7 < sma_20:
        trend = "BEARISH"
    else:
        trend = "NEUTRAL"

    dates = history.index.strftime("%Y-%m-%d").tolist()
    prices = [round(float(x), 2) for x in history["Close"].tolist()]
    sma7_list = [None if pd.isna(x) else round(float(x), 2) for x in history["SMA_7"].tolist()]
    sma20_list = [None if pd.isna(x) else round(float(x), 2) for x in history["SMA_20"].tolist()]

    return {
        "current_price": round(current_price, 2),
        "sma_7": round(float(sma_7), 2) if sma_7 is not None else None,
        "sma_20": round(float(sma_20), 2) if sma_20 is not None else None,
        "volatility": round(volatility, 4),
        "trend": trend,
        "price_history": {
            "dates": dates,
            "prices": prices,
            "sma7": sma7_list,
            "sma20": sma20_list,
        },
    }

get_market_data = tool("Market Data Tool")(_get_market_data)

def _get_market_news(ticker: str) -> str:
    """Fetch recent news for a ticker using multiple sources with fallback."""
    ticker = ticker.strip().upper()
    if not ticker:
        raise ValueError("Ticker symbol is required.")

    news_items = []

    # Try finnhub first (if API key available)
    finnhub_key = os.getenv("FINNHUB_API_KEY")
    if finnhub_key:
        try:
            import finnhub
            finnhub_client = finnhub.Client(api_key=finnhub_key)
            news = finnhub_client.company_news(ticker, _from="2024-01-01", to="2024-12-31")
            if news:
                for item in news[:10]:  # Limit to 10 most recent
                    # Filter for ticker mentions
                    if ticker.lower() in item.get('headline', '').lower() or ticker.lower() in item.get('summary', '').lower():
                        news_items.append({
                            'headline': item.get('headline', ''),
                            'summary': item.get('summary', ''),
                            'url': item.get('url', ''),
                            'datetime': item.get('datetime', 0)
                        })
        except Exception as e:
            print(f"Finnhub error: {e}")

    # Fallback to yfinance news if finnhub fails or no key
    if not news_items:
        try:
            stock = yf.Ticker(ticker)
            news_data = stock.news
            if news_data:
                for item in news_data[:10]:
                    # Filter for ticker mentions in title
                    title = item.get('title', '')
                    if ticker.lower() in title.lower():
                        news_items.append({
                            'headline': title,
                            'summary': item.get('summary', ''),
                            'url': item.get('link', ''),
                            'datetime': item.get('providerPublishTime', 0)
                        })
        except Exception as e:
            print(f"YFinance news error: {e}")

    # If still no news, return neutral message
    if not news_items:
        return "System Note: No significant news events in the last 48 hours. Sentiment is fundamentally NEUTRAL."

    # Format news for analysis
    formatted_news = []
    for item in news_items[:5]:  # Limit to 5 for analysis
        formatted_news.append(f"Headline: {item['headline']}\nSummary: {item['summary']}\n")

    return "\n---\n".join(formatted_news)

get_market_news = tool("Market News Tool")(_get_market_news)
