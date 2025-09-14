# -*- coding: utf-8 -*-
"""
Created on Mon Sep  1 16:10:41 2025
@author: jimmy susanto
Refactored on Sun May 26 2024 to match PRD style guidelines.
"""
import streamlit as st
import pandas as pd
import numpy as np
import os
import textwrap
import plotly.express as px
import pycountry
import plotly.io as pio
import plotly.graph_objects as go
from streamlit_plotly_events import plotly_events

# ============== CONFIG ==============
st.set_page_config(page_title="Carbon Dashboard", page_icon=":bar_chart:", layout="wide")

# ============== TAILWIND CSS CDN & CUSTOM STYLING ==============
# Inject Tailwind and override Streamlit's default dark theme with PRD's light style
st.markdown("""
<script src="https://cdn.tailwindcss.com"></script>
<style>

    /* PRD Global Background */
    .main {
        background-color: #f8fafc !important; /* bg-slate-50 */
    }
    /* Override Streamlit's default dark background for containers */
    .stApp {
        background-color: #f8fafc !important;
    }
    /* PRD Card Style */
    .prd-card {
        background: white;
        border-radius: 1rem; /* rounded-2xl */
        box-shadow: 0 1px 3px 0 rgba(0, 0, 0, 0.1), 0 1px 2px -1px rgba(0, 0, 0, 0.1); /* shadow-sm */
        border: 1px solid #e2e8f0; /* border-slate-100 */
        padding: 1.5rem; /* p-6 */
        margin-bottom: 1.5rem;
    }
    /* PRD Section Header */
    .prd-section-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 1rem;
    }
    .prd-section-title {
        font-size: 1.25rem; /* text-xl */
        font-weight: 600; /* font-semibold */
        color: #1e293b; /* text-slate-800 */
    }
    .prd-section-subtitle {
        font-size: 0.875rem; /* text-sm */
        color: #64748b; /* text-slate-500 */
        margin-top: 0.25rem;
    }
    /* PRD Filter Button (using indigo/violet palette) */
    .filter-button {
        background: linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%); /* indigo-500 to violet-500 */
        color: #ffffff;
        border: none;
        padding: 0.5rem 1rem;
        border-radius: 0.75rem; /* rounded-xl */
        font-weight: 500;
        font-size: 0.875rem;
        transition: all 0.2s;
        cursor: pointer;
    }
    .filter-button:hover {
        background: linear-gradient(135deg, #4f46e5 0%, #7c3aed 100%); /* indigo-600 to violet-600 */
        transform: translateY(-1px);
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06);
    }
    /* PRD Stat Pill (for potential future use) */
    .stat-pill {
        display: inline-flex;
        align-items: center;
        gap: 0.5rem;
        border-radius: 0.75rem; /* rounded-xl */
        padding: 0.5rem 0.75rem; /* px-3 py-2 */
        font-size: 0.875rem; /* text-sm */
        background: rgba(15, 23, 42, 0.7); /* bg-slate-900/70 */
        backdrop-filter: blur(4px);
        border: 1px solid rgba(15, 23, 42, 0.6); /* border-slate-900/60 */
        box-shadow: 0 1px 2px 0 rgba(0, 0, 0, 0.05); /* shadow-sm */
        color: #ffffff;
    }
    /* Ensure Plotly charts have a white background to match cards */
    .js-plotly-plot .plotly {
        background-color: white !important;
    }
    /* Responsive adjustments */
    @media (max-width: 768px) {
        .filter-container {
            flex-direction: column;
            gap: 1rem;
        }
        .filter-item {
            width: 100%;
        }
    }
</style>
""", unsafe_allow_html=True)

# ============== HEADER ==============
st.markdown("""
<div class="prd-card">
    <h1 class="text-3xl md:text-4xl font-bold text-indigo-600">Carbon Project Analysis Dashboard</h1>
    <p class="text-lg mt-2 text-gray-700">Interactive visualization of carbon credit projects worldwide</p>
</div>
""", unsafe_allow_html=True)

# ============== DATA LOADING & SETUP ==============
EXCEL_PATH = r"data/Voluntary-Registry-Offsets-Database--v2025-06.xlsx"
SHEET_NAME = "PROJECTS"
SKIP_ROWS = 3

