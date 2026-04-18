import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import ta
from statsmodels.tsa.arima.model import ARIMA
from datetime import datetime, timedelta
import warnings
warnings.filterwarnings('ignore')

st.set_page_config(page_title="FinSight Pro V2", page_icon="💎", layout="wide")

st.markdown("""
<style>
    .main {background-color: #0E1117;}
    .stMetric {background-color: #1C1F26; padding: 15px; border-radius: 10px;}
</style>
""", unsafe_allow_html=True)

st.title("💎 FinSight Pro V2.0 - ARIMA Edition")
st.caption("No Prophet Drama. Pure Statsmodels. Chalega 100%")

with st.sidebar:
    st.header("⚙️ Control Panel")
    uploaded_file = st.file_uploader("Upload Stock CSV", type=['csv'])
    n_days = st.slider("Forecast Days", 7, 120, 30)
    run_btn = st.button("🚀 LAUNCH ANALYSIS", type="primary", use_container_width=True)

if run_btn and uploaded_file is not None:
    with st.spinner("ARIMA Model Training... 10 second lagega..."):
        data = pd.read_csv(uploaded_file)
        data.columns = data.columns.str.strip().str.title()
        
        # Auto-fix column names - Candlose भी चलेगा
        col_map = {'Candlose':'Close', 'Candle':'Close', 'Price':'Close', 'Adj Close':'Close'}
        data = data.rename(columns=col_map)
        
        if 'Date' not in data.columns or 'Close' not in data.columns:
            st.error(f"CSV में Date + Close चाहिए. मिले: {list(data.columns)}")
            st.stop()
            
        data['Date'] = pd.to_datetime(data['Date'])
        data = data.sort_values('Date').set_index('Date')
        data = data.asfreq('D')  # Daily frequency fix
        data['Close'] = data['Close'].ffill()
        
        # Indicators
        data['RSI'] = ta.momentum.RSIIndicator(data['Close']).rsi()
        data['SMA20'] = ta.trend.SMAIndicator(data['Close'], 20).sma_indicator()
        data['SMA50'] = ta.trend.SMAIndicator(data['Close'], 50).sma_indicator()
        
        # ARIMA Model - No compilation needed
        model = ARIMA(data['Close'], order=(5,1,0))
        model_fit = model.fit()
        forecast = model_fit.forecast(steps=n_days)
        
        # Future dates
        last_date = data.index[-1]
        future_dates = pd.date_range(last_date + timedelta(days=1), periods=n_days)
        forecast_df = pd.DataFrame({'Date': future_dates, 'Forecast': forecast})
    
    # Metrics
    st.subheader(f"📊 Analysis Report")
    last_price = data['Close'].iloc[-1]
    target_price = forecast.iloc[-1]
    change = ((target_price - last_price)/last_price)*100
    rsi_val = data['RSI'].iloc[-1]
    
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Last Price", f"₹{last_price:.2f}")
    c2.metric(f"{n_days}D Target", f"₹{target_price:.2f}", f"{change:.2f}%")
    c3.metric("RSI", f"{rsi_val:.1f}", "Oversold" if rsi_val<30 else "Overbought" if rsi_val>70 else "Neutral")
    c4.metric("Trend", "BULLISH 🐂" if data['SMA20'].iloc[-1] > data['SMA50'].iloc[-1] else "BEARISH 🐻")
    
    # Chart 1: Price + Forecast + SMA
    fig1 = go.Figure()
    fig1.add_trace(go.Scatter(x=data.index, y=data['Close'], name='Actual Price', line=dict(color='#FF6B35', width=2)))
    fig1.add_trace(go.Scatter(x=data.index, y=data['SMA20'], name='SMA 20', line=dict(color='yellow', dash='dot')))
    fig1.add_trace(go.Scatter(x=data.index, y=data['SMA50'], name='SMA 50', line=dict(color='cyan', dash='dot')))
    fig1.add_trace(go.Scatter(x=forecast_df['Date'], y=forecast_df['Forecast'], name='ARIMA Forecast', line=dict(color='#00D4FF', width=3)))
    fig1.update_layout(template="plotly_dark", height=500, title="Price Action + ARIMA Forecast")
    st.plotly_chart(fig1, use_container_width=True)
    
    # Chart 2: RSI
    fig2 = go.Figure()
    fig2.add_trace(go.Scatter(x=data.index, y=data['RSI'], name='RSI', line=dict(color='magenta')))
    fig2.add_hline(y=70, line_dash="dash", line_color="red", annotation_text="Overbought")
    fig2.add_hline(y=30, line_dash="dash", line_color="lime", annotation_text="Oversold")
    fig2.update_layout(template="plotly_dark", height=300, title="RSI Momentum", yaxis_range=[0,100])
    st.plotly_chart(fig2, use_container_width=True)
    
    # Download
    future_data = forecast_df.copy()
    future_data.columns = ['Date','Predicted']
    st.download_button("📥 Download Forecast CSV", future_data.to_csv(index=False), f"forecast_{datetime.now().date()}.csv")

elif run_btn:
    st.warning("भाई पहले CSV Upload कर 👆")
else:
    st.info("👈 CSV Upload करके LAUNCH दबा")
    st.code("CSV चाहिए: Date,Close या Date,Candlose")
    
    sample = pd.DataFrame({
        'Date': pd.date_range('2024-01-01', periods=200),
        'Close': 150 + pd.Series(range(200)).cumsum() * 0.2 + pd.Series(range(200)).apply(lambda x: (x%10)-5)
    })
    st.download_button("📥 Sample CSV Download Kar", sample.to_csv(index=False), "sample_stock.csv")

st.markdown("---")
st.caption("4 Raat ki mehnat ke baad... Finally Chala! | FinSight Pro V2.0 ARIMA")