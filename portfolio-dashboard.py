# -*- coding: utf-8 -*-
"""
Created on Mon Sep  1 16:10:41 2025

@author: jimmy susanto
"""

import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import os
import textwrap
import plotly.express as px
import pycountry
import plotly.io as pio
import plotly.graph_objects as go
from streamlit_plotly_events import plotly_events

# ============== CONFIG ==============
st.set_page_config(
    page_title="Carbon Dashboard", 
    page_icon=":bar_chart:", 
    layout="wide",
    initial_sidebar_state="expanded"
)

# ============== CSS STYLES ==============
st.markdown("""
<link href="https://cdn.jsdelivr.net/npm/tailwindcss@2.2.19/dist/tailwind.min.css" rel="stylesheet">
<link href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@300;400;500;600;700&display=swap" rel="stylesheet">

<style>
    /* Global font and theme */
    .stApp,h2,h3,h4,p,h1 {
        font-family: 'Plus Jakarta Sans',sans-serif!important;
    }
    
    /* Custom header styling */
    .dashboard-header {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 2rem;
        border-radius: 1rem;
        margin-bottom: 1rem;
        color: white;
        text-align: center;
        box-shadow: 0 10px 25px rgba(0,0,0,0.2);
    }
    
    .dashboard-title {
        font-size: 2.5rem;
        font-weight: 700;
        margin: 0;
        text-shadow: 0 2px 4px rgba(0,0,0,0.3);
    }
    
    .dashboard-subtitle {
        font-size: 1.2rem;
        font-weight: 300;
        opacity: 0.9;
        margin-top: 0.5rem;
    }
    
    /* Sidebar styling */
    .css-1d391kg {
        background: linear-gradient(180deg, #1e293b 0%, #0f172a 100%);
        border-right: 1px solid #374151;
    }
    
    .sidebar-header {
        padding: 0.5rem;
        border-bottom: 1px solid #374151;
        margin-bottom: 0.5rem;
    }
    
    .sidebar-title {
        color: #f1f5f9;
        font-size: 1.25rem;
        font-weight: 600;
        margin: 0;
        display: flex;
        align-items: center;
        gap: 0.5rem;
    }
    
    /* Filter styling */
    .filter-section {
        margin-bottom: 1.5rem;
        padding: 1rem;
        background: rgba(30, 41, 59, 0.5);
        border-radius: 0.75rem;
        border: 1px solid #374151;
        backdrop-filter: blur(10px);
    }
    
    .filter-label {
        color: #cbd5e1;
        font-size: 0.875rem;
        font-weight: 500;
        margin-bottom: 0.5rem;
        text-transform: uppercase;
        letter-spacing: 0.025em;
    }
    
    /* Multiselect styling */
    .stMultiSelect > div > div {
        background-color: #374151 !important;
        border: 1px solid #4b5563 !important;
        border-radius: 0.5rem !important;
    }
    
    .stMultiSelect > div > div:focus-within {
        border-color: #667eea !important;
        box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1) !important;
    }
    
    /* Reset button styling */
    .stButton > button {
        width: 100%;
        background: linear-gradient(135deg, #ef4444 0%, #dc2626 100%) !important;
        color: white !important;
        border: none !important;
        padding: 0.75rem 1rem !important;
        border-radius: 0.5rem !important;
        font-weight: 500 !important;
        font-family: 'Plus Jakarta Sans', sans-serif !important;
        transition: all 0.2s ease !important;
    }
    
    .stButton > button:hover {
        transform: translateY(-1px) !important;
        box-shadow: 0 4px 12px rgba(239, 68, 68, 0.4) !important;
    }
    
    /* Main content area */
    .main-content {
        background: rgba(15, 23, 42, 0.02);
        border-radius: 1rem;
        padding: 0;
        margin: 1rem 0;
    }
    
    /* Data table styling */
    .dataframe {
        border-radius: 0.75rem !important;
        overflow: hidden !important;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1) !important;
        border: 1px solid #374151 !important;
    }
    
    /* Section headers */
    .section-header {
        color: #f1f5f9;
        font-size: 1.25rem!important;
        font-weight: 600;
        text-align: left;
        margin: 2rem 0 1rem 0!important;
        padding: 10rem;
        background: transparent;
        border-bottom: 2px solid #374151;
        
    }
    
    /* Stats card */
    .stats-card {
        background: linear-gradient(135deg, #334155 0%, #1e293b 100%);
        padding: 1.5rem;
        border-radius: 0.75rem;
        color: white;
        text-align: center;
        border: 1px solid #475569;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
    }
    
    .stats-number {
        font-size: 2rem;
        font-weight: 700;
        color: #667eea;
    }
    
    .stats-label {
        font-size: 0.875rem;
        opacity: 0.8;
        margin-top: 0.5rem;
    }
    
    /* Mobile sidebar toggle */
    .sidebar-toggle {
        display: none;
        position: fixed;
        top: 1rem;
        left: 1rem;
        z-index: 1000;
        background: #1e293b;
        color: white;
        border: none;
        padding: 0.5rem;
        border-radius: 0.5rem;
        cursor: pointer;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
    }
    
    @media (max-width: 768px) {
        .sidebar-toggle {
            display: block;
        }
        
        .dashboard-title {
            font-size: 1.75rem;
        }
        
        .main-content {
            padding: 1rem;
            margin: 0.5rem 0;
        }
    }
    
    /* Hover effects for charts */
    .plotly-graph-div {
        border-radius: 0.75rem;
        overflow: hidden;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
        border: 1px solid rgba(55, 65, 81, 0.3);
        transition: all 0.2s ease;
    }
    
    .plotly-graph-div:hover {
        box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.2);
        transform: translateY(-2px);
    }
    
    /* Separator styling */
    hr {
        border: none;
        height: 1px;
        background: linear-gradient(90deg, transparent, #374151, transparent);
        margin: 3rem 0;
    }
</style>
""", unsafe_allow_html=True)