# Since we're using a light theme, we need to update the Plotly template
# Define a global template that matches the PRD's light theme
pio.templates["prd_light"] = go.layout.Template(
    layout=go.Layout(
        paper_bgcolor="white",
        plot_bgcolor="white",
        font=dict(color="#1e293b"), # text-slate-800
        margin=dict(t=50, r=10, b=40, l=10),
        xaxis=dict(
            tickfont=dict(color="#64748b"), # text-slate-500
            gridcolor='rgba(15,23,42,0.06)', # PRD grid color
            showgrid=True,
            zeroline=False
        ),
        yaxis=dict(
            tickfont=dict(color="#64748b"),
            gridcolor='rgba(15,23,42,0.06)',
            showgrid=True,
            zeroline=False
        ),
        legend=dict(
            font=dict(color="#1e293b"),
            bgcolor="rgba(255,255,255,0.8)"
        ),
        coloraxis=dict(
            colorbar=dict(
                tickfont=dict(color="#64748b"),
            )
        ),
    )
)
# Apply it everywhere by default
pio.templates.default = "prd_light"

# ============== HELPERS ==============
def multiselect_with_all(label, options, key):
    """
    Renders a checkbox 'Select all' + a multiselect.
    If 'Select all' is checked, returns all options and (optionally) disables the widget.
    """
    # Show the checkbox
    select_all = st.checkbox(f"Select all {label}", value=False, key=f"{key}_all")
    # Multiselect (disabled if 'select all' is on; still shows what's selected)
    selected = st.multiselect(
        label,
        options,
        default=(options if select_all else []),
        key=key,
        disabled=select_all  # comment this out if your Streamlit version doesn't support 'disabled'
    )
    # If the checkbox is on, force-return all options; otherwise return user selection
    return options if select_all else selected

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
    # Keep only columns we need (guard for missing ones)
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
    df = df[df["Project ID"].notna()]  # ensure valid rows
    # Coerce numeric credit cols
    numeric_cols = [
        "Total_Credits_Issued", "Total_Credits_Retired", "Total_Credits_Remaining",
        "Total_Buffer_Pool_Deposits", "Reversals_Covered_by_Buffer", "Reversals_Not_Covered_by_Buffer",
        "Buffer_Credits_Released"
    ]
    for c in numeric_cols:
        if c in df.columns:
            df[c] = pd.to_numeric(df[c], errors="coerce").fillna(0)
    # Fill category NAs for grouping/filters visibility
    for c in ["Voluntary_Registry", "Scope", "Type", "Reduction_Removal", "Region", "Country"]:
        if c in df.columns:
            df[c] = df[c].fillna("Unknown")
    return df

df_projects = load_projects(EXCEL_PATH, SHEET_NAME, SKIP_ROWS)

# ============== TOP FILTERS (STATIC, REPLACING SIDEBAR) ==============
st.markdown('<div class="prd-card">', unsafe_allow_html=True)
st.markdown("""
<div class="prd-section-header">
    <div>
        <h2 class="prd-section-title">Filters</h2>
        <p class="prd-section-subtitle">Customize your view</p>
    </div>
</div>
""", unsafe_allow_html=True)

# --- init session state once
for k in ["region_sel","country_sel","registry_sel","scope_sel","type_sel","redrem_sel","master_all"]:
    st.session_state.setdefault(k, [] if k.endswith("_sel") else False)

# --- Reset button
if st.button("Reset all filters", key="reset_top"):
    for k in list(st.session_state.keys()):
        if k.endswith("_sel") or k == "master_all":
            st.session_state.pop(k, None)
    st.rerun()

