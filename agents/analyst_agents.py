from crewai import Agent
from tools.yfinance_tools import get_stock_data
from tools.haystack_tools import query_financial_knowledge_base
from tools.market_data import get_market_news
import os
from pydantic import BaseModel

# Pydantic models for output validation
class DataAnalysisOutput(BaseModel):
    ticker: str
    current_price: float
    sma_7: float
    sma_20: float
    volatility_pct: float
    technical_trend: str  # BULLISH|BEARISH|NEUTRAL

class NewsAnalysisOutput(BaseModel):
    ticker: str
    overall_sentiment: str  # POSITIVE|NEGATIVE|NEUTRAL
    sentiment_score: float  # -1.0 to 1.0
    key_insights: list[str]
    rag_context_found: bool

class RiskAnalysisOutput(BaseModel):
    risk_score_0_to_100: int  # 0-100
    risk_level: str  # LOW|MEDIUM|HIGH
    primary_risk_factor: str

class FinalDecisionOutput(BaseModel):
    final_decision: str  # BUY|HOLD|SELL
    confidence_score: float  # 0.0-1.0
    justification: str

def create_agents():
    # 1. Data Analyst Agent
    data_analyst = Agent(
        role='Senior Quantitative Financial Data Analyst',
        goal='Analyze OHLCV data and calculate SMA 7, SMA 20, and Volatility to determine absolute trend.',
        backstory=(
            "You are a senior quantitative analyst specializing in technical analysis. "
            "You fetch the latest market data for a ticker, calculate SMA 7, SMA 20, and volatility percentage. "
            "You determine the absolute trend as BULLISH, BEARISH, or NEUTRAL. "
            "CRITICAL: You MUST format your ENTIRE final response strictly as a valid JSON object. "
            "Do not include markdown code blocks or any conversational text. "
            "Output Schema: {ticker: str, current_price: float, sma_7: float, sma_20: float, volatility_pct: float, technical_trend: 'BULLISH|BEARISH|NEUTRAL'}"
        ),
        verbose=True,
        allow_delegation=False,
        tools=[get_stock_data],
        max_retries=3
    )

    # 2. News Analyst Agent
    news_analyst = Agent(
        role='Chief Financial NLP & Sentiment Analyst',
        goal='Extract precise insights from news and RAG, calculate clear sentiment score.',
        backstory=(
            "You are a financial news analyst. You query the RAG document database and recent news for a ticker. "
            "You extract the 3 most critical financial insights. You determine overall sentiment. "
            "CRITICAL: You MUST format your ENTIRE final response strictly as a valid JSON object. "
            "Output Schema: {ticker: str, overall_sentiment: 'POSITIVE|NEGATIVE|NEUTRAL', sentiment_score: float, key_insights: [str, str, str], rag_context_found: bool}"
        ),
        verbose=True,
        allow_delegation=False,
        tools=[query_financial_knowledge_base, get_market_news],
        max_retries=3
    )

    # 3. Risk Analyst Agent
    risk_analyst = Agent(
        role='Senior Institutional Risk Manager',
        goal='Reconcile technical volatility with market sentiment to calculate weighted risk score.',
        backstory=(
            "You are the Chief Risk Officer. You review JSON outputs from Data and News Analysts. "
            "If volatility > 4% and sentiment is NEGATIVE, risk is HIGH. "
            "If volatility < 2% and sentiment is POSITIVE, risk is LOW. "
            "Otherwise, MEDIUM. Calculate risk_score_0_to_100 and identify primary_risk_factor. "
            "CRITICAL: Return ONLY a valid JSON object. "
            "Output Schema: {risk_score_0_to_100: int, risk_level: 'LOW|MEDIUM|HIGH', primary_risk_factor: str}"
        ),
        verbose=True,
        allow_delegation=False,
        max_retries=3
    )

    # 4. Investment Advisor Agent
    investment_advisor = Agent(
        role='Lead Portfolio Manager & Investment Advisor',
        goal='Make final BUY/HOLD/SELL decision based on trend, sentiment, and risk with confidence score.',
        backstory=(
            "You are the Lead Portfolio Manager. You review technical trend, sentiment, and risk level. "
            "Rules: BUY if Trend=BULLISH + Sentiment=POSITIVE + Risk=LOW/MEDIUM. "
            "SELL if Trend=BEARISH or Sentiment=NEGATIVE or Risk=HIGH. HOLD otherwise. "
            "Calculate confidence_score (0.0-1.0). Provide 2-sentence justification. "
            "CRITICAL: Return ONLY a valid JSON object. "
            "Output Schema: {final_decision: 'BUY|HOLD|SELL', confidence_score: float, justification: str}"
        ),
        verbose=True,
        allow_delegation=False,
        max_retries=3
    )

    return data_analyst, news_analyst, risk_analyst, investment_advisor
