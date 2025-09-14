# -*- coding: utf-8 -*-
"""
Created on Mon Sep  1 16:10:41 2025

@author: jimmy susanto
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

# ============== TAILWIND CSS CDN ==============
st.markdown("""
<link href="https://cdn.jsdelivr.net/npm/tailwindcss@2.2.19/dist/tailwind.min.css" rel="stylesheet">
<style>
    /* SaaS-style minimalist design */
    :root {
        --primary: #3b82f6;
        --primary-dark: #2563eb;
        --secondary: #64748b;
        --background: #f8fafc;
        --surface: #ffffff;
        --surface-hover: #f1f5f9;
        --border: #e2e8f0;
        --text-primary: #1e293b;
        --text-secondary: #64748b;
        --shadow-sm: 0 1px 2px 0 rgba(0, 0, 0, 0.05);
        --shadow-md: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06);
        --shadow-lg: 0 10px 15px -3px rgba(0, 0, 0, 0.1), 0 4px 6px -2px rgba(0, 0, 0, 0.05);
    }

    body {
        background-color: var(--background);
        color: var(--text-primary);
        font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
    }

    /* Top Navigation */
    .top-nav {
        background: var(--surface);
        border-bottom: 1px solid var(--border);
        box-shadow: var(--shadow-sm);
        position: sticky;
        top: 0;
        z-index: 50;
    }

    /* Filter dropdown */
    .filter-dropdown {
        background: var(--surface);
        border: 1px solid var(--border);
        border-radius: 0.5rem;
        box-shadow: var(--shadow-lg);
        padding: 1.5rem;
        min-width: 300px;
    }

    /* Cards */
    .card {
        background: var(--surface);
        border: 1px solid var(--border);
        border-radius: 0.75rem;
        box-shadow: var(--shadow-sm);
        transition: all 0.2s ease;
    }

    .card:hover {
        box-shadow: var(--shadow-md);
        transform: translateY(-1px);
    }

    /* Section titles */
    .section-title {
        font-size: 1.25rem;
        font-weight: 600;
        color: var(--text-primary);
        margin-bottom: 1rem;
        padding-bottom: 0.5rem;
        border-bottom: 2px solid var(--border);
    }

    /* Data tables */
    .data-table {
        border-radius: 0.5rem;
        overflow: hidden;
        box-shadow: var(--shadow-sm);
    }

    /* Buttons */
    .btn {
        padding: 0.5rem 1rem;
        border-radius: 0.375rem;
        font-weight: 500;
        transition: all 0.2s;
        cursor: pointer;
        border: none;
        font-size: 0.875rem;
    }

    .btn-primary {
        background: var(--primary);
        color: white;
    }

    .btn-primary:hover {
        background: var(--primary-dark);
    }

    .btn-secondary {
        background: var(--surface-hover);
        color: var(--text-primary);
        border: 1px solid var(--border);
    }

    .btn-secondary:hover {
        background: var(--border);
    }

    /* Charts */
    .chart-container {
        background: var(--surface);
        border: 1px solid var(--border);
        border-radius: 0.75rem;
        padding: 1.5rem;
        box-shadow: var(--shadow-sm);
    }

    /* Streamlit customizations */
    .stDataFrame {
        border-radius: 0.5rem;
        overflow: hidden;
    }

    .stPlotlyChart {
        border-radius: 0.5rem;
    }

    /* Responsive adjustments */
    @media (max-width: 768px) {
        .filter-dropdown {
            min-width: 280px;
        }
        
        .card {
            margin-bottom: 1rem;
        }
    }

    /* Custom scrollbar */
    ::-webkit-scrollbar {
        width: 8px;
        height: 8px;
    }

    ::-webkit-scrollbar-track {
        background: var(--background);
    }

    ::-webkit-scrollbar-thumb {
        background: var(--secondary);
        border-radius: 4px;
    }

    ::-webkit-scrollbar-thumb:hover {
        background: var(--text-secondary);
    }