# Create a container for filters with a responsive grid
filter_container = st.container()
with filter_container:
    # Use columns for a responsive layout
    cols = st.columns(2) if len(st.session_state.region_sel) > 0 else st.columns(3)
    
    def uniq_sorted(s):
        return sorted(pd.Series(s).dropna().unique().tolist())

    # ========= 1) compute parent options FIRST (unfiltered) =========
    region_opts   = uniq_sorted(df_projects["Region"])               if "Region" in df_projects else []
    scope_opts    = uniq_sorted(df_projects["Scope"])                if "Scope" in df_projects else []
    registry_opts = uniq_sorted(df_projects["Voluntary_Registry"])   if "Voluntary_Registry" in df_projects else []
    redrem_all    = uniq_sorted(df_projects["Reduction_Removal"])    if "Reduction_Removal" in df_projects else []

    # ========= 2) master-all checkbox (callback sets state, no rerun) =========
    def _apply_master_all():
        """Write full option lists into the *_sel keys BEFORE widgets are rendered."""
        if st.session_state.master_all:
            # Parent selections (global lists)
            st.session_state.region_sel   = region_opts[:]
            st.session_state.scope_sel    = scope_opts[:]
            st.session_state.registry_sel = registry_opts[:]
            st.session_state.redrem_sel   = redrem_all[:]   # provisional; may reduce after child opts computed

    st.checkbox("Select all for every filter", key="master_all", on_change=_apply_master_all)

    # ========= 3) compute CHILD options based on parents FIRST =========
    df_children = df_projects.copy()
    if st.session_state.region_sel:
        df_children = df_children[df_children["Region"].isin(st.session_state.region_sel)]
    if st.session_state.scope_sel:
        df_children = df_children[df_children["Scope"].isin(st.session_state.scope_sel)]
    country_opts = uniq_sorted(df_children["Country"]) if "Country" in df_children else []
    type_opts    = uniq_sorted(df_children["Type"])    if "Type" in df_children else []

    # ========= 4) render PARENT widgets =========
    def _clear_type_on_scope_change():
        # When Scope changes, clear Type so it can repopulate with valid defaults
        st.session_state["type_sel"] = []

    with cols[0]:
        st.multiselect("Registry", options=registry_opts, key="registry_sel",
                       disabled=st.session_state.master_all)
        st.multiselect("Region", options=region_opts, key="region_sel",
                       disabled=st.session_state.master_all)
        st.multiselect("Country", options=country_opts, key="country_sel",
                       disabled=st.session_state.master_all)

    with cols[1]:
        st.multiselect(
            "Scope",
            options=scope_opts,
            key="scope_sel",
            disabled=st.session_state.master_all,
            on_change=_clear_type_on_scope_change,
        )
        
        # If user hasn't chosen any Type, default to "all valid Types under current Scope(s)"
        type_default = st.session_state.get("type_sel") or type_opts[:]
        # Clamp any existing child selections to allowed values (only if session state exists)
        if "type_sel" in st.session_state:
            st.session_state.type_sel    = [v for v in st.session_state.type_sel    if v in type_opts]
        # If master_all is on, also fill child selections NOW (still before child widgets are rendered)
        if st.session_state.master_all:
            st.session_state.type_sel    = type_opts[:]

        st.multiselect(
            "Type",
            options=type_opts,
            default=type_default,           # << make "all under scope" the default
            key="type_sel",
            disabled=st.session_state.master_all
        )

    # Render the last filter in a new row if needed for better layout
    if len(cols) == 2:
        st.multiselect("Reduction / Removal", options=redrem_all, key="redrem_sel",
                       disabled=st.session_state.master_all)

st.markdown('</div>', unsafe_allow_html=True) # Close filter card

# ========= 5) build the mask FIRST =========
mask = pd.Series(True, index=df_projects.index)
if st.session_state.region_sel:
    mask &= df_projects["Region"].isin(st.session_state.region_sel)
if st.session_state.country_sel:
    mask &= df_projects["Country"].isin(st.session_state.country_sel)
if st.session_state.registry_sel:
    mask &= df_projects["Voluntary_Registry"].isin(st.session_state.registry_sel)
if st.session_state.scope_sel:
    mask &= df_projects["Scope"].isin(st.session_state.scope_sel)
effective_scopes = st.session_state.scope_sel or scope_opts
# Recompute allowed Types under current scopes (same logic as df_children)
allowed_types = uniq_sorted(
    df_projects.loc[df_projects["Scope"].isin(effective_scopes), "Type"]
) if "Type" in df_projects else []
effective_types = st.session_state.type_sel or allowed_types
if allowed_types:  # only if Type column exists
    mask &= df_projects["Type"].isin(effective_types)
if st.session_state.redrem_sel:
    mask &= df_projects["Reduction_Removal"].isin(st.session_state.redrem_sel)
df_sel = df_projects[mask].copy()

# ============== TOP TABLE ==============
st.markdown('<div class="prd-card">', unsafe_allow_html=True)
st.markdown("""
<div class="prd-section-header">
    <div>
        <h2 class="prd-section-title">List of Projects</h2>
        <p class="prd-section-subtitle">Filtered view of carbon credit projects</p>
    </div>
</div>
""", unsafe_allow_html=True)
st.caption(f"Showing {len(df_sel):,} of {len(df_projects):,} projects")

# Nice formatting for big numbers
def fmt_int(x):
    try:
        return f"{int(x):,}"
    except Exception:
        return x

