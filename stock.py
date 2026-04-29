import streamlit as st
from nsepython import *
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime, timedelta
import numpy as np

st.set_page_config(page_title="FinVista Nexus", page_icon="🚀", layout="wide", initial_sidebar_state="collapsed")

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@400;700;900&family=Rajdhani:wght@300;500;700&display=swap');
  .stApp {background: #0a0a0f; background-image: radial-gradient(circle at 20% 50%, rgba(120, 119, 198, 0.3) 0%, transparent 50%);}
  .nexus-header {font-family: 'Orbitron', sans-serif; font-size: 3.5rem; font-weight: 900; background: linear-gradient(45deg, #00d9ff, #7a00ff, #ff00c8); -webkit-background-clip: text; -webkit-text-fill-color: transparent; text-align: center; letter-spacing: 8px; margin-bottom: 1rem;}
  .glass-card {background: rgba(255, 255, 255, 0.05); backdrop-filter: blur(10px); border-radius: 20px; border: 1px solid rgba(255, 255, 255, 0.1); padding: 1.2rem;}
  .metric-value {font-family: 'Orbitron', sans-serif; font-size: 2rem; font-weight: 700; background: linear-gradient(90deg, #00d9ff, #ffffff); -webkit-background-clip: text; -webkit-text-fill-color: transparent;}
  .metric-label {font-family: 'Rajdhani', sans-serif; color: #7a00ff; font-size: 0.8rem; letter-spacing: 2px; text-transform: uppercase;}
  .signal-buy {color: #00ff88; text-shadow: 0 0 20px #00ff88; font-family: 'Orbitron'; font-size: 1.5rem; font-weight: 700;}
  .signal-sell {color: #ff0055; text-shadow: 0 0 20px #ff0055; font-family: 'Orbitron'; font-size: 1.5rem; font-weight: 700;}
  .signal-hold {color: #ffaa00; text-shadow: 0 0 20px #ffaa00; font-family: 'Orbitron'; font-size: 1.5rem; font-weight: 700;}
  .stButton>button {background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; border: 2px solid #00d9ff; border-radius: 12px; font-family: 'Rajdhani', sans-serif; font-weight: 700;}
</style>
""", unsafe_allow_html=True)

st.markdown('<p class="nexus-header">FINVISTA NEXUS</p>', unsafe_allow_html=True)

if 'ticker' not in st.session_state:
    st.session_state.ticker = "RELIANCE"

mode = st.selectbox("SELECT MODE", ["SINGLE ASSET", "WATCHLIST", "COMPARE"], label_visibility="collapsed")

if mode == "SINGLE ASSET":
    cols = st.columns(6)
    trending = ["RELIANCE", "TCS", "INFY", "HDFCBANK", "ICICIBANK", "SBIN"]

    for idx, name in enumerate(trending):
        with cols[idx % 6]:
            if st.button(name, key=name, use_container_width=True):
                st.session_state.ticker = name

    with st.expander("🔍 SEARCH"):
        search = st.text_input("Symbol", placeholder="RELIANCE, TCS", label_visibility="collapsed")
        if st.button("SCAN", use_container_width=True):
            if search:
                st.session_state.ticker = search.upper().strip().replace(".NS", "")

    st.markdown("---")

    @st.cache_data(ttl=300)
    def fetch_nse_data(symbol):
        try:
            # NSE se live quote
            quote = nse_quote_ltp(symbol)
            # NSE se historical data
            end_date = datetime.now()
            start_date = end_date - timedelta(days=365)
            hist = equity_history(symbol, "EQ", start_date.strftime("%d-%m-%Y"), end_date.strftime("%d-%m-%Y"))

            if hist.empty:
                return None, None

            hist = hist.rename(columns={'CH_TIMESTAMP': 'Date', 'CH_OPENING_PRICE': 'open', 'CH_TRADE_HIGH_PRICE': 'high',
                                      'CH_TRADE_LOW_PRICE': 'low', 'CH_CLOSING_PRICE': 'close', 'CH_TOT_TRADED_QTY': 'volume'})
            hist['Date'] = pd.to_datetime(hist['Date'])
            hist = hist.set_index('Date')
            hist = hist.sort_index()

            # Info ke liye
            info = nse_eq(symbol)

            return hist, info
        except Exception as e:
            return None, None

    ticker = st.session_state.ticker
    with st.spinner(f'LOADING {ticker}...'):
        hist, info = fetch_nse_data(ticker)

        if hist is None or hist.empty:
            st.error(f"Unable to fetch data for {ticker}. NSE server busy.")
            st.info("Try: RELIANCE, TCS, INFY, HDFCBANK")
            st.stop()

    current_price = hist['close'][-1]
    prev_close = hist['close'][-2] if len(hist) > 1 else current_price
    change = current_price - prev_close
    change_pct = (change / prev_close) * 100 if prev_close!= 0 else 0

    hist['SMA20'] = hist['close'].rolling(20).mean()
    hist['SMA50'] = hist['close'].rolling(50).mean()
    delta = hist['close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
    rs = gain / loss
    hist['RSI'] = 100 - (100 / (1 + rs))
    rsi = hist['RSI'][-1] if not pd.isna(hist['RSI'][-1]) else 50

    if rsi < 30:
        signal = "STRONG BUY"; signal_class = "signal-buy"; signal_icon = "▲▲"
    elif rsi > 70:
        signal = "SELL"; signal_class = "signal-sell"; signal_icon = "▼▼"
    elif current_price > hist['SMA50'][-1]:
        signal = "BUY"; signal_class = "signal-buy"; signal_icon = "▲▲"
    else:
        signal = "HOLD"; signal_class = "signal-hold"; signal_icon = "■■■"

    st.markdown(f"## {info.get('info', {}).get('companyName', ticker)} // {ticker}")

    col1, col2, col3, col4, col5 = st.columns(5)
    with col1:
        st.markdown('<div class="glass-card">', unsafe_allow_html=True)
        st.markdown('<p class="metric-label">Price</p>', unsafe_allow_html=True)
        st.markdown(f'<p class="metric-value">₹{current_price:.2f}</p>', unsafe_allow_html=True)
        st.markdown(f'<p style="color:{"#00ff88" if change_pct>0 else "#ff0055"};">{change_pct:+.2f}%</p>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)
    with col2:
        st.markdown('<div class="glass-card">', unsafe_allow_html=True)
        st.markdown('<p class="metric-label">Day High</p>', unsafe_allow_html=True)
        st.markdown(f'<p class="metric-value">₹{hist["high"][-1]:.2f}</p>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)
    with col3:
        st.markdown('<div class="glass-card">', unsafe_allow_html=True)
        st.markdown('<p class="metric-label">Day Low</p>', unsafe_allow_html=True)
        st.markdown(f'<p class="metric-value">₹{hist["low"][-1]:.2f}</p>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)
    with col4:
        st.markdown('<div class="glass-card">', unsafe_allow_html=True)
        st.markdown('<p class="metric-label">RSI</p>', unsafe_allow_html=True)
        st.markdown(f'<p class="metric-value">{rsi:.1f}</p>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)
    with col5:
        st.markdown('<div class="glass-card">', unsafe_allow_html=True)
        st.markdown('<p class="metric-label">Signal</p>', unsafe_allow_html=True)
        st.markdown(f'<p class="{signal_class}">{signal_icon} {signal}</p>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

    st.markdown("---")
    tab1, tab2, tab3 = st.tabs(["CHART", "DATA", "FORECAST"])

    with tab1:
        fig = go.Figure()
        fig.add_trace(go.Candlestick(x=hist.index, open=hist['open'], high=hist['high'], low=hist['low'], close=hist['close'], increasing_line_color='#00ff88', decreasing_line_color='#ff0055'))
        fig.add_trace(go.Scatter(x=hist.index, y=hist['SMA20'], line=dict(color='#00d9ff', width=2), name='SMA 20'))
        fig.add_trace(go.Scatter(x=hist.index, y=hist['SMA50'], line=dict(color='#7a00ff', width=2), name='SMA 50'))
        fig.update_layout(template="plotly_dark", height=500, xaxis_rangeslider_visible=False, paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", margin=dict(l=0, r=0, t=30, b=0))
        st.plotly_chart(fig, use_container_width=True)

    with tab2:
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("52W High", f"₹{hist['high'].max():.2f}")
            st.metric("Volume", f"{hist['volume'][-1]:,.0f}")
        with col2:
            st.metric("52W Low", f"₹{hist['low'].min():.2f}")
            st.metric("Avg Volume", f"{hist['volume'].mean():,.0f}")
        with col3:
            st.metric("30D Avg", f"₹{hist['close'].tail(30).mean():.2f}")
            st.metric("Volatility", f"{hist['close'].pct_change().std()*100:.2f}%")

    with tab3:
        pred_days = st.slider("DAYS", 1, 30, 7, label_visibility="collapsed")
        volatility = hist['close'].pct_change().std()
        trend = (hist['SMA20'][-1] - hist['SMA20'][-10]) / hist['SMA20'][-10] if len(hist) > 10 else 0
        future_price = current_price * (1 + trend * pred_days / 10)
        pred_change = ((future_price - current_price) / current_price) * 100
        col1, col2, col3 = st.columns(3)
        with col1:
            st.markdown('<div class="glass-card">', unsafe_allow_html=True)
            st.markdown('<p class="metric-label">Target</p>', unsafe_allow_html=True)
            st.markdown(f'<p class="metric-value">₹{future_price:.2f}</p>', unsafe_allow_html=True)
            st.markdown(f'<p style="color:{"#00ff88" if pred_change>0 else "#ff0055"};">{pred_change:+.2f}%</p>', unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)
        with col2:
            st.markdown('<div class="glass-card">', unsafe_allow_html=True)
            st.markdown('<p class="metric-label">Confidence</p>', unsafe_allow_html=True)
            confidence = max(60, min(95, 100 - abs(rsi - 50)))
            st.markdown(f'<p class="metric-value">{confidence:.0f}%</p>', unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)
        with col3:
            st.markdown('<div class="glass-card">', unsafe_allow_html=True)
            st.markdown('<p class="metric-label">Risk</p>', unsafe_allow_html=True)
            risk = "LOW" if volatility < 0.02 else "MEDIUM" if volatility < 0.04 else "HIGH"
            risk_color = "#00ff88" if risk=="LOW" else "#ffaa00" if risk=="MEDIUM" else "#ff0055"
            st.markdown(f'<p class="metric-value" style="color:{risk_color};">{risk}</p>', unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)

elif mode == "WATCHLIST":
    st.markdown("### WATCHLIST")
    st.info("Add stocks from SINGLE ASSET mode first")

elif mode == "COMPARE":
    st.markdown("### COMPARE")
    symbols = st.text_input("Enter symbols comma separated", "RELIANCE,TCS,INFY", label_visibility="collapsed")
    if st.button("COMPARE NOW"):
        fig = go.Figure()
        for tick in symbols.split(','):
            tick = tick.strip()
            try:
                hist = equity_history(tick, "EQ", "01-01-2024", datetime.now().strftime("%d-%m-%Y"))
                if not hist.empty:
                    hist['Date'] = pd.to_datetime(hist['CH_TIMESTAMP'])
                    hist = hist.set_index('Date').sort_index()
                    norm_price = (hist['CH_CLOSING_PRICE'] / hist['CH_CLOSING_PRICE'][0]) * 100
                    fig.add_trace(go.Scatter(x=hist.index, y=norm_price, name=tick, mode='lines'))
            except:
                pass
        fig.update_layout(template="plotly_dark", height=500, paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", yaxis_title="Normalized Price (%)")
        st.plotly_chart(fig, use_container_width=True)

st.markdown("---")
st.markdown("""<div style='text-align: center; font-family: Rajdhani, sans-serif; color: #333; font-size: 0.7rem;'>FINVISTA NEXUS v8.0 - NSE DIRECT</div>""", unsafe_allow_html=True)