</style>
""", unsafe_allow_html=True)

# ============== DATA LOADING ==============
EXCEL_PATH = r"data/Voluntary-Registry-Offsets-Database--v2025-06.xlsx"
SHEET_NAME = "PROJECTS"
SKIP_ROWS = 3

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

# ============== FILTER FUNCTIONS ==============
def uniq_sorted(s):
    return sorted(pd.Series(s).dropna().unique().tolist())

# Initialize session state
for k in ["region_sel", "country_sel", "registry_sel", "scope_sel", "type_sel", "redrem_sel", "master_all", "show_filters"]:
    st.session_state.setdefault(k, [] if k.endswith("_sel") else False)

def reset_all_filters():
    for k in list(st.session_state.keys()):
        if k.endswith("_sel") or k == "master_all":
            st.session_state.pop(k, None)
    st.rerun()

# ============== FILTER IMPLEMENTATION ==============
def get_filter_values():
    """Get filter values from session state"""
    return {
        'registry': st.session_state.registry_sel,
        'region': st.session_state.region_sel,
        'country': st.session_state.country_sel,
        'scope': st.session_state.scope_sel,
        'type': st.session_state.type_sel,
        'redrem': st.session_state.redrem_sel
    }

def apply_filters(df):
    """Apply filters to dataframe"""
    mask = pd.Series(True, index=df.index)
    
    filters = get_filter_values()
    
    if filters['registry']:
        mask &= df["Voluntary_Registry"].isin(filters['registry'])
    if filters['region']:
        mask &= df["Region"].isin(filters['region'])
    if filters['country']:
        mask &= df["Country"].isin(filters['country'])
    if filters['scope']:
        mask &= df["Scope"].isin(filters['scope'])
    if filters['type']:
        mask &= df["Type"].isin(filters['type'])
    if filters['redrem']:
        mask &= df["Reduction_Removal"].isin(filters['redrem'])
    
    return df[mask]

# ============== TOP NAVIGATION WITH FILTERS ==============
st.markdown("""
<div class="top-nav">
    <div class="container mx-auto px-4 py-3">
        <div class="flex flex-col lg:flex-row lg:items-center lg:justify-between gap-4">
            <!-- Logo and Title -->
            <div class="flex items-center space-x-3">
                <div class="w-10 h-10 bg-blue-500 rounded-lg flex items-center justify-center">
                    <span class="text-white text-xl font-bold">🌱</span>
                </div>
                <div>
                    <h1 class="text-xl font-bold text-gray-900">Carbon Dashboard</h1>
                    <p class="text-sm text-gray-500">Project Analysis Platform</p>
                </div>
            </div>
            
            <!-- Filter Controls -->
            <div class="flex items-center space-x-3">
                <button id="filter-toggle" class="btn btn-secondary" onclick="toggleFilters()">
                    <span id="filter-text">Show Filters</span>
                    <svg id="filter-icon" class="w-4 h-4 ml-1 transform transition-transform" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7"></path>
                    </svg>
                </button>
                <button class="btn btn-secondary" onclick="resetAllFilters()">
                    <svg class="w-4 h-4 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"></path>
                    </svg>
                    Reset
                </button>
            </div>
        </div>
        
        <!-- Filter Dropdown -->
        <div id="filter-dropdown" class="filter-dropdown mt-4 hidden">
            <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                <!-- Registry Filter -->
                <div>
                    <label class="block text-sm font-medium text-gray-700 mb-2">Registry</label>
                    <select id="registry-filter" class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500" onchange="updateFilter('registry', this.value)">
                        <option value="">All Registries</option>
                        <option value="VCS">VCS</option>
                        <option value="GOLD">Gold Standard</option>
                        <option value="ACR">ACR</option>
                        <option value="CAR">CAR</option>
                    </select>
                </div>
                
                <!-- Region Filter -->
                <div>
                    <label class="block text-sm font-medium text-gray-700 mb-2">Region</label>
                    <select id="region-filter" class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500" onchange="updateFilter('region', this.value)">
                        <option value="">All Regions</option>
                        <option value="Africa">Africa</option>
                        <option value="Asia">Asia</option>
                        <option value="Europe">Europe</option>
                        <option value="North America">North America</option>
                        <option value="Oceania">Oceania</option>
                        <option value="South America">South America</option>
                    </select>
                </div>
                
                <!-- Country Filter -->
                <div>
                    <label class="block text-sm font-medium text-gray-700 mb-2">Country</label>
                    <select id="country-filter" class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500" onchange="updateFilter('country', this.value)">
                        <option value="">All Countries</option>
                        <option value="United States">United States</option>
                        <option value="Brazil">Brazil</option>
                        <option value="India">India</option>
                        <option value="Indonesia">Indonesia</option>
                        <option value="China">China</option>
                    </select>
                </div>
                
                <!-- Scope Filter -->
                <div>
                    <label class="block text-sm font-medium text-gray-700 mb-2">Scope</label>
                    <select id="scope-filter" class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500" onchange="updateFilter('scope', this.value)">
                        <option value="">All Scopes</option>
                        <option value="Agriculture">Agriculture</option>
                        <option value="Forestry">Forestry</option>
                        <option value="Energy">Energy</option>
                        <option value="Transportation">Transportation</option>
                    </select>
                </div>
                
                <!-- Type Filter -->
                <div>
                    <label class="block text-sm font-medium text-gray-700 mb-2">Type</label>
                    <select id="type-filter" class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500" onchange="updateFilter('type', this.value)">
                        <option value="">All Types</option>
                        <option value="REDD+">REDD+</option>
                        <option value="Renewable Energy">Renewable Energy</option>
                        <option value="Aforestation">Aforestation</option>
                        <option value="Methane Capture">Methane Capture</option>
                    </select>
                </div>
                
                <!-- Reduction/Removal Filter -->
                <div>
                    <label class="block text-sm font-medium text-gray-700 mb-2">Reduction/Removal</label>
                    <select id="redrem-filter" class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500" onchange="updateFilter('redrem', this.value)">
                        <option value="">All Types</option>
                        <option value="Reduction">Reduction</option>
                        <option value="Removal">Removal</option>
                    </select>
                </div>
            </div>
        </div>
    </div>