display_cols = [c for c in [
    "Project ID", "Project Name", "Voluntary_Registry", "Voluntary_Status", "Region", "Country",
    "Scope", "Type", "Reduction_Removal",
    "Total_Credits_Issued", "Total_Credits_Retired", "Total_Credits_Remaining"
] if c in df_sel.columns]
df_display = df_sel[display_cols].copy()
for c in ["Total_Credits_Issued", "Total_Credits_Retired", "Total_Credits_Remaining"]:
    if c in df_display.columns:
        df_display[c] = df_display[c].map(fmt_int)

st.dataframe(df_display, use_container_width=True)
st.markdown('</div>', unsafe_allow_html=True) # Close card

# ============== TWO SIDE-BY-SIDE PLOTS ==============
# --- helper to wrap tick labels with <br> so Plotly renders multi-line ticks
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

# Build both datasets up-front
counts_std = (
    df_sel["Voluntary_Registry"]
    .value_counts(dropna=False)
    .sort_index()
    .rename_axis("Voluntary_Registry")
    .reset_index(name="Counts")
)
counts_std["tick_label"] = counts_std["Voluntary_Registry"].apply(lambda s: wrap_with_br(s, 12))
counts_rr = (
    df_sel["Reduction_Removal"]
    .value_counts(dropna=False)
    .sort_index()
    .rename_axis("Reduction_Removal")
    .reset_index(name="Counts")
)
counts_rr["tick_label"] = counts_rr["Reduction_Removal"].apply(lambda s: wrap_with_br(s, 12))

# Choose ONE consistent figure height & margins for both charts
FIG_H = 520
BOTTOM_MARGIN = 30  # enough space for multi-line ticks

st.markdown('<div class="prd-card">', unsafe_allow_html=True)
st.markdown("""
<div class="prd-section-header">
    <div>
        <h2 class="prd-section-title">Project Distribution</h2>
        <p class="prd-section-subtitle">Analyze projects by registry and type</p>
    </div>
</div>
""", unsafe_allow_html=True)

col1, col2 = st.columns(2)
with col1:
    if counts_std.empty:
        st.info("No data to display. Adjust your filters.")
    else:
        fig_std = px.bar(
            counts_std,
            x="Voluntary_Registry",
            y="Counts",
            text="Counts",
            title="Projects by Registry (Filtered)",
            height=FIG_H,
        )
        # apply wrapped ticks & keep horizontal labels
        fig_std.update_xaxes(
            ticktext=counts_std["tick_label"],
            tickvals=counts_std["Voluntary_Registry"],
            tickangle=0,
            automargin=True,
            tickfont=dict(size=11, color="#64748b"),
        )
        fig_std.update_traces(
            hovertemplate="%{x}<br>Projects: %{y:,}<extra></extra>",
            textposition="outside",
            cliponaxis=False,
            marker_color='#6366f1' # indigo-500
        )
        fig_std.update_layout(
            margin=dict(t=20, r=10, b=BOTTOM_MARGIN, l=10),
            xaxis_title="Voluntary Registry",
            yaxis_title="Number of Projects",
            title_x=0.5
        )
        st.plotly_chart(fig_std, use_container_width=True)

with col2:
    if counts_rr.empty:
        st.info("No data to display. Adjust your filters.")
    else:
        fig_rr = px.bar(
            counts_rr,
            x="Reduction_Removal",
            y="Counts",
            text="Counts",
            title="Projects by Reduction/Removal (Filtered)",
            height=FIG_H,  # ← SAME height
        )
        # apply wrapped ticks & keep horizontal labels
        fig_rr.update_xaxes(
            ticktext=counts_rr["tick_label"],
            tickvals=counts_rr["Reduction_Removal"],
            tickangle=0,
            automargin=True,
            tickfont=dict(size=11, color="#64748b"),
        )
        fig_rr.update_traces(
            hovertemplate="%{x}<br>Projects: %{y:,}<extra></extra>",
            textposition="outside",
            cliponaxis=False,
            marker_color='#8b5cf6' # violet-500
        )
        fig_rr.update_layout(
            margin=dict(t=20, r=10, b=BOTTOM_MARGIN, l=10),  # ← SAME margins
            xaxis_title="Reduction / Removal",
            yaxis_title="Number of Projects",
            title_x=0.5
        )
        st.plotly_chart(fig_rr, use_container_width=True)
st.markdown('</div>', unsafe_allow_html=True) # Close card

