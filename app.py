import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go

# ─────────────────────────────────────────────────────────────────────────────
# PAGE CONFIG
# ─────────────────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="India MPI Dashboard",
    page_icon="🇮🇳",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─────────────────────────────────────────────────────────────────────────────
# CSS
# ─────────────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
    .banner {
        background: linear-gradient(120deg, #0d47a1, #1976d2, #42a5f5);
        padding: 2.2rem 2rem;
        border-radius: 14px;
        color: white;
        text-align: center;
        margin-bottom: 1.8rem;
    }
    .banner h1 { font-size: 1.9rem; margin: 0 0 0.4rem; font-weight: 700; }
    .banner p  { font-size: 0.95rem; opacity: 0.88; margin: 0; }
    .sec-head {
        font-size: 1rem;
        font-weight: 700;
        color: #0d47a1;
        border-left: 4px solid #1976d2;
        padding-left: 0.6rem;
        margin: 1.4rem 0 0.6rem;
    }
    .info-card {
        background: #e8f4fd;
        border-left: 4px solid #1976d2;
        border-radius: 0 8px 8px 0;
        padding: 0.8rem 1rem;
        font-size: 0.88rem;
        color: #0d47a1;
        margin-top: 1rem;
    }
    [data-testid="stMetric"] {
        background: #f0f6ff;
        border: 1px solid #c9dcf5;
        border-radius: 10px;
        padding: 0.7rem 1rem !important;
    }
    section[data-testid="stSidebar"] { background: #eef3fc; }
</style>
""", unsafe_allow_html=True)


# ─────────────────────────────────────────────────────────────────────────────
# DATA
# ─────────────────────────────────────────────────────────────────────────────
@st.cache_data
def load_data():
    mpi = pd.read_excel("mpi_project_data_sources.xlsx", sheet_name="NITI_MPI_States")
    hdi = pd.read_excel("mpi_project_data_sources.xlsx", sheet_name="GDL_SHDI_States")

    hdi_clean = hdi[hdi["state_ut"] != "Total"].copy().reset_index(drop=True)
    hdi_long = hdi_clean.melt(
        id_vars=["state_ut"],
        value_vars=["2019", "2020", "2021", "2022", "2023"],
        var_name="year",
        value_name="hdi_value",
    )
    hdi_long["year"]      = hdi_long["year"].astype(int)
    hdi_long["hdi_value"] = pd.to_numeric(hdi_long["hdi_value"], errors="coerce")

    def cat(v):
        if v >= 30:   return "High Poverty"
        elif v >= 15: return "Moderate Poverty"
        elif v >= 5:  return "Low Poverty"
        else:         return "Very Low Poverty"

    mpi["category"]         = mpi["headcount_2019_21_pct"].apply(cat)
    mpi["improvement_abs"]  = mpi["change_pct_points"].abs()
    mpi["improvement_rate"] = (
        (mpi["headcount_2015_16_pct"] - mpi["headcount_2019_21_pct"])
        / mpi["headcount_2015_16_pct"] * 100
    ).round(1)

    return mpi, hdi_clean, hdi_long


mpi_df, hdi_df, hdi_long = load_data()

# ─────────────────────────────────────────────────────────────────────────────
# SIDEBAR
# ─────────────────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## 🇮🇳 MPI Dashboard")
    st.markdown("---")
    page = st.radio(
        "Navigate",
        ["📊 Overview", "🗺️ State Explorer", "📈 HDI Trends", "🔬 MPI Predictor", "📋 Data Table"],
    )
    st.markdown("---")
    st.markdown("**Filters** *(Overview)*")
    all_cats  = sorted(mpi_df["category"].unique())
    sel_cats  = st.multiselect("Poverty Category", all_cats, default=all_cats)
    lo        = float(mpi_df["headcount_2019_21_pct"].min())
    hi        = float(mpi_df["headcount_2019_21_pct"].max())
    pov_range = st.slider("Poverty Rate Range (%)", lo, hi, (lo, hi), 0.1)
    st.markdown("---")
    st.caption("Sources: NITI Aayog MPI 2023\nGlobal Data Lab SHDI")

filtered = mpi_df[
    mpi_df["category"].isin(sel_cats) &
    mpi_df["headcount_2019_21_pct"].between(*pov_range)
].copy()

# ─────────────────────────────────────────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────────────────────────────────────────
COLORS = {
    "High Poverty":     "#e53935",
    "Moderate Poverty": "#fb8c00",
    "Low Poverty":      "#43a047",
    "Very Low Poverty": "#1e88e5",
}

def banner(title, subtitle=""):
    st.markdown(
        f'<div class="banner"><h1>{title}</h1>'
        + (f"<p>{subtitle}</p>" if subtitle else "")
        + "</div>",
        unsafe_allow_html=True,
    )

def sec(label):
    st.markdown(f'<div class="sec-head">{label}</div>', unsafe_allow_html=True)

def card(text):
    st.markdown(f'<div class="info-card">{text}</div>', unsafe_allow_html=True)


# ═════════════════════════════════════════════════════════════════════════════
# PAGE 1 — OVERVIEW
# ═════════════════════════════════════════════════════════════════════════════
if page == "📊 Overview":
    banner("🇮🇳 India MPI Dashboard",
           "NITI Aayog MPI 2023 · Applied Business Analytics Final Project")

    avg_now  = mpi_df["headcount_2019_21_pct"].mean()
    avg_then = mpi_df["headcount_2015_16_pct"].mean()
    best_row = mpi_df.loc[mpi_df["improvement_abs"].idxmax()]
    high_n   = int((mpi_df["headcount_2019_21_pct"] >= 30).sum())

    k1, k2, k3, k4 = st.columns(4)
    k1.metric("States / UTs", len(mpi_df))
    k2.metric("Avg Headcount 2019-21", f"{avg_now:.1f}%", f"{avg_now - avg_then:+.1f}%")
    k3.metric("Most Improved", best_row["state_ut"], f"{best_row['change_pct_points']:.1f} pp")
    k4.metric("High Poverty States (≥30%)", high_n)

    st.markdown("---")
    c1, c2 = st.columns(2)

    with c1:
        sec("Top 10 States by MPI Headcount 2019-21")
        top10 = filtered.nlargest(10, "headcount_2019_21_pct")
        fig = px.bar(
            top10, x="headcount_2019_21_pct", y="state_ut",
            orientation="h", color="category",
            color_discrete_map=COLORS, text="headcount_2019_21_pct",
            labels={"headcount_2019_21_pct": "Headcount (%)", "state_ut": "", "category": "Category"},
        )
        fig.update_traces(texttemplate="%{text:.1f}%", textposition="outside")
        fig.update_layout(
            height=400, plot_bgcolor="white",
            yaxis=dict(autorange="reversed"),
            legend=dict(orientation="h", y=-0.18, x=0),
            margin=dict(l=5, r=45, t=10, b=10),
        )
        st.plotly_chart(fig, use_container_width=True)

    with c2:
        sec("Before vs After: Top 10 Most Improved States")
        top_imp = filtered.nlargest(10, "improvement_abs")
        fig2 = go.Figure()
        fig2.add_trace(go.Bar(
            name="2015-16", x=top_imp["state_ut"],
            y=top_imp["headcount_2015_16_pct"], marker_color="#ef9a9a",
        ))
        fig2.add_trace(go.Bar(
            name="2019-21", x=top_imp["state_ut"],
            y=top_imp["headcount_2019_21_pct"], marker_color="#42a5f5",
        ))
        fig2.update_layout(
            barmode="group", height=400, plot_bgcolor="white",
            xaxis_tickangle=-35,
            legend=dict(orientation="h", y=1.08),
            margin=dict(l=5, r=5, t=10, b=10),
        )
        st.plotly_chart(fig2, use_container_width=True)

    c3, c4 = st.columns(2)

    with c3:
        sec("Category Distribution (2021)")
        counts = filtered["category"].value_counts()
        fig3 = px.pie(
            values=counts.values, names=counts.index,
            color=counts.index, color_discrete_map=COLORS, hole=0.45,
        )
        fig3.update_layout(height=340, margin=dict(l=5, r=5, t=10, b=10))
        st.plotly_chart(fig3, use_container_width=True)

    with c4:
        sec("Improvement Rate vs Current Poverty Level")
        fig4 = px.scatter(
            filtered, x="headcount_2019_21_pct", y="improvement_rate",
            size="improvement_abs", color="category",
            color_discrete_map=COLORS, hover_name="state_ut",
            labels={
                "headcount_2019_21_pct": "Current Poverty (%)",
                "improvement_rate": "Improvement Rate (%)",
                "category": "Category",
            },
        )
        fig4.update_layout(height=340, plot_bgcolor="white", margin=dict(l=5, r=5, t=10, b=10))
        st.plotly_chart(fig4, use_container_width=True)

    card("💡 <b>Key Insight:</b> Bihar leads in absolute reduction (−18.13 pp), while Uttar Pradesh "
         "and Madhya Pradesh show the fastest proportional improvement — high-poverty states can "
         "achieve rapid gains with targeted multi-sector interventions.")


# ═════════════════════════════════════════════════════════════════════════════
# PAGE 2 — STATE EXPLORER
# ═════════════════════════════════════════════════════════════════════════════
elif page == "🗺️ State Explorer":
    banner("🗺️ State Explorer", "Drill into any State or Union Territory")

    states = sorted(mpi_df["state_ut"].tolist())
    sel    = st.selectbox("Select a State / UT", states)
    row    = mpi_df[mpi_df["state_ut"] == sel].iloc[0]

    m1, m2, m3, m4 = st.columns(4)
    m1.metric("MPI Headcount 2019-21", f"{row['headcount_2019_21_pct']:.2f}%")
    m2.metric("MPI Headcount 2015-16", f"{row['headcount_2015_16_pct']:.2f}%")
    m3.metric("Change", f"{row['change_pct_points']:.2f} pp")
    m4.metric("Category", row["category"])

    fig_g = go.Figure(go.Indicator(
        mode="gauge+number+delta",
        value=float(row["headcount_2019_21_pct"]),
        delta={"reference": float(row["headcount_2015_16_pct"]), "valueformat": ".1f"},
        title={"text": f"MPI Headcount — {sel}"},
        gauge={
            "axis": {"range": [0, 60]},
            "bar":  {"color": "#1565c0"},
            "steps": [
                {"range": [0,  5],  "color": "#c8e6c9"},
                {"range": [5,  15], "color": "#fff9c4"},
                {"range": [15, 30], "color": "#ffe0b2"},
                {"range": [30, 60], "color": "#ffcdd2"},
            ],
            "threshold": {
                "line": {"color": "red", "width": 3},
                "value": float(row["headcount_2015_16_pct"]),
            },
        },
    ))
    fig_g.update_layout(height=350, margin=dict(l=30, r=30, t=60, b=20))
    st.plotly_chart(fig_g, use_container_width=True)

    ranked = mpi_df.sort_values("headcount_2019_21_pct", ascending=False).reset_index(drop=True)
    rank   = int(ranked[ranked["state_ut"] == sel].index[0]) + 1
    st.info(f"📌 **{sel}** ranks **#{rank}** out of {len(mpi_df)} States/UTs (1 = highest poverty)")

    sec("National Comparison (2019-21)")
    fig_cmp = px.bar(
        ranked, x="state_ut", y="headcount_2019_21_pct",
        color=ranked["state_ut"].apply(lambda x: "Selected" if x == sel else "Other"),
        color_discrete_map={"Selected": "#e53935", "Other": "#90caf9"},
        labels={"headcount_2019_21_pct": "MPI Headcount (%)", "state_ut": ""},
    )
    fig_cmp.update_layout(
        height=380, showlegend=False, xaxis_tickangle=-45,
        plot_bgcolor="white", margin=dict(l=5, r=5, t=10, b=10),
    )
    st.plotly_chart(fig_cmp, use_container_width=True)

    hdi_row = hdi_df[hdi_df["state_ut"].str.strip().str.lower() == sel.strip().lower()]
    if not hdi_row.empty:
        sec(f"HDI Trend for {sel} (2019–2023)")
        years = [2019, 2020, 2021, 2022, 2023]
        vals  = [float(hdi_row.iloc[0][str(y)]) for y in years]
        fig_h = px.line(x=years, y=vals, markers=True,
                        labels={"x": "Year", "y": "HDI Value"})
        fig_h.update_traces(line_color="#1565c0", line_width=2.5, marker_size=9)
        fig_h.update_layout(plot_bgcolor="white", height=300,
                            margin=dict(l=5, r=5, t=10, b=10))
        st.plotly_chart(fig_h, use_container_width=True)
    else:
        st.info(f"HDI data not available for {sel}.")


# ═════════════════════════════════════════════════════════════════════════════
# PAGE 3 — HDI TRENDS
# ═════════════════════════════════════════════════════════════════════════════
elif page == "📈 HDI Trends":
    banner("📈 HDI Trends", "Subnational Human Development Index 2019–2023")

    all_hdi = sorted(hdi_long["state_ut"].unique())
    defaults = [s for s in ["Bihar", "Kerala", "Uttar Pradesh", "Tamil Nadu"] if s in all_hdi]

    c1, c2 = st.columns(2)
    with c1:
        sel_states = st.multiselect("Select States", all_hdi, default=defaults)
    with c2:
        yr = st.select_slider("Year Range", options=[2019, 2020, 2021, 2022, 2023],
                              value=(2019, 2023))

    if sel_states:
        fh = hdi_long[hdi_long["state_ut"].isin(sel_states) & hdi_long["year"].between(*yr)]
        fig_t = px.line(fh, x="year", y="hdi_value", color="state_ut", markers=True,
                        labels={"hdi_value": "HDI Value", "year": "Year", "state_ut": "State"},
                        title="Subnational HDI Comparison")
        fig_t.update_traces(line_width=2.5, marker_size=8)
        fig_t.update_layout(height=440, plot_bgcolor="white",
                            margin=dict(l=5, r=5, t=40, b=10))
        st.plotly_chart(fig_t, use_container_width=True)
    else:
        st.warning("Please select at least one state.")

    sec("HDI vs MPI Relationship (2021)")
    hdi_2021 = hdi_long[hdi_long["year"] == 2021][["state_ut", "hdi_value"]].copy()
    merged   = pd.merge(mpi_df, hdi_2021, on="state_ut").dropna(
        subset=["hdi_value", "headcount_2019_21_pct"])

    if not merged.empty:
        x_arr  = merged["hdi_value"].values.astype(float)
        y_arr  = merged["headcount_2019_21_pct"].values.astype(float)
        m_fit, b_fit = np.polyfit(x_arr, y_arr, 1)
        x_line = np.linspace(x_arr.min(), x_arr.max(), 100)
        y_line = m_fit * x_line + b_fit

        fig_s = px.scatter(
            merged, x="hdi_value", y="headcount_2019_21_pct",
            color="category", color_discrete_map=COLORS, hover_name="state_ut",
            labels={"hdi_value": "HDI (2021)",
                    "headcount_2019_21_pct": "MPI Headcount % (2019-21)",
                    "category": "Category"},
            title="Higher HDI correlates with Lower Poverty",
        )
        fig_s.add_scatter(x=x_line, y=y_line, mode="lines",
                          line=dict(color="#1565c0", width=2, dash="dash"),
                          name="Trend (OLS)")
        fig_s.update_layout(height=440, plot_bgcolor="white",
                            margin=dict(l=5, r=5, t=40, b=10))
        st.plotly_chart(fig_s, use_container_width=True)

        corr = float(np.corrcoef(x_arr, y_arr)[0, 1])
        card(f"📊 <b>Pearson Correlation (HDI vs MPI):</b> {corr:.3f} — Strong negative "
             "relationship: higher human development consistently accompanies lower "
             "multidimensional poverty.")
    else:
        st.info("No overlapping states found between MPI and HDI datasets for 2021.")


# ═════════════════════════════════════════════════════════════════════════════
# PAGE 4 — MPI PREDICTOR
# ═════════════════════════════════════════════════════════════════════════════
elif page == "🔬 MPI Predictor":
    banner("🔬 MPI Score Estimator",
           "Estimate a custom MPI score using the OPHI methodology")

    st.markdown("### 📐 Formula")
    st.latex(r"MPI = H \times A")
    st.markdown("> **H** = Headcount ratio &nbsp;|&nbsp; **A** = Average intensity of deprivation")
    st.markdown("---")

    c1, c2, c3 = st.columns(3)

    with c1:
        st.markdown("**🏫 Education (1/3)**")
        school_yrs = st.slider("Years of Schooling (%)",  0, 100, 40)
        school_att = st.slider("School Attendance (%)",   0, 100, 30)

    with c2:
        st.markdown("**🏥 Health (1/3)**")
        nutrition  = st.slider("Nutrition (%)",           0, 100, 35)
        child_mort = st.slider("Child Mortality (%)",     0, 100, 20)

    with c3:
        st.markdown("**🏠 Living Standards (1/3)**")
        cooking     = st.slider("Cooking Fuel (%)",   0, 100, 50)
        sanitation  = st.slider("Sanitation (%)",     0, 100, 45)
        water       = st.slider("Drinking Water (%)", 0, 100, 25)
        electricity = st.slider("Electricity (%)",    0, 100, 20)
        housing     = st.slider("Housing (%)",        0, 100, 30)
        assets      = st.slider("Assets (%)",         0, 100, 35)

    k = st.slider("Poverty Threshold (k)", 0.10, 1.00, 0.33, 0.01)

    W = {"school_yrs": 1/6, "school_att": 1/6, "nutrition": 1/6, "child_mort": 1/6,
         "cooking": 1/18, "sanitation": 1/18, "water": 1/18,
         "electricity": 1/18, "housing": 1/18, "assets": 1/18}
    V = {"school_yrs": school_yrs/100, "school_att": school_att/100,
         "nutrition": nutrition/100, "child_mort": child_mort/100,
         "cooking": cooking/100, "sanitation": sanitation/100,
         "water": water/100, "electricity": electricity/100,
         "housing": housing/100, "assets": assets/100}

    c_score = sum(W[d] * V[d] for d in W)
    H_val   = min(1.0, c_score / k) if k > 0 else 0.0
    A_val   = c_score
    MPI_val = round(H_val * A_val, 4)

    st.markdown("---")
    r1, r2, r3 = st.columns(3)
    r1.metric("Weighted Deprivation Score", f"{c_score:.3f}")
    r2.metric("Headcount Ratio (H)", f"{H_val:.3f}")
    r3.metric("🎯 Estimated MPI", f"{MPI_val:.4f}")

    if   MPI_val < 0.01: st.success("✅ Very Low Poverty — strong performance across all dimensions.")
    elif MPI_val < 0.05: st.info("🟡 Low Poverty — some gaps; targeted interventions advised.")
    elif MPI_val < 0.15: st.warning("🟠 Moderate Poverty — significant multi-dimensional gaps.")
    else:                st.error("🔴 High Poverty — urgent multi-sector intervention required.")

    sec("Dimensional Contribution Chart")
    dim_w = [W[d] * V[d] for d in W]
    fig_d = px.bar(x=list(W.keys()), y=dim_w, color=dim_w,
                   color_continuous_scale="OrRd",
                   labels={"x": "Dimension", "y": "Weighted Deprivation", "color": "Score"})
    fig_d.update_layout(plot_bgcolor="white", height=370, coloraxis_showscale=False,
                        xaxis_tickangle=-30, margin=dict(l=5, r=5, t=10, b=60))
    st.plotly_chart(fig_d, use_container_width=True)


# ═════════════════════════════════════════════════════════════════════════════
# PAGE 5 — DATA TABLE
# ═════════════════════════════════════════════════════════════════════════════
elif page == "📋 Data Table":
    banner("📋 Data Table", "Browse and download the underlying datasets")

    tab1, tab2 = st.tabs(["📌 NITI Aayog MPI Data", "📌 GDL Subnational HDI Data"])

    with tab1:
        st.markdown(f"**{len(filtered)} records** shown after sidebar filters")
        cols = ["state_ut", "headcount_2019_21_pct", "headcount_2015_16_pct",
                "change_pct_points", "improvement_rate", "category"]
        st.dataframe(filtered[cols].reset_index(drop=True),
                     use_container_width=True, height=480)
        st.download_button("⬇️ Download MPI Data (CSV)",
                           filtered[cols].to_csv(index=False).encode(),
                           "mpi_data.csv", "text/csv")

    with tab2:
        st.markdown(f"**{len(hdi_long)} records** (all states · all years)")
        st.dataframe(hdi_long.reset_index(drop=True),
                     use_container_width=True, height=480)
        st.download_button("⬇️ Download HDI Data (CSV)",
                           hdi_long.to_csv(index=False).encode(),
                           "hdi_data.csv", "text/csv")


# ─────────────────────────────────────────────────────────────────────────────
# FOOTER
# ─────────────────────────────────────────────────────────────────────────────
st.markdown("---")
st.markdown(
    "<p style='text-align:center;color:#999;font-size:0.78rem;'>"
    "Sources: NITI Aayog National MPI 2023 · Global Data Lab SHDI India · "
    "Federal Bank TSM Centre of Excellence &nbsp;|&nbsp; ABA Final Project</p>",
    unsafe_allow_html=True,
)
