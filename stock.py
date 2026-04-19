import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import ta
from sklearn.preprocessing import MinMaxScaler
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import LSTM, Dense, Dropout
from pandas_datareader import data as pdr
from datetime import datetime, timedelta
import warnings
warnings.filterwarnings('ignore')

st.set_page_config(page_title="FinSight Pro V4", page_icon="🧠", layout="wide")

st.markdown("""
<style>
   .stMetric {background-color: #1C1F26; padding: 15px; border-radius: 10px; border: 1px solid #2E3440;}
   .stMetric label {color: #D8DEE9!important;}
   .stMetric div {color: #ECEFF4!important; font-size: 22px!important;}
   .signal-buy {background-color: #0E4429; padding: 20px; border-radius: 10px; text-align: center;}
   .signal-sell {background-color: #5A1A1A; padding: 20px; border-radius: 10px; text-align: center;}
   .signal-hold {background-color: #3E3E1A; padding: 20px; border-radius: 10px; text-align: center;}
</style>
""", unsafe_allow_html=True)

st.title("🧠 FinSight Pro V4.0 - LSTM Neural Engine")
st.caption("Deep Learning Predictions | Multi-Indicator AI | Professional Grade")

with st.sidebar:
    st.header("Control Panel")

    data_source = st.radio("Data Source:", ["Live Stock Symbol", "Upload CSV"])

    if data_source == "Live Stock Symbol":
        ticker = st.text_input("Stock Symbol", "RELIANCE.NS", help="NSE: RELIANCE.NS, TCS.NS | US: AAPL, TSLA, MSFT")
        period = st.selectbox("Historical Data", ["1y", "2y", "3y", "5y"], index=1)
        uploaded_file = None
    else:
        uploaded_file = st.file_uploader("Upload Stock CSV", type=['csv'])
        ticker = "Custom CSV"
        period = None

    n_days = st.slider("Forecast Days", 7, 90, 30)
    lstm_epochs = st.slider("LSTM Training Epochs", 10, 100, 50, help="Higher = More Accurate but Slower")
    run_btn = st.button("LAUNCH LSTM ANALYSIS", type="primary", use_container_width=True)

def load_stock_data():
    if data_source == "Live Stock Symbol":
        with st.spinner(f"Fetching {ticker} from Stooq..."):
            try:
                stooq_symbol = ticker.lower().replace('.ns', '.in')
                df = pdr.DataReader(stooq_symbol, 'stooq', start=datetime.now() - timedelta(days=int(period[0])*365))
                df = df.reset_index()
                df.columns = df.columns.str.title()
                df = df[['Date', 'Close', 'High', 'Low', 'Open', 'Volume']].dropna()
                st.success(f"Loaded {len(df)} trading days")
                return df
            except Exception as e:
                st.error(f"Data Fetch Error: {e}")
                st.stop()
    else:
        data = pd.read_csv(uploaded_file)
        data.columns = data.columns.str.strip().str.title()
        col_map = {'Candlose':'Close', 'Candle':'Close', 'Price':'Close', 'Adj Close':'Close'}
        data = data.rename(columns=col_map)
        required = ['Date', 'Close', 'High', 'Low', 'Open', 'Volume']
        for col in required:
            if col not in data.columns:
                if col == 'Volume': data[col] = 0
                else: st.error(f"Missing column: {col}"); st.stop()
        return data[required]

def create_lstm_model(data, n_days):
    close_data = data['Close'].values.reshape(-1, 1)
    scaler = MinMaxScaler(feature_range=(0, 1))
    scaled_data = scaler.fit_transform(close_data)

    lookback = 60
    x_train, y_train = [], []
    for i in range(lookback, len(scaled_data)):
        x_train.append(scaled_data[i-lookback:i, 0])
        y_train.append(scaled_data[i, 0])
    x_train, y_train = np.array(x_train), np.array(y_train)
    x_train = np.reshape(x_train, (x_train.shape[0], x_train.shape[1], 1))

    model = Sequential([
        LSTM(50, return_sequences=True, input_shape=(x_train.shape[1], 1)),
        Dropout(0.2),
        LSTM(50, return_sequences=False),
        Dropout(0.2),
        Dense(25),
        Dense(1)
    ])
    model.compile(optimizer='adam', loss='mean_squared_error')
    model.fit(x_train, y_train, batch_size=32, epochs=lstm_epochs, verbose=0)

    last_60_days = scaled_data[-lookback:]
    predictions = []
    current_batch = last_60_days.reshape((1, lookback, 1))

    for i in range(n_days):
        pred = model.predict(current_batch, verbose=0)[0]
        predictions.append(pred)
        current_batch = np.append(current_batch[:, 1:, :], [[pred]], axis=1)

    predictions = scaler.inverse_transform(predictions)
    return predictions.flatten()