# ============== STACKED CREDITS BY REDUCTION/REMOVAL ==============
st.markdown('<div class="prd-card">', unsafe_allow_html=True)
st.markdown("""
<div class="prd-section-header">
    <div>
        <h2 class="prd-section-title">Credits by Reduction/Removal (Filtered)</h2>
        <p class="prd-section-subtitle">Distribution of carbon credits by type</p>
    </div>
</div>
""", unsafe_allow_html=True)

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
    # ----- Show table (Retired, Remaining, Issued as sum) -----
    tb = credits_by_rr[["Total_Credits_Retired", "Total_Credits_Remaining", "Total_Credits_Issued_calc"]].copy()
    tb = tb.rename(columns={"Total_Credits_Issued_calc": "Total_Credits_Issued"}).astype("int64")
    st.dataframe(tb.applymap(lambda x: f"{x:,}"), use_container_width=True)
    # ----- Plot: Retired + Remaining stacked, Issued as line -----
    def wrap_with_br(s: str, width: int = 12) -> str:
        s = str(s)
        words, lines, line = s.split(), [], ""
        for w in words:
            if len(line) + (1 if line else 0) + len(w) <= width:
                line = (line + " " + w).strip()
            else:
                lines.append(line); line = w
        if line: lines.append(line)
        return "<br>".join(lines) if len(s) > width else s

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
        title="Issued (line) vs Retired + Remaining (stack) — Filtered",
        color_discrete_map={"Total_Credits_Retired": "#6366f1", "Total_Credits_Remaining": "#8b5cf6"} # indigo/violet
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
        marker=dict(size=8, color='#0ea5e9'), # sky-500
        line=dict(width=2, color='#0ea5e9'),
        hovertemplate="%{x}<br>Total Issued: %{y:,}<extra></extra>",
    )
    # PRD theme + room for wrapped ticks
    fig_cr.update_layout(
        margin=dict(t=55, r=10, b=30, l=10),
        xaxis_title="Reduction / Removal",
        yaxis_title="Credits",
        legend_title_text="Category",
        title_x=0.5
    )
    fig_cr.update_xaxes(tickangle=0, automargin=True, tickfont=dict(color="#64748b"))
    st.plotly_chart(fig_cr, use_container_width=True)
st.markdown('</div>', unsafe_allow_html=True) # Close card

# ============== PROJECTS BY REDUCTION/REMOVAL BY STANDARD ==============
st.markdown('<div class="prd-card">', unsafe_allow_html=True)
st.markdown("""
<div class="prd-section-header">
    <div>
        <h2 class="prd-section-title">Projects by Reduction/Removal by Standard</h2>
        <p class="prd-section-subtitle">Cross-analysis of projects by registry and type</p>
    </div>
</div>
""", unsafe_allow_html=True)

needed_cols = {"Voluntary_Registry", "Reduction_Removal"}
if df_sel.empty or not needed_cols.issubset(df_sel.columns):
    st.info("No data to display. Adjust your filters.")
else:
    # Long-form counts (already perfect for stacked bars)
    projects_by_redrem_by_std = (
        df_sel.groupby("Voluntary_Registry")["Reduction_Removal"]
        .value_counts(dropna=False)
        .rename("Counts")
        .reset_index()
        .sort_values(["Voluntary_Registry", "Reduction_Removal"])
    )
    # Show crosstab table for transparency
    ctab = pd.crosstab(
        index=projects_by_redrem_by_std["Voluntary_Registry"],
        columns=projects_by_redrem_by_std["Reduction_Removal"],
        values=projects_by_redrem_by_std["Counts"],
        aggfunc="sum",
    ).fillna(0).astype(int).sort_index()
    st.dataframe(ctab, use_container_width=True)
    # Plotly stacked bar
    def wrap_with_br(s: str, width: int = 14) -> str:
        s = str(s)
        words, lines, line = s.split(), [], ""
        for w in words:
            if len(line) + (1 if line else 0) + len(w) <= width:
                line = (line + " " + w).strip()
            else:
                lines.append(line); line = w
        if line: lines.append(line)
        return "<br>".join(lines) if len(s) > width else s

    df_plot = projects_by_redrem_by_std.copy()
    df_plot["Voluntary_Registry_wrapped"] = df_plot["Voluntary_Registry"].apply(lambda s: wrap_with_br(s, 14))
    fig_ct = px.bar(
        df_plot,
        x="Voluntary_Registry_wrapped",
        y="Counts",
        color="Reduction_Removal",
        barmode="stack",
        text="Counts",
        title="Projects by Reduction/Removal per Registry (Filtered)",
        color_discrete_sequence=px.colors.qualitative.Vivid # Using a vivid palette for multiple categories
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
        title_x=0.5
    )
    fig_ct.update_xaxes(tickangle=0, automargin=True, tickfont=dict(color="#64748b"))
    st.plotly_chart(fig_ct, use_container_width=True)
