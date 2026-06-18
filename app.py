import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime

from data import load_market_data
from zone_engine import scan_supply_demand_zones

# --------------------------------------------------
# PAGE CONFIG
# --------------------------------------------------

st.set_page_config(
    page_title="Supply & Demand Scanner",
    page_icon="📊",
    layout="wide"
)

st.title("📊 Institutional Supply & Demand Scanner")

# --------------------------------------------------
# SIDEBAR
# --------------------------------------------------

st.sidebar.header("Scanner Settings")

market = st.sidebar.selectbox(
    "Market",
    [
        "Forex",
        "Crypto",
        "Commodity",
        "US Stocks",
        "NSE"
    ]
)

timeframe = st.sidebar.selectbox(
    "Timeframe",
    [
        "15m",
        "30m",
        "1h",
        "4h",
        "1d"
    ],
    index=2
)

bars = st.sidebar.slider(
    "History Bars",
    200,
    3000,
    1000,
    100
)

profile = st.sidebar.selectbox(
    "Zone Quality",
    [
        "Good",
        "Strong",
        "Best"
    ]
)

base_counts = st.sidebar.multiselect(
    "Base Candles",
    [1, 2, 3],
    default=[1, 2, 3]
)

legout_counts = st.sidebar.multiselect(
    "Legout Candles",
    [1, 2, 3, "More Than 3"],
    default=[1]
)

status_filter = st.sidebar.multiselect(
    "Zone Status",
    [
        "FRESH",
        "USED",
        "SL HIT",
        "TARGET HIT"
    ],
    default=["FRESH"]
)

scan_btn = st.sidebar.button(
    "🔍 Scan Market",
    use_container_width=True
)

# --------------------------------------------------
# MAIN AREA
# --------------------------------------------------

placeholder = st.empty()

progress = st.progress(0)

table_placeholder = st.empty()

chart_placeholder = st.empty()

# =====================================================
# SCAN MARKET
# =====================================================

if scan_btn:

    placeholder.info("Downloading market data...")

    market_data = load_market_data(
        market=market,
        timeframe=timeframe,
        bars=bars
    )

    total = len(market_data)

    if total == 0:

        st.error("No symbols found.")

        st.stop()

    all_zones = []

    completed = 0

    for symbol, df in market_data.items():

        completed += 1

        progress.progress(
            completed / total,
            text=f"Scanning {symbol} ({completed}/{total})"
        )

        try:

            zones = scan_supply_demand_zones(
                df=df,
                symbol_name=symbol,
                tf_name=timeframe,
                selected_base_counts=base_counts,
                selected_legout_counts=legout_counts,
                profile=profile
            )

            if zones:

                all_zones.extend(zones)

        except Exception as e:

            st.warning(f"{symbol} : {e}")

    progress.empty()

    if len(all_zones) == 0:

        st.warning("No zones found.")

        st.stop()

    results = pd.DataFrame(all_zones)

    # -----------------------------------
    # FILTER STATUS
    # -----------------------------------

    if len(status_filter):

        results = results[
            results["Status"].isin(status_filter)
        ]

    # -----------------------------------
    # SORT
    # -----------------------------------

    results = results.sort_values(

        by=[
            "Strength",
            "Base Count",
            "Legout Count"
        ],

        ascending=False

    ).reset_index(drop=True)

    # -----------------------------------
    # SHOW RESULT
    # -----------------------------------

    placeholder.success(

        f"{len(results)} Zones Found"

    )

    st.subheader("Detected Zones")

    st.dataframe(

        results,

        use_container_width=True,

        height=550

    )

    # -----------------------------------
    # DOWNLOAD CSV
    # -----------------------------------

    csv = results.to_csv(index=False)

    st.download_button(

        "📥 Download CSV",

        csv,

        file_name=f"SupplyDemand_{market}_{timeframe}.csv",

        mime="text/csv"

    )

    # -----------------------------------
    # SELECT CHART
    # -----------------------------------

    st.subheader("Zone Chart")

    selected_symbol = st.selectbox(

        "Choose Symbol",

        results["Symbol"].unique()

    )

    selected_df = market_data[selected_symbol]

    selected_zone = results[
        results["Symbol"] == selected_symbol
    ].iloc[0]

# =====================================================
# PLOTLY CHART
# =====================================================

fig = go.Figure()

fig.add_trace(

    go.Candlestick(

        x=selected_df.index,

        open=selected_df["Open"],

        high=selected_df["High"],

        low=selected_df["Low"],

        close=selected_df["Close"],

        name="Price"

    )

)

# --------------------------------------------------
# DRAW ZONE
# --------------------------------------------------

zone_color = (
    "rgba(0,255,0,0.25)"
    if selected_zone["Type"] == "Demand"
    else "rgba(255,0,0,0.25)"
)

fig.add_hrect(

    y0=selected_zone["Distal"],

    y1=selected_zone["Proximal"],

    fillcolor=zone_color,

    line_width=0,

    opacity=0.30

)

# --------------------------------------------------
# PROXIMAL
# --------------------------------------------------

fig.add_hline(

    y=selected_zone["Proximal"],

    line_dash="dot",

    annotation_text="Proximal"

)

# --------------------------------------------------
# DISTAL
# --------------------------------------------------

fig.add_hline(

    y=selected_zone["Distal"],

    line_dash="dot",

    annotation_text="Distal"

)

# --------------------------------------------------
# TARGET
# --------------------------------------------------

fig.add_hline(

    y=selected_zone["Target (1:2)"],

    line_color="blue",

    annotation_text="Target"

)

fig.update_layout(

    height=750,

    xaxis_rangeslider_visible=False,

    template="plotly_dark",

    title=f"{selected_symbol} ({timeframe})"

)

st.plotly_chart(

    fig,

    use_container_width=True

)

# =====================================================
# METRICS
# =====================================================

col1, col2, col3, col4 = st.columns(4)

col1.metric(
    "Profile",
    selected_zone["Profile"]
)

col2.metric(
    "Strength",
    selected_zone["Strength"]
)

col3.metric(
    "Status",
    selected_zone["Status"]
)

col4.metric(
    "Pattern",
    selected_zone["Pattern"]
)

# =====================================================
# ZONE DETAILS
# =====================================================

with st.expander("Zone Details", expanded=False):

    st.write(selected_zone)

# =====================================================
# FOOTER
# =====================================================

st.caption(
    "Institutional Supply & Demand Scanner"
)