# ============== HEADER ==============
st.markdown("""
<div class="dashboard-header">
    <h1 class="dashboard-title">🌍 Carbon Project Dashboard</h1>
    <p class="dashboard-subtitle">Comprehensive insights into global carbon offset projects</p>
</div>
""", unsafe_allow_html=True)

EXCEL_PATH = r"data/Voluntary-Registry-Offsets-Database--v2025-06.xlsx"
SHEET_NAME = "PROJECTS"
SKIP_ROWS = 3

# ============== BACKGROUND SETTING ==============
ST_BG = "#0e1117"

# Define a global template that matches Streamlit dark
pio.templates["st_dark"] = go.layout.Template(
    layout=go.Layout(
        paper_bgcolor=ST_BG,
        plot_bgcolor=ST_BG,
        font=dict(color="white", family="Plus Jakarta Sans"),
        margin=dict(t=20, r=10, b=40, l=10),
        xaxis=dict(tickfont=dict(color="white"), titlefont=dict(color="white")),
        yaxis=dict(tickfont=dict(color="white"), titlefont=dict(color="white")),
        legend=dict(font=dict(color="white")),
        coloraxis=dict(
            colorbar=dict(
                tickfont=dict(color="white"),
                titlefont=dict(color="white"),
            )
        ),
    )
)

pio.templates.default = "st_dark"

# ============== HELPERS ==============
@st.cache_data(show_spinner=False)
def load_projects(path, sheet_name, skip_rows):
    df = pd.read_excel(path, sheet_name=sheet_name, skiprows=skip_rows)

    # Normalize column names: strip, collapse spaces, replace \n, unify separators
    def fix_col(c):
        c = str(c).replace("\n", " ").strip()
        c = " ".join(c.split())  # collapse repeated spaces
        return c

    df.columns = [fix_col(c) for c in df.columns]

    # Friendly renames (after normalization)
    ren = {
        "Voluntary Registry": "Voluntary_Registry",
        "Voluntary Status": "Voluntary_Status",
        "Type": "Type",
        "Total Credits Issued": "Total_Credits_Issued",
        "Total Credits Retired": "Total_Credits_Retired",
        "Total Credits Remaining": "Total_Credits_Remaining",
        "Total Buffer Pool Deposits": "Total_Buffer_Pool_Deposits",
        "Reversals Covered by Buffer Pool": "Reversals_Covered_by_Buffer",
        "Reversals Not Covered by Buffer": "Reversals_Not_Covered_by_Buffer",
        "Buffer Credits Released to Project": "Buffer_Credits_Released",
        "ARB / WA Project": "ARB_WA_Project",
        "First Year of Project (Vintage)": "First_Vintage_Year",
        "Methodology / Protocol": "Methodology_Protocol",
        "Methodology Version": "Methodology_Version",
        "Project Site Location": "Project_Site_Location",
        "Project Developer": "Project_Developer",
        "Reduction / Removal": "Reduction_Removal",
    }
    df = df.rename(columns={k: v for k, v in ren.items() if k in df.columns})

    # Keep only columns we need
    wanted = [
        "Project ID", "Project Name", "Voluntary_Registry", "ARB_WA_Project", "Voluntary_Status",
        "Scope", "Type", "Reduction_Removal", "Methodology_Protocol", "Methodology_Version",
        "Region", "Country", "State", "Project_Site_Location", "Project_Developer",
        "Total_Credits_Issued", "Total_Credits_Retired", "Total_Credits_Remaining",
        "Total_Buffer_Pool_Deposits", "Reversals_Covered_by_Buffer", "Reversals_Not_Covered_by_Buffer",
        "Buffer_Credits_Released", "First_Vintage_Year"
    ]
    existing = [c for c in wanted if c in df.columns]
    df = df[existing].copy()

    # Basic cleaning
    df = df[df["Project ID"].notna()]
    
    # Coerce numeric credit cols
    numeric_cols = [
        "Total_Credits_Issued", "Total_Credits_Retired", "Total_Credits_Remaining",
        "Total_Buffer_Pool_Deposits", "Reversals_Covered_by_Buffer", "Reversals_Not_Covered_by_Buffer",
        "Buffer_Credits_Released"
    ]
    for c in numeric_cols:
        if c in df.columns:
            df[c] = pd.to_numeric(df[c], errors="coerce").fillna(0)

    # Fill category NAs
    for c in ["Voluntary_Registry", "Scope", "Type", "Reduction_Removal", "Region", "Country"]:
        if c in df.columns:
            df[c] = df[c].fillna("Unknown")

    return df

