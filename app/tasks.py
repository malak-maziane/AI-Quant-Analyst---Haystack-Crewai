import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from crewai import Task
from app.agents import DataAnalysisOutput, NewsAnalysisOutput, RiskAnalysisOutput, FinalDecisionOutput, BacktestingOutput, AutoTradingOutput, PredictionsOutput, AlertsOutput

def market_analysis_task(ticker: str, agent) -> Task:
    """
    Creates the market analysis task for the Data Analyst with comprehensive explanation output.
    """
    return Task(
        description=f"Analyze the latest market data for {ticker}. Calculate technical indicators (SMA 7, SMA 20, volatility) and determine the trend direction. Provide a clear explanation of the trend and how the technical indicators support it.",
        expected_output="JSON with ticker, current_price, sma_7, sma_20, volatility_pct, technical_trend, and trend_explanation",
        agent=agent,
        output_json=DataAnalysisOutput
    )

def news_analysis_task(ticker: str, agent, document_path: str = None) -> Task:
    """
    Creates the news analysis task for the News Analyst with comprehensive explanation output.
    """
    return Task(
        description=f"Analyze market sentiment for {ticker} by querying the RAG database and recent news. Extract 3 critical financial insights and determine overall sentiment. Explain the sentiment drivers and their market implications.",
        expected_output="JSON with ticker, overall_sentiment, sentiment_score, key_insights, rag_context_found, and sentiment_explanation",
        agent=agent,
        output_json=NewsAnalysisOutput
    )

def risk_assessment_task(ticker: str, agent) -> Task:
    """
    Creates the risk assessment task for the Risk Analyst with comprehensive explanation output.
    """
    return Task(
        description=f"Conduct comprehensive risk assessment for {ticker} using volatility and sentiment data. Calculate risk score and identify primary risk factors. Provide detailed explanation of risk drivers, implications, and considerations.",
        expected_output="JSON with risk_score_0_to_100, risk_level, primary_risk_factor, and detailed_risk_explanation",
        agent=agent,
        output_json=RiskAnalysisOutput
    )

def investment_recommendation_task(ticker: str, agent) -> Task:
    """
    Creates the investment recommendation task for the Investment Advisor with comprehensive explanation output.
    """
    return Task(
        description=f"Make a comprehensive BUY/HOLD/SELL recommendation for {ticker} based on technical trend, sentiment, and risk analysis. Analyze all factors, calculate confidence score, and provide detailed reasoning for the decision.",
        expected_output="JSON with final_decision, confidence_score, justification, key_factors_analysis, and decision_reasoning",
        agent=agent,
        output_json=FinalDecisionOutput
    )

def backtesting_task(ticker: str, agent) -> Task:
    """
    Creates the backtesting task for strategy testing and performance analysis.
    """
    return Task(
        description=f"Design and backtest multiple trading strategies for {ticker} using historical data. Test strategies like SMA crossover, RSI, and MACD. Calculate comprehensive performance metrics including returns, Sharpe ratio, drawdowns, and win rates. Provide detailed analysis of strategy performance.",
        expected_output="JSON with strategy_name, total_return_pct, sharpe_ratio, max_drawdown_pct, win_rate_pct, total_trades, backtest_period_days, performance_summary, and risk_metrics",
        agent=agent,
        output_json=BacktestingOutput
    )

def auto_trading_task(ticker: str, agent) -> Task:
    """
    Creates the auto trading task for automated strategy execution and position management.
    """
    return Task(
        description=f"Develop and execute an automated trading strategy for {ticker}. Analyze current market conditions, determine position sizing, set stop-loss and take-profit levels, and generate real-time trading signals. Monitor performance and manage risk exposure.",
        expected_output="JSON with strategy_name, current_position, entry_price, stop_loss, take_profit, position_size_pct, risk_per_trade_pct, trading_signals, and performance_metrics",
        agent=agent,
        output_json=AutoTradingOutput
    )

def predictions_task(ticker: str, agent) -> Task:
    """
    Creates the predictions task for ML-based price forecasting.
    """
    return Task(
        description=f"Build and deploy machine learning models to predict {ticker} price movements for 7-day and 30-day horizons. Use historical data, technical indicators, and sentiment analysis. Provide confidence intervals, model accuracy, and detailed explanation of predictions.",
        expected_output="JSON with ticker, predicted_price_7d, predicted_price_30d, confidence_interval, model_accuracy, prediction_explanation, key_drivers, and risk_assessment",
        agent=agent,
        output_json=PredictionsOutput
    )

def alerts_task(ticker: str, agent) -> Task:
    """
    Creates the alerts task for real-time market monitoring and notifications.
    """
    return Task(
        description=f"Monitor {ticker} continuously for significant market events and generate timely alerts. Track price movements, technical breakouts, news sentiment changes, and risk thresholds. Provide active alerts, triggered notifications, and monitoring status.",
        expected_output="JSON with ticker, active_alerts, triggered_alerts, alert_types, monitoring_status, and last_update",
        agent=agent,
        output_json=AlertsOutput
    )

# For standalone testing
if __name__ == "__main__":
    print("Testing app/tasks.py...")
    print("Task functions defined:")
    print("1. market_analysis_task")
    print("2. news_analysis_task")
    print("3. risk_assessment_task")
    print("4. investment_recommendation_task")
    print("Total: 4 task functions")