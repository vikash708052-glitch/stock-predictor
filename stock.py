import streamlit as st
import pandas as pd
from prophet import Prophet
import plotly.graph_objects as go
import ta
from datetime import datetime

st.set_page_config(page_title="FinSight Pro V2", page_icon="💎", layout="wide")

# Custom CSS for attractive look
st.markdown("""
<style>
    .main {background-color: #0E1117;}
    .stMetric {background-color: #1C1F26; padding: 15px; border-radius: 10px;}
</style>
""", unsafe_allow_html=True)

st.title("💎 FinSight Pro V2.0 - Gajab Kamal Edition")
st.caption("Technical Analysis + AI Forecast + Sexy Charts")

with st.sidebar:
    st.header("⚙️ Control Panel")
    uploaded_file = st.file_uploader("Upload Stock CSV", type=['csv'])
    n_days = st.slider("Forecast Days", 7, 120, 30)
    run_btn = st.button("🚀 LAUNCH ANALYSIS", type="primary", use_container_width=True)

if run_btn and uploaded_file is not None:
    with st.spinner("AI is here... making imprassive..."):
        data = pd.read_csv(uploaded_file)
        data.columns = data.columns.str.strip().str.title()
        
        # Auto-fix column names
        col_map = {'Candlose':'Close', 'Candle':'Close', 'Price':'Close', 'Adj Close':'Close'}
        data = data.rename(columns=col_map)
        
        if 'Date' not in data.columns or 'Close' not in data.columns:
            st.error(f"CSV in Date + Close need. find: {list(data.columns)}")
            st.stop()
            
        data['Date'] = pd.to_datetime(data['Date'])
        data = data.sort_values('Date').set_index('Date')
        
        # imprassive Indicators
        data['RSI'] = ta.momentum.RSIIndicator(data['Close']).rsi()
        data['SMA20'] = ta.trend.SMAIndicator(data['Close'], 20).sma_indicator()
        data['SMA50'] = ta.trend.SMAIndicator(data['Close'], 50).sma_indicator()
        
        # Prophet Model
        df_prophet = data.reset_index()[['Date','Close']].rename(columns={'Date':'ds','Close':'y'})
        m = Prophet(daily_seasonality=True, weekly_seasonality=True, yearly_seasonality=True)
        m.fit(df_prophet)
        future = m.make_future_dataframe(periods=n_days)
        forecast = m.predict(future)
    
    # imprassive Metrics
    st.subheader(f"📊 Analysis Report")
    last_price = data['Close'].iloc[-1]
    target_price = forecast['yhat'].iloc[-1]
    change = ((target_price - last_price)/last_price)*100
    rsi_val = data['RSI'].iloc[-1]
    
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Last Price", f"₹{last_price:.2f}")
    c2.metric(f"{n_days}D Target", f"₹{target_price:.2f}", f"{change:.2f}%")
    c3.metric("RSI", f"{rsi_val:.1f}", "Oversold" if rsi_val<30 else "Overbought" if rsi_val>70 else "Neutral")
    c4.metric("Trend", "BULLISH 🐂" if data['SMA20'].iloc[-1] > data['SMA50'].iloc[-1] else "BEARISH 🐻")
    
    # imprassive Chart 1: Price + Forecast + SMA
    fig1 = go.Figure()
    fig1.add_trace(go.Scatter(x=data.index, y=data['Close'], name='Actual Price', line=dict(color='#FF6B35', width=2)))
    fig1.add_trace(go.Scatter(x=data.index, y=data['SMA20'], name='SMA 20', line=dict(color='yellow', dash='dot')))
    fig1.add_trace(go.Scatter(x=data.index, y=data['SMA50'], name='SMA 50', line=dict(color='cyan', dash='dot')))
    fig1.add_trace(go.Scatter(x=forecast['ds'], y=forecast['yhat'], name='AI Forecast', line=dict(color='#00D4FF', width=3)))
    fig1.add_trace(go.Scatter(x=forecast['ds'], y=forecast['yhat_upper'], fill=None, mode='lines', line=dict(color='rgba(0,212,255,0.1)'), showlegend=False))
    fig1.add_trace(go.Scatter(x=forecast['ds'], y=forecast['yhat_lower'], fill='tonexty', mode='lines', line=dict(color='rgba(0,212,255,0.1)'), name='Confidence'))
    fig1.update_layout(template="plotly_dark", height=500, title="Price Action + AI Forecast", xaxis_rangeslider_visible=False)
    st.plotly_chart(fig1, use_container_width=True)
    
    # imprassive Chart 2: RSI
    fig2 = go.Figure()
    fig2.add_trace(go.Scatter(x=data.index, y=data['RSI'], name='RSI', line=dict(color='magenta')))
    fig2.add_hline(y=70, line_dash="dash", line_color="red", annotation_text="Overbought")
    fig2.add_hline(y=30, line_dash="dash", line_color="lime", annotation_text="Oversold")
    fig2.update_layout(template="plotly_dark", height=300, title="RSI Momentum", yaxis_range=[0,100])
    st.plotly_chart(fig2, use_container_width=True)
    
    # Download Button
    future_data = forecast[['ds','yhat','yhat_lower','yhat_upper']].tail(n_days)
    future_data.columns = ['Date','Predicted','Low_Est','High_Est']
    st.download_button("📥 Download Forecast CSV", future_data.to_csv(index=False), f"forecast_{datetime.now().date()}.csv")

elif run_btn:
    st.warning("first CSV Upload 👆")
else:
    st.info("👈 CSV Upload and LAUNCH click")
    st.code("CSV want: Date,Close or Date,Candlose\n2024-01-01,150.25\n2024-01-02,152.30")
    
    sample = pd.DataFrame({
        'Date': pd.date_range('2024-01-01', periods=200),
        'Close': 150 + pd.Series(range(200)).cumsum() * 0.2
    })
    st.download_button("📥 Sample CSV Download Kar", sample.to_csv(index=False), "sample_stock.csv")

st.markdown("---")
st.caption("Made with ❤️ after 4 raat ki mehnat | FinSight Pro V2.0")