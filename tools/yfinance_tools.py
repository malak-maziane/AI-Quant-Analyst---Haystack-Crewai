import yfinance as yf
from crewai.tools import tool
import pandas as pd
import numpy as np

@tool("Stock Data Tool")
def get_stock_data(ticker: str) -> str:
    """
    Fetches stock data for a given ticker.
    Returns current price, SMA 7, SMA 20, volatility percentage, and trend analysis.
    """
    try:
        stock = yf.Ticker(ticker)
        hist = stock.history(period="3mo")  # Get 3 months for better calculations
        if hist.empty:
            # Try fallback ticker (MSFT) if not already tried
            if ticker.upper() != "MSFT":
                fallback_ticker = "MSFT"
                fallback_stock = yf.Ticker(fallback_ticker)
                fallback_hist = fallback_stock.history(period="3mo")
                if not fallback_hist.empty:
                    return (
                        f"No data found for '{ticker}'. Showing example data for '{fallback_ticker}':\n"
                        f"Ticker: {fallback_ticker}\n"
                        f"Current Price: ${fallback_hist['Close'].iloc[-1]:.2f}\n"
                        f"SMA 7: ${fallback_hist['Close'].tail(7).mean():.2f}\n"
                        f"SMA 20: ${fallback_hist['Close'].tail(20).mean():.2f}\n"
                        f"Volatility %: {fallback_hist['Close'].pct_change().dropna().tail(20).std() * 100:.2f}%\n"
                        f"Technical Trend: {'BULLISH' if fallback_hist['Close'].tail(7).mean() > fallback_hist['Close'].tail(20).mean() else 'BEARISH' if fallback_hist['Close'].tail(7).mean() < fallback_hist['Close'].tail(20).mean() else 'NEUTRAL'}"
                    )
            return f"Invalid or unavailable stock ticker: {ticker}. Please try another symbol."

        # Calculate metrics
        latest_price = hist['Close'].iloc[-1]

        # SMA calculations
        sma_7 = hist['Close'].tail(7).mean()
        sma_20 = hist['Close'].tail(20).mean()

        # Volatility as coefficient of variation (std/mean) over last 20 days
        returns = hist['Close'].pct_change().dropna()
        volatility_pct = returns.tail(20).std() * 100  # Convert to percentage

        # Determine trend
        if sma_7 > sma_20:
            trend = "BULLISH"
        elif sma_7 < sma_20:
            trend = "BEARISH"
        else:
            trend = "NEUTRAL"

        return (
            f"Ticker: {ticker}\n"
            f"Current Price: ${latest_price:.2f}\n"
            f"SMA 7: ${sma_7:.2f}\n"
            f"SMA 20: ${sma_20:.2f}\n"
            f"Volatility %: {volatility_pct:.2f}%\n"
            f"Technical Trend: {trend}"
        )
    except Exception as e:
        return f"Error fetching stock data for {ticker}: {str(e)}\nThis ticker may be invalid, delisted, or data is temporarily unavailable."
