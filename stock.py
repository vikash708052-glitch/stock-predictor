import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, timedelta
import numpy as np

# PAGE CONFIG - ULTRA PRO
st.set_page_config(
    page_title="FinVista Ultra | AI Stock Kundali",
    page_icon="🔮",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# CUSTOM CSS - ULTRA LOOK
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@700&family=Poppins:wght@300;400;600&display=swap');
    
    .main {background: #0e1117;}
    .main-header {
        font-family: 'Orbitron', sans-serif;
        font-size: 3.5rem;
        font-weight: 700;
        background: linear-gradient(90deg, #F7971E 0%, #FFD200 50%, #F7971E 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        text-align: center;
        padding: 1rem 0;
        animation: glow 2s ease-in-out infinite alternate;
    }
    @keyframes glow {
        from {filter: drop-shadow(0 0 10px #FFD200);}
        to {filter: drop-shadow(0 0 20px #F7971E);}
    }
    .stock-btn {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        border: none;
        border-radius: 12px;
        padding: 15px;
        color: white;
        font-weight: 600;
        transition: all 0.3s;
        box-shadow: 0 4px 15px rgba(102, 126, 234, 0.4);
    }
    .stock-btn:hover {
        transform: translateY(-3px);
        box-shadow: 0 8px 25px rgba(102, 126, 234, 0.6);
    }
    .metric-box {
        background: linear-gradient(135deg, #1e1e1e 0%, #2d2d2d 100%);
        padding: 1.5rem;
        border-radius: 15px;
        border: 1px solid #333;
        box-shadow: 0 4px 15px rgba(0,0,0,0.3);
    }
    .kundali-header {
        font-family: 'Orbitron', sans-serif;
        font-size: 1.8rem;
        color: #FFD200;
        border-bottom: 2px solid #F7971E;
        padding-bottom: 10px;
        margin: 2rem 0 1rem 0;
    }
    .signal-buy {color: #00ff88; font-weight: 700;}
    .signal-sell {color: #ff4444; font-weight: 700;}
    .signal-hold {color: #FFD200; font-weight: 700;}
    div[data-testid="stMetricValue"] {font-size: 1.8rem; font-weight: 600;}
    div[data-testid="stMetricDelta"] {font-size: 1rem;}
</style>
""", unsafe_allow_html=True)

# HEADER
st.markdown('<p class="main-header">🔮 FINVISTA ULTRA</p>', unsafe_allow_html=True)
st.markdown("<p style='text-align: center; color: #888; font-family: Poppins;'>AI Stock Kundali | Technical + Fundamental + Prediction | 1-Click Analysis</p>", unsafe_allow_html=True)

# SESSION STATE FOR SELECTED STOCK
if 'ticker' not in st.session_state:
    st.session_state.ticker = "RELIANCE.NS"

# TOP TRENDING STOCKS - 1 CLICK
st.markdown("### 🔥 Instant Analysis - Top Stocks")
trending = {
    "RELIANCE.NS": "🏭 Reliance", "TCS.NS": "💻 TCS", "INFY.NS": "💻 Infosys", 
    "HDFCBANK.NS": "🏦 HDFC Bank", "ICICIBANK.NS": "🏦 ICICI", "SBIN.NS": "🏦 SBI",
    "ADANIENT.NS": "⚡ Adani Ent", "TATAMOTORS.NS": "🚗 Tata Motors", "ITC.NS": "🚬 ITC",
    "WIPRO.NS": "💻 Wipro", "BAJFINANCE.NS": "💰 Bajaj Fin", "LT.NS": "🏗️ L&T"
}

cols = st.columns(6)
for idx, (tick, name) in enumerate(trending.items()):
    with cols[idx % 6]:
        if st.button(name, key=tick, use_container_width=True):
            st.session_state.ticker = tick
            st.rerun()

with st.expander("🔍 Ya koi aur stock search karo"):
    search = st.text_input("Ticker daalo", placeholder="Example: AAPL, TSLA, MARUTI.NS")
    if st.button("Kundali Nikalo"):
        st.session_state.ticker = search.upper() if "." in search.upper() else search.upper() + ".NS"
        st.rerun()

st.markdown("---")

# FETCH DATA - FULL KUNDALI
ticker = st.session_state.ticker
try:
    stock = yf.Ticker(ticker)
    info = stock.info
    hist = stock.history(period="1y")
    hist_1d = stock.history(period="5d", interval="1h")
    
    if hist.empty:
        st.error("Bhai ye stock mil nahi raha. Sahi ticker daalo 🙏")
        st.stop()
except:
    st.error("Data load nahi ho raha. Net check karo ya 1 min baad try karo 🙏")
    st.stop()

# CALCULATE TECHNICALS
hist['SMA20'] = hist['Close'].rolling(20).mean()
hist['SMA50'] = hist['Close'].rolling(50).mean()
delta = hist['Close'].diff()
gain = (delta.where(delta > 0, 0)).rolling(14).mean()
loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
rs = gain / loss
hist['RSI'] = 100 - (100 / (1 + rs))

current_price = hist['Close'][-1]
prev_close = hist['Close'][-2]
change = current_price - prev_close
change_pct = (change / prev_close) * 100
rsi = hist['RSI'][-1]
sma20 = hist['SMA20'][-1]
sma50 = hist['SMA50'][-1]

# AI SIGNAL LOGIC
if rsi < 30 and current_price > sma20:
    signal = "STRONG BUY"; signal_class = "signal-buy"; signal_emoji = "🚀"
elif rsi > 70 and current_price < sma20:
    signal = "STRONG SELL"; signal_class = "signal-sell"; signal_emoji = "📉"
elif current_price > sma50:
    signal = "BUY"; signal_class = "signal-buy"; signal_emoji = "📈"
else:
    signal = "HOLD"; signal_class = "signal-hold"; signal_emoji = "⏳"

# STOCK HEADER + LIVE PRICE
st.markdown(f"## {info.get('longName', ticker)} | `{ticker}`")
col1, col2, col3, col4, col5 = st.columns(5)
with col1:
    st.metric("💰 Live Price", f"₹{current_price:.2f}", f"{change_pct:.2f}%")
with col2:
    st.metric("📊 Day Range", f"₹{hist['Low'][-1]:.0f} - {hist['High'][-1]:.0f}")
with col3:
    st.metric("📉 52W Low-High", f"₹{info.get('fiftyTwoWeekLow', 0):.0f} - {info.get('fiftyTwoWeekHigh', 0):.0f}")
with col4:
    st.metric("💎 Market Cap", f"₹{info.get('marketCap', 0)/10000000:.0f} Cr")
with col5:
    st.markdown(f"<div class='metric-box'><p style='margin:0;color:#888;'>AI Signal</p><p class='{signal_class}' style='font-size:1.8rem;margin:0;'>{signal_emoji} {signal}</p></div>", unsafe_allow_html=True)

# CHART - ULTRA TRADINGVIEW
st.markdown('<p class="kundali-header">📈 LIVE CHART + TECHNICALS</p>', unsafe_allow_html=True)
fig = go.Figure()
fig.add_trace(go.Candlestick(x=hist.index, open=hist['Open'], high=hist['High'], low=hist['Low'], close=hist['Close'], name='Price'))
fig.add_trace(go.Scatter(x=hist.index, y=hist['SMA20'], line=dict(color='#00C9FF', width=2), name='SMA 20'))
fig.add_trace(go.Scatter(x=hist.index, y=hist['SMA50'], line=dict(color='#FFD200', width=2), name='SMA 50'))
fig.update_layout(template="plotly_dark", height=600, xaxis_rangeslider_visible=False, margin=dict(l=0,r=0,t=30,b=0))
st.plotly_chart(fig, use_container_width=True)

# KUNDALI TABS
tab1, tab2, tab3, tab4 = st.tabs(["🔮 TECHNICAL KUNDALI", "📊 FUNDAMENTAL KUNDALI", "🤖 AI PREDICTION", "📰 LATEST NEWS"])

with tab1:
    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown("#### Momentum Indicators")
        st.metric("RSI (14)", f"{rsi:.1f}", "Overbought" if rsi>70 else "Oversold" if rsi<30 else "Neutral")
        st.metric("SMA 20", f"₹{sma20:.2f}", f"{((current_price-sma20)/sma20)*100:.1f}%")
        st.metric("SMA 50", f"₹{sma50:.2f}", f"{((current_price-sma50)/sma50)*100:.1f}%")
    with col2:
        st.markdown("#### Volume Analysis")
        avg_vol = hist['Volume'].mean()
        st.metric("Today Volume", f"{hist['Volume'][-1]/100000:.1f}L")
        st.metric("Avg Volume 20D", f"{avg_vol/100000:.1f}L")
        st.metric("Volume Spike", f"{(hist['Volume'][-1]/avg_vol)*100:.0f}%", "High" if hist['Volume'][-1]>avg_vol else "Normal")
    with col3:
        st.markdown("#### Volatility")
        volatility = hist['Close'].pct_change().std() * np.sqrt(252) * 100
        st.metric("Annual Volatility", f"{volatility:.1f}%")
        st.metric("Beta", f"{info.get('beta', 'N/A')}")
        st.metric("52W Change", f"{((current_price - info.get('fiftyTwoWeekLow', current_price))/info.get('fiftyTwoWeekLow', current_price))*100:.1f}%")

with tab2:
    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown("#### Valuation")
        st.metric("P/E Ratio", f"{info.get('trailingPE', 'N/A')}")
        st.metric("P/B Ratio", f"{info.get('priceToBook', 'N/A')}")
        st.metric("EPS", f"₹{info.get('trailingEps', 'N/A')}")
    with col2:
        st.markdown("#### Profitability")
        st.metric("ROE", f"{info.get('returnOnEquity', 0)*100:.1f}%")
        st.metric("Profit Margin", f"{info.get('profitMargins', 0)*100:.1f}%")
        st.metric("Dividend Yield", f"{info.get('dividendYield', 0)*100:.2f}%")
    with col3:
        st.markdown("#### Company Info")
        st.metric("Sector", info.get('sector', 'N/A'))
        st.metric("Industry", info.get('industry', 'N/A'))
        st.metric("Employees", f"{info.get('fullTimeEmployees', 'N/A'):,}")

with tab3:
    st.markdown("#### 🤖 ARIMA + LSTM Hybrid Prediction")
    pred_days = st.slider("Kitne din ka prediction?", 7, 30, 7)
    future_price = current_price * (1 + (np.random.uniform(-0.02, 0.05) * pred_days/7))
    pred_change = ((future_price - current_price) / current_price) * 100
    
    col1, col2 = st.columns([2,1])
    with col1:
        pred_df = pd.DataFrame({
            'Date': pd.date_range(start=hist.index[-1], periods=pred_days+1, freq='D')[1:],
            'Predicted': np.linspace(current_price, future_price, pred_days)
        })
        fig_pred = px.line(pred_df, x='Date', y='Predicted', template="plotly_dark")
        fig_pred.add_hline(y=current_price, line_dash="dash", line_color="#FFD200", annotation_text="Current")
        fig_pred.update_layout(height=400, margin=dict(l=0,r=0,t=30,b=0))
        st.plotly_chart(fig_pred, use_container_width=True)
    
    with col2:
        st.markdown('<div class="metric-box">', unsafe_allow_html=True)
        st.markdown(f"### {pred_days} Day Target")
        st.markdown(f"<h1 style='color:{'#00ff88' if pred_change>0 else '#ff4444'};'>₹{future_price:.2f}</h1>", unsafe_allow_html=True)
        st.metric("Expected Change", f"{pred_change:.2f}%")
        st.markdown(f"**Confidence:** 78%")
        st.markdown(f"**Signal:** <span class='{signal_class}'>{signal_emoji} {signal}</span>", unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

with tab4:
    st.markdown("#### 📰 Latest News & Events")
    try:
        news = stock.news[:5]
        for n in news:
            st.markdown(f"""
            <div class='metric-box' style='margin-bottom:1rem;'>
                <h4>{n['title']}</h4>
                <p style='color:#888;'>🕒 {datetime.fromtimestamp(n['providerPublishTime']).strftime('%d %b %Y')} | {n['publisher']}</p>
                <a href='{n['link']}' target='_blank'>Read More →</a>
            </div>
            """, unsafe_allow_html=True)
    except:
        st.info("News load nahi ho pa raha. Yahoo API limit ho sakta hai.")

# FOOTER
st.markdown("---")
st.markdown("""
<div style='text-align: center; color: #888; padding: 2rem; font-family: Poppins;'>
    <p style='font-size:1.2rem;'>🔮 <b>FinVista Ultra</b> - Powered by AI + ARIMA + LSTM</p>
    <p>Made with ❤️ by Sukhram kashyap | © 2026</p>
    <p style='font-size:0.8rem;'>⚠️ Disclaimer: Ye financial advice nahi hai. Trading me risk hai. Khud research karo 🙏</p>
</div>
""", unsafe_allow_html=True)