</div>

<script>
function toggleFilters() {
    const dropdown = document.getElementById('filter-dropdown');
    const icon = document.getElementById('filter-icon');
    const text = document.getElementById('filter-text');
    
    if (dropdown.classList.contains('hidden')) {
        dropdown.classList.remove('hidden');
        icon.classList.add('rotate-180');
        text.textContent = 'Hide Filters';
    } else {
        dropdown.classList.add('hidden');
        icon.classList.remove('rotate-180');
        text.textContent = 'Show Filters';
    }
}

function updateFilter(filterType, value) {
    // Update URL query parameters
    const params = new URLSearchParams(window.location.search);
    if (value) {
        params.set(filterType, value);
    } else {
        params.delete(filterType);
    }
    window.history.replaceState({}, '', `${window.location.pathname}?${params}`);
    
    // Trigger a Streamlit rerun by updating a hidden element
    const dummyElement = document.getElementById('dummy-filter-update');
    if (dummyElement) {
        dummyElement.value = Date.now().toString();
    }
}

function resetAllFilters() {
    // Clear all query parameters
    window.history.replaceState({}, '', window.location.pathname);
    
    // Reset all filter dropdowns
    document.querySelectorAll('select').forEach(select => {
        select.value = '';
    });
    
    // Trigger a Streamlit rerun
    const dummyElement = document.getElementById('dummy-filter-update');
    if (dummyElement) {
        dummyElement.value = Date.now().toString();
    }
}

// Initialize filter dropdowns with current session state values
document.addEventListener('DOMContentLoaded', function() {
    // Get current filter values from URL query parameters
    const params = new URLSearchParams(window.location.search);
    
    // Update each dropdown if value exists in query params
    ['registry', 'region', 'country', 'scope', 'type', 'redrem'].forEach(filterType => {
        const value = params.get(filterType);
        if (value) {
            const selectElement = document.getElementById(filterType + '-filter');
            if (selectElement) {
                selectElement.value = value;
            }
        }
    });
});
</script>