st.markdown('</div>', unsafe_allow_html=True) # Close card

# ============== PROJECTS BY SCOPE ==============
st.markdown('<div class="prd-card">', unsafe_allow_html=True)
st.markdown("""
<div class="prd-section-header">
    <div>
        <h2 class="prd-section-title">Projects by Scope</h2>
        <p class="prd-section-subtitle">Distribution of projects by their scope categories</p>
    </div>
</div>
""", unsafe_allow_html=True)

# Handle possible legacy column name " Type" just in case
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
    # Crosstab (Scope x Type)
    ctab_st = pd.crosstab(
        index=scope_type["Scope"],
        columns=scope_type[type_col],
        values=scope_type["Counts"],
        aggfunc="sum",
    ).fillna(0).astype(int).sort_index()
    # Show the table
    st.dataframe(ctab_st, use_container_width=True)
    # ---------- Sunburst ----------
    fig_sb = px.sunburst(
        scope_type,
        path=["Scope", type_col],
        values="Counts",
        hover_data={"Counts": True},
        width=700, height=700,
        color_discrete_sequence=px.colors.qualitative.Prism
    )
    # Match PRD light background
    fig_sb.update_layout(
        margin=dict(t=40, r=10, b=40, l=10),
        title_x=0.5
    )
    # Slightly larger labels for readability
    fig_sb.update_traces(textfont_size=14)
    # Display in Streamlit
    st.plotly_chart(fig_sb, use_container_width=True)
st.markdown('</div>', unsafe_allow_html=True) # Close card

# ============== PROJECTS BY SCOPE BY STANDARD ==============
st.markdown('<div class="prd-card">', unsafe_allow_html=True)
st.markdown("""
<div class="prd-section-header">
    <div>
        <h2 class="prd-section-title">Projects by Scope by Standard</h2>
        <p class="prd-section-subtitle">Multi-level analysis of projects by registry, scope, and type</p>
    </div>
</div>
""", unsafe_allow_html=True)

# Handle possible legacy column name " Type"
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
    # Crosstab: (Registry, Scope) x Type
    ctab_rst = pd.crosstab(
        index=[reg_scope_type["Voluntary_Registry"], reg_scope_type["Scope"]],
        columns=reg_scope_type[type_col],
        values=reg_scope_type["Counts"],
        aggfunc="sum",
    ).fillna(0).astype(int).sort_index()
    # Show the table
    st.dataframe(ctab_rst, use_container_width=True)
    # ---------- Sunburst ----------
    fig_sb2 = px.sunburst(
        reg_scope_type,
        path=["Voluntary_Registry", "Scope", type_col],
        values="Counts",
        hover_data={"Counts": True},
        width=700, height=700,
        color_discrete_sequence=px.colors.qualitative.Dark24
    )
    # Match PRD light background
    fig_sb2.update_layout(
        margin=dict(t=40, r=10, b=40, l=10),
        title_x=0.5
    )
    # Slightly larger labels for readability
    fig_sb2.update_traces(textfont_size=14)
    # Display in Streamlit
    st.plotly_chart(fig_sb2, use_container_width=True)
st.markdown('</div>', unsafe_allow_html=True) # Close card

# ============== DISTRIBUTION OF PROJECTS ACROSS COUNTRIES ==============
st.markdown('<div class="prd-card">', unsafe_allow_html=True)
st.markdown("""
<div class="prd-section-header">
    <div>
        <h2 class="prd-section-title">Distribution of Projects Across Countries</h2>
        <p class="prd-section-subtitle">Geographic distribution of carbon credit projects</p>
    </div>
</div>
""", unsafe_allow_html=True)

def standardize_country(name):
    try:
        return pycountry.countries.lookup(name).name
    except LookupError:
        return name

if "country_filter" not in st.session_state:
    st.session_state.country_filter = []  # persisted selection from clicks

needed_cols = {"Country"}
if df_sel.empty or not needed_cols.issubset(df_sel.columns):
    st.info("No data to display. Adjust your filters.")