df_projects = load_projects(EXCEL_PATH, SHEET_NAME, SKIP_ROWS)

# ============== SIDEBAR FILTERS ==============
with st.sidebar:
    st.markdown("""
    <div class="sidebar-header">
        <h2 class="sidebar-title">
            🔍 Filters
        </h2>
    </div>
    """, unsafe_allow_html=True)

    def uniq_sorted(s):
        return sorted(pd.Series(s).dropna().unique().tolist())

    # Initialize session state
    for k in ["region_sel","country_sel","registry_sel","scope_sel","type_sel","redrem_sel","country_filter"]:
        if k == "country_filter":
            st.session_state.setdefault(k, [])
        else:
            st.session_state.setdefault(k, [])

    # Compute options
    region_opts = uniq_sorted(df_projects["Region"]) if "Region" in df_projects else []
    country_opts = uniq_sorted(df_projects["Country"]) if "Country" in df_projects else []
    scope_opts = uniq_sorted(df_projects["Scope"]) if "Scope" in df_projects else []
    type_opts = uniq_sorted(df_projects["Type"]) if "Type" in df_projects else []
    registry_opts = uniq_sorted(df_projects["Voluntary_Registry"]) if "Voluntary_Registry" in df_projects else []
    redrem_all = uniq_sorted(df_projects["Reduction_Removal"]) if "Reduction_Removal" in df_projects else []

    # Dynamic filtering logic
    df_temp = df_projects.copy()
    
    # Filter sections with custom styling
    st.markdown('<div class="filter-section hidden">', unsafe_allow_html=True)
    st.markdown('<p class="filter-label">📍 By Geography</p>', unsafe_allow_html=True)
    
    region_sel = st.multiselect("Region", options=region_opts, key="region_sel")
    
    # Dynamic country filtering
    if region_sel:
        df_temp = df_temp[df_temp["Region"].isin(region_sel)]
        country_opts = uniq_sorted(df_temp["Country"]) if "Country" in df_temp else []
    
    country_sel = st.multiselect("Country", options=country_opts, key="country_sel")
    st.markdown('</div>', unsafe_allow_html=True)

    st.markdown('<div class="filter-section hidden">', unsafe_allow_html=True)
    st.markdown('<p class="filter-label">🏭 by Project</p>', unsafe_allow_html=True)
    
    scope_sel = st.multiselect("Scope", options=scope_opts, key="scope_sel")
    
    # Dynamic type filtering based on scope
    if scope_sel:
        df_temp = df_projects.copy()
        if region_sel:
            df_temp = df_temp[df_temp["Region"].isin(region_sel)]
        if country_sel:
            df_temp = df_temp[df_temp["Country"].isin(country_sel)]
        df_temp = df_temp[df_temp["Scope"].isin(scope_sel)]
        type_opts = uniq_sorted(df_temp["Type"]) if "Type" in df_temp else []
    
    type_sel = st.multiselect("Type", options=type_opts, key="type_sel")
    st.markdown('</div>', unsafe_allow_html=True)

    st.markdown('<div class="filter-section hidden">', unsafe_allow_html=True)
    st.markdown('<p class="filter-label">📋 by Registry</p>', unsafe_allow_html=True)
    
    registry_sel = st.multiselect("Registry", options=registry_opts, key="registry_sel")
    redrem_sel = st.multiselect("Reduction / Removal", options=redrem_all, key="redrem_sel")
    st.markdown('</div>', unsafe_allow_html=True)

    # Reset button
    if st.button("🔄 Reset All Filters", key="reset_filters"):
        # Clear all filter keys
        keys_to_clear = ["registry_sel", "region_sel", "country_sel", "scope_sel", "type_sel", "redrem_sel", "country_filter"]
        for key in keys_to_clear:
            if key in st.session_state:
                del st.session_state[key]
        st.rerun()

# ============== APPLY FILTERS ==============
mask = pd.Series(True, index=df_projects.index)

if st.session_state.region_sel:
    mask &= df_projects["Region"].isin(st.session_state.region_sel)
if st.session_state.country_sel:
    mask &= df_projects["Country"].isin(st.session_state.country_sel)
if st.session_state.registry_sel:
    mask &= df_projects["Voluntary_Registry"].isin(st.session_state.registry_sel)
