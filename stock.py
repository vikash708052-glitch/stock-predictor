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
    with st.spinner("Fetching data from Yahoo..."):
        try:
            # Fix 1: Session reset FOR Yahoo block not block 
            yf.shared._requests = None
            
            # Fix 2: period use , start/end not
            data = yf.download(ticker, period="2y", interval="1d", progress=False, auto_adjust=True)
            
            # Fix 3: MultiIndex column fix - yfinance anytime (Price, Ticker) creat
            if isinstance(data.columns, pd.MultiIndex):
                data.columns = data.columns.droplevel(1)
            
            # Fix 4: Empty check with better message
            if data.empty or len(data) < 30:
                st.error(f"No data for {ticker}. Yahoo blocked Streamlit IP. 2 min बाद try करो या दूसरा stock डालो: MSFT, GOOGL")
                st.stop()
                
        except Exception as e:
            st.error(f"Yahoo Error: {str(e)}. App reboot or change ticker .")
            st.stop()
    
    # data is ok
    data = data.dropna()
    data['RSI'] = ta.momentum.RSIIndicator(data['Close']).rsi()
    data['50MA'] = data['Close'].rolling(50).mean()
    
    # clean df for prophet
    df_prophet = data.reset_index()[['Date','Close']].rename(columns={'Date':'ds','Close':'y'})
    df_prophet = df_prophet.dropna()
    
    with st.spinner("Training Prophet AI Model..."):
        m = Prophet(daily_seasonality=True, yearly_seasonality=True)
        m.fit(df_prophet)
        future = m.make_future_dataframe(periods=n_days)
        forecast = m.predict(future)
    
    # other is same 