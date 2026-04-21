import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go

# ── Page config ────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="India MPI Dashboard",
    page_icon="🇮🇳",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Custom CSS ─────────────────────────────────────────────────────────────────
st.markdown("""
<style>
    .main-header {
        background: linear-gradient(135deg, #1a237e 0%, #1565c0 100%);
        padding: 2.5rem 2rem;
        border-radius: 16px;
        margin-bottom: 2rem;
        color: white;
        text-align: center;
    }
    .main-header h1 { font-size: 2rem; margin: 0 0 0.5rem; }
    .main-header p  { font-size: 1rem; opacity: 0.85; margin: 0; }
    .section-title {
        font-size: 1.1rem;
        font-weight: 700;
        color: #1a237e;
        margin: 1.2rem 0 0.6rem;
        padding-bottom: 4px;
        border-bottom: 2px solid #e3f2fd;
    }
    .insight-box {
        background: #e3f2fd;
        border-left: 4px solid #1565c0;
        border-radius: 0 8px 8px 0;
        padding: 0.9rem 1rem;
        margin: 0.8rem 0;
        font-size: 0.9rem;
        color: #0d47a1;
    }
    [data-testid="stMetric"] {
        background: #f8faff;
        border: 1px solid #e3eaf5;
        border-radius: 10px;
        padding: 0.8rem 1rem;
    }
    [data-testid="stSidebar"] { background: #f0f4ff; }
</style>
""", unsafe_allow_html=True)


# ── Data Loading ───────────────────────────────────────────────────────────────
@st.cache_data
def load_data():
    mpi = pd.read_excel("mpi_project_data_sources.xlsx", sheet_name="NITI_MPI_States")
    hdi = pd.read_excel("mpi_project_data_sources.xlsx", sheet_name="GDL_SHDI_States")

    hdi_clean = hdi[hdi["state_ut"] != "Total"].copy()
    hdi_long = hdi_clean.melt(
        id_vars=["state_ut", "source", "source_url"],
        value_vars=["2019", "2020", "2021", "2022", "2023"],
        var_name="year",
        value_name="hdi_value"
    )
    hdi_long["year"] = hdi_long["year"].astype(int)

    def categorize(val):
        if val >= 30:   return "High Poverty"
        elif val >= 15: return "Moderate Poverty"
        elif val >= 5:  return "Low Poverty"
        else:           return "Very Low Poverty"

    mpi["poverty_category_2021"] = mpi["headcount_2019_21_pct"].apply(categorize)
    mpi["poverty_category_2016"] = mpi["headcount_2015_16_pct"].apply(categorize)
    mpi["improvement"]           = mpi["change_pct_points"].abs()
    mpi["improvement_rate"]      = (
        (mpi["headcount_2015_16_pct"] - mpi["headcount_2019_21_pct"])
        / mpi["headcount_2015_16_pct"] * 100
    ).round(1)

    return mpi, hdi_clean, hdi_long


mpi_df, hdi_df, hdi_long = load_data()

# ── Sidebar ────────────────────────────────────────────────────────────────────
with st.sidebar:
    st.image(
        "https://upload.wikimedia.org/wikipedia/en/thumb/4/41/Flag_of_India.svg/320px-Flag_of_India.svg.png",
        width=100,
    )
    st.markdown("## 🗺️ Navigation")
    page = st.radio(
        "Go to",
        ["📊 Overview", "🗺️ State Explorer", "📈 HDI Trends", "🔬 MPI Predictor", "📋 Data Table"],
        label_visibility="collapsed",
    )
    st.markdown("---")
    st.markdown("### Filters")
    categories = sorted(mpi_df["poverty_category_2021"].unique().tolist())
    selected_cats = st.multiselect("Poverty Categories", categories, default=categories)
    min_pov = float(mpi_df["headcount_2019_21_pct"].min())
    max_pov = float(mpi_df["headcount_2019_21_pct"].max())
    pov_range = st.slider("Poverty Rate Range (2019-21) %", min_pov, max_pov, (min_pov, max_pov), 0.1)
    st.markdown("---")
    st.caption("Data: NITI Aayog MPI 2023 & Global Data Lab SHDI\nBuilt for ABA Final Project")

filtered_mpi = mpi_df[
    (mpi_df["poverty_category_2021"].isin(selected_cats)) &
    (mpi_df["headcount_2019_21_pct"].between(*pov_range))
].copy()