if st.session_state.scope_sel:
    mask &= df_projects["Scope"].isin(st.session_state.scope_sel)
if st.session_state.type_sel:
    mask &= df_projects["Type"].isin(st.session_state.type_sel)
if st.session_state.redrem_sel:
    mask &= df_projects["Reduction_Removal"].isin(st.session_state.redrem_sel)

df_sel = df_projects[mask].copy()

# ============== MAIN CONTENT ==============
st.markdown('<div class="main-content">', unsafe_allow_html=True)

# Stats overview
col1, col2, col3, col4 = st.columns(4)
with col1:
    st.markdown(f"""
    <div class="stats-card">
        <div class="stats-number">{len(df_sel):,}</div>
        <div class="stats-label">Total Projects</div>
    </div>
    """, unsafe_allow_html=True)

with col2:
    total_issued = df_sel["Total_Credits_Issued"].sum() if "Total_Credits_Issued" in df_sel.columns else 0
    st.markdown(f"""
    <div class="stats-card">
        <div class="stats-number">{total_issued:,.0f}</div>
        <div class="stats-label">Credits Issued</div>
    </div>
    """, unsafe_allow_html=True)

with col3:
    total_retired = df_sel["Total_Credits_Retired"].sum() if "Total_Credits_Retired" in df_sel.columns else 0
    st.markdown(f"""
    <div class="stats-card">
        <div class="stats-number">{total_retired:,.0f}</div>
        <div class="stats-label">Credits Retired</div>
    </div>
    """, unsafe_allow_html=True)

with col4:
    countries_count = df_sel["Country"].nunique() if "Country" in df_sel.columns else 0
    st.markdown(f"""
    <div class="stats-card">
        <div class="stats-number">{countries_count}</div>
        <div class="stats-label">Countries</div>
    </div>
    """, unsafe_allow_html=True)

# ============== PROJECT TABLE ==============
st.markdown('<h2 class="section-header">📊 Projects Overview</h2>', unsafe_allow_html=True)

# Project ID filter for table only
project_id_filter = st.text_input("🔍 Filter by Project ID (table only)", placeholder="Enter Project ID...")

# Apply project ID filter to table data only
if project_id_filter:
    df_table = df_sel[df_sel["Project ID"].astype(str).str.contains(project_id_filter, case=False, na=False)]
else:
    df_table = df_sel.copy()

# Format display data
def fmt_int(x):
    try:
        return f"{int(x):,}"
    except Exception:
        return x

display_cols = [c for c in [
    "Project ID", "Project Name", "Voluntary_Registry", "Voluntary_Status", "Region", "Country",
    "Scope", "Type", "Reduction_Removal",
    "Total_Credits_Issued", "Total_Credits_Retired", "Total_Credits_Remaining"
] if c in df_table.columns]

df_display = df_table[display_cols].copy()
for c in ["Total_Credits_Issued", "Total_Credits_Retired", "Total_Credits_Remaining"]:
    if c in df_display.columns:
        df_display[c] = df_display[c].map(fmt_int)

st.dataframe(df_display, use_container_width=True, height=400)

# ============== CHARTS SECTION ==============
st.markdown("---")

# Helper function for text wrapping
def wrap_with_br(s: str, width: int = 12) -> str:
    words = str(s).split()
    lines, line = [], ""
    for w in words:
        if len(line) + len(w) + (1 if line else 0) <= width:
            line = (line + " " + w).strip()
        else:
            lines.append(line)
            line = w
    if line:
        lines.append(line)
    return "<br>".join(lines)

# Registry and Reduction/Removal charts
col1, col2 = st.columns(2)

with col1:
    st.markdown('<h3 class="section-header">📈 Projects by Registry</h3>', unsafe_allow_html=True)
    
    counts_std = (
        df_sel["Voluntary_Registry"]
        .value_counts(dropna=False)
        .sort_index()
        .rename_axis("Voluntary_Registry")
        .reset_index(name="Counts")
    )
    
    if not counts_std.empty:
        counts_std["tick_label"] = counts_std["Voluntary_Registry"].apply(lambda s: wrap_with_br(s, 12))
        
        fig_std = px.bar(
            counts_std,
            x="Voluntary_Registry",
            y="Counts",
            text="Counts",
            color="Counts",
            color_continuous_scale="viridis",
            height=520
        )
        
        fig_std.update_xaxes(
            ticktext=counts_std["tick_label"],
            tickvals=counts_std["Voluntary_Registry"],
            tickangle=0,
            automargin=True,
            tickfont=dict(size=11),
        )
        
        fig_std.update_traces(
            hovertemplate="%{x}<br>Projects: %{y:,}<extra></extra>",
            textposition="outside",
            cliponaxis=False,
        )
        
        fig_std.update_layout(
            showlegend=False,
            margin=dict(t=20, r=10, b=30, l=10),
            xaxis_title="Voluntary Registry",
            yaxis_title="Number of Projects",
        )
        st.plotly_chart(fig_std, use_container_width=True)

