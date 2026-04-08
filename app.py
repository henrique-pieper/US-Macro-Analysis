import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import numpy as np
from scipy import stats

st.set_page_config(
    page_title="US Macroeconomic Analysis",
    layout="wide"
)

@st.cache_data
def load_data():
    macro = pd.read_csv("data/processed/macro_data_processed.csv", index_col="date", parse_dates=True)
    cycles = pd.read_csv("data/processed/business_cycles.csv", index_col="date", parse_dates=True)
    phillips = pd.read_csv("data/processed/phillips_curve.csv", index_col="date", parse_dates=True)
    misery = pd.read_csv("data/processed/misery_index.csv", index_col="date", parse_dates=True)
    return macro, cycles, phillips, misery

macro, cycles, phillips, misery = load_data()

# helper para pares de recessão
def get_recession_pairs(df):
    rec = df["recession"].dropna()
    starts = rec[(rec == 1) & (rec.shift(1) == 0)].index.tolist()
    ends = rec[(rec == 0) & (rec.shift(1) == 1)].index.tolist()
    if rec.iloc[0] == 1:
        starts = [rec.index[0]] + starts
    return list(zip(starts, ends[:len(starts)]))

pairs = get_recession_pairs(macro)

# sidebar
st.sidebar.title("Navigation")
section = st.sidebar.radio("Go to", [
    "Overview",
    "Business Cycles",
    "Phillips Curve",
    "Misery Index"
])

st.title("US Macroeconomic Analysis")
st.markdown("Analysis of key US macroeconomic indicators from 1970 to the present using FRED data.")

# ── OVERVIEW ──
if section == "Overview":
    st.header("Macroeconomic Indicators")

    series = {
        "Real GDP (Billions USD)": macro["gdp_real"],
        "Unemployment Rate (%)": macro["unemployment"],
        "CPI (Index)": macro["cpi"],
        "Federal Funds Rate (%)": macro["fed_funds_rate"],
    }

    fig = make_subplots(rows=4, cols=1, subplot_titles=list(series.keys()), vertical_spacing=0.08)

    for i, (title, data) in enumerate(series.items(), start=1):
        fig.add_trace(go.Scatter(x=data.dropna().index, y=data.dropna().values,
                                  mode="lines", line=dict(color="#e05c5c", width=1.5), showlegend=False), row=i, col=1)

    for start, end in pairs:
        for row in range(1, 5):
            fig.add_vrect(x0=start, x1=end, fillcolor="gray", opacity=0.2, layer="below", line_width=0, row=row, col=1)

    fig.update_layout(height=900, paper_bgcolor="#111111", plot_bgcolor="#111111",
                      font=dict(color="white"), title_text="US Macroeconomic Indicators (1970–present) — Shaded: NBER Recessions", title_font_size=14)
    fig.update_xaxes(gridcolor="#333333")
    fig.update_yaxes(gridcolor="#333333")
    st.plotly_chart(fig, use_container_width=True)

# ── BUSINESS CYCLES ──
elif section == "Business Cycles":
    st.header("Business Cycles — HP Filter")

    fig = make_subplots(rows=2, cols=1, subplot_titles=("Real GDP vs Trend", "Business Cycle Component"), vertical_spacing=0.12)

    fig.add_trace(go.Scatter(x=cycles.index, y=cycles["gdp_real"], mode="lines", name="Real GDP",
                              line=dict(color="#e05c5c", width=1.5)), row=1, col=1)
    fig.add_trace(go.Scatter(x=cycles.index, y=cycles["trend"], mode="lines", name="Trend",
                              line=dict(color="white", width=1.5, dash="dash")), row=1, col=1)
    fig.add_trace(go.Scatter(x=cycles.index, y=cycles["cycle"], mode="lines", name="Cycle",
                              line=dict(color="#e05c5c", width=1.5), fill="tozeroy",
                              fillcolor="rgba(224, 92, 92, 0.2)"), row=2, col=1)
    fig.add_hline(y=0, line_dash="dash", line_color="white", opacity=0.5, row=2, col=1)

    for start, end in pairs:
        for row in range(1, 3):
            fig.add_vrect(x0=start, x1=end, fillcolor="gray", opacity=0.2, layer="below", line_width=0, row=row, col=1)

    fig.update_layout(height=700, paper_bgcolor="#111111", plot_bgcolor="#111111",
                      font=dict(color="white"), legend=dict(orientation="h", y=1.05))
    fig.update_xaxes(gridcolor="#333333")
    fig.update_yaxes(gridcolor="#333333")
    st.plotly_chart(fig, use_container_width=True)

