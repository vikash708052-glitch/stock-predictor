import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from datetime import date, timedelta, datetime
from sklearn.preprocessing import MinMaxScaler
from sklearn.metrics import mean_absolute_error, mean_squared_error
from tensorflow.keras.models import Sequential, load_model
from tensorflow.keras.layers import Input, LSTM, Dense, Dropout
import os
import pickle

st.set_page_config(page_title="Stock Predictor Pro", layout="wide", page_icon="🚀")
st.title('🚀 Stock Predictor Pro Max')

# --- Sidebar ---
st.sidebar.header('⚙️ Control Panel')
st.sidebar.header("Upload Stock Data")
uploaded_file = st.sidebar.file_uploader("CSV Upload Karo", type="csv")

prediction_days = st.sidebar.slider('LSTM Lookback Days', 30, 200, 100)
future_days = st.sidebar.slider('Future Forecast Days', 1, 60, 30)
epochs = st.sidebar.slider('Training Epochs', 5, 50, 15)

# --- Functions ---
@st.cache_data
def load_data_from_csv(uploaded_file):
    if uploaded_file is not None:
        data = pd.read_csv(uploaded_file)
        data.rename(columns={
            'Close/Last': 'Close',
            'close/last': 'Close',
            'CLOSE': 'Close',
            'Adj Close': 'Close',
            'Price': 'Close',
            'ltp': 'Close',
            'VOLUME': 'Volume',
            'Vol.': 'Volume',
            'HIGH': 'High',
            'LOW': 'Low',
            'OPEN': 'Open'
        }, inplace=True)

        for col in ['Close', 'Open', 'High', 'Low', 'Volume']:
            if col in data.columns:
                data[col] = data[col].replace('[\₹,\$,]', '', regex=True).astype(float)

        data['Date'] = pd.to_datetime(data['Date'], format='mixed', dayfirst=True)
        data = data.sort_values('Date', ascending=True)
        data.reset_index(drop=True, inplace=True)
        return data
    return None

def add_technical_indicators(data):
    data['MA100'] = data['Close'].rolling(100).mean()
    data['MA200'] = data['Close'].rolling(200).mean()
    data['Volume_MA'] = data['Volume'].rolling(20).mean()
    data.dropna(inplace=True)
    return data

def create_model(input_shape):
    model = Sequential([
        Input(shape=input_shape),
        LSTM(64, return_sequences=True),
        Dropout(0.3),
        LSTM(64, return_sequences=True),
        Dropout(0.3),
        LSTM(32),
        Dropout(0.2),
        Dense(16, activation='relu'),
        Dense(1)
    ])
    model.compile(optimizer='adam', loss='mean_squared_error')
    return model

# --- Main Logic ---
data = load_data_from_csv(uploaded_file)

if data is None:
    st.warning("Upload CSV file in sidebar first")
    st.stop()

if uploaded_file is not None:
    stock_name = uploaded_file.name.split('.')[0].upper()

    # Model and Scaler of file names
    model_path = f"saved_models/{stock_name}_model.h5"
    scaler_path = f"saved_models/{stock_name}_scaler.pkl"

    # creat Folder if not
    os.makedirs("saved_models", exist_ok=True)

col1, col2 = st.sidebar.columns(2)
with col1:
    train_btn = st.button("🎯 Train Model", type="primary", use_container_width=True)
with col2:
    predict_btn = st.button("🔮 Predict", use_container_width=True)

# --- Training ---
if train_btn:
    data = add_technical_indicators(data)

    if len(data) < prediction_days + 50:
        st.error(f"Kam se kam {prediction_days + 50} din ka data chahiye. Tumhare paas {len(data)} din ka hai.")
        st.stop()

    with st.spinner(f'Training LSTM for {stock_name}... Only on time do this ☕'):
        close_data = data['Close'].values.reshape(-1, 1)
        scaler = MinMaxScaler(feature_range=(0, 1))
        scaled_data = scaler.fit_transform(close_data)

        x, y = [], []
        for i in range(prediction_days, len(scaled_data)):
            x.append(scaled_data[i-prediction_days:i, 0])
            y.append(scaled_data[i, 0])
        x, y = np.array(x), np.array(y)
        x = np.reshape(x, (x.shape[0], x.shape[1], 1))

        # Test split for metrics
        split = int(len(x) * 0.8)
        x_train, x_test = x[:split], x[split:]
        y_train, y_test = y[:split], y[split:]

        model = create_model((x_train.shape[1], 1))
        model.fit(x_train, y_train, epochs=epochs, batch_size=32, verbose=0)

        # Test accuracy show
        test_predictions = model.predict(x_test, verbose=0)
        test_predictions = scaler.inverse_transform(test_predictions)
        y_test_actual = scaler.inverse_transform(y_test.reshape(-1, 1))

        mae = mean_absolute_error(y_test_actual, test_predictions)
        mape = np.mean(np.abs((y_test_actual - test_predictions) / y_test_actual)) * 100

        # Model and Scaler Save 
        model.save(model_path)
        with open(scaler_path, 'wb') as f:
            pickle.dump(scaler, f)

    st.success(f"✅ Model Saved! Accuracy: {100-mape:.1f}% | MAE: ${mae:.2f}")
    st.info("Ab 'Predict' button click.that time run close ofter Terminal .")
    st.balloons()

