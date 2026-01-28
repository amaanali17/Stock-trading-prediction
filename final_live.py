import streamlit as st
import pandas as pd
import yfinance as yf
from streamlit_autorefresh import st_autorefresh
import plotly.graph_objects as go
import time
import threading
from threading import Lock

# ------------------------------------
# STREAMLIT CONFIG
# ------------------------------------

st.set_page_config(layout="wide")
st.title("📈 Live Stock Chart")


# ------------------------------------
# FETCH DATA
# ------------------------------------

def fetch_stock_data(symbol="RELIANCE.NS", interval="1m", period="1d"):
    """Fetch stock data from yfinance"""
    try:
        print(f"Fetching {symbol}...")
        data = yf.download(symbol, interval=interval, period=period, progress=False, timeout=15)
        if data is not None and not data.empty:
            # Flatten multi-level columns if present
            if isinstance(data.columns, pd.MultiIndex):
                data.columns = data.columns.droplevel(1)
            print(f"Got {len(data)} candles for {symbol}")
            return data
        else:
            print(f" No data for {symbol}")
            return pd.DataFrame()
    except Exception as e:
        print(f"Error fetching {symbol}: {e}")
        return pd.DataFrame()


# ------------------------------------
# BACKGROUND THREAD
# ------------------------------------

def data_refresh_worker():
    """Background thread to refresh data"""
    
    print("Background worker started")
    
    while True:
        try:
            new_data = fetch_stock_data("RELIANCE.NS", interval="1m", period="1d")
            
            if not new_data.empty:
                st.session_state.stock_data = new_data.copy()
                print(f" Data refreshed successfully")
            
            time.sleep(300) 
            
        except Exception as e:
            print(f"✗ Worker error: {e}")
            time.sleep(60)


# ------------------------------------
# INITIALIZE SESSION STATE
# ------------------------------------

if "data_initialized" not in st.session_state:
    print("Loading initial data...")
    initial_data = fetch_stock_data("RELIANCE.NS", interval="1m", period="1d")
    st.session_state.stock_data = initial_data
    st.session_state.data_initialized = True
    print("Initial data loaded")
    
    thread = threading.Thread(target=data_refresh_worker, daemon=True)
    thread.start()
    print("Worker thread started")


# ------------------------------------
# AUTO REFRESH UI
# ------------------------------------

st_autorefresh(interval=5000, key="refresh_ticker")

# ------------------------------------
# DISPLAY
# ------------------------------------

display_data = st.session_state.get("stock_data", pd.DataFrame())

if display_data is not None and not display_data.empty:
    
    df = display_data.reset_index()
    
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.droplevel(1)
    
    if 'Datetime' in df.columns and 'Date' not in df.columns:
        df.rename(columns={'Datetime': 'Date'}, inplace=True)
    
    fig = go.Figure(data=[go.Candlestick(
        x=df['Date'],
        open=df['Open'],
        high=df['High'],
        low=df['Low'],
        close=df['Close'],
        name='RELIANCE'
    )])

    fig.update_layout(
        title="RELIANCE - Today's Intraday Chart (1 Min Candlesticks)",
        yaxis_title='Stock Price (INR)',
        template='plotly_white',
        height=600,
        xaxis_rangeslider_visible=False,
        hovermode='x unified'
    )

    st.plotly_chart(fig, width='stretch')
    
    st.subheader("📊 Price Data (Today)")
    st.dataframe(
        df[['Date', 'Open', 'High', 'Low', 'Close', 'Volume']],
        width='stretch',
        hide_index=True
    )
    
    # Show stats
    col1, col2, col3, col4 = st.columns(4)
    latest = df.iloc[-1]
    with col1:
        st.metric("Latest Close", f"₹{latest['Close']:.2f}")
    with col2:
        st.metric("Day High", f"₹{latest['High']:.2f}")
    with col3:
        st.metric("Day Low", f"₹{latest['Low']:.2f}")
    with col4:
        st.metric("Volume", f"{int(latest['Volume']/1e6)}M")

else:   
    st.info("⏳ **Loading stock data...**\n\nThis takes 15-30 seconds on first load.")
