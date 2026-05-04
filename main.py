import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# --- CONFIGURATION ---
os.environ["OPENAI_API_BASE"] = "https://api.openai.com/v1"
os.environ["OPENAI_MODEL_NAME"] = "gpt-4o"
# API key should be in .env file
if not os.getenv("OPENAI_API_KEY"):
    print("Warning: OPENAI_API_KEY not found. Running in fallback mode.")

from crewai import Task, Crew, Process
from agents.analyst_agents import create_agents, DataAnalysisOutput, NewsAnalysisOutput, RiskAnalysisOutput, FinalDecisionOutput
from tools.haystack_tools import index_pdf_to_store
from textwrap import dedent
import json

def main():
    print("==========================================")
    print("Welcome to the AI Quant Analyst Assistant!")
    print("==========================================")

    ticker = "AAPL"
    report_file = "AAPL_Q1_2025_Financial_Report.pdf"

    # Load environment variables and check API key
    load_dotenv()
    
    # Check if we have API key
    api_key = os.getenv("OPENAI_API_KEY")
    has_api_key = bool(api_key and api_key.startswith("sk-") and len(api_key) > 20)
    
    # Force fallback mode if API key exists but might be invalid/quota exceeded
    force_fallback = os.getenv("FORCE_FALLBACK", "false").lower() == "true"
    
    if not has_api_key or force_fallback:
        print("No valid OpenAI API key found or fallback mode forced. Running in fallback mode (deterministic analysis).")
        from app.crew import QuantAnalystCrew
        crew_system = QuantAnalystCrew(ticker, report_file)
        result = crew_system.run()
        print("\n\n" + "="*50)
        print("                 FINAL REPORT                 ")
        print("="*50)
        print(json.dumps(result, indent=2))
        print("="*50)
        return

    print(f"\n[2] Starting the AI analysis pipeline for {ticker}...\n")

    # Instantiate agents
    data_analyst, news_analyst, risk_analyst, investment_advisor = create_agents()

    # Define tasks with strict JSON outputs
    data_task = Task(
        description=dedent(f'''
            You are a quantitative analyst. Your task is to fetch the latest market data for the ticker {ticker}.
            Calculate the SMA 7, SMA 20, and Volatility. Determine the absolute trend (BULLISH, BEARISH, or NEUTRAL).
        '''),
        expected_output="Strict JSON object with ticker, current_price, sma_7, sma_20, volatility_pct, technical_trend",
        agent=data_analyst,
        output_json=DataAnalysisOutput
    )

    news_task = Task(
        description=dedent(f'''
            You are a financial news analyst. Your task is to query the RAG document database and recent news for {ticker}.
            Extract the 3 most critical financial insights. Determine the overall sentiment.
        '''),
        expected_output="Strict JSON object with ticker, overall_sentiment, sentiment_score, key_insights, rag_context_found",
        agent=news_analyst,
        context=[data_task],  # Depends on data task
        output_json=NewsAnalysisOutput
    )

    risk_task = Task(
        description=dedent(f'''
            You are the Chief Risk Officer. Review the JSON output from the Data Analyst and the News Analyst.
            If volatility is > 4% and sentiment is NEGATIVE, risk is HIGH.
            If volatility is < 2% and sentiment is POSITIVE, risk is LOW.
            Otherwise, it is MEDIUM.
        '''),
        expected_output="Strict JSON object with risk_score_0_to_100, risk_level, primary_risk_factor",
        agent=risk_analyst,
        context=[data_task, news_task],  # Depends on both previous tasks
        output_json=RiskAnalysisOutput
    )

    advisor_task = Task(
        description=dedent(f'''
            You are the Lead Portfolio Manager. Review the technical trend (Data Analyst), sentiment (News Analyst), and risk level (Risk Analyst).
            Rules:
            - BUY if Trend=BULLISH + Sentiment=POSITIVE + Risk=LOW/MEDIUM
            - SELL if Trend=BEARISH or Sentiment=NEGATIVE or Risk=HIGH
            - HOLD otherwise.
            Calculate a confidence score (0.0 to 1.0).
        '''),
        expected_output="Strict JSON object with final_decision, confidence_score, justification",
        agent=investment_advisor,
        context=[data_task, news_task, risk_task],  # Depends on all previous tasks
        output_json=FinalDecisionOutput
    )

    # Form the crew with sequential process
    financial_crew = Crew(
        agents=[data_analyst, news_analyst, risk_analyst, investment_advisor],
        tasks=[data_task, news_task, risk_task, advisor_task],
        process=Process.sequential,
        verbose=True
    )

    try:
        # Execute tasks
        result = financial_crew.kickoff()

        # Parse and validate the final result
        final_output = advisor_task.output.raw
        try:
            parsed_result = json.loads(final_output)
            print("\n\n" + "="*50)
            print("                 FINAL REPORT                 ")
            print("="*50)
            print(json.dumps(parsed_result, indent=2))
            print("="*50)
        except json.JSONDecodeError:
            print(f"Error parsing final output: {final_output}")
            print("Falling back to raw output...")
            print(result)

    except Exception as e:
        print(f"An error occurred during execution: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