with col2:
    st.markdown('<h3 class="section-header">🌱 Projects by Type</h3>', unsafe_allow_html=True)
    
    counts_rr = (
        df_sel["Reduction_Removal"]
        .value_counts(dropna=False)
        .sort_index()
        .rename_axis("Reduction_Removal")
        .reset_index(name="Counts")
    )
    
    if not counts_rr.empty:
        counts_rr["tick_label"] = counts_rr["Reduction_Removal"].apply(lambda s: wrap_with_br(s, 12))
        
        fig_rr = px.bar(
            counts_rr,
            x="Reduction_Removal",
            y="Counts",
            text="Counts",
            color="Counts",
            color_continuous_scale="plasma",
            height=520
        )
        
        fig_rr.update_xaxes(
            ticktext=counts_rr["tick_label"],
            tickvals=counts_rr["Reduction_Removal"],
            tickangle=0,
            automargin=True,
            tickfont=dict(size=11),
        )
        
        fig_rr.update_traces(
            hovertemplate="%{x}<br>Projects: %{y:,}<extra></extra>",
            textposition="outside",
            cliponaxis=False,
        )
        
        fig_rr.update_layout(
            showlegend=False,
            margin=dict(t=20, r=10, b=30, l=10),
            xaxis_title="Reduction / Removal",
            yaxis_title="Number of Projects",
        )
        st.plotly_chart(fig_rr, use_container_width=True)

st.markdown("---")

# ============== STACKED CREDITS BY REDUCTION/REMOVAL ==============
st.markdown('<h2 class="section-header">💰 Credits by Reduction/Removal</h2>', unsafe_allow_html=True)

needed_cols = {"Reduction_Removal", "Total_Credits_Issued", "Total_Credits_Retired", "Total_Credits_Remaining"}
if df_sel.empty or not needed_cols.issubset(df_sel.columns):
    st.info("No data to display. Adjust your filters.")
else:
    credits_by_rr = (
        df_sel
        .groupby("Reduction_Removal", dropna=False)[
            ["Total_Credits_Issued", "Total_Credits_Retired", "Total_Credits_Remaining"]
        ]
        .sum(numeric_only=True)
        .sort_index()
    )

    # Enforce Issued = Retired + Remaining for display
    credits_by_rr["Total_Credits_Issued_calc"] = (
        credits_by_rr["Total_Credits_Retired"] + credits_by_rr["Total_Credits_Remaining"]
    )

    # Show table
    tb = credits_by_rr[["Total_Credits_Retired", "Total_Credits_Remaining", "Total_Credits_Issued_calc"]].copy()
    tb = tb.rename(columns={"Total_Credits_Issued_calc": "Total_Credits_Issued"}).astype("int64")
    st.dataframe(tb.applymap(lambda x: f"{x:,}"), use_container_width=True)

    # Plot: Retired + Remaining stacked, Issued as line
    bar_df = credits_by_rr.reset_index()
    bar_df["Reduction_Removal_wrapped"] = bar_df["Reduction_Removal"].apply(lambda s: wrap_with_br(s, 12))

    # Stack only the components
    bar_long = bar_df.melt(
        id_vars=["Reduction_Removal", "Reduction_Removal_wrapped"],
        value_vars=["Total_Credits_Retired", "Total_Credits_Remaining"],
        var_name="Category",
        value_name="Credits",
    )

    fig_cr = px.bar(
        bar_long,
        x="Reduction_Removal_wrapped",
        y="Credits",
        color="Category",
        barmode="stack",
        text="Credits",
        title="Issued (line) vs Retired + Remaining (stack)",
        color_discrete_sequence=["#ef4444", "#10b981"]
    )

    # Format bar segment hover + text
    fig_cr.update_traces(
        texttemplate="%{text:,}",
        hovertemplate="%{x}<br>%{legendgroup}: %{y:,}<extra></extra>",
        cliponaxis=False,
    )

    # Add Issued as total line with markers
    fig_cr.add_scatter(
        x=bar_df["Reduction_Removal_wrapped"],
        y=bar_df["Total_Credits_Issued_calc"],
        mode="lines+markers",
        name="Total Credits Issued",
        marker=dict(size=8, color="#667eea"),
        line=dict(width=2, color="#667eea"),
        hovertemplate="%{x}<br>Total Issued: %{y:,}<extra></extra>",
    )

    fig_cr.update_layout(
        margin=dict(t=55, r=10, b=30, l=10),
        xaxis_title="Reduction / Removal",
        yaxis_title="Credits",
        legend_title_text="Category",
    )
    fig_cr.update_xaxes(tickangle=0, automargin=True)

    st.plotly_chart(fig_cr, use_container_width=True)

st.markdown("---")

# ============== PROJECTS BY REDUCTION/REMOVAL BY STANDARD ==============
st.markdown('<h2 class="section-header">📋 Projects by Reduction/Removal by Standard</h2>', unsafe_allow_html=True)

