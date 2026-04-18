import streamlit as st
import yfinance as yf
import pandas as pd
from prophet import Prophet
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import date, timedelta
import ta

st.set_page_config(page_title="FinSight Pro", page_icon="📊", layout="wide", initial_sidebar_state="expanded")

st.markdown("""
<style>
    .main > div {padding-top: 1rem;}
    .stMetric {
        background: rgba(28, 131, 225, 0.1);
        border: 1px solid rgba(28, 131, 225, 0.2);
        padding: 15px;
        border-radius: 10px;
    }
    h1 {text-align: center; color: #1C83E1;}
    .signal-buy {color: #00C853; font-weight: 700; font-size: 20px;}
    .signal-sell {color: #D50000; font-weight: 700; font-size: 20px;}
    .signal-hold {color: #FFA000; font-weight: 700; font-size: 20px;}
</style>
""", unsafe_allow_html=True)

st.title("📊 FinSight Pro")
st.caption("AI-Powered Stock Forecasting & Technical Analysis")

with st.sidebar:
    st.header("⚙️ Control Panel")
    ticker = st.text_input("Stock Ticker", "RELIANCE.NS", help="Example: TCS.NS, INFY.NS, AAPL")
    col1, col2 = st.columns(2)
    start_date = col1.date_input("From", date.today() - timedelta(days=730))
    n_days = col2.slider("Forecast Days", 7, 120, 30)
    run_btn = st.button("🚀 Analyze Stock", use_container_width=True, type="primary")

if run_btn:
    with st.spinner("Fetching data & running AI models..."):
        data = yf.download(ticker, start=start_date, end=date.today(), progress=False)
        if data.empty:
            st.error(f"No data found for {ticker}. Please check the symbol.")
            st.stop()
        
        data['RSI'] = ta.momentum.RSIIndicator(data['Close']).rsi()
        data['50MA'] = data['Close'].rolling(50).mean()
        
        df_prophet = data.reset_index()[['Date', 'Close']].rename(columns={'Date': 'ds', 'Close': 'y'})
        m = Prophet(daily_seasonality=True, yearly_seasonality=True)
        m.fit(df_prophet)
        future = m.make_future_dataframe(periods=n_days)
        forecast = m.predict(future)
        
        st.subheader(f"Dashboard: {ticker}")
        last_price = data['Close'].iloc[-1]
        pred_price = forecast['yhat'].iloc[-1]
        change_pct = ((pred_price - last_price) / last_price) * 100
        
        c1, c2, c3 = st.columns(3)
        c1.metric("Current Price", f"₹{last_price:.2f}")
        c2.metric(f"{n_days}D Target", f"₹{pred_price:.2f}", f"{change_pct:.2f}%")
        c3.metric("RSI", f"{data['RSI'].iloc[-1]:.1f}")
        
        if change_pct > 3 and data['RSI'].iloc[-1] < 70:
            signal = "<p class='signal-buy'>STRONG BUY 📈</p>"
        elif change_pct < -3:
            signal = "<p class='signal-sell'>STRONG SELL 📉</p>"
        else:
            signal = "<p class='signal-hold'>HOLD / WAIT ⚖️</p>"
        st.markdown(signal, unsafe_allow_html=True)
        
        fig = make_subplots(rows=2, cols=1, shared_xaxes=True, vertical_spacing=0.1, row_heights=[0.7, 0.3])
        fig.add_trace(go.Candlestick(x=data.index, open=data['Open'], high=data['High'], low=data['Low'], close=data['Close'], name="Price"), row=1, col=1)
        fig.add_trace(go.Scatter(x=forecast['ds'], y=forecast['yhat'], name='Forecast', line=dict(color='#1C83E1')), row=1, col=1)
        fig.add_trace(go.Scatter(x=data.index, y=data['RSI'], name='RSI', line=dict(color='purple')), row=2, col=1)
        fig.update_layout(height=700, xaxis_rangeslider_visible=False, template="plotly_dark")
        st.plotly_chart(fig, use_container_width=True)
else:
    st.info("👈 choose stock from Left sidebar and 'Analyze Stock' click to start")

st.caption("FinSight Pro v2.0 | Disclaimer: For educational purposes only.")