def calculate_indicators(data):
    data['RSI'] = ta.momentum.RSIIndicator(data['Close']).rsi()
    data['SMA20'] = ta.trend.SMAIndicator(data['Close'], 20).sma_indicator()
    data['SMA50'] = ta.trend.SMAIndicator(data['Close'], 50).sma_indicator()
    data['EMA12'] = ta.trend.EMAIndicator(data['Close'], 12).ema_indicator()
    data['EMA26'] = ta.trend.EMAIndicator(data['Close'], 26).ema_indicator()
    macd = ta.trend.MACD(data['Close'])
    data['MACD'] = macd.macd()
    data['MACD_Signal'] = macd.macd_signal()
    data['MACD_Hist'] = macd.macd_diff()
    bb = ta.volatility.BollingerBands(data['Close'])
    data['BB_High'] = bb.bollinger_hband()
    data['BB_Low'] = bb.bollinger_lband()
    data['BB_Mid'] = bb.bollinger_mavg()
    stoch = ta.momentum.StochasticOscillator(data['High'], data['Low'], data['Close'])
    data['Stoch'] = stoch.stoch()
    data['ADX'] = ta.trend.ADXIndicator(data['High'], data['Low'], data['Close']).adx()
    data['OBV'] = ta.volume.OnBalanceVolumeIndicator(data['Close'], data['Volume']).on_balance_volume()
    return data

def generate_signal(data):
    last = data.iloc[-1]
    buy_signals = 0
    sell_signals = 0

    if last['RSI'] < 30: buy_signals += 2
    elif last['RSI'] > 70: sell_signals += 2

    if last['MACD'] > last['MACD_Signal']: buy_signals += 1
    else: sell_signals += 1

    if last['Close'] > last['SMA20'] > last['SMA50']: buy_signals += 2
    elif last['Close'] < last['SMA20'] < last['SMA50']: sell_signals += 2

    if last['Close'] < last['BB_Low']: buy_signals += 1
    elif last['Close'] > last['BB_High']: sell_signals += 1

    if last['Stoch'] < 20: buy_signals += 1
    elif last['Stoch'] > 80: sell_signals += 1

    if buy_signals > sell_signals + 2: return "BUY", buy_signals, sell_signals
    elif sell_signals > buy_signals + 2: return "SELL", buy_signals, sell_signals
    else: return "HOLD", buy_signals, sell_signals