needed_cols = {"Voluntary_Registry", "Reduction_Removal"}
if df_sel.empty or not needed_cols.issubset(df_sel.columns):
    st.info("No data to display. Adjust your filters.")
else:
    # Long-form counts
    projects_by_redrem_by_std = (
        df_sel.groupby("Voluntary_Registry")["Reduction_Removal"]
        .value_counts(dropna=False)
        .rename("Counts")
        .reset_index()
        .sort_values(["Voluntary_Registry", "Reduction_Removal"])
    )

    # Show crosstab table
    ctab = pd.crosstab(
        index=projects_by_redrem_by_std["Voluntary_Registry"],
        columns=projects_by_redrem_by_std["Reduction_Removal"],
        values=projects_by_redrem_by_std["Counts"],
        aggfunc="sum",
    ).fillna(0).astype(int).sort_index()
    st.dataframe(ctab, use_container_width=True)

    # Plotly stacked bar
    df_plot = projects_by_redrem_by_std.copy()
    df_plot["Voluntary_Registry_wrapped"] = df_plot["Voluntary_Registry"].apply(lambda s: wrap_with_br(s, 14))

    fig_ct = px.bar(
        df_plot,
        x="Voluntary_Registry_wrapped",
        y="Counts",
        color="Reduction_Removal",
        barmode="stack",
        text="Counts",
        title="Projects by Reduction/Removal per Registry",
        color_discrete_sequence=px.colors.qualitative.Set3
    )
    fig_ct.update_traces(
        texttemplate="%{text:,}",
        hovertemplate="%{x}<br>%{legendgroup}: %{y:,}<extra></extra>",
        cliponaxis=False,
    )
    fig_ct.update_layout(
        margin=dict(t=55, r=10, b=40, l=10),
        xaxis_title="Voluntary Registry",
        yaxis_title="Number of Projects",
    )
    fig_ct.update_xaxes(tickangle=0, automargin=True)

    st.plotly_chart(fig_ct, use_container_width=True)

st.markdown("---")

# ============== SUNBURST CHARTS IN 1x2 LAYOUT ==============
st.markdown('<h2 class="section-header">🎯🏢 Projects by Scope & Scope by Standard</h2>', unsafe_allow_html=True)

# Create 1 row x 2 columns layout
col1, col2 = st.columns(2)

with col1:
    # st.markdown('<h3 class="section-header">🎯 Projects by Scope</h3>', unsafe_allow_html=True)
    
    type_col = "Type" if "Type" in df_sel.columns else (" Type" if " Type" in df_sel.columns else None)
    needed_cols = {"Scope", type_col} if type_col else set()

    if (df_sel.empty) or (not needed_cols) or (not needed_cols.issubset(df_sel.columns)):
        st.info("No data to display. Adjust your filters.")
    else:
        # Long-form counts
        scope_type = (
            df_sel.groupby("Scope")[type_col]
            .value_counts(dropna=False)
            .rename("Counts")
            .reset_index()
            .sort_values(["Scope", type_col])
        )

        # Sunburst chart
        fig_sb = px.sunburst(
            scope_type,
            path=["Scope", type_col],
            values="Counts",
            hover_data={"Counts": True},
            width=500, height=500,
            color_discrete_sequence=px.colors.qualitative.Pastel
        )

        fig_sb.update_layout(
            margin=dict(t=40, r=10, b=40, l=10)
        )

        fig_sb.update_traces(textfont_size=12)

        st.plotly_chart(fig_sb, use_container_width=True)

with col2:
    # st.markdown('<h3 class="section-header">🏢 Projects by Scope by Standard</h3>', unsafe_allow_html=True)
    
    type_col = "Type" if "Type" in df_sel.columns else (" Type" if " Type" in df_sel.columns else None)
    needed_cols = {"Voluntary_Registry", "Scope", type_col} if type_col else set()

    if (df_sel.empty) or (not needed_cols) or (not needed_cols.issubset(df_sel.columns)):
        st.info("No data to display. Adjust your filters.")
    else:
        # Long-form counts
        reg_scope_type = (
            df_sel.groupby(["Voluntary_Registry", "Scope"])[type_col]
            .value_counts(dropna=False)
            .rename("Counts")
            .reset_index()
            .sort_values(["Voluntary_Registry", "Scope", type_col])
        )

        # Sunburst chart
        fig_sb2 = px.sunburst(
            reg_scope_type,
            path=["Voluntary_Registry", "Scope", type_col],
            values="Counts",
            hover_data={"Counts": True},
            width=500, height=500,
            color_discrete_sequence=px.colors.qualitative.Set2
        )
        
        fig_sb2.update_layout(
            margin=dict(t=40, r=10, b=40, l=10)
        )

        fig_sb2.update_traces(textfont_size=12)

        st.plotly_chart(fig_sb2, use_container_width=True)

st.markdown("---")

