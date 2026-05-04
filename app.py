import streamlit as st
import json
import os
import tempfile
from datetime import datetime

import plotly.graph_objects as go

from app.crew import QuantAnalystCrew
from app.utils import validate_ticker, get_company_name, format_recommendation_badge, format_risk_badge

# ── Page config ────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="AI Quant Analyst",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ── Dark Blue CSS Theme + Nav Button Fix ───────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600&family=JetBrains+Mono:wght@400;500&display=swap');

html, body, .stApp { background-color: #0b1120 !important; font-family: 'Inter', sans-serif !important; color: #c8d6f0 !important; }

section[data-testid="stSidebar"] { background-color: #0d1626 !important; border-right: 1px solid #1a2845 !important; }
section[data-testid="stSidebar"] label, section[data-testid="stSidebar"] p,
section[data-testid="stSidebar"] span, section[data-testid="stSidebar"] div { color: #8899bb !important; }
section[data-testid="stSidebar"] h1, section[data-testid="stSidebar"] h2,
section[data-testid="stSidebar"] h3 { color: #ffffff !important; }

.main .block-container { background-color: #0b1120 !important; padding: 2rem 2.5rem !important; }
h1, h2, h3 { color: #ffffff !important; font-weight: 500 !important; }

.main-header { font-size: 2rem; font-weight: 600; color: #7eb3ff; text-align: center; margin-bottom: 1.5rem; letter-spacing: -0.5px; }

div[data-testid="metric-container"] { background-color: #111f3a !important; border: 1px solid #1a2d52 !important; border-radius: 10px !important; padding: 1rem 1.2rem !important; }
div[data-testid="metric-container"] > div > div:first-child { color: #5a7aa8 !important; font-size: 11px !important; font-weight: 500 !important; text-transform: uppercase !important; letter-spacing: 0.8px !important; }
div[data-testid="metric-container"] > div > div:nth-child(2) { color: #ffffff !important; font-size: 1.5rem !important; font-weight: 500 !important; font-family: 'JetBrains Mono', monospace !important; }

div[data-testid="stTabs"] button[data-baseweb="tab"] { background-color: #111f3a !important; color: #5a7aa8 !important; border: 1px solid #1a2d52 !important; border-radius: 8px !important; font-size: 13px !important; font-weight: 500 !important; padding: 0.5rem 1rem !important; margin-right: 6px !important; }
div[data-testid="stTabs"] button[data-baseweb="tab"][aria-selected="true"] { background-color: #1a3060 !important; color: #7eb3ff !important; border-color: #2a4a8a !important; }
div[data-testid="stTabsContent"] { background-color: #0e1a30 !important; border: 1px solid #1a2d52 !important; border-radius: 0 10px 10px 10px !important; padding: 1.5rem !important; }

div[data-testid="stProgress"] > div { background-color: #111f3a !important; border-radius: 10px !important; }
div[data-testid="stProgress"] > div > div { background: linear-gradient(90deg, #3b5bdb, #7eb3ff) !important; border-radius: 10px !important; }

.stButton > button { background-color: #1a3060 !important; color: #7eb3ff !important; border: 1px solid #2a4a8a !important; border-radius: 8px !important; font-weight: 500 !important; font-size: 13px !important; min-width: 160px !important; white-space: nowrap !important; overflow: hidden; text-overflow: ellipsis; }
.stButton > button:hover { background-color: #234080 !important; color: #ffffff !important; }
.stButton > button[kind="primary"] { background-color: #3b5bdb !important; color: #ffffff !important; border-color: #3b5bdb !important; }
.stButton > button[kind="primary"]:hover { background-color: #4c6ef5 !important; }

.stTextInput input { background-color: #111f3a !important; border: 1px solid #1a2d52 !important; color: #c8d6f0 !important; border-radius: 8px !important; }
.stTextInput input::placeholder { color: #3a5070 !important; }
div[data-testid="stFileUploader"] { background-color: #111f3a !important; border: 1px dashed #1a2d52 !important; border-radius: 8px !important; }
div[data-testid="stExpander"] { background-color: #111f3a !important; border: 1px solid #1a2d52 !important; border-radius: 8px !important; }
div[data-testid="stExpander"] summary { color: #7eb3ff !important; }

.stMarkdown p, .stMarkdown li { color: #8899bb !important; }
.stMarkdown strong { color: #c8d6f0 !important; }
.stMarkdown a { color: #7eb3ff !important; }
.stCaption, caption { color: #3a5070 !important; font-size: 12px !important; }
hr { border-color: #1a2d52 !important; }

.stRadio label { background-color: #111f3a !important; border: 1px solid #1a2d52 !important; border-radius: 8px !important; padding: 0.6rem 1rem !important; color: #8899bb !important; }
.stRadio label:hover { border-color: #3b5bdb !important; color: #7eb3ff !important; }

.decision-buy { background-color: #0a2218; color: #4ade80; padding: 1rem 2rem; border-radius: 10px; text-align: center; font-size: 2rem; font-weight: 600; border: 1px solid #1a4d30; font-family: 'JetBrains Mono', monospace; letter-spacing: 2px; }
.decision-hold { background-color: #2a2000; color: #fbbf24; padding: 1rem 2rem; border-radius: 10px; text-align: center; font-size: 2rem; font-weight: 600; border: 1px solid #4d3a00; font-family: 'JetBrains Mono', monospace; letter-spacing: 2px; }
.decision-sell { background-color: #2a0d0d; color: #f87171; padding: 1rem 2rem; border-radius: 10px; text-align: center; font-size: 2rem; font-weight: 600; border: 1px solid #4d1a1a; font-family: 'JetBrains Mono', monospace; letter-spacing: 2px; }

.info-card { background-color: #111f3a; border: 1px solid #1a2d52; border-radius: 10px; padding: 1.2rem 1.5rem; margin-bottom: 1rem; }
.insight-row { background: #111f3a; border: 1px solid #1a2d52; border-left: 3px solid #3b5bdb; border-radius: 6px; padding: 0.6rem 1rem; margin-bottom: 8px; font-size: 13px; color: #c8d6f0; }
.passage-row { background: #0e1a30; border: 1px solid #1a2d52; border-left: 3px solid #fbbf24; border-radius: 6px; padding: 0.8rem 1rem; margin-bottom: 8px; font-size: 13px; color: #8899bb; }
.alert-row { background: #2a1500; border: 1px solid #fb923c44; border-left: 3px solid #fb923c; border-radius: 6px; padding: 0.6rem 1rem; margin-bottom: 8px; font-size: 13px; color: #fb923c; }
.trend-row { border-radius: 8px; padding: 0.75rem 1rem; margin: 1rem 0; display: flex; align-items: center; gap: 12px; }
.qa-card { background: #0e1a30; border: 1px solid #1a2d52; border-left: 3px solid #3b5bdb; border-radius: 8px; padding: 1rem; font-size: 13px; color: #c8d6f0; line-height: 1.6; }

::-webkit-scrollbar { width: 6px; }
::-webkit-scrollbar-track { background: #0b1120; }
::-webkit-scrollbar-thumb { background: #1a2d52; border-radius: 3px; }
</style>
""", unsafe_allow_html=True)

# ── Plotly dark template ───────────────────────────────────────────────────────
PLOTLY_LAYOUT = dict(
    template="plotly_dark",
    paper_bgcolor="#0e1a30",
    plot_bgcolor="#0e1a30",
    font=dict(family="Inter, sans-serif", color="#8899bb"),
    xaxis=dict(gridcolor="#1a2d52", linecolor="#1a2d52", tickfont=dict(color="#5a7aa8")),
    yaxis=dict(gridcolor="#1a2d52", linecolor="#1a2d52", tickfont=dict(color="#5a7aa8")),
    legend=dict(bgcolor="rgba(0,0,0,0)", bordercolor="#1a2d52"),
    margin=dict(l=20, r=20, t=40, b=20),
    height=380,
)

# ── Sidebar ────────────────────────────────────────────────────────────────────
with st.sidebar:
    st.title("📊 AI Quant Analyst")
    st.markdown("---")


    # Navigation horizontale avec vrais boutons flexbox
    nav_options = ["Dashboard", "Market Data", "News & Docs", "Risk Analysis", "Recommendation", "Predictions", "Alerts"]
    nav_selected = st.session_state.get("page", "Dashboard")
    nav_options = ["Dashboard", "Market Data", "News & Docs", "Risk Analysis", "Recommendation", "Predictions", "Alerts"]
    nav_form = st.form(key="nav_form")
    with nav_form:
        st.markdown("""
        <div style='display:flex; gap:0px; justify-content:center; margin-bottom:18px; flex-wrap:wrap;'>
        """, unsafe_allow_html=True)
        nav_clicked = None
        for opt in nav_options:
            btn = st.form_submit_button(opt, use_container_width=False)
            if btn:
                nav_clicked = opt
        st.markdown("</div>", unsafe_allow_html=True)
    if nav_clicked:
        st.session_state["page"] = nav_clicked
    page = st.session_state.get("page", "Dashboard")

    st.markdown("---")

    if page == "Dashboard":
        ticker = st.text_input("Stock Ticker", placeholder="e.g. AAPL", key="ticker_input").upper().strip()
        uploaded_file = st.file_uploader("Financial Document", type=["pdf", "txt"])
        analyze_btn = st.button("🔍 Analyze", type="primary", use_container_width=True)
    else:
        ticker = st.session_state.get("ticker_input", "")
        uploaded_file = None
        analyze_btn = False

    st.markdown("---")
    st.subheader("🤖 About the AI Agents")
    st.markdown("""
    **Data Analyst**: Analyzes market data & trends  
    **News Analyst**: Processes documents & sentiment  
    **Risk Analyst**: Evaluates investment risk  
    **Investment Advisor**: Makes final recommendations
    """)
    st.subheader("🛠️ Tech Stack")
    st.markdown("- Haystack + CrewAI\n- yfinance + pandas\n- Flask + Streamlit\n- Python 3.10+")
    st.caption("⚠️ Educational purposes only. Not financial advice.")
    with st.expander("📚 Glossaire pour débutants"):
        st.markdown("""
        **SMA**: Moyenne mobile simple (7 ou 20 jours).  
        **Bullish/Bearish**: Tendance haussière / baissière.  
        **Volatilité**: Variation des prix — haute = risque élevé.  
        **Sentiment**: Ton positif/négatif des nouvelles.  
        **Risk Score**: Risque sur 100.
        """)

# ── Helpers ────────────────────────────────────────────────────────────────────

def _trend_badge(trend: str):
    colors = {"BULLISH": ("#4ade80", "#0a2218", "📈"), "BEARISH": ("#f87171", "#2a0d0d", "📉"), "NEUTRAL": ("#fbbf24", "#2a2000", "➡️")}
    color, bg, icon = colors.get(trend, colors["NEUTRAL"])
    st.markdown(f"""<div class="trend-row" style="background:{bg}; border:1px solid {color}33;">
        <span style="font-size:18px;">{icon}</span>
        <span style="color:{color}; font-weight:600; font-size:14px;">Trend: {trend}</span>
    </div>""", unsafe_allow_html=True)


def _sentiment_badge(sentiment: str):
    colors = {"POSITIVE": ("#4ade80", "#0a2218"), "NEGATIVE": ("#f87171", "#2a0d0d"), "NEUTRAL": ("#fbbf24", "#2a2000")}
    color, bg = colors.get(sentiment, colors["NEUTRAL"])
    st.markdown(f"""<div style="background:{bg}; border:1px solid {color}33; border-radius:8px;
        padding:0.75rem 1.2rem; margin-bottom:1rem; display:inline-flex; align-items:center; gap:10px;">
        <span style="color:{color}; font-weight:600; font-size:14px;">📰 Sentiment: {sentiment}</span>
    </div>""", unsafe_allow_html=True)


def _risk_badge(level: str, score: int):
    colors = {"LOW": ("#4ade80", "#0a2218"), "MEDIUM": ("#fbbf24", "#2a2000"),
              "HIGH": ("#fb923c", "#2a1500"), "CRITICAL": ("#f87171", "#2a0d0d")}
    color, bg = colors.get(level, colors["MEDIUM"])
    st.markdown(f"""<div style="background:{bg}; border:1px solid {color}44;
        border-radius:10px; padding:1rem; text-align:center;">
        <div style="color:{color}; font-size:1.4rem; font-weight:600;">{level}</div>
        <div style="color:{color}88; font-size:11px;">Risk Level — {score}/100</div>
    </div>""", unsafe_allow_html=True)


def _price_chart(market_data: dict, ticker: str = ""):
    if not market_data.get('price_history', {}).get('dates'):
        st.info("No price history available")
        return
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=market_data['price_history']['dates'],
        y=market_data['price_history']['prices'],
        mode='lines', name='Closing Price',
        line=dict(color='#3b5bdb', width=2),
        fill='tozeroy', fillcolor='rgba(59,91,219,0.08)'
    ))
    fig.add_trace(go.Scatter(
        x=market_data['price_history']['dates'],
        y=market_data['price_history']['sma7'],
        mode='lines', name='SMA 7',
        line=dict(color='#7eb3ff', width=1.5, dash='dash')
    ))
    fig.add_trace(go.Scatter(
        x=market_data['price_history']['dates'],
        y=market_data['price_history']['sma20'],
        mode='lines', name='SMA 20',
        line=dict(color='#fbbf24', width=1.5, dash='dot')
    ))
    fig.update_layout(
        title=dict(text=f"Price History — {ticker}", font=dict(color="#7eb3ff", size=14)),
        xaxis_title="Date", yaxis_title="Price (USD)",
        **PLOTLY_LAYOUT
    )
    st.plotly_chart(fig, use_container_width=True)


def _no_analysis_warning():
    st.info("Veuillez d'abord analyser une action dans le Dashboard.")


# ── Page: Dashboard ────────────────────────────────────────────────────────────

def page_dashboard():
    if not st.session_state.get("analysis_done", False):
        st.markdown('<h1 class="main-header">AI Quant Analyst Assistant</h1>', unsafe_allow_html=True)
        col_l, col_c, col_r = st.columns([1, 3, 1])
        with col_c:
            st.markdown("""
            <div style="background:#111f3a; border:1px solid #1a2d52; border-radius:12px; padding:2rem; text-align:center; margin-bottom:2rem;">
                <p style="color:#5a7aa8; font-size:14px; margin-bottom:1.5rem;">Multi-Agent Financial Decision System</p>
                <div style="display:flex; flex-direction:column; gap:12px; text-align:left;">
                    <div style="display:flex; align-items:center; gap:12px;"><span>📊</span><span style="color:#c8d6f0; font-size:14px;">Real-time market data analysis</span></div>
                    <div style="display:flex; align-items:center; gap:12px;"><span>📰</span><span style="color:#c8d6f0; font-size:14px;">Document and news sentiment analysis</span></div>
                    <div style="display:flex; align-items:center; gap:12px;"><span>⚠️</span><span style="color:#c8d6f0; font-size:14px;">Risk assessment and alerts</span></div>
                    <div style="display:flex; align-items:center; gap:12px;"><span>✅</span><span style="color:#c8d6f0; font-size:14px;">AI-powered investment recommendations</span></div>
                </div>
            </div>
            """, unsafe_allow_html=True)

        if analyze_btn and ticker:
            if not validate_ticker(ticker):
                st.error("Invalid stock ticker. Please try again.")
            else:
                document_path = None
                if uploaded_file is not None:
                    uploads_dir = os.path.join(os.path.dirname(__file__), "uploads")
                    os.makedirs(uploads_dir, exist_ok=True)
                    document_path = os.path.join(uploads_dir, uploaded_file.name)
                    with open(document_path, "wb") as f:
                        f.write(uploaded_file.getvalue())
                    st.session_state["document_path"] = document_path
                else:
                    st.session_state["document_path"] = None

                with st.spinner("🤖 AI agents are analyzing..."):
                    crew = QuantAnalystCrew(ticker, st.session_state.get("document_path"))
                    result = crew.run()
                    st.session_state["result"] = result
                    st.session_state["last_ticker"] = ticker
                    st.session_state["analysis_done"] = True
                    st.rerun()
        return

    # ── Results ──
    result = st.session_state["result"]

    if result.get("status") == "error":
        st.error(f"❌ Analysis Failed: {result.get('error', 'Unknown error')}")
        col1, col2 = st.columns(2)
        with col1:
            if st.button("🔄 Try Again", use_container_width=True):
                st.session_state.clear(); st.rerun()
        with col2:
            if st.button("⬅️ Back", use_container_width=True):
                del st.session_state["analysis_done"]; st.rerun()
        st.stop()

    market_data = result.get("market_data", {})
    news_analysis = result.get("news_analysis", {})
    risk_assessment = result.get("risk_assessment", {})
    recommendation = result.get("recommendation", {})
    decision = recommendation.get("decision", "HOLD")

    # Header
    col1, col2, col3 = st.columns([3, 1, 1])
    with col1:
        st.markdown(f"""<div style="margin-bottom:0.5rem;">
            <span style="color:#5a7aa8; font-size:12px; text-transform:uppercase; letter-spacing:1px;">Analysis Report</span>
            <h1 style="margin:0; color:#ffffff; font-size:1.6rem;">{result.get('ticker','—')} — {result.get('company_name','')}</h1>
        </div>""", unsafe_allow_html=True)
    with col2:
        st.metric("Date", result.get('date', datetime.now().strftime("%Y-%m-%d")))
    with col3:
        st.markdown(f'<div class="decision-{decision.lower()}">{decision}</div>', unsafe_allow_html=True)

    st.markdown("<div style='height:12px'></div>", unsafe_allow_html=True)

    # Metrics row
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Current Price", f"${market_data.get('current_price', 0):.2f}")
    with col2:
        st.metric("SMA 7", f"${market_data.get('sma_7', 0):.2f}")
    with col3:
        st.metric("SMA 20", f"${market_data.get('sma_20', 0):.2f}")
    with col4:
        vol = market_data.get('volatility', 0)
        st.metric("Volatility", f"{vol:.2%}" if vol < 1 else f"{vol:.2f}%")

    # Chart + recommendation side by side
    col1, col2 = st.columns([2, 1], gap="large")
    with col1:
        _price_chart(market_data, result.get('ticker', ''))
    with col2:
        conf_colors = {"HIGH": "#4ade80", "MEDIUM": "#fbbf24", "LOW": "#f87171"}
        conf = recommendation.get('confidence', 'MEDIUM')
        conf_color = conf_colors.get(conf, "#fbbf24")
        st.markdown(f"""<div style="background:#111f3a; border:1px solid #1a2d52; border-radius:10px; padding:1.5rem; height:100%;">
            <div style="color:#5a7aa8; font-size:11px; text-transform:uppercase; margin-bottom:0.5rem;">Recommendation</div>
            <div class="decision-{decision.lower()}" style="margin-bottom:0.75rem;">{decision}</div>
            <span style="background:#0e1a30; border:1px solid {conf_color}44; color:{conf_color};
                font-size:11px; padding:3px 10px; border-radius:20px;">{conf} confidence</span>
            <p style="color:#8899bb; font-size:12px; margin-top:1rem; line-height:1.6;">
                {recommendation.get('reasoning', '')[:200]}
            </p>
            <div style="border-top:1px solid #1a2d52; margin-top:1rem; padding-top:0.75rem;
                display:flex; justify-content:space-between;">
                <span style="color:#5a7aa8; font-size:12px;">Risk Score</span>
                <span style="color:#fbbf24; font-size:12px; font-weight:600;">{risk_assessment.get('score', 0)}/100</span>
            </div>
        </div>""", unsafe_allow_html=True)



    # News insights table avec vraies news yfinance (filtrées)
    st.markdown("### News Sentiment & Insights")
    import requests
    news_items = []
    ticker_symbol = result.get('ticker', '')
    # Utilisation de Finnhub pour des news financières exactes par ticker
    finnhub_key = os.getenv('FINNHUB_API_KEY')
    if finnhub_key and ticker_symbol:
        try:
            url = f'https://finnhub.io/api/v1/company-news?symbol={ticker_symbol}&from=2024-01-01&to=2026-12-31&token={finnhub_key}'
            resp = requests.get(url, timeout=5)
            data = resp.json()
            # Trie par date décroissante
            data = sorted(data, key=lambda x: x.get('datetime', 0), reverse=True)
            for art in data[:3]:
                title = art.get('headline')
                link = art.get('url')
                summary = art.get('summary', '')
                if title and link:
                    news_items.append({'title': title, 'link': link, 'summary': summary})
        except Exception as e:
            print("[DEBUG] Exception Finnhub:", e)
    if news_items:
        for news in news_items:
            title = news.get('title', 'No title')
            link = news.get('link', '#')
            summary = news.get('summary', '')
            st.markdown(f'<div class="insight-row"><a href="{link}" target="_blank"><b>{title}</b></a><br><span style="font-size:12px; color:#8899bb;">{summary}</span></div>', unsafe_allow_html=True)
    else:
        st.info("Aucune news trouvée pour ce ticker (Finnhub). Vérifie le ticker ou ta clé FINNHUB_API_KEY.")

    # Insights IA (en plus)
    insights = news_analysis.get('insights', [])
    if insights:
        st.markdown("**Insights :**")
        for insight in insights[:5]:
            st.markdown(f'<div class="insight-row">{insight}</div>', unsafe_allow_html=True)

    if st.session_state.get("question") and news_analysis.get("question_answer"):
        st.markdown(f"""<div style="background:#111f3a; border:1px solid #1a2d52; border-radius:10px; padding:1.2rem; margin-top:1rem;">
            <div style="color:#5a7aa8; font-size:11px; text-transform:uppercase; margin-bottom:0.5rem;">
                Réponse à: "{st.session_state['question']}"
            </div>
            <p style="color:#c8d6f0; font-size:13px; line-height:1.7; margin:0;">
                {news_analysis['question_answer'][:800]}
            </p>
        </div>""", unsafe_allow_html=True)

    # Actions
    st.markdown("<div style='height:1rem'></div>", unsafe_allow_html=True)
    col1, col2 = st.columns(2)
    with col1:
        if st.button("🔄 Analyze Another", use_container_width=True):
            st.session_state.clear(); st.rerun()
    with col2:
        st.download_button(
            "📥 Download JSON",
            data=json.dumps(result, indent=2),
            file_name=f"analysis_{result.get('ticker','unknown')}.json",
            mime="application/json",
            use_container_width=True
        )


# ── Page: Market Data ──────────────────────────────────────────────────────────

def page_market_data():
    st.markdown('<h1 class="main-header">Market Data Analysis</h1>', unsafe_allow_html=True)
    if not st.session_state.get("analysis_done"):
        _no_analysis_warning(); return

    result = st.session_state["result"]
    market_data = result.get("market_data", {})

    col1, col2, col3, col4 = st.columns(4)
    with col1: st.metric("Prix actuel", f"${market_data.get('current_price', 0):.2f}")
    with col2: st.metric("SMA 7", f"${market_data.get('sma_7', 0):.2f}")
    with col3: st.metric("SMA 20", f"${market_data.get('sma_20', 0):.2f}")
    with col4:
        vol = market_data.get('volatility', 0)
        st.metric("Volatilité", f"{vol:.2%}" if vol < 1 else f"{vol:.2f}%")

    _trend_badge(market_data.get('trend', 'NEUTRAL'))
    _price_chart(market_data, result.get('ticker', ''))


# ── Page: News & Docs ──────────────────────────────────────────────────────────

def page_news_docs():
    st.markdown('<h1 class="main-header">News & Documents</h1>', unsafe_allow_html=True)

    if not st.session_state.get("analysis_done"):
        _no_analysis_warning(); return

    result = st.session_state["result"]
    news_analysis = result.get("news_analysis", {})

    # Sentiment
    _sentiment_badge(news_analysis.get('sentiment', 'NEUTRAL'))

    # Insights
    st.markdown("**Key Insights:**")
    for insight in news_analysis.get('insights', []):
        st.markdown(f'<div class="insight-row">{insight}</div>', unsafe_allow_html=True)

    # RAG passages
    rag_passages = news_analysis.get('rag_passages', [])
    if rag_passages:
        st.markdown("**Retrieved Passages (RAG):**")
        for p in rag_passages:
            st.markdown(f'<div class="passage-row">{p[:400]}</div>', unsafe_allow_html=True)

    kb = news_analysis.get('knowledge_base', False)
    if kb:
        st.success("📚 RAG Knowledge Base activée pour cette analyse.")
    else:
        st.info("📚 Analyse textuelle standard (pas de RAG).")

    st.caption(f"Sources analysées: {news_analysis.get('sources_used', 0)} — Type: {news_analysis.get('source_type', 'N/A')}")

    st.markdown("---")

    # ── Interactive Q&A ──
    st.subheader("🔍 Recherche intelligente (Haystack RAG)")
    rag_question = st.text_input(
        "Posez une question sur cette action:",
        placeholder="e.g. Quels sont les risques principaux pour AAPL?",
        key="rag_question_input"
    )

    if st.button("🔎 Rechercher", type="secondary") and rag_question:
        with st.spinner("🤖 Recherche dans la base de connaissances..."):
            from tools.document_reader import _get_document_knowledge_response
            rag_resp = _get_document_knowledge_response(
                result.get("ticker", ""),
                st.session_state.get("document_path"),
                rag_question
            )
        st.markdown("**💡 Réponse:**")
        answer = rag_resp.get("question_answer", "Aucune réponse trouvée.")
        # Fallback explicite si la réponse indique qu'aucun passage pertinent n'a été trouvé
        import re
        def has_question_keywords_in_answer(question, answer):
            keywords = [w.lower() for w in re.findall(r"\b\w{4,}\b", question or "")]
            return any(kw in answer.lower() for kw in keywords)

        if answer.startswith("No highly relevant passage") or "aucune réponse trouvée" in answer.lower() or not has_question_keywords_in_answer(rag_question, answer):
            # Si la question concerne le prix, fallback à market_data
            if any(k in rag_question.lower() for k in ["price", "prix", "current price", "cours", "valeur"]):
                price = result.get("market_data", {}).get("current_price")
                if price is not None:
                    answer = f"Current price: ${price:.2f} (from market data)"
                else:
                    answer = "Le prix actuel n'est pas disponible dans les données de marché."
            else:
                answer = "La réponse à votre question n'a pas été trouvée dans les documents analysés."
        st.markdown(f'<div class="qa-card">{answer[:1000]}</div>', unsafe_allow_html=True)
        st.caption(f"Basé sur {rag_resp.get('sources_used', 0)} sources · Knowledge Base: {'✅' if rag_resp.get('knowledge_base') else '❌'}")

    st.markdown("---")

    # ── Document Analysis ──
    st.subheader("📎 Analyse automatique d'un document")
    uploaded_doc = st.file_uploader("Téléchargez un document (PDF, TXT)", type=["pdf", "txt"], key="news_doc_uploader")
    if uploaded_doc and st.button("📖 Analyser", type="secondary"):
        with st.spinner("Analyse en cours..."):
            uploads_dir = os.path.join(os.path.dirname(__file__), "uploads")
            os.makedirs(uploads_dir, exist_ok=True)
            doc_path_new = os.path.join(uploads_dir, uploaded_doc.name)
            with open(doc_path_new, "wb") as f:
                f.write(uploaded_doc.getvalue())
            from app.news_docs_pipeline import DocumentAnalysisPipeline
            analysis = DocumentAnalysisPipeline().analyze(doc_path_new)
        if analysis.get("error"):
            st.error(analysis["error"])
        else:
            st.markdown(f"**Type détecté:** {analysis.get('doc_type', 'Inconnu')}")
            st.markdown(f"**Résumé:** {analysis.get('summary', '')}")
            _sentiment_badge(analysis.get('sentiment', 'NEUTRAL'))
            if analysis.get("key_entities"):
                st.markdown("**Entités clés:** " + " ".join(f"`{e}`" for e in analysis["key_entities"]))
            if analysis.get("raw_text_preview"):
                with st.expander("Aperçu du texte"):
                    st.write(analysis["raw_text_preview"])
            for section in analysis.get("sections", []):
                with st.expander(section.get("title", "Section")):
                    for ins in section.get("insights", []):
                        st.markdown(f'<div class="insight-row">{ins}</div>', unsafe_allow_html=True)


# ── Page: Risk Analysis ────────────────────────────────────────────────────────

def page_risk():
    st.markdown('<h1 class="main-header">Risk Analysis</h1>', unsafe_allow_html=True)
    if not st.session_state.get("analysis_done"):
        _no_analysis_warning(); return

    risk = st.session_state["result"].get("risk_assessment", {})
    score = risk.get('score', 50)
    level = risk.get('level', 'MEDIUM')

    col1, col2 = st.columns([2, 1])
    with col1:
        st.metric("Risk Score", f"{score}/100")
        st.progress(score / 100)
    with col2:
        _risk_badge(level, score)

    alerts = risk.get('alerts', [])
    if alerts:
        st.markdown("**⚠️ Risk Alerts:**")
        for alert in alerts:
            st.markdown(f'<div class="alert-row">⚠️ {alert}</div>', unsafe_allow_html=True)

    st.markdown("---")
    st.markdown("""
    **Explication du Risk Score:**
    - **Volatilité** : variation des prix sur la période analysée
    - **Sentiment** : ton positif/négatif des actualités financières
    - **Indicateurs structurels** : tendance du marché (SMA)

    Un score < 25 = risque faible · 25–50 = modéré · 50–75 = élevé · > 75 = critique.
    """)


# ── Page: Recommendation ──────────────────────────────────────────────────────

def page_recommendation():
    st.markdown('<h1 class="main-header">Recommendation</h1>', unsafe_allow_html=True)
    if not st.session_state.get("analysis_done"):
        _no_analysis_warning(); return

    result = st.session_state["result"]
    rec = result.get("recommendation", {})
    decision = rec.get('decision', 'HOLD')
    conf_colors = {"HIGH": "#4ade80", "MEDIUM": "#fbbf24", "LOW": "#f87171"}
    conf = rec.get('confidence', 'MEDIUM')

    col1, col2 = st.columns([1, 2])
    with col1:
        st.markdown(f'<div class="decision-{decision.lower()}">{decision}</div>', unsafe_allow_html=True)
        color = conf_colors.get(conf, "#fbbf24")
        st.markdown(f"""<div style="text-align:center; margin-top:0.75rem;">
            <span style="background:#111f3a; border:1px solid {color}44; color:{color};
                font-size:12px; padding:4px 12px; border-radius:20px;">{conf} confidence</span>
        </div>""", unsafe_allow_html=True)
    with col2:
        st.markdown(f"""<div style="background:#111f3a; border:1px solid #1a2d52; border-radius:10px; padding:1.2rem;">
            <div style="color:#5a7aa8; font-size:11px; text-transform:uppercase; margin-bottom:0.5rem;">Reasoning</div>
            <p style="color:#c8d6f0; font-size:13px; line-height:1.7; margin:0;">{rec.get('reasoning', 'N/A')}</p>
        </div>""", unsafe_allow_html=True)

    st.caption(f"⚠️ {rec.get('disclaimer', 'For educational purposes only.')}")
    st.markdown("---")
    st.markdown("""
    **Explication des signaux:**
    - **SMA** : croisement SMA7 > SMA20 → signal haussier (Bullish BUY)
    - **Sentiment** : actualités positives renforcent la recommandation d'achat
    - **Volatilité** : haute volatilité augmente le risque perçu → peut inverser la décision
    """)

# ── Page: Predictions ──────────────────────────────────────────────────────────

def page_predictions():
    st.markdown('<h1 class="main-header">Predictions</h1>', unsafe_allow_html=True)

    if not st.session_state.get("analysis_done"):
        _no_analysis_warning()
        return

    result = st.session_state["result"]
    market_data = result.get("market_data", {})
    recommendation = result.get("recommendation", {})

    current_price = market_data.get("current_price", 0)
    trend = market_data.get("trend", "NEUTRAL")
    volatility = market_data.get("volatility", 0)

    # Fake prediction logic for UI demo
    if trend == "BULLISH":
        predicted_price = current_price * 1.05
        direction = "UP"
        confidence = 78
        sentiment = "Positive momentum detected from SMA crossover and recent trend."
    elif trend == "BEARISH":
        predicted_price = current_price * 0.95
        direction = "DOWN"
        confidence = 72
        sentiment = "Negative pressure detected from moving averages and volatility."
    else:
        predicted_price = current_price * 1.01
        direction = "SIDEWAYS"
        confidence = 55
        sentiment = "No strong directional signal detected."

    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Current Price", f"${current_price:.2f}")
    with col2:
        st.metric("Predicted Price (7d)", f"${predicted_price:.2f}")
    with col3:
        st.metric("Prediction Confidence", f"{confidence}%")

    st.markdown("---")

    arrow = "📈" if direction == "UP" else "📉" if direction == "DOWN" else "➡️"
    color = "#4ade80" if direction == "UP" else "#f87171" if direction == "DOWN" else "#fbbf24"

    st.markdown(f"""
    <div style="background:#111f3a; border:1px solid #1a2d52; border-radius:12px; padding:1.5rem;">
        <div style="font-size:1.2rem; color:{color}; font-weight:600; margin-bottom:0.5rem;">
            {arrow} Expected Direction: {direction}
        </div>
        <p style="color:#8899bb; font-size:13px; line-height:1.7;">
            {sentiment}
        </p>
        <p style="color:#5a7aa8; font-size:12px;">
            Estimated volatility: {volatility:.2%} · Recommendation: {recommendation.get("decision", "HOLD")}
        </p>
    </div>
    """, unsafe_allow_html=True)
# ── Page: Alerts ───────────────────────────────────────────────────────────────

def page_alerts():
    st.markdown('<h1 class="main-header">Alerts</h1>', unsafe_allow_html=True)

    if not st.session_state.get("analysis_done"):
        _no_analysis_warning()
        return

    result = st.session_state["result"]
    market_data = result.get("market_data", {})
    risk = result.get("risk_assessment", {})
    news_analysis = result.get("news_analysis", {})

    alerts = []

    volatility = market_data.get("volatility", 0)
    trend = market_data.get("trend", "NEUTRAL")
    risk_score = risk.get("score", 50)
    sentiment = news_analysis.get("sentiment", "NEUTRAL")

    if volatility > 0.04:
        alerts.append("High volatility detected. Price swings may be significant.")

    if risk_score > 70:
        alerts.append("Risk score is elevated. Consider reducing exposure.")

    if sentiment == "NEGATIVE":
        alerts.append("Negative news sentiment detected around the stock.")

    if trend == "BEARISH":
        alerts.append("Bearish trend detected: SMA 7 is below SMA 20.")

    if not alerts:
        alerts.append("No major alerts detected at the moment.")

    st.markdown("### Active Alerts")

    for alert in alerts:
        st.markdown(f"""
        <div class="alert-row">
            ⚠️ {alert}
        </div>
        """, unsafe_allow_html=True)

    st.markdown("---")

    st.markdown("""
    <div style="background:#111f3a; border:1px solid #1a2d52; border-radius:10px; padding:1.2rem;">
        <div style="color:#7eb3ff; font-size:14px; font-weight:600; margin-bottom:0.5rem;">
            🔔 Future Alert Types
        </div>
        <ul style="color:#8899bb; font-size:13px; line-height:1.8;">
            <li>Price crosses above SMA 20</li>
            <li>Risk score exceeds threshold</li>
            <li>Sudden increase in volatility</li>
            <li>Major negative financial news</li>
            <li>BUY / SELL recommendation change</li>
        </ul>
    </div>
    """, unsafe_allow_html=True)
# ── Page: Placeholder pages ────────────────────────────────────────────────────

def page_coming_soon(title: str, description: str):
    st.markdown(f'<h1 class="main-header">{title}</h1>', unsafe_allow_html=True)
    if not st.session_state.get("analysis_done"):
        _no_analysis_warning(); return
    st.markdown(f"""<div style="background:#111f3a; border:1px solid #1a2d52; border-radius:12px;
        padding:3rem; text-align:center; margin-top:2rem;">
        <div style="font-size:3rem; margin-bottom:1rem;">🚧</div>
        <h2 style="color:#7eb3ff;">{title}</h2>
        <p style="color:#5a7aa8; margin-top:0.5rem;">{description}</p>
        <p style="color:#3a5070; font-size:12px; margin-top:1rem;">Fonctionnalité en développement — bientôt disponible</p>
    </div>""", unsafe_allow_html=True)


# ── Router ─────────────────────────────────────────────────────────────────────

if page == "Dashboard":
    page_dashboard()
elif page == "Market Data":
    page_market_data()
elif page == "News & Docs":
    page_news_docs()
elif page == "Risk Analysis":
    page_risk()
elif page == "Recommendation":
    page_recommendation()
elif page == "Predictions":
    page_predictions()
elif page == "Alerts":
    page_alerts()

# ── Footer ─────────────────────────────────────────────────────────────────────
st.markdown("<hr style='border-color:#1a2d52; margin-top:3rem;'>", unsafe_allow_html=True)
st.markdown("""<p style='text-align:center; color:#1e3460; font-size:12px;'>
</p>""", unsafe_allow_html=True)