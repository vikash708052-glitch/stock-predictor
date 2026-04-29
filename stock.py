import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, timedelta
import numpy as np
import time

st.set_page_config(page_title="FinVista Nexus", page_icon="🚀", layout="wide", initial_sidebar_state="collapsed")

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@400;700;900&family=Rajdhani:wght@300;500;700&display=swap');
   .stApp {background: #0a0a0f; background-image: radial-gradient(circle at 20% 50%, rgba(120, 119, 198, 0.3) 0%, transparent 50%);}
   .nexus-header {font-family: 'Orbitron', sans-serif; font-size: 3.5rem; font-weight: 900; background: linear-gradient(45deg, #00d9ff, #7a00ff, #ff00c8); -webkit-background-clip: text; -webkit-text-fill-color: transparent; text-align: center; letter-spacing: 8px; margin-bottom: 1rem;}
   .glass-card {background: rgba(255, 255, 255, 0.05); backdrop-filter: blur(10px); border-radius: 20px; border: 1px solid rgba(255, 255, 255, 0.1); padding: 1.2rem; box-shadow: 0 8px 32px 0 rgba(0, 217, 255, 0.2);}
   .metric-value {font-family: 'Orbitron', sans-serif; font-size: 2rem; font-weight: 700; background: linear-gradient(90deg, #00d9ff, #ffffff); -webkit-background-clip: text; -webkit-text-fill-color: transparent;}
   .metric-label {font-family: 'Rajdhani', sans-serif; color: #7a00ff; font-size: 0.8rem; letter-spacing: 2px; text-transform: uppercase;}
   .signal-buy {color: #00ff88; text-shadow: 0 0 20px #00ff88; font-family: 'Orbitron'; font-size: 1.5rem; font-weight: 700;}
   .signal-sell {color: #ff0055; text-shadow: 0 0 20px #ff0055; font-family: 'Orbitron'; font-size: 1.5rem; font-weight: 700;}
   .signal-hold {color: #ffaa00; text-shadow: 0 0 20px #ffaa00; font-family: 'Orbitron'; font-size: 1.5rem; font-weight: 700;}
   .news-card {background: rgba(255, 255, 255, 0.03); border-left: 3px solid #00d9ff; padding: 1rem; margin: 0.8rem 0; border-radius: 10px;}
   .stButton>button {background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; border: 2px solid #00d9ff; border-radius: 12px; font-family: 'Rajdhani', sans-serif; font-weight: 700;}
   .stTabs [data-baseweb="tab-list"] {gap: 8px;}
   .stTabs [data-baseweb="tab"] {background: rgba(255,255,255,0.05); border-radius: 10px; font-family: 'Rajdhani', sans-serif; font-weight: 700;}
</style>
""", unsafe_allow_html=True)

st.markdown('<p class="nexus-header">FINVISTA NEXUS</p>', unsafe_allow_html=True)

# SESSION STATE
if 'ticker' not in st.session_state:
    st.session_state.ticker = "RELIANCE.NS"
if 'watchlist' not in st.session_state:
    st.session_state.watchlist = ["RELIANCE.NS", "TCS.NS", "INFY.NS"]
if 'compare_list' not in st.session_state:
    st.session_state.compare_list = []

# MAIN MODE SELECTOR
mode = st.selectbox("SELECT MODE", ["SINGLE ASSET", "PORTFOLIO TRACKER", "COMPARE", "SCREENER"], label_visibility="collapsed")

if mode == "SINGLE ASSET":
    # QUICK ACCESS
    cols = st.columns(6)
    trending = {"RELIANCE.NS": "RELIANCE", "TCS.NS": "TCS", "INFY.NS": "INFOSYS", "HDFCBANK.NS": "HDFC BANK", "ICICIBANK.NS": "ICICI BANK", "SBIN.NS": "SBI"}

    for idx, (tick, name) in enumerate(trending.items()):
        with cols[idx % 6]:
            if st.button(name, key=tick, use_container_width=True):
                st.session_state.ticker = tick

    col1, col2 = st.columns([3,1])
    with col1:
        with st.expander("🔍 SEARCH"):
            search = st.text_input("Symbol", placeholder="RELIANCE, TSLA", label_visibility="collapsed")
            if st.button("SCAN", use_container_width=True):
                if search:
                    search = search.upper().strip()
                    indian = ['RELIANCE','TCS','INFY','HDFCBANK','ICICIBANK','SBIN','ADANIENT','TATAMOTORS','ITC','WIPRO','BAJFINANCE','LT','MARUTI','AXISBANK']
                    if search in indian and '.NS' not in search:
                        search = search + '.NS'
                    elif '.' not in search and len(search) <= 10:
                        search = search + '.NS'
                    st.session_state.ticker = search
    with col2:
        if st.button("⭐ ADD TO WATCHLIST", use_container_width=True):
            if st.session_state.ticker not in st.session_state.watchlist:
                st.session_state.watchlist.append(st.session_state.ticker)
                st.success("Added!")

    st.markdown("---")

    @st.cache_data(ttl=300)
    def fetch_data(ticker):
        try:
            stock = yf.Ticker(ticker)
            hist = stock.history(period="1y", interval="1d")
            if hist.empty:
                return None, None, None
            info = stock.info
            try:
                news = stock.news
            except:
                news = []
            return hist, info, news
        except:
            return None, None, None

    ticker = st.session_state.ticker
    with st.spinner(f'LOADING {ticker}...'):
        hist, info, news = fetch_data(ticker)

        if hist is None or hist.empty:
            st.error(f"Unable to fetch data for {ticker}. Try again in 2 minutes.")
            st.stop()

    # CALCULATIONS
    current_price = hist['Close'][-1]
    prev_close = hist['Close'][-2] if len(hist) > 1 else current_price
    change = current_price - prev_close
    change_pct = (change / prev_close) * 100 if prev_close!= 0 else 0

    hist['SMA20'] = hist['Close'].rolling(20).mean()
    hist['SMA50'] = hist['Close'].rolling(50).mean()
    delta = hist['Close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
    rs = gain / loss
    hist['RSI'] = 100 - (100 / (1 + rs))
    rsi = hist['RSI'][-1] if not pd.isna(hist['RSI'][-1]) else 50

    if rsi < 30 and current_price > hist['SMA20'][-1]:
        signal = "STRONG BUY"; signal_class = "signal-buy"; signal_icon = "▲▲"
    elif rsi > 70 and current_price < hist['SMA20'][-1]:
        signal = "STRONG SELL"; signal_class = "signal-sell"; signal_icon = "▼▼"
    elif current_price > hist['SMA50'][-1]:
        signal = "BUY"; signal_class = "signal-buy"; signal_icon = "▲▲"
    else:
        signal = "HOLD"; signal_class = "signal-hold"; signal_icon = "■■■"

    st.markdown(f"## {info.get('longName', ticker)} // {ticker}")

    col1, col2, col3, col4, col5 = st.columns(5)
    with col1:
        st.markdown('<div class="glass-card">', unsafe_allow_html=True)
        st.markdown('<p class="metric-label">Price</p>', unsafe_allow_html=True)
        st.markdown(f'<p class="metric-value">₹{current_price:.2f}</p>', unsafe_allow_html=True)
        st.markdown(f'<p style="color:{"#00ff88" if change_pct>0 else "#ff0055"};">{change_pct:+.2f}%</p>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)
    with col2:
        st.markdown('<div class="glass-card">', unsafe_allow_html=True)
        st.markdown('<p class="metric-label">Market Cap</p>', unsafe_allow_html=True)
        st.markdown(f'<p class="metric-value">₹{info.get("marketCap", 0)/10000000:.0f}Cr</p>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)
    with col3:
        st.markdown('<div class="glass-card">', unsafe_allow_html=True)
        st.markdown('<p class="metric-label">P/E</p>', unsafe_allow_html=True)
        st.markdown(f'<p class="metric-value">{info.get("trailingPE", "N/A")}</p>', unsafe_allow_html=True)
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
    tab1, tab2, tab3, tab4 = st.tabs(["CHART", "DATA", "NEWS", "FORECAST"])

    with tab1:
        fig = go.Figure()
        fig.add_trace(go.Candlestick(x=hist.index, open=hist['Open'], high=hist['High'], low=hist['Low'], close=hist['Close'], increasing_line_color='#00ff88', decreasing_line_color='#ff0055'))
        fig.add_trace(go.Scatter(x=hist.index, y=hist['SMA20'], line=dict(color='#00d9ff', width=2), name='SMA 20'))
        fig.add_trace(go.Scatter(x=hist.index, y=hist['SMA50'], line=dict(color='#7a00ff', width=2), name='SMA 50'))
        fig.update_layout(template="plotly_dark", height=500, xaxis_rangeslider_visible=False, paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", margin=dict(l=0, r=0, t=30, b=0))
        st.plotly_chart(fig, use_container_width=True)

    with tab2:
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("P/E Ratio", f"{info.get('trailingPE', 'N/A')}")
            st.metric("EPS", f"₹{info.get('trailingEps', 'N/A')}")
            st.metric("Dividend Yield", f"{info.get('dividendYield', 0)*100:.2f}%")
        with col2:
            st.metric("Profit Margin", f"{info.get('profitMargins', 0)*100:.1f}%")
            st.metric("ROE", f"{info.get('returnOnEquity', 0)*100:.1f}%")
            st.metric("Beta", f"{info.get('beta', 'N/A')}")
        with col3:
            st.metric("52W High", f"₹{info.get('fiftyTwoWeekHigh', 0):.2f}")
            st.metric("52W Low", f"₹{info.get('fiftyTwoWeekLow', 0):.2f}")
            st.metric("50D Avg", f"₹{info.get('fiftyDayAverage', 0):.2f}")

    with tab3:
        if news and len(news) > 0:
            for article in news[:8]:
                pub_date = datetime.fromtimestamp(article['providerPublishTime']).strftime('%d %b %Y')
                st.markdown(f"""<div class="news-card"><h4 style="color: #00d9ff; margin: 0 0 0.5rem 0;">{article['title']}</h4><p style="color: #7a00ff; font-size: 0.85rem;">{pub_date} | {article['publisher']}</p><a href="{article['link']}" target="_blank" style="color: #00d9ff;">View →</a></div>""", unsafe_allow_html=True)
        else:
            st.info("No articles available.")

    with tab4:
        pred_days = st.slider("DAYS", 1, 30, 7, label_visibility="collapsed")
        volatility = hist['Close'].pct_change().std()
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

elif mode == "PORTFOLIO TRACKER":
    st.markdown("### WATCHLIST")
    if len(st.session_state.watchlist) == 0:
        st.info("Watchlist empty. Add stocks from SINGLE ASSET mode.")
    else:
        data_list = []
        for tick in st.session_state.watchlist:
            try:
                stock = yf.Ticker(tick)
                hist = stock.history(period="5d")
                if not hist.empty:
                    price = hist['Close'][-1]
                    change = ((hist['Close'][-1] - hist['Close'][0]) / hist['Close'][0]) * 100
                    data_list.append({"Symbol": tick, "Price": f"₹{price:.2f}", "5D Change": f"{change:+.2f}%"})
            except:
                pass

        if data_list:
            df = pd.DataFrame(data_list)
            st.dataframe(df, use_container_width=True, hide_index=True)

        if st.button("CLEAR WATCHLIST"):
            st.session_state.watchlist = []
            st.rerun()

elif mode == "COMPARE":
    st.markdown("### COMPARE MULTIPLE STOCKS")
    col1, col2 = st.columns([3,1])
    with col1:
        compare_input = st.text_input("Add Symbol", placeholder="RELIANCE.NS, TCS.NS", label_visibility="collapsed")
    with col2:
        if st.button("ADD", use_container_width=True):
            if compare_input and compare_input.upper() not in st.session_state.compare_list:
                st.session_state.compare_list.append(compare_input.upper())

    if len(st.session_state.compare_list) > 0:
        st.write("Selected:", ", ".join(st.session_state.compare_list))
        if st.button("COMPARE NOW"):
            fig = go.Figure()
            for tick in st.session_state.compare_list:
                try:
                    hist = yf.Ticker(tick).history(period="6mo")
                    if not hist.empty:
                        norm_price = (hist['Close'] / hist['Close'][0]) * 100
                        fig.add_trace(go.Scatter(x=hist.index, y=norm_price, name=tick, mode='lines'))
                except:
                    pass
            fig.update_layout(template="plotly_dark", height=500, paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", yaxis_title="Normalized Price (%)")
            st.plotly_chart(fig, use_container_width=True)

        if st.button("CLEAR LIST"):
            st.session_state.compare_list = []
            st.rerun()

elif mode == "SCREENER":
    st.markdown("### STOCK SCREENER")
    col1, col2, col3 = st.columns(3)
    with col1:
        min_pe = st.number_input("Min P/E", value=0.0)
    with col2:
        max_pe = st.number_input("Max P/E", value=50.0)
    with col3:
        min_mcap = st.number_input("Min Market Cap (Cr)", value=1000)

    if st.button("SCAN MARKET"):
        scan_list = ["RELIANCE.NS", "TCS.NS", "INFY.NS", "HDFCBANK.NS", "ICICIBANK.NS", "SBIN.NS", "ITC.NS", "WIPRO.NS", "BAJFINANCE.NS", "LT.NS"]
        results = []
        with st.spinner("Scanning..."):
            for tick in scan_list:
                try:
                    stock = yf.Ticker(tick)
                    info = stock.info
                    pe = info.get('trailingPE', 0)
                    mcap = info.get('marketCap', 0) / 10000000
                    if min_pe <= pe <= max_pe and mcap >= min_mcap:
                        results.append({"Symbol": tick, "Name": info.get('longName', ''), "P/E": f"{pe:.2f}", "Market Cap": f"₹{mcap:.0f}Cr"})
                except:
                    pass

        if results:
            st.dataframe(pd.DataFrame(results), use_container_width=True, hide_index=True)
        else:
            st.warning("No stocks match criteria.")

st.markdown("---")
st.markdown("""<div style='text-align: center; font-family: Rajdhani, sans-serif; color: #333; font-size: 0.7rem;'>FINVISTA NEXUS v6.0</div>""", unsafe_allow_html=True)
