import streamlit as st
import pandas as pd
from prophet import Prophet
import plotly.graph_objects as go
import ta

st.set_page_config(page_title="FinSight Pro", page_icon="📊", layout="wide")
st.title("📊 FinSight Pro - CSV Edition")
st.caption("No Internet Data Needed. Upload Your Own CSV!")

with st.sidebar:
    st.header("⚙️ Control Panel")
    uploaded_file = st.file_uploader("Upload Stock CSV", type=['csv'], help="Columns needed: Date, Close")
    n_days = st.slider("Forecast Days", 7, 120, 30)
    run_btn = st.button("🚀 Analyze Stock", type="primary")

if run_btn and uploaded_file is not None:
    with st.spinner("Reading your CSV..."):
        try:
            data = pd.read_csv(uploaded_file)
            
            # Column name fix - Date ya date, Close ya close run all
            data.columns = data.columns.str.title()
            
            if 'Date' not in data.columns or 'Close' not in data.columns:
                st.error("CSV in 'Date'  'Candlose' column it is importent")
                st.stop()
                
            data['Date'] = pd.to_datetime(data['Date'])
            data = data.sort_values('Date')
            data = data.set_index('Date')
            
        except Exception as e:
            st.error(f"CSV Error: {e}")
            st.stop()
    
    data['RSI'] = ta.momentum.RSIIndicator(data['Close']).rsi()
    df_prophet = data.reset_index()[['Date','Close']].rename(columns={'Date':'ds','Close':'y'})
    
    with st.spinner("Training Prophet AI on your data..."):
        m = Prophet(daily_seasonality=True)
        m.fit(df_prophet)
        future = m.make_future_dataframe(periods=n_days)
        forecast = m.predict(future)
    
    st.subheader(f"Forecast for Your Stock")
    c1, c2, c3 = st.columns(3)
    c1.metric("Last Price", f"{data['Close'].iloc[-1]:.2f}")
    c2.metric(f"{n_days}D Target", f"{forecast['yhat'].iloc[-1]:.2f}")
    c3.metric("Change %", f"{((forecast['yhat'].iloc[-1] - data['Close'].iloc[-1])/data['Close'].iloc[-1]*100):.2f}%")
    
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=data.index, y=data['Close'], name='Actual', line=dict(color='orange')))
    fig.add_trace(go.Scatter(x=forecast['ds'], y=forecast['yhat'], name='Forecast', line=dict(color='#1C83E1')))
    fig.update_layout(template="plotly_dark", height=500)
    st.plotly_chart(fig, use_container_width=True)

elif run_btn and uploaded_file is None:
    st.warning("first CSV Upload 👆")
else:
    st.info("👈  CSV file upload from sidebar")
    st.code("CSV Format Example:\nDate,Close\n2023-01-01,150.25\n2023-01-02,152.30\n2023-01-03,151.80")
    
    # Sample CSV download button
    sample = pd.DataFrame({
        'Date': pd.date_range('2024-01-01', periods=100),
        'Close': 150 + pd.Series(range(100)).cumsum() * 0.1 + pd.Series(range(100)).apply(lambda x: x%5)
    })
    st.download_button("📥 Download Sample CSV", sample.to_csv(index=False), "sample_stock.csv")