import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime
import numpy as np

st.set_page_config(
    page_title="FinVista Nexus",
    page_icon="🚀",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# CLEAN FUTURISTIC CSS
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@400;700;900&family=Rajdhani:wght@300;500;700&display=swap');
    
    .stApp {
        background: #0a0a0f;
        background-image: 
            radial-gradient(circle at 20% 50%, rgba(120, 119, 198, 0.3) 0%, transparent 50%),
            radial-gradient(circle at 80% 80%, rgba(255, 119, 198, 0.3) 0%, transparent 50%);
    }
    
    .nexus-header {
        font-family: 'Orbitron', sans-serif;
        font-size: 4rem;
        font-weight: 900;
        background: linear-gradient(45deg, #00d9ff, #7a00ff, #ff00c8);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        text-align: center;
        letter-spacing: 8px;
        animation: flicker 3s infinite alternate;
        margin-bottom: 2rem;
    }
    
    @keyframes flicker {
        0%, 100% { filter: drop-shadow(0 0 20px #00d9ff); }
        50% { filter: drop-shadow(0 0 40px #7a00ff); }
    }
    
    .glass-card {
        background: rgba(255, 255, 255, 0.05);
        backdrop-filter: blur(10px);
        border-radius: 20px;
        border: 1px solid rgba(255, 255, 255, 0.1);
        padding: 1.5rem;
        box-shadow: 0 8px 32px 0 rgba(0, 217, 255, 0.2);
    }
    
    .metric-value {
        font-family: 'Orbitron', sans-serif;
        font-size: 2.2rem;
        font-weight: 700;
        background: linear-gradient(90deg, #00d9ff, #ffffff);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }
    
    .metric-label {
        font-family: 'Rajdhani', sans-serif;
        color: #7a00ff;
        font-size: 0.85rem;
        letter-spacing: 2px;
        text-transform: uppercase;
    }
    
    .signal-buy {color: #00ff88; text-shadow: 0 0 20px #00ff88; font-family: 'Orbitron'; font-size: 1.8rem; font-weight: 700;}
    .signal-sell {color: #ff0055; text-shadow: 0 0 20px #ff0055; font-family: 'Orbitron'; font-size: 1.8rem; font-weight: 700;}
    .signal-hold {color: #ffaa00; text-shadow: 0 0 20px #ffaa00; font-family: 'Orbitron'; font-size: 1.8rem; font-weight: 700;}
    
    .news-card {
        background: rgba(255, 255, 255, 0.03);
        border-left: 3px solid #00d9ff;
        padding: 1.2rem;
        margin: 1rem 0;
        border-radius: 10px;
    }
    
    .news-card:hover {
        background: rgba(0, 217, 255, 0.1);
        border-left: 3px solid #7a00ff;
    }
    
    .stButton>button {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        border: 2px solid #00d9ff;
        border-radius: 12px;
        font-family: 'Rajdhani', sans-serif;
        font-weight: 700;
    }
    
    .stButton>button:hover {
        box-shadow: 0 0 30px #00d9ff;
        transform: scale(1.05);
    }
</style>
""", unsafe_allow_html=True)

# HEADER - ONLY LOGO
st.markdown('<p class="nexus-header">FINVISTA NEXUS</p>', unsafe_allow_html=True)

# SESSION STATE
if 'ticker' not in st.session_state:
    st.session_state.ticker = "RELIANCE.NS"

# QUICK ACCESS
cols = st.columns(6)
trending = {
    "RELIANCE.NS": "RELIANCE", "TCS.NS": "TCS", "INFY.NS": "INFOSYS", 
    "HDFCBANK.NS": "HDFC BANK", "ICICIBANK.NS": "ICICI BANK", "SBIN.NS": "SBI",
    "ADANIENT.NS": "ADANI ENT", "TATAMOTORS.NS": "TATA MOTORS", "ITC.NS": "ITC",
    "WIPRO.NS": "WIPRO", "BAJFINANCE.NS": "BAJAJ FIN", "LT.NS": "L&T"
}

for idx, (tick, name) in enumerate(trending.items()):
    with cols[idx % 6]:
        if st.button(name, key=tick, use_container_width=True):
            st.session_state.ticker = tick

with st.expander("🔍 SEARCH"):
    search = st.text_input("Enter Symbol", placeholder="Example: RELIANCE, TSLA, AAPL", label_visibility="collapsed")
    if st.button("SCAN", use_container_width=True):
        if search:
            search = search.upper().strip()
            # Indian stocks ke liye auto .NS add karo
            indian_stocks = ['RELIANCE', 'TCS', 'INFY', 'HDFCBANK', 'ICICIBANK', 'SBIN', 'ADANIENT', 
                           'TATAMOTORS', 'ITC', 'WIPRO', 'BAJFINANCE', 'LT', 'MARUTI', 'AXISBANK']
            if search in indian_stocks and '.NS' not in search:
                search = search + '.NS'
            elif '.' not in search and len(search) <= 10:
                search = search + '.NS'
            st.session_state.ticker = search

st.markdown("---")

# DATA FETCH
ticker = st.session_state.ticker

with st.expander("🔍 SEARCH"):
    search = st.text_input("Enter Symbol", placeholder="Example: RELIANCE, TSLA, AAPL", label_visibility="collapsed")
    if st.button("SCAN", use_container_width=True):
        if search:
            search = search.upper().strip()
            # Indian stocks ke liye auto .NS add karo
            indian_stocks = ['RELIANCE', 'TCS', 'INFY', 'HDFCBANK', 'ICICIBANK', 'SBIN', 'ADANIENT', 
                           'TATAMOTORS', 'ITC', 'WIPRO', 'BAJFINANCE', 'LT', 'MARUTI', 'AXISBANK']
            if search in indian_stocks and '.NS' not in search:
                search = search + '.NS'
            elif '.' not in search and len(search) <= 10:
                search = search + '.NS'
            st.session_state.ticker = search
        
        if hist.empty:
            st.error(f"ERROR: No data available for {ticker}")
            st.stop()
            
    except Exception as e:
        st.error(f"CONNECTION ERROR: Unable to fetch data")
        st.stop()

# CALCULATIONS
current_price = hist['Close'][-1]
prev_close = hist['Close'][-2]
change = current_price - prev_close
change_pct = (change / prev_close) * 100

hist['SMA20'] = hist['Close'].rolling(20).mean()
hist['SMA50'] = hist['Close'].rolling(50).mean()
hist['SMA200'] = hist['Close'].rolling(200).mean()
delta = hist['Close'].diff()
gain = (delta.where(delta > 0, 0)).rolling(14).mean()
loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
rs = gain / loss
hist['RSI'] = 100 - (100 / (1 + rs))
rsi = hist['RSI'][-1]

# SIGNAL
if rsi < 30 and current_price > hist['SMA20'][-1]:
    signal = "STRONG BUY"; signal_class = "signal-buy"; signal_icon = "▲▲"
elif rsi > 70 and current_price < hist['SMA20'][-1]:
    signal = "STRONG SELL"; signal_class = "signal-sell"; signal_icon = "▼▼"
elif current_price > hist['SMA50'][-1]:
    signal = "BUY"; signal_class = "signal-buy"; signal_icon = "▲▲"
elif current_price < hist['SMA50'][-1]:
    signal = "SELL"; signal_class = "signal-sell"; signal_icon = "▼▼"
else:
    signal = "HOLD"; signal_class = "signal-hold"; signal_icon = "■■■"

# ASSET HEADER
st.markdown(f"## {info.get('longName', ticker)} // {ticker}")
st.caption(f"{info.get('sector', 'N/A')} | {info.get('industry', 'N/A')}")

# METRICS
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

# TABS - CLEAN NAMES
tab1, tab2, tab3, tab4 = st.tabs(["CHART", "DATA", "NEWS", "FORECAST"])

with tab1:
    # 3D CHART
    recent_hist = hist.tail(90).copy()
    recent_hist['Index'] = range(len(recent_hist))
    
    fig_3d = go.Figure(data=[go.Scatter3d(
        x=recent_hist['Index'],
        y=recent_hist['Volume'],
        z=recent_hist['Close'],
        mode='lines+markers',
        marker=dict(size=4, color=recent_hist['Close'], colorscale='Viridis', showscale=True),
        line=dict(color='#00d9ff', width=4)
    )])
    
    fig_3d.update_layout(
        scene=dict(xaxis_title='Time', yaxis_title='Volume', zaxis_title='Price', bgcolor="rgba(0,0,0,0)"),
        paper_bgcolor="rgba(0,0,0,0)", height=500, margin=dict(l=0, r=0, t=30, b=0),
        font=dict(color="#00d9ff")
    )
    st.plotly_chart(fig_3d, use_container_width=True)
    
    # CANDLESTICK
    fig = go.Figure()
    fig.add_trace(go.Candlestick(x=hist.index, open=hist['Open'], high=hist['High'], low=hist['Low'], close=hist['Close'],
                                 increasing_line_color='#00ff88', decreasing_line_color='#ff0055'))
    fig.add_trace(go.Scatter(x=hist.index, y=hist['SMA20'], line=dict(color='#00d9ff', width=2), name='SMA 20'))
    fig.add_trace(go.Scatter(x=hist.index, y=hist['SMA50'], line=dict(color='#7a00ff', width=2), name='SMA 50'))
    
    fig.update_layout(template="plotly_dark", height=500, xaxis_rangeslider_visible=False,
                      paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                      margin=dict(l=0, r=0, t=30, b=0), font=dict(color="#00d9ff"))
    st.plotly_chart(fig, use_container_width=True)

with tab2:
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("#### VALUATION")
        st.metric("P/E Ratio", f"{info.get('trailingPE', 'N/A')}")
        st.metric("P/B Ratio", f"{info.get('priceToBook', 'N/A')}")
        st.metric("EPS", f"₹{info.get('trailingEps', 'N/A')}")
        st.metric("Dividend Yield", f"{info.get('dividendYield', 0)*100:.2f}%")
    
    with col2:
        st.markdown("#### PERFORMANCE")
        st.metric("Profit Margin", f"{info.get('profitMargins', 0)*100:.1f}%")
        st.metric("ROE", f"{info.get('returnOnEquity', 0)*100:.1f}%")
        st.metric("Revenue", f"₹{info.get('totalRevenue', 0)/10000000:.0f} Cr")
        st.metric("Beta", f"{info.get('beta', 'N/A')}")
    
    with col3:
        st.markdown("#### RANGE")
        st.metric("52W High", f"₹{info.get('fiftyTwoWeekHigh', 0):.2f}")
        st.metric("52W Low", f"₹{info.get('fiftyTwoWeekLow', 0):.2f}")
        st.metric("50D Avg", f"₹{info.get('fiftyDayAverage', 0):.2f}")
        st.metric("200D Avg", f"₹{info.get('twoHundredDayAverage', 0):.2f}")
    
    st.markdown("---")
    st.markdown(f'<div class="glass-card">{info.get("longBusinessSummary", "No data available.")}</div>', unsafe_allow_html=True)

with tab3:
    if news:
        for article in news[:10]:
            pub_date = datetime.fromtimestamp(article['providerPublishTime']).strftime('%d %b %Y, %H:%M')
            st.markdown(f"""
            <div class="news-card">
                <h4 style="color: #00d9ff; margin: 0 0 0.5rem 0;">{article['title']}</h4>
                <p style="color: #7a00ff; font-size: 0.85rem; margin: 0;">
                    {pub_date} | {article['publisher']}
                </p>
                <a href="{article['link']}" target="_blank" style="color: #00d9ff; text-decoration: none;">
                    View Article →
                </a>
            </div>
            """, unsafe_allow_html=True)
    else:
        st.info("No recent articles available.")

with tab4:
    pred_days = st.slider("DAYS", 1, 30, 7, label_visibility="collapsed")
    
    volatility = hist['Close'].pct_change().std()
    trend = (hist['SMA20'][-1] - hist['SMA20'][-10]) / hist['SMA20'][-10]
    future_price = current_price * (1 + trend * pred_days / 10 + np.random.uniform(-volatility, volatility))
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
        st.progress(confidence/100)
        st.markdown('</div>', unsafe_allow_html=True)
    
    with col3:
        st.markdown('<div class="glass-card">', unsafe_allow_html=True)
        st.markdown('<p class="metric-label">Risk</p>', unsafe_allow_html=True)
        risk = "LOW" if volatility < 0.02 else "MEDIUM" if volatility < 0.04 else "HIGH"
        risk_color = "#00ff88" if risk=="LOW" else "#ffaa00" if risk=="MEDIUM" else "#ff0055"
        st.markdown(f'<p class="metric-value" style="color:{risk_color};">{risk}</p>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)
    
    # Prediction chart
    pred_dates = pd.date_range(start=hist.index[-1], periods=pred_days+1, freq='D')[1:]
    pred_prices = np.linspace(current_price, future_price, pred_days)
    
    fig_pred = go.Figure()
    fig_pred.add_trace(go.Scatter(x=hist.index.tail(30), y=hist['Close'].tail(30), mode='lines', name='History', line=dict(color='#00d9ff')))
    fig_pred.add_trace(go.Scatter(x=pred_dates, y=pred_prices, mode='lines+markers', name='Projection', 
                                  line=dict(color='#ff00c8', dash='dash', width=3)))
    fig_pred.update_layout(template="plotly_dark", height=400, paper_bgcolor="rgba(0,0,0,0)",
                           plot_bgcolor="rgba(0,0,0,0)", margin=dict(l=0, r=0, t=30, b=0))
    st.plotly_chart(fig_pred, use_container_width=True)

# FOOTER
st.markdown("---")
st.markdown("""
<div style='text-align: center; font-family: Rajdhani, sans-serif; color: #333; font-size: 0.7rem;'>
    FINVISTA NEXUS v5.0 | NOT FINANCIAL ADVICE
</div>
""", unsafe_allow_html=True)
