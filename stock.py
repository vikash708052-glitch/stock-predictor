import streamlit as st
import yfinance as yf
import pandas as pd
from prophet import Prophet
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import date, timedelta
import ta

st.set_page_config(page_title="FinSight Pro", page_icon="📊", layout="wide")
st.title("📊 FinSight Pro")

with st.sidebar:
    st.header("⚙️ Control Panel")
    ticker = st.text_input("Stock Ticker", "RELIANCE.NS")
    n_days = st.slider("Forecast Days", 7, 120, 30)
    run_btn = st.button("🚀 Analyze Stock", type="primary")

if run_btn:
    data = yf.download(ticker, start=date.today()-timedelta(days=730), end=date.today())
    if data.empty:
        st.error("No data found")
        st.stop()
    
    data['RSI'] = ta.momentum.RSIIndicator(data['Close']).rsi()
    df = data.reset_index()[['Date','Close']].rename(columns={'Date':'ds','Close':'y'})
    m = Prophet()
    m.fit(df)
    future = m.make_future_dataframe(periods=n_days)
    forecast = m.predict(future)
    
    st.line_chart(forecast.set_index('ds')['yhat'])
    st.metric("Prediction", f"₹{forecast['yhat'].iloc[-1]:.2f}")
else:
    st.info("👈 Sidebar to Analyze click")