"""
asurdev Sentinel - Streamlit Dashboard
"""
import streamlit as st
import asyncio
import json
from datetime import datetime

st.set_page_config(
    page_title="asurdev Sentinel",
    page_icon="🔭",
    layout="wide"
)

st.title("🔭 asurdev Sentinel")
st.caption("Multi-Agent Trading Advisor")


def init_session():
    if "history" not in st.session_state:
        st.session_state.history = []


def render_signal(result):
    signal = result.get("signal", "NEUTRAL")
    confidence = result.get("confidence", 50)
    
    if signal == "BULLISH":
        st.success(f"### 🟢 {signal} ({confidence}% confidence)")
    elif signal == "BEARISH":
        st.error(f"### 🔴 {signal} ({confidence}% confidence)")
    else:
        st.warning(f"### 🟡 {signal} ({confidence}% confidence)")


async def run_analysis(symbol: str, action: str):
    from agents import get_orchestrator
    
    orchestrator = get_orchestrator()
    return await orchestrator.analyze(symbol, action)


def main():
    init_session()
    
    col1, col2 = st.columns([1, 3])
    
    with col1:
        st.header("Settings")
        symbol = st.selectbox("Symbol", ["BTC", "ETH", "SOL", "BNB", "XRP"])
        action = st.selectbox("Action", ["buy", "sell", "hold"])
        
        if st.button("Analyze", type="primary"):
            with st.spinner("Analyzing..."):
                result = asyncio.run(run_analysis(symbol, action))
                st.session_state.history.append({
                    "symbol": symbol,
                    "result": result,
                    "timestamp": datetime.now()
                })
    
    with col2:
        if st.session_state.history:
            latest = st.session_state.history[-1]
            st.subheader(f"Latest: {latest['symbol']}")
            render_signal(latest["result"])
            
            with st.expander("Details"):
                st.json(latest["result"])
        else:
            st.info("Click 'Analyze' to start")


if __name__ == "__main__":
    main()