# ══════════════════════════════════════════════════════════════════════════════
# PAGE 1 – OVERVIEW
# ══════════════════════════════════════════════════════════════════════════════
if page == "📊 Overview":
    st.markdown("""
    <div class="main-header">
        <h1>🇮🇳 India Multidimensional Poverty Index Dashboard</h1>
        <p>NITI Aayog MPI 2023 · Applied Business Analytics Final Project</p>
    </div>
    """, unsafe_allow_html=True)

    c1, c2, c3, c4 = st.columns(4)
    avg_now  = mpi_df["headcount_2019_21_pct"].mean()
    avg_then = mpi_df["headcount_2015_16_pct"].mean()
    best_idx = mpi_df["change_pct_points"].idxmin()
    best     = mpi_df.loc[best_idx, "state_ut"]
    best_val = mpi_df.loc[best_idx, "change_pct_points"]
    high_pov = int((mpi_df["headcount_2019_21_pct"] >= 30).sum())

    c1.metric("States / UTs Covered", len(mpi_df))
    c2.metric("Avg MPI Headcount 2019-21", f"{avg_now:.1f}%", delta=f"{avg_now - avg_then:.1f}%")
    c3.metric("Best Improvement", best, delta=f"{best_val:.1f} pp")
    c4.metric("High Poverty States (≥30%)", high_pov)

    st.markdown("---")
    col_a, col_b = st.columns(2)

    with col_a:
        st.markdown('<div class="section-title">Top 10 States – MPI Headcount 2019-21</div>', unsafe_allow_html=True)
        top10 = filtered_mpi.nlargest(10, "headcount_2019_21_pct")
        fig = px.bar(
            top10, x="headcount_2019_21_pct", y="state_ut",
            orientation="h", color="headcount_2019_21_pct",
            color_continuous_scale="Reds",
            labels={"headcount_2019_21_pct": "MPI Headcount (%)", "state_ut": ""},
            text="headcount_2019_21_pct",
        )
        fig.update_traces(texttemplate="%{text:.1f}%", textposition="outside")
        fig.update_layout(
            height=400, showlegend=False, coloraxis_showscale=False,
            plot_bgcolor="white", yaxis=dict(autorange="reversed"),
            margin=dict(l=10, r=30, t=10, b=10),
        )
        st.plotly_chart(fig, use_container_width=True)

    with col_b:
        st.markdown('<div class="section-title">Poverty Reduction Progress (2016 → 2021)</div>', unsafe_allow_html=True)
        top_improved = filtered_mpi.nlargest(10, "improvement")
        fig2 = go.Figure()
        fig2.add_trace(go.Bar(
            name="2015-16", x=top_improved["state_ut"],
            y=top_improved["headcount_2015_16_pct"], marker_color="#ef5350",
        ))
        fig2.add_trace(go.Bar(
            name="2019-21", x=top_improved["state_ut"],
            y=top_improved["headcount_2019_21_pct"], marker_color="#42a5f5",
        ))
        fig2.update_layout(
            barmode="group", height=400, plot_bgcolor="white",
            xaxis_tickangle=-30, legend=dict(orientation="h", y=1.1),
            margin=dict(l=10, r=10, t=10, b=10),
        )
        st.plotly_chart(fig2, use_container_width=True)

    col_c, col_d = st.columns(2)

    with col_c:
        st.markdown('<div class="section-title">Poverty Category Distribution</div>', unsafe_allow_html=True)
        cat_counts = filtered_mpi["poverty_category_2021"].value_counts()
        fig3 = px.pie(
            values=cat_counts.values, names=cat_counts.index,
            color_discrete_sequence=px.colors.sequential.Blues_r, hole=0.45,
        )
        fig3.update_layout(height=350, margin=dict(l=10, r=10, t=10, b=10))
        st.plotly_chart(fig3, use_container_width=True)

    with col_d:
        st.markdown('<div class="section-title">Improvement Rate vs Current Poverty</div>', unsafe_allow_html=True)
        fig4 = px.scatter(
            filtered_mpi, x="headcount_2019_21_pct", y="improvement_rate",
            size="improvement", color="poverty_category_2021",
            hover_name="state_ut",
            labels={
                "headcount_2019_21_pct": "Current Poverty (%)",
                "improvement_rate": "Improvement Rate (%)",
                "poverty_category_2021": "Category",
            },
            color_discrete_sequence=px.colors.qualitative.Set2,
        )
        fig4.update_layout(height=350, plot_bgcolor="white", margin=dict(l=10, r=10, t=10, b=10))
        st.plotly_chart(fig4, use_container_width=True)

    st.markdown(
        '<div class="insight-box">💡 <b>Key Insight:</b> Bihar leads in absolute reduction '
        '(-18.13 pp), while Uttar Pradesh and Madhya Pradesh show fastest proportional improvement '
        '— demonstrating that high-poverty states can achieve rapid gains with targeted interventions.</div>',
        unsafe_allow_html=True,
    )