if run_btn:
    if data_source == "Upload CSV" and uploaded_file is None:
        st.warning("Please upload CSV or select Live Symbol")
        st.stop()

    data = load_stock_data()
    data['Date'] = pd.to_datetime(data['Date'])
    data = data.sort_values('Date').set_index('Date')
    data = data.asfreq('B')
    data = data.ffill()

    with st.spinner(f"Training LSTM Neural Network... {lstm_epochs} epochs... Please wait 1-2 minutes..."):
        data = calculate_indicators(data)
        lstm_preds = create_lstm_model(data, n_days)

        last_date = data.index[-1]
        future_dates = pd.date_range(last_date + timedelta(days=1), periods=n_days, freq='B')
        forecast_df = pd.DataFrame({'Date': future_dates, 'LSTM_Forecast': lstm_preds})

    st.subheader(f"Analysis Report - {ticker}")
    last_price = data['Close'].iloc[-1]
    target_price = lstm_preds[-1]
    change = ((target_price - last_price)/last_price)*100
    rsi_val = data['RSI'].iloc[-1]
    signal, buy_cnt, sell_cnt = generate_signal(data)

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Last Price", f"₹{last_price:.2f}")
    c2.metric(f"{n_days}D LSTM Target", f"₹{target_price:.2f}", f"{change:.2f}%")
    c3.metric("RSI", f"{rsi_val:.1f}", "Oversold" if rsi_val<30 else "Overbought" if rsi_val>70 else "Neutral")
    c4.metric("ADX Trend Strength", f"{data['ADX'].iloc[-1]:.1f}", "Strong" if data['ADX'].iloc[-1]>25 else "Weak")

    if signal == "BUY":
        st.markdown(f'<div class="signal-buy"><h2>🟢 BUY SIGNAL</h2><p>Buy Score: {buy_cnt} | Sell Score: {sell_cnt}</p></div>', unsafe_allow_html=True)
    elif signal == "SELL":
        st.markdown(f'<div class="signal-sell"><h2>🔴 SELL SIGNAL</h2><p>Buy Score: {buy_cnt} | Sell Score: {sell_cnt}</p></div>', unsafe_allow_html=True)
    else:
        st.markdown(f'<div class="signal-hold"><h2>🟡 HOLD SIGNAL</h2><p>Buy Score: {buy_cnt} | Sell Score: {sell_cnt}</p></div>', unsafe_allow_html=True)

    fig1 = make_subplots(rows=3, cols=1, shared_xaxes=True, vertical_spacing=0.05,
                         subplot_titles=('Price + Bollinger + LSTM Forecast', 'Volume + OBV', 'RSI + Stochastic'),
                         row_heights=[0.5, 0.25, 0.25])

    fig1.add_trace(go.Scatter(x=data.index, y=data['BB_High'], line=dict(color='gray', width=1, dash='dot'), showlegend=False), row=1, col=1)
    fig1.add_trace(go.Scatter(x=data.index, y=data['BB_Low'], fill='tonexty', line=dict(color='gray', width=1, dash='dot'), fillcolor='rgba(128,128,128,0.1)', name='Bollinger'), row=1, col=1)
    fig1.add_trace(go.Scatter(x=data.index, y=data['Close'], name='Price', line=dict(color='#FF6B35', width=2)), row=1, col=1)
    fig1.add_trace(go.Scatter(x=data.index, y=data['SMA20'], name='SMA20', line=dict(color='yellow', dash='dot')), row=1, col=1)
    fig1.add_trace(go.Scatter(x=data.index, y=data['SMA50'], name='SMA50', line=dict(color='cyan', dash='dot')), row=1, col=1)
    fig1.add_trace(go.Scatter(x=forecast_df['Date'], y=forecast_df['LSTM_Forecast'], name='LSTM Forecast', line=dict(color='#00FF88', width=3)), row=1, col=1)

    fig1.add_trace(go.Bar(x=data.index, y=data['Volume'], name='Volume', marker_color='rgba(100,100,255,0.3)'), row=2, col=1)
    fig1.add_trace(go.Scatter(x=data.index, y=data['OBV'], name='OBV', line=dict(color='magenta')), row=2, col=1)

    fig1.add_trace(go.Scatter(x=data.index, y=data['RSI'], name='RSI', line=dict(color='#FF00FF')), row=3, col=1)
    fig1.add_trace(go.Scatter(x=data.index, y=data['Stoch'], name='Stochastic', line=dict(color='#00FFFF')), row=3, col=1)
    fig1.add_hline(y=70, line_dash="dash", line_color="red", row=3, col=1)
    fig1.add_hline(y=30, line_dash="dash", line_color="lime", row=3, col=1)

    fig1.update_layout(template="plotly_dark", height=900, showlegend=True)
    fig1.update_yaxes(range=[0,100], row=3, col=1)
    st.plotly_chart(fig1, use_container_width=True)

    fig2 = go.Figure()
    fig2.add_trace(go.Bar(x=data.index, y=data['MACD_Hist'], name='MACD Histogram', marker_color=np.where(data['MACD_Hist']>0, 'lime', 'red')))
    fig2.add_trace(go.Scatter(x=data.index, y=data['MACD'], name='MACD', line=dict(color='cyan')))
    fig2.add_trace(go.Scatter(x=data.index, y=data['MACD_Signal'], name='Signal', line=dict(color='orange')))
    fig2.update_layout(template="plotly_dark", height=300, title="MACD Indicator")
    st.plotly_chart(fig2, use_container_width=True)

    future_data = forecast_df.copy()
    future_data.columns = ['Date','LSTM_Predicted']
    st.download_button("Download LSTM Forecast CSV", future_data.to_csv(index=False), f"lstm_forecast_{ticker}_{datetime.now().date()}.csv")

else:
    st.info("Enter Stock Symbol: RELIANCE.NS, TCS.NS, AAPL, TSLA, MSFT, GOOGL")
    st.code("NSE: RELIANCE.NS, TCS.NS, INFY.NS, HDFCBANK.NS, ICICIBANK.NS\nUS: AAPL, TSLA, MSFT, GOOGL, AMZN, NVDA")

    sample = pd.DataFrame({
        'Date': pd.date_range('2023-01-01', periods=500, freq='B'),
        'Close': 150 + np.cumsum(np.random.randn(500)),
        'High': 152 + np.cumsum(np.random.randn(500)),
        'Low': 148 + np.cumsum(np.random.randn(500)),
        'Open': 150 + np.cumsum(np.random.randn(500)),
        'Volume': np.random.randint(100000, 5000000, 500)
    })
    st.download_button("Download Sample CSV", sample.to_csv(index=False), "sample_stock_v4.csv")

st.markdown("---")
st.caption("FinSight Pro V4.0 | LSTM Neural Network | Built with 4 nights of dedication | 2026")