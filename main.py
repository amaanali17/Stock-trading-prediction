import streamlit as st
import pandas as pd
import yfinance as yf
import prompts as sm

from datetime import date
from prophet import Prophet
from prophet.plot import plot_plotly
from plotly import graph_objs as go

from ddgs import DDGS
from langchain.tools import tool
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.agents import create_agent

col1, col2 = st.columns([2, 1])
st.set_page_config(layout="wide")

START = "2015-01-01"
TODAY = date.today().strftime("%Y-%m-%d")

with col1:
    st.title("Stock Prediction App")

# user_input = st.text_input('Enter Stock Ticker', 'TSLA')
stocks = ("AAPL", "GOOG", "MSFT", "GME", "TSLA")
with col1:
    selected_stock = st.selectbox("Select dataset for prediction", stocks)
    n_years = st.slider("Years of prediction:", 1, 4)
period = n_years * 365


@st.cache_data
def load_data(ticker):
    df = yf.download(
        ticker,
        start=START,
        end=TODAY,
        progress=False,
        group_by="column"
    )
    df.columns = df.columns.get_level_values(0)

    df.reset_index(inplace=True)
    return df



with col1:
    data_load_state = st.text("Loading data...")
data = load_data(selected_stock)

with col1:
    data_load_state.text("Loading data...done!")
    st.subheader("Raw data")
    st.write(data.tail())


def plot_raw_data():
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=data["Date"], y=data["Open"], name="stock_open"))
    fig.add_trace(go.Scatter(x=data["Date"], y=data["Close"], name="stock_close"))
    fig.update_layout(
        title_text="Time Series Data",
        xaxis_rangeslider_visible=True
    )
    with col1:
        st.plotly_chart(fig)


plot_raw_data()


# ======================
# Forecasting
# ======================

df_train = pd.DataFrame()
df_train["ds"] = pd.to_datetime(data["Date"])
df_train["y"] = pd.to_numeric(data["Close"], errors="coerce")

df_train.dropna(inplace=True)


m = Prophet()
m.fit(df_train)

future = m.make_future_dataframe(periods=period)
forecast = m.predict(future)

with col1:
    st.subheader("Forecast data")
    st.write(forecast.tail())

    st.write("Forecast data")
fig1 = plot_plotly(m, forecast)

with col1:
    
    st.plotly_chart(fig1)

    st.write("Forecast components")
fig2 = m.plot_components(forecast)

with col1:
    
    st.write(fig2)

#===========
#CHAT BOT
#============


#LangChain part

#tools
#TOOLS
@tool
def search_web(query: str) -> str:
    """
    Search the web for real-time information using DuckDuckGo.
    Returns top search result snippets.
    """

    results = []

    with DDGS() as ddgs:
        search_results = ddgs.text(
            query,
            region="wt-wt",
            safesearch="moderate",
            max_results=5
        )

        for r in search_results:
            results.append(
                f"Title: {r.get('title')}\n"
                f"Source: {r.get('href')}\n"
                f"Summary: {r.get('body')}\n"
            )

    return f"Search results for '{query}':" + "\n".join(results)

tools = [search_web]

#LLM Part
llm = ChatGoogleGenerativeAI(
    model="gemini-2.5-flash",
    temperature = 0.3,
    google_api_key="AIzaSyCvb2bnF91BoxPN7fDKk6oBgbW3M8vf1Xc"
)

agent = create_agent(
    model = llm,
    tools = tools,
    system_prompt = sm.system_prompt
)

#StreamLit part 

with col2:
    st.title("CHAT BOT")
    st.image("assets/botImage.png", width=300)
    # Initialize chat history
    if "messages" not in st.session_state:
        st.session_state.messages = []

    # Display history
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    # Chat input at bottom
    if prompt := st.chat_input("Ask about the stock / chart..."):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        with st.chat_message("assistant"):
            answer = agent.invoke({"messages": [{"role": "user", "content": prompt}]})
            ai_message = answer["messages"][-1].content[0]["text"]
            st.markdown(ai_message)

        st.session_state.messages.append({"role": "assistant", "content": str(ai_message)})
    
    
        
        