else:
    # Counts by country from the filtered dataset (global sidebar filters already applied to df_sel)
    mapping = df_sel["Country"].value_counts(dropna=False).reset_index(name="Counts")
    mapping.rename(columns={"index": "Country"}, inplace=True)
    mapping["Country"] = mapping["Country"].apply(standardize_country)
    # ✅ NO EXTRA SIDEBAR FILTER HERE
    # Apply only the click selection (if any)
    if st.session_state.country_filter:
        mapping_view = mapping[mapping["Country"].isin(st.session_state.country_filter)].copy()
    else:
        mapping_view = mapping.copy()
    # Show table
    st.dataframe(mapping_view, use_container_width=True)
    # Build full map (so you can always click any country)
    fig_map = px.choropleth(
        data_frame=mapping,  # full, not filtered, so you can click new countries
        locations="Country",
        locationmode="country names",
        color="Counts",
        hover_name="Country",
        #title="Number of Projects per Country",
        color_continuous_scale="Viridis",
        custom_data=["Country"],  # for reliable click retrieval
    )
    # PRD light theme & auto-zoom to the current view
    fig_map.update_layout(
        paper_bgcolor="white",
        plot_bgcolor="white",
        font=dict(color="#1e293b"),
        margin=dict(t=40, r=10, b=40, l=10)
    )
    # Fit to the *currently displayed* countries in the table
    fig_map.update_geos(fitbounds="locations", visible=False, bgcolor="white")
    # Display the map
    st.plotly_chart(fig_map, use_container_width=True)
#    st.caption("Tip: click a country on the map to filter. Use the button below to clear.")
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
st.markdown('</div>', unsafe_allow_html=True) # Close card

# ============== DISTRIBUTION OF PROJECTS ACROSS COUNTRIES BY STANDARD ==============
st.markdown('<div class="prd-card">', unsafe_allow_html=True)
st.markdown("""
<div class="prd-section-header">
    <div>
        <h2 class="prd-section-title">Distribution of Projects Across Countries by Standard</h2>
        <p class="prd-section-subtitle">Geographic distribution by voluntary registry</p>
    </div>
</div>
""", unsafe_allow_html=True)

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
    st.dataframe(four_blocks, use_container_width=True)
    # Which registry columns to plot (use the ones that actually exist)
    desired = ["VCS", "GOLD", "ACR", "CAR"]
    available = [c for c in desired if c in four_blocks.columns]
    if len(available) < 4:
        # Try common alternates if your source uses long names
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
        # Keep order and ensure uniqueness
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
            paper_bgcolor="white",
            plot_bgcolor="white",
            font=dict(color="#1e293b")
        )
        # 🔄 This line auto-zooms to filtered countries (e.g., Indonesia)
        fig.update_geos(fitbounds="locations", visible=False, bgcolor="white")
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
    # Row 1
    c1, c2 = st.columns(2)
    with c1:
        if len(figs) > 0:
            st.plotly_chart(figs[0], use_container_width=True)
    with c2:
        if len(figs) > 1:
            st.plotly_chart(figs[1], use_container_width=True)
    # Row 2
    c3, c4 = st.columns(2)
    with c3:
        if len(figs) > 2:
            st.plotly_chart(figs[2], use_container_width=True)
    with c4:
        if len(figs) > 3:
            st.plotly_chart(figs[3], use_container_width=True)
st.markdown('</div>', unsafe_allow_html=True) # Close card

# ============== Number of projects are running for the first time per Standard in time series ==============
st.markdown('<div class="prd-card">', unsafe_allow_html=True)
st.markdown("""
<div class="prd-section-header">
    <div>
        <h2 class="prd-section-title">Project Starts by Standard Over Time (by First Vintage Year)</h2>
        <p class="prd-section-subtitle">Timeline of project initiations by registry</p>
    </div>
</div>
""", unsafe_allow_html=True)

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
    # Ensure datetime type for plotting (keep only valid years)
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
    # Show table
    # st.dataframe(pivot_vintage, use_container_width=True)
    # ---------- Line chart ----------
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
        #title="Projects by First Vintage Year per Registry",
        markers=True,
        color_discrete_sequence=px.colors.qualitative.Bold
    )
    # PRD theme + auto-fit x-axis
    fig_vintage.update_layout(
        margin=dict(t=50, r=10, b=40, l=10),
        xaxis=dict(title="First Vintage Year", tickformat="%Y", tickfont=dict(color="#64748b")),
        yaxis=dict(title="Number of Projects", tickfont=dict(color="#64748b")),
        title_x=0.5
    )
    # Auto-zoom to the available vintages
    fig_vintage.update_xaxes(range=[pivot_vintage.index.min(), pivot_vintage.index.max()])
    st.plotly_chart(fig_vintage, use_container_width=True)