# ============== DISTRIBUTION OF PROJECTS ACROSS COUNTRIES ==============
st.markdown('<h2 class="section-header">🌍 Distribution of Projects Across Countries</h2>', unsafe_allow_html=True)

def standardize_country(name):
    try:
        return pycountry.countries.lookup(name).name
    except LookupError:
        return name

needed_cols = {"Country"}
if df_sel.empty or not needed_cols.issubset(df_sel.columns):
    st.info("No data to display. Adjust your filters.")
else:
    # Counts by country from the filtered dataset
    mapping = df_sel["Country"].value_counts(dropna=False).reset_index(name="Counts")
    mapping.rename(columns={"index": "Country"}, inplace=True)
    mapping["Country"] = mapping["Country"].apply(standardize_country)

    # Apply only the click selection (if any)
    if st.session_state.country_filter:
        mapping_view = mapping[mapping["Country"].isin(st.session_state.country_filter)].copy()
    else:
        mapping_view = mapping.copy()

    # Show table
    # st.dataframe(mapping_view, use_container_width=True)

    # Build full map
    fig_map = px.choropleth(
        data_frame=mapping,
        locations="Country",
        locationmode="country names",
        color="Counts",
        hover_name="Country",
        color_continuous_scale="Viridis",
        custom_data=["Country"],
    )
    
    fig_map.update_layout(
        paper_bgcolor=ST_BG, 
        plot_bgcolor=ST_BG, 
        font=dict(color="white"),
        margin=dict(t=40, r=10, b=40, l=10)
    )
    fig_map.update_geos(fitbounds="locations", visible=False, bgcolor=ST_BG)

    st.caption("Tip: click a country on the map to filter. Use the reset button to clear.")
    clicks = plotly_events(
        fig_map, click_event=True, select_event=False, hover_event=False,
        override_height=600, override_width="100%"
    )

    if clicks:
        cd = clicks[0].get("customdata")
        clicked = (cd[0] if isinstance(cd, list) and cd else None) or clicks[0].get("location")
        if clicked:
            st.session_state.country_filter = [clicked]
            st.rerun()
    
    
st.markdown("---")

# ============== DISTRIBUTION OF PROJECTS ACROSS COUNTRIES BY STANDARD ==============
st.markdown('<h2 class="section-header">🗺️ Distribution of Projects Across Countries by Standard</h2>', unsafe_allow_html=True)

def standardize_country(name):
    try:
        return pycountry.countries.lookup(name).name
    except Exception:
        return name

needed_cols = {"Country", "Voluntary_Registry", "Project ID"}
if df_sel.empty or not needed_cols.issubset(df_sel.columns):
    st.info("No data to display. Adjust your filters.")
else:
    # Pivot: rows = Country, columns = Registry, values = Project count
    four_blocks = (
        df_sel.pivot_table(
            index="Country",
            columns="Voluntary_Registry",
            values="Project ID",
            aggfunc="count",
        )
        .fillna(0)
        .astype(int)
        .reset_index()
    )

    # Normalize country names
    four_blocks["Country"] = four_blocks["Country"].apply(standardize_country)

    # Show the table
    # st.dataframe(four_blocks, use_container_width=True)

    # Which registry columns to plot
    desired = ["VCS", "GOLD", "ACR", "CAR"]
    available = [c for c in desired if c in four_blocks.columns]
    if len(available) < 4:
        # Try common alternates
        alternates = {
            "VCS": ["Verra", "Verified Carbon Standard"],
            "GOLD": ["Gold Standard"],
            "ACR": ["American Carbon Registry"],
            "CAR": ["Climate Action Reserve"],
        }
        for short, alts in alternates.items():
            if short not in available:
                for alt in alts:
                    if alt in four_blocks.columns:
                        four_blocks[short] = four_blocks[alt]
                        available.append(short)
                        break
        available = [c for c in desired if c in set(available)]

    # Helper to build one choropleth
    def make_map(df, value_col, title):
        fig = px.choropleth(
            data_frame=df,
            locations="Country",
            locationmode="country names",
            color=value_col,
            hover_name="Country",
            title=title,
            projection="natural earth",
            color_continuous_scale="Viridis",
        )
        fig.update_layout(
            margin=dict(t=50, r=10, b=10, l=10),
        )
        fig.update_geos(fitbounds="locations", visible=False, bgcolor=ST_BG)
        return fig

    # Build figures (up to 4)
    figs = []
    titles = {
        "VCS": "VCS projects in every country",
        "GOLD": "GOLD projects in every country",
        "ACR": "ACR projects in every country",
        "CAR": "CAR projects in every country",
    }
    for col in available:
        figs.append(make_map(four_blocks, col, titles.get(col, f"{col} projects in every country")))

    # Render as 2×2 grid
    c1, c2 = st.columns(2)
    with c1:
        if len(figs) > 0:
            st.plotly_chart(figs[0], use_container_width=True)
    with c2:
        if len(figs) > 1:
            st.plotly_chart(figs[1], use_container_width=True)

    c3, c4 = st.columns(2)
    with c3:
        if len(figs) > 2:
            st.plotly_chart(figs[2], use_container_width=True)
    with c4:
        if len(figs) > 3:
            st.plotly_chart(figs[3], use_container_width=True)