# ── PHILLIPS CURVE ──
elif section == "Phillips Curve":
    st.header("Phillips Curve by Decade")

    phillips["inflation"] = phillips["cpi"].pct_change(12) * 100 if "cpi" in phillips.columns else phillips["inflation"]

    colors = {"1970s": "#e05c5c", "1980s": "#e08c5c", "1990s": "#e0d95c", "2000s": "#5ce07a", "2010s+": "#5cb8e0"}

    fig = go.Figure()

    for period, group in phillips.groupby("period", observed=True):
        x_vals = group["unemployment"].dropna().values
        y_vals = group["inflation"].dropna().values
        if len(x_vals) < 2:
            continue
        slope, intercept, _, _, _ = stats.linregress(x_vals, y_vals)
        x_line = np.linspace(x_vals.min(), x_vals.max(), 100)
        y_line = slope * x_line + intercept

        fig.add_trace(go.Scatter(x=x_vals, y=y_vals, mode="markers", name=str(period),
                                  marker=dict(color=colors.get(str(period), "white"), size=4, opacity=0.5),
                                  legendgroup=str(period)))
        fig.add_trace(go.Scatter(x=x_line, y=y_line, mode="lines", name=f"{period} trend",
                                  line=dict(color=colors.get(str(period), "white"), width=2),
                                  legendgroup=str(period), showlegend=False))

    fig.update_layout(height=600, title_text="Phillips Curve — US (1970–present) by Decade",
                      xaxis_title="Unemployment Rate (%)", yaxis_title="Inflation Rate (% YoY)",
                      paper_bgcolor="#111111", plot_bgcolor="#111111", font=dict(color="white"),
                      legend=dict(orientation="h", y=1.08))
    fig.update_xaxes(gridcolor="#333333")
    fig.update_yaxes(gridcolor="#333333")
    st.plotly_chart(fig, use_container_width=True)

# ── MISERY INDEX ──
elif section == "Misery Index":
    st.header("Misery Index")

    rec = misery["recession"]
    starts = rec[(rec == 1) & (rec.shift(1) == 0)].index.tolist()
    ends = rec[(rec == 0) & (rec.shift(1) == 1)].index.tolist()
    if rec.iloc[0] == 1:
        starts = [rec.index[0]] + starts
    misery_pairs = list(zip(starts, ends[:len(starts)]))

    fig = go.Figure()

    fig.add_trace(go.Scatter(x=misery.index, y=misery["unemployment"], mode="lines", name="Unemployment",
                              line=dict(color="#5cb8e0", width=1.2), stackgroup="one", fillcolor="rgba(92, 184, 224, 0.4)"))
    fig.add_trace(go.Scatter(x=misery.index, y=misery["inflation"], mode="lines", name="Inflation",
                              line=dict(color="#e05c5c", width=1.2), stackgroup="one", fillcolor="rgba(224, 92, 92, 0.4)"))
    fig.add_trace(go.Scatter(x=misery.index, y=misery["misery_index"], mode="lines", name="Misery Index",
                              line=dict(color="white", width=2)))
    fig.add_hline(y=misery["misery_index"].mean(), line_dash="dash", line_color="yellow", opacity=0.6,
                  annotation_text=f"Historical avg: {misery['misery_index'].mean():.1f}",
                  annotation_position="top left", annotation_font_color="yellow")

    for start, end in misery_pairs:
        fig.add_vrect(x0=start, x1=end, fillcolor="gray", opacity=0.2, layer="below", line_width=0)

    fig.update_layout(height=500, title_text="US Misery Index (1970–present)",
                      xaxis_title="Date", yaxis_title="Misery Index",
                      paper_bgcolor="#111111", plot_bgcolor="#111111", font=dict(color="white"),
                      legend=dict(orientation="h", y=1.08))
    fig.update_xaxes(gridcolor="#333333")
    fig.update_yaxes(gridcolor="#333333")
    st.plotly_chart(fig, use_container_width=True)