st.markdown('</div>', unsafe_allow_html=True) # Close card

# ============== Number of projects (Top 20) by Standard by Country ==============
st.markdown('<div class="prd-card">', unsafe_allow_html=True)
st.markdown("""
<div class="prd-section-header">
    <div>
        <h2 class="prd-section-title">Top 20 Countries with Most Projects (Stacked by Registry)</h2>
        <p class="prd-section-subtitle">Leading countries in carbon credit project development</p>
    </div>
</div>
""", unsafe_allow_html=True)

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
    # Try to map common long names to short codes if short codes are missing
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
    # Any still-missing desired columns → add as zeros
    for col in desired:
        if col not in project_country_2.columns:
            project_country_2[col] = 0
    # Compute total across registries
    project_country_2["Sum"] = project_country_2[desired].sum(axis=1)
    # Sort by Sum desc
    project_country_2 = project_country_2.sort_values(by="Sum", ascending=False)
    # Show table
    # st.dataframe(project_country_2, use_container_width=True)
    # ---------- Plotly bars: Top 20 ----------
    top20 = project_country_2.head(20).copy()
    # Horizontal stacked bar (better readability for country names)
    fig_top20 = px.bar(
        top20.sort_values("Sum", ascending=True),  # ascending so largest at top after orientation='h'
        y="Country",
        x=desired,                      # wide-form (stacked by registry)
        orientation="h",
        #title="Top 20 Countries with Most Projects (Stacked by Registry)",
        color_discrete_sequence=px.colors.qualitative.Set3
    )
    fig_top20.update_layout(
        barmode="stack",
        margin=dict(t=60, r=10, b=10, l=10),
        xaxis_title="Number of Projects",
        yaxis_title="Country",
        title_x=0.5
    )
    # Optional: show totals as text at bar end
    fig_top20.update_traces(texttemplate=None)  # keep clean; can set to "%{x}" if you want per-segment
    # Add total labels using a scatter trace if you want—omitted here to keep it simple
    st.plotly_chart(fig_top20, use_container_width=True)
st.markdown('</div>', unsafe_allow_html=True) # Close card

# ============== Final Section (Duplicate from original, kept for completeness) ==============
st.markdown('<div class="prd-card">', unsafe_allow_html=True)
st.markdown("""
<div class="prd-section-header">
    <div>
        <h2 class="prd-section-title">Distribution of projects across countries by Standard</h2>
        <p class="prd-section-subtitle">Geographic distribution by voluntary registry</p>
    </div>
</div>
""", unsafe_allow_html=True)

needed_cols = {"Country", "Voluntary_Registry", "Project ID"}
if df_sel.empty or not needed_cols.issubset(df_sel.columns):
    st.info("No data to display. Adjust your filters.")
else:
    # Pivot table: rows = Country, columns = Registry, values = Project count
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
    # Show the table
    # st.dataframe(four_blocks, use_container_width=True)
    # Which registry columns to map
    cases = ["VCS", "GOLD", "ACR", "CAR"]
    available = [c for c in cases if c in four_blocks.columns]
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
            width=600, height=500,
        )
        # PRD theme + auto-zoom
        fig.update_layout(
            margin=dict(t=40, r=10, b=10, l=10),
            paper_bgcolor="white",
            plot_bgcolor="white",
            font=dict(color="#1e293b")
        )
        fig.update_geos(fitbounds="locations", visible=False, bgcolor="white")
        return fig

    figs = [
        make_map(four_blocks, col, f"{col} projects in every country")
        for col in available
    ]
    # Arrange maps in a 2×2 grid
    row1_col1, row1_col2 = st.columns(2)
    with row1_col1:
        if len(figs) > 0:
            st.plotly_chart(figs[0], use_container_width=True)
    with row1_col2:
        if len(figs) > 1:
            st.plotly_chart(figs[1], use_container_width=True)
    row2_col1, row2_col2 = st.columns(2)
    with row2_col1:
        if len(figs) > 2:
            st.plotly_chart(figs[2], use_container_width=True)
    with row2_col2:
        if len(figs) > 3:
            st.plotly_chart(figs[3], use_container_width=True)
st.markdown('</div>', unsafe_allow_html=True) # Close final card