# ══════════════════════════════════════════════════════════════════════════════
# PAGE 2 – STATE EXPLORER
# ══════════════════════════════════════════════════════════════════════════════
elif page == "🗺️ State Explorer":
    st.markdown("""
    <div class="main-header">
        <h1>🗺️ State-Level MPI Explorer</h1>
        <p>Drill down into any State or Union Territory</p>
    </div>
    """, unsafe_allow_html=True)

    states = sorted(mpi_df["state_ut"].tolist())
    selected_state = st.selectbox("Select a State / UT", states)
    row = mpi_df[mpi_df["state_ut"] == selected_state].iloc[0]

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("MPI Headcount 2019-21", f"{row['headcount_2019_21_pct']:.2f}%")
    c2.metric("MPI Headcount 2015-16", f"{row['headcount_2015_16_pct']:.2f}%")
    c3.metric("Absolute Change", f"{row['change_pct_points']:.2f} pp")
    c4.metric("Category (2021)", row["poverty_category_2021"])

    fig_gauge = go.Figure(go.Indicator(
        mode="gauge+number+delta",
        value=float(row["headcount_2019_21_pct"]),
        delta={"reference": float(row["headcount_2015_16_pct"]), "valueformat": ".1f"},
        title={"text": f"MPI Headcount — {selected_state}"},
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
    fig_gauge.update_layout(height=360, margin=dict(l=30, r=30, t=60, b=20))
    st.plotly_chart(fig_gauge, use_container_width=True)

    mpi_sorted = mpi_df.sort_values("headcount_2019_21_pct", ascending=False).reset_index(drop=True)
    rank = int(mpi_sorted[mpi_sorted["state_ut"] == selected_state].index[0]) + 1
    st.info(f"📌 **{selected_state}** ranks **#{rank}** out of {len(mpi_df)} States/UTs (1 = highest poverty)")

    fig_cmp = px.bar(
        mpi_sorted, x="state_ut", y="headcount_2019_21_pct",
        color=mpi_sorted["state_ut"].apply(lambda x: "Selected" if x == selected_state else "Other"),
        color_discrete_map={"Selected": "#e53935", "Other": "#90caf9"},
        labels={"headcount_2019_21_pct": "MPI Headcount (%)", "state_ut": ""},
        title="All States Comparison (2019-21)",
    )
    fig_cmp.update_layout(
        height=400, showlegend=False, xaxis_tickangle=-45,
        plot_bgcolor="white", margin=dict(l=10, r=10, t=40, b=10),
    )
    st.plotly_chart(fig_cmp, use_container_width=True)

    hdi_row = hdi_df[hdi_df["state_ut"].str.strip().str.lower() == selected_state.strip().lower()]
    if not hdi_row.empty:
        st.markdown("### 📈 Subnational HDI Trend (2019–2023)")
        years = [2019, 2020, 2021, 2022, 2023]
        vals  = [float(hdi_row.iloc[0][str(y)]) for y in years]
        fig_hdi = px.line(
            x=years, y=vals, markers=True,
            labels={"x": "Year", "y": "HDI Value"},
            title=f"HDI Trend — {selected_state}",
        )
        fig_hdi.update_traces(line_color="#1565c0", marker_size=10)
        fig_hdi.update_layout(plot_bgcolor="white", height=320, margin=dict(l=10, r=10, t=40, b=10))
        st.plotly_chart(fig_hdi, use_container_width=True)
    else:
        st.info(f"HDI data not available for {selected_state}.")


# ══════════════════════════════════════════════════════════════════════════════
# PAGE 3 – HDI TRENDS
# ══════════════════════════════════════════════════════════════════════════════
elif page == "📈 HDI Trends":
    st.markdown("""
    <div class="main-header">
        <h1>📈 Subnational HDI Trends (2019–2023)</h1>
        <p>Compare Human Development Index across states over time</p>
    </div>
    """, unsafe_allow_html=True)

    all_states_hdi  = sorted(hdi_long[hdi_long["state_ut"] != "Total"]["state_ut"].unique())
    default_states  = [s for s in ["Bihar", "Kerala", "Uttar Pradesh", "Tamil Nadu"] if s in all_states_hdi]

    col1, col2 = st.columns(2)
    with col1:
        selected_states_hdi = st.multiselect(
            "Select States to Compare", all_states_hdi, default=default_states
        )
    with col2:
        year_range = st.select_slider(
            "Year Range", options=[2019, 2020, 2021, 2022, 2023], value=(2019, 2023)
        )

    if selected_states_hdi:
        filtered_hdi = hdi_long[
            (hdi_long["state_ut"].isin(selected_states_hdi)) &
            (hdi_long["year"].between(*year_range))
        ]
        fig_trend = px.line(
            filtered_hdi, x="year", y="hdi_value", color="state_ut",
            markers=True,
            labels={"hdi_value": "HDI Value", "year": "Year", "state_ut": "State"},
            title="Subnational HDI Comparison",
        )
        fig_trend.update_traces(line_width=2.5, marker_size=8)
        fig_trend.update_layout(height=450, plot_bgcolor="white", margin=dict(l=10, r=10, t=40, b=10))
        st.plotly_chart(fig_trend, use_container_width=True)
    else:
        st.warning("Please select at least one state above.")

    st.markdown("### 🔗 HDI–MPI Relationship (2021)")
    hdi_2021 = hdi_long[hdi_long["year"] == 2021][["state_ut", "hdi_value"]].copy()
    merged   = pd.merge(mpi_df, hdi_2021, on="state_ut")

    if not merged.empty:
        fig_corr = px.scatter(
            merged, x="hdi_value", y="headcount_2019_21_pct",
            hover_name="state_ut", trendline="ols",
            color="poverty_category_2021",
            labels={
                "hdi_value": "HDI (2021)",
                "headcount_2019_21_pct": "MPI Headcount % (2019-21)",
                "poverty_category_2021": "Category",
            },
            title="HDI vs MPI Headcount — Higher HDI → Lower Poverty",
        )
        fig_corr.update_layout(height=450, plot_bgcolor="white", margin=dict(l=10, r=10, t=40, b=10))
        st.plotly_chart(fig_corr, use_container_width=True)
        corr = merged["hdi_value"].corr(merged["headcount_2019_21_pct"])
        st.markdown(
            f'<div class="insight-box">📊 <b>Pearson Correlation (HDI vs MPI):</b> {corr:.3f} — '
            "Strong negative relationship confirms that higher human development consistently "
            "accompanies lower multidimensional poverty.</div>",
            unsafe_allow_html=True,
        )
    else:
        st.info("No overlapping states found between MPI and HDI datasets for 2021.")


# ══════════════════════════════════════════════════════════════════════════════
# PAGE 4 – MPI PREDICTOR
# ══════════════════════════════════════════════════════════════════════════════
elif page == "🔬 MPI Predictor":
    st.markdown("""
    <div class="main-header">
        <h1>🔬 MPI Score Estimator</h1>
        <p>Enter dimension-wise deprivation values to estimate a custom MPI score</p>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("### 📐 OPHI MPI Formula")
    st.latex(r"MPI = H \times A")
    st.markdown("> **H** = Headcount ratio (share of population who are MPI poor) &nbsp;|&nbsp; **A** = Intensity (average deprivation share among poor)")

    st.markdown("---")
    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown("**🏫 Education (weight = 1/3)**")
        school_years  = st.slider("Years of Schooling deprivation (%)",  0, 100, 40)
        school_attend = st.slider("School Attendance deprivation (%)",   0, 100, 30)

    with col2:
        st.markdown("**🏥 Health (weight = 1/3)**")
        nutrition  = st.slider("Nutrition deprivation (%)",       0, 100, 35)
        child_mort = st.slider("Child Mortality deprivation (%)", 0, 100, 20)

    with col3:
        st.markdown("**🏠 Living Standards (weight = 1/3)**")
        cooking_fuel   = st.slider("Cooking Fuel deprivation (%)",   0, 100, 50)
        sanitation     = st.slider("Sanitation deprivation (%)",     0, 100, 45)
        drinking_water = st.slider("Drinking Water deprivation (%)", 0, 100, 25)
        electricity    = st.slider("Electricity deprivation (%)",    0, 100, 20)
        housing        = st.slider("Housing deprivation (%)",        0, 100, 30)
        assets         = st.slider("Assets deprivation (%)",         0, 100, 35)

    poverty_threshold = st.slider(
        "Poverty Threshold (k) — minimum weighted deprivations to be MPI poor",
        0.10, 1.00, 0.33, 0.01,
    )

    weights = {
        "school_years":  1/6,  "school_attend": 1/6,
        "nutrition":     1/6,  "child_mort":    1/6,
        "cooking_fuel": 1/18,  "sanitation":   1/18,
        "drinking_water":1/18, "electricity":  1/18,
        "housing":      1/18,  "assets":       1/18,
    }
    raw_vals = {
        "school_years":   school_years  / 100,
        "school_attend":  school_attend / 100,
        "nutrition":      nutrition     / 100,
        "child_mort":     child_mort    / 100,
        "cooking_fuel":   cooking_fuel  / 100,
        "sanitation":     sanitation    / 100,
        "drinking_water": drinking_water/ 100,
        "electricity":    electricity   / 100,
        "housing":        housing       / 100,
        "assets":         assets        / 100,
    }

    c_score = sum(weights[k] * raw_vals[k] for k in weights)
    H   = min(1.0, c_score / poverty_threshold) if poverty_threshold > 0 else 0.0
    A   = c_score if c_score > 0 else 0.0
    MPI = round(H * A, 4)

    st.markdown("---")
    cr1, cr2, cr3 = st.columns(3)
    cr1.metric("Weighted Deprivation Score", f"{c_score:.3f}")
    cr2.metric("Estimated Headcount Ratio (H)", f"{H:.3f}")
    cr3.metric("🎯 Estimated MPI", f"{MPI:.4f}")

    if MPI < 0.01:
        st.success("✅ Very Low Poverty — This region performs well across all dimensions.")
    elif MPI < 0.05:
        st.info("🟡 Low Poverty — Moderate deprivations exist; targeted interventions recommended.")
    elif MPI < 0.15:
        st.warning("🟠 Moderate Poverty — Significant gaps in multiple dimensions require attention.")
    else:
        st.error("🔴 High Poverty — Urgent multi-sectoral policy intervention needed.")

    st.markdown("### 📊 Dimensional Contribution to Deprivation")
    dim_labels   = list(raw_vals.keys())
    dim_weighted = [weights[k] * raw_vals[k] for k in dim_labels]
    fig_dims = px.bar(
        x=dim_labels, y=dim_weighted,
        color=dim_weighted, color_continuous_scale="Reds",
        labels={"x": "Dimension", "y": "Weighted Deprivation"},
        title="Contribution of Each Dimension to Overall Deprivation Score",
    )
    fig_dims.update_layout(
        plot_bgcolor="white", height=380,
        coloraxis_showscale=False,
        margin=dict(l=10, r=10, t=40, b=60),
        xaxis_tickangle=-30,
    )
    st.plotly_chart(fig_dims, use_container_width=True)


# ══════════════════════════════════════════════════════════════════════════════
# PAGE 5 – DATA TABLE
# ══════════════════════════════════════════════════════════════════════════════
elif page == "📋 Data Table":
    st.markdown("""
    <div class="main-header">
        <h1>📋 Full Dataset</h1>
        <p>Browse, filter, and download the underlying data</p>
    </div>
    """, unsafe_allow_html=True)

    tab1, tab2 = st.tabs(["NITI Aayog MPI Data", "GDL Subnational HDI Data"])

    with tab1:
        st.markdown(f"**{len(filtered_mpi)} records** after filters")
        display_cols = [
            "state_ut", "headcount_2019_21_pct", "headcount_2015_16_pct",
            "change_pct_points", "improvement_rate", "poverty_category_2021",
        ]
        st.dataframe(filtered_mpi[display_cols], use_container_width=True, height=500)
        csv1 = filtered_mpi[display_cols].to_csv(index=False).encode()
        st.download_button("⬇️ Download Filtered MPI Data (CSV)", csv1, "mpi_filtered.csv", "text/csv")

    with tab2:
        st.markdown(f"**{len(hdi_long)} records** (all states, all years)")
        st.dataframe(hdi_long, use_container_width=True, height=500)
        csv2 = hdi_long.to_csv(index=False).encode()
        st.download_button("⬇️ Download HDI Data (CSV)", csv2, "hdi_data.csv", "text/csv")


# ── Footer ─────────────────────────────────────────────────────────────────────
st.markdown("---")
st.markdown(
    "<p style='text-align:center; color:#888; font-size:0.8rem;'>"
    "Sources: NITI Aayog National MPI 2023 · Global Data Lab SHDI India · "
    "Federal Bank TSM Centre of Excellence | ABA Final Project</p>",
    unsafe_allow_html=True,
)