st.markdown("---")

# ============== PROJECT STARTS BY STANDARD OVER TIME ==============
st.markdown('<h2 class="section-header">📅 Project Starts by Standard Over Time (by First Vintage Year)</h2>', unsafe_allow_html=True)

needed_cols = {"Voluntary_Registry", "First_Vintage_Year"}
if df_sel.empty or not needed_cols.issubset(df_sel.columns):
    st.info("No data to display. Adjust your filters.")
else:
    # Group counts
    first_year_vintage = (
        df_sel.groupby("Voluntary_Registry")["First_Vintage_Year"]
        .value_counts(dropna=False)
        .rename("Counts")
        .reset_index()
    )

    # Ensure datetime type for plotting
    first_year_vintage["First_Vintage_Year"] = pd.to_numeric(
        first_year_vintage["First_Vintage_Year"], errors="coerce"
    ).dropna()
    first_year_vintage["First_Vintage_Year"] = pd.to_datetime(
        first_year_vintage["First_Vintage_Year"], format="%Y"
    )

    # Pivot: rows = vintage years, columns = registries, values = project counts
    pivot_vintage = (
        first_year_vintage.pivot_table(
            index="First_Vintage_Year",
            columns="Voluntary_Registry",
            values="Counts",
            aggfunc="sum",
        )
        .fillna(0)
        .astype(int)
        .sort_index()
    )

    # Line chart
    pivot_reset = pivot_vintage.reset_index().melt(
        id_vars="First_Vintage_Year",
        var_name="Registry",
        value_name="Counts",
    )

    fig_vintage = px.line(
        pivot_reset,
        x="First_Vintage_Year",
        y="Counts",
        color="Registry",
        markers=True,
        color_discrete_sequence=px.colors.qualitative.Set1
    )

    fig_vintage.update_layout(
        margin=dict(t=50, r=10, b=40, l=10),
        xaxis=dict(title="First Vintage Year", tickformat="%Y"),
        yaxis=dict(title="Number of Projects"),
    )

    fig_vintage.update_xaxes(range=[pivot_vintage.index.min(), pivot_vintage.index.max()])

    st.plotly_chart(fig_vintage, use_container_width=True)

st.markdown("---")

# ============== TOP 20 COUNTRIES ==============
st.markdown('<h2 class="section-header">🏆 Top 20 Countries with Most Projects (Stacked by Registry)</h2>', unsafe_allow_html=True)

needed_cols = {"Voluntary_Registry", "Country", "Project ID"}
if df_sel.empty or not needed_cols.issubset(df_sel.columns):
    st.info("No data to display. Adjust your filters.")
else:
    # Long-form counts
    projects_country = (
        df_sel.groupby("Voluntary_Registry")["Country"]
        .value_counts(dropna=False)
        .rename("Counts")
        .reset_index()
    )

    # Pivot: rows = Country, columns = Registry, values = Counts
    project_country_2 = (
        projects_country.pivot_table(
            index="Country",
            columns="Voluntary_Registry",
            values="Counts",
            aggfunc="sum",
        )
        .fillna(0)
        .astype(int)
        .reset_index()
    )

    # Normalize/ensure expected registry columns exist
    desired = ["ACR", "ART", "CAR", "GOLD", "VCS"]
    alternates = {
        "VCS": ["Verra", "Verified Carbon Standard"],
        "GOLD": ["Gold Standard"],
        "ACR": ["American Carbon Registry"],
        "CAR": ["Climate Action Reserve"],
        "ART": ["Architecture for REDD+ Transactions", "ART TREES"],
    }
    for short, alts in alternates.items():
        if short not in project_country_2.columns:
            for alt in alts:
                if alt in project_country_2.columns:
                    project_country_2[short] = project_country_2[alt]
                    break
    
    for col in desired:
        if col not in project_country_2.columns:
            project_country_2[col] = 0

    # Compute total across registries
    project_country_2["Sum"] = project_country_2[desired].sum(axis=1)

    # Sort by Sum desc and take top 20
    top20 = project_country_2.sort_values(by="Sum", ascending=False).head(20).copy()

    # Horizontal stacked bar
    fig_top20 = px.bar(
        top20.sort_values("Sum", ascending=True),
        y="Country",
        x=desired,
        orientation="h",
        color_discrete_sequence=px.colors.qualitative.Set3
    )
    fig_top20.update_layout(
        barmode="stack",
        margin=dict(t=60, r=10, b=10, l=10),
        xaxis_title="Number of Projects",
        yaxis_title="Country",
    )

    st.plotly_chart(fig_top20, use_container_width=True)

st.markdown('</div>', unsafe_allow_html=True)  # Close main-content