# --- Prediction ---
if predict_btn:
    if not os.path.exists(model_path):
        st.error("Pehle 'Train Model' button click. Model save not in this time.")
        st.stop()

    data = add_technical_indicators(data)

    # Saved Model Load  - just 1 second 
    with st.spinner('Loading saved model...'):
        model = load_model(model_path)
        with open(scaler_path, 'rb') as f:
            scaler = pickle.load(f)

    st.subheader(f"{stock_name} Stock Data")
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Latest Price", f"${float(data['Close'].iloc[-1]):.2f}",
               f"{float(data['Close'].iloc[-1] - data['Close'].iloc[-2]):.2f}")
    col2.metric("MA100", f"${float(data['MA100'].iloc[-1]):.2f}")
    col3.metric("MA200", f"${float(data['MA200'].iloc[-1]):.2f}")
    col4.metric("Volume", f"{int(data['Volume'].iloc[-1]):,}")

    # Candlestick Chart
    st.subheader('📊 Candlestick + Volume')
    fig1 = go.Figure()
    fig1.add_trace(go.Candlestick(x=data['Date'], open=data['Open'], high=data['High'],
                                  low=data['Low'], close=data['Close'], name='OHLC'))
    fig1.add_trace(go.Scatter(x=data['Date'], y=data['MA100'], name='MA100', line=dict(color='orange')))
    fig1.add_trace(go.Scatter(x=data['Date'], y=data['MA200'], name='MA200', line=dict(color='purple')))
    fig1.update_layout(height=600, xaxis_rangeslider_visible=False)
    st.plotly_chart(fig1, width='stretch')

    # Future Forecast - No Training Needed
    close_data = data['Close'].values.reshape(-1, 1)
    scaled_data = scaler.transform(close_data)

    last_sequence = scaled_data[-prediction_days:]
    future_predictions = []
    for _ in range(future_days):
        next_pred = model.predict(last_sequence.reshape(1, prediction_days, 1), verbose=0)
        future_predictions.append(next_pred[0, 0])
        last_sequence = np.append(last_sequence[1:], next_pred, axis=0)
    future_predictions = scaler.inverse_transform(np.array(future_predictions).reshape(-1, 1))

    # Future Forecast Plot
    st.subheader(f'🔮 AI Forecast: Next {future_days} Days')
    last_date = data['Date'].iloc[-1]
    future_dates = pd.date_range(start=last_date + timedelta(days=1), periods=future_days)

    fig3 = go.Figure()
    fig3.add_trace(go.Scatter(x=data['Date'][-90:], y=data['Close'][-90:],
                             name='Historical', line=dict(color='#00D9FF', width=2)))
    fig3.add_trace(go.Scatter(x=future_dates, y=future_predictions.flatten(),
                             name='AI Forecast', line=dict(color='#FF006E', width=3, dash='dot'),
                             fill='tozeroy', fillcolor='rgba(255,0,110,0.1)'))
    fig3.update_layout(height=500, hovermode='x unified',
                      title=f"{stock_name} Price Prediction")
    st.plotly_chart(fig3, width='stretch')

    # Forecast Table
    with st.expander("📋 View Detailed Forecast Table"):
        forecast_df = pd.DataFrame({
            'Date': future_dates.strftime('%Y-%m-%d'),
            'Predicted Price': [f"${p[0]:.2f}" for p in future_predictions],
            'Change from Today': [f"{(p[0] - float(data['Close'].iloc[-1]))/float(data['Close'].iloc[-1])*100:.2f}%" for p in future_predictions]
        })
        st.dataframe(forecast_df, width='stretch')

    change = future_predictions[-1][0] - float(data['Close'].iloc[-1])
    change_pct = (change / float(data['Close'].iloc[-1])) * 100
    st.success(f"✅ Prediction Done! Day+1: ${future_predictions[0][0]:.2f} | Day+{future_days}: ${future_predictions[-1][0]:.2f} ({change_pct:+.2f}%)")

else:
    st.info("👈 1. CSV upload 2. 'Train Model' one click 3. Fir hamesha 'Predict' click")
    st.image("https://cdn-icons-png.flaticon.com/512/2329/2329087.png", width=200)