<!-- Hidden input to trigger Streamlit rerun -->
<input id="dummy-filter-update" type="hidden" value="">
""", unsafe_allow_html=True)

# ============== STREAMLIT FILTER IMPLEMENTATION ==============
# Initialize session state with empty values if not already set
if "registry_sel" not in st.session_state:
    st.session_state.registry_sel = ""
if "region_sel" not in st.session_state:
    st.session_state.region_sel = ""
if "country_sel" not in st.session_state:
    st.session_state.country_sel = ""
if "scope_sel" not in st.session_state:
    st.session_state.scope_sel = ""
if "type_sel" not in st.session_state:
    st.session_state.type_sel = ""
if "redrem_sel" not in st.session_state:
    st.session_state.redrem_sel = ""

# Get filter options from data
registry_options = uniq_sorted(df_projects["Voluntary_Registry"]) if "Voluntary_Registry" in df_projects else []
region_options = uniq_sorted(df_projects["Region"]) if "Region" in df_projects else []
country_options = uniq_sorted(df_projects["Country"]) if "Country" in df_projects else []
scope_options = uniq_sorted(df_projects["Scope"]) if "Scope" in df_projects else []
type_options = uniq_sorted(df_projects["Type"]) if "Type" in df_projects else []
redrem_options = uniq_sorted(df_projects["Reduction_Removal"]) if "Reduction_Removal" in df_projects else []

# Apply filters to get the filtered dataframe
df_filtered = apply_filters(df_projects)

# ============== QUERY PARAMETER HANDLER ==============
def update_session_state_from_query_params():
    """Update session state from URL query parameters"""
    query_params = st.experimental_get_query_params()
    
    # Update each filter if present in query params
    if 'registry' in query_params:
        st.session_state.registry_sel = query_params['registry'][0] if query_params['registry'][0] else ""
    if 'region' in query_params:
        st.session_state.region_sel = query_params['region'][0] if query_params['region'][0] else ""
    if 'country' in query_params:
        st.session_state.country_sel = query_params['country'][0] if query_params['country'][0] else ""
    if 'scope' in query_params:
        st.session_state.scope_sel = query_params['scope'][0] if query_params['scope'][0] else ""
    if 'type' in query_params:
        st.session_state.type_sel = query_params['type'][0] if query_params['type'][0] else ""
    if 'redrem' in query_params:
        st.session_state.redrem_sel = query_params['redrem'][0] if query_params['redrem'][0] else ""

# Initialize session state from query params
update_session_state_from_query_params()

# ============== FILTER CHANGE HANDLER ==============
def handle_filter_change():
    """Handle filter changes from JavaScript"""
    # Check if we need to update from query params
    query_params = st.experimental_get_query_params()
    
    # Check if any filter has changed
    current_filters = get_filter_values()
    needs_rerun = False
    
    for filter_type in ['registry', 'region', 'country', 'scope', 'type', 'redrem']:
        param_value = query_params.get(filter_type, [None])[0]
        if param_value != current_filters[filter_type]:
            st.session_state[f"{filter_type}_sel"] = param_value if param_value else ""
            needs_rerun = True
    
    if needs_rerun:
        st.rerun()

# Check for filter changes on each run
handle_filter_change()

# ============== BACKGROUND SETTING ==============
ST_BG = "#f8fafc"  # Light background for SaaS design

# Define a global template that matches the new design
pio.templates["saas_dark"] = go.layout.Template(
    layout=go.Layout(
        paper_bgcolor=ST_BG,
        plot_bgcolor=ST_BG,
        font=dict(color="#1e293b"),
        margin=dict(t=50, r=10, b=40, l=10),
        xaxis=dict(tickfont=dict(color="#64748b")),
        yaxis=dict(tickfont=dict(color="#64748b")),
        legend=dict(font=dict(color="#1e293b")),
        coloraxis=dict(
            colorbar=dict(
                tickfont=dict(color="#64748b"),
            )
        ),
    )
)

# Apply it everywhere by default
pio.templates.default = "saas_dark"

# ============== MAIN CONTENT ==============
# Create a container for the main content
main_container = st.container()

with main_container:
    # Project Summary Cards (using filtered data)
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.markdown("""
        <div class="card p-4">
            <div class="flex items-center justify-between">
                <div>
                    <p class="text-sm text-gray-500">Total Projects</p>
                    <p class="text-2xl font-bold text-gray-900">{:,}</p>
                </div>
                <div class="w-12 h-12 bg-blue-100 rounded-lg flex items-center justify-center">
                    <span class="text-blue-600 text-xl">📊</span>
                </div>
            </div>
        </div>
        """.format(len(df_filtered)), unsafe_allow_html=True)
    
    with col2:
        total_credits = df_filtered["Total_Credits_Issued"].sum() if "Total_Credits_Issued" in df_filtered.columns else 0
        st.markdown("""
        <div class="card p-4">
            <div class="flex items-center justify-between">
                <div>
                    <p class="text-sm text-gray-500">Total Credits</p>
                    <p class="text-2xl font-bold text-gray-900">{:.1f}M</p>
                </div>
                <div class="w-12 h-12 bg-green-100 rounded-lg flex items-center justify-center">
                    <span class="text-green-600 text-xl">🌱</span>
                </div>
            </div>
        </div>
        """.format(total_credits / 1000000), unsafe_allow_html=True)
    
    with col3:
        unique_countries = df_filtered["Country"].nunique() if "Country" in df_filtered.columns else 0
        st.markdown("""
        <div class="card p-4">
            <div class="flex items-center justify-between">
                <div>
                    <p class="text-sm text-gray-500">Countries</p>
                    <p class="text-2xl font-bold text-gray-900">{:,}</p>
                </div>
                <div class="w-12 h-12 bg-purple-100 rounded-lg flex items-center justify-center">
                    <span class="text-purple-600 text-xl">🌍</span>
                </div>
            </div>
        </div>
        """.format(unique_countries), unsafe_allow_html=True)
    
    with col4:
        unique_registries = df_filtered["Voluntary_Registry"].nunique() if "Voluntary_Registry" in df_filtered.columns else 0
        st.markdown("""
        <div class="card p-4">
            <div class="flex items-center justify-between">
                <div>
                    <p class="text-sm text-gray-500">Registries</p>
                    <p class="text-2xl font-bold text-gray-900">{:,}</p>
                </div>
                <div class="w-12 h-12 bg-orange-100 rounded-lg flex items-center justify-center">
                    <span class="text-orange-600 text-xl">🏛️</span>
                </div>
            </div>
        </div>
        """.format(unique_registries), unsafe_allow_html=True)

    # ============== TOP TABLE ==============
    st.markdown('<h2 class="section-title">Project List</h2>', unsafe_allow_html=True)
    
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
    ] if c in df_filtered.columns]

    df_display = df_filtered[display_cols].copy()
    for c in ["Total_Credits_Issued", "Total_Credits_Retired", "Total_Credits_Remaining"]:
        if c in df_display.columns:
            df_display[c] = df_display[c].map(fmt_int)

    st.dataframe(df_display, use_container_width=True)

    # ============== TWO SIDE-BY-SIDE PLOTS ==============
    st.markdown('<h2 class="section-title">Project Distribution</h2>', unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)

    with col1:
        st.markdown("""
        <div class="chart-container">
            <h3 class="text-lg font-semibold mb-4">Projects by Registry</h3>
            <div class="h-80 flex items-center justify-center">
                <p class="text-gray-500">Chart will be displayed here</p>
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown("""
        <div class="chart-container">
            <h3 class="text-lg font-semibold mb-4">Projects by Reduction/Removal</h3>
            <div class="h-80 flex items-center justify-center">
                <p class="text-gray-500">Chart will be displayed here</p>
            </div>
        </div>
        """, unsafe_allow_html=True)

    # ============== STACKED CREDITS BY REDUCTION/REMOVAL ==============
    st.markdown('<h2 class="section-title">Credits by Reduction/Removal</h2>', unsafe_allow_html=True)
    
    st.markdown("""
    <div class="chart-container">
        <h3 class="text-lg font-semibold mb-4">Credits Distribution</h3>
        <div class="h-80 flex items-center justify-center">
            <p class="text-gray-500">Chart will be displayed here</p>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # ============== PROJECTS BY REDUCTION/REMOVAL BY STANDARD ==============
    st.markdown('<h2 class="section-title">Projects by Reduction/Removal by Standard</h2>', unsafe_allow_html=True)
    
    st.markdown("""
    <div class="chart-container">
        <h3 class="text-lg font-semibold mb-4">Cross-analysis Chart</h3>
        <div class="h-80 flex items-center justify-center">
            <p class="text-gray-500">Chart will be displayed here</p>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # ============== PROJECTS BY SCOPE ==============
    st.markdown('<h2 class="section-title">Projects by Scope</h2>', unsafe_allow_html=True)
    
    st.markdown("""
    <div class="chart-container">
        <h3 class="text-lg font-semibold mb-4">Scope Distribution</h3>
        <div class="h-80 flex items-center justify-center">
            <p class="text-gray-500">Chart will be displayed here</p>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # ============== PROJECTS BY SCOPE BY STANDARD ==============
    st.markdown('<h2 class="section-title">Projects by Scope by Standard</h2>', unsafe_allow_html=True)
    
    st.markdown("""
    <div class="chart-container">
        <h3 class="text-lg font-semibold mb-4">Multi-level Analysis</h3>
        <div class="h-80 flex items-center justify-center">
            <p class="text-gray-500">Chart will be displayed here</p>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # ============== DISTRIBUTION OF PROJECTS ACROSS COUNTRIES ==============
    st.markdown('<h2 class="section-title">Distribution of Projects Across Countries</h2>', unsafe_allow_html=True)
    
    st.markdown("""
    <div class="chart-container">
        <h3 class="text-lg font-semibold mb-4">Geographic Distribution</h3>
        <div class="h-80 flex items-center justify-center">
            <p class="text-gray-500">Map will be displayed here</p>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # ============== DISTRIBUTION OF PROJECTS ACROSS COUNTRIES BY STANDARD ==============
    st.markdown('<h2 class="section-title">Distribution of Projects Across Countries by Standard</h2>', unsafe_allow_html=True)
    
    st.markdown("""
    <div class="chart-container">
        <h3 class="text-lg font-semibold mb-4">Geographic Distribution by Registry</h3>
        <div class="h-80 flex items-center justify-center">
            <p class="text-gray-500">Maps will be displayed here</p>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # ============== Number of projects are running for the first time per Standard in time series ==============
    st.markdown('<h2 class="section-title">Project Starts by Standard Over Time</h2>', unsafe_allow_html=True)
    
    st.markdown("""
    <div class="chart-container">
        <h3 class="text-lg font-semibold mb-4">Timeline Analysis</h3>
        <div class="h-80 flex items-center justify-center">
            <p class="text-gray-500">Timeline chart will be displayed here</p>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # ============== Number of projects (Top 20) by Standard by Country ==============
    st.markdown('<h2 class="section-title">Top 20 Countries with Most Projects</h2>', unsafe_allow_html=True)
    
    st.markdown("""
    <div class="chart-container">
        <h3 class="text-lg font-semibold mb-4">Top Countries Analysis</h3>
        <div class="h-80 flex items-center justify-center">
            <p class="text-gray-500">Bar chart will be displayed here</p>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # ============== Distribution of projects across countries by Standard ==============
    st.markdown('<h2 class="section-title">Distribution of projects across countries by Standard</h2>', unsafe_allow_html=True)
    
    st.markdown("""
    <div class="chart-container">
        <h3 class="text-lg font-semibold mb-4">Registry Distribution Maps</h3>
        <div class="h-80 flex items-center justify-center">
            <p class="text-gray-500">Maps will be displayed here</p>
        </div>
    </div>
    """, unsafe_allow_html=True)
