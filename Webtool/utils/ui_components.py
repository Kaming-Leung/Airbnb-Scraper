# ============================================================================
# UI Components Module
# ============================================================================
"""
Reusable UI components for the Streamlit dashboard.
"""

import streamlit as st
import pandas as pd
from typing import Dict, Any
from .filters import get_filter_ranges


def render_location_selector(structure: Dict[str, list]) -> tuple:
    """
    Render state and city selection dropdowns.
    
    Args:
        structure: Dictionary mapping states to cities
        
    Returns:
        Tuple of (selected_state, selected_city, load_clicked)
    """
    st.markdown("### 📍 Select Location")
    
    if not structure:
        st.warning("No data found in `data/States/` folder")
        st.info("Expected structure: `data/States/{state}/{city}/files.csv`")
        return None, None, False
    
    # State selection
    states = list(structure.keys())
    selected_state = st.selectbox(
        "State:",
        options=states,
        key="state_selector"
    )
    
    # City selection (based on selected state)
    if selected_state:
        cities = structure[selected_state]
        selected_city = st.selectbox(
            "City:",
            options=cities,
            key="city_selector"
        )
    else:
        selected_city = None
    
    # Load button
    load_clicked = False
    if selected_state and selected_city:
        if st.button("Load Data", type="primary", use_container_width=True):
            load_clicked = True
    
    return selected_state, selected_city, load_clicked


def render_filter_form(df: pd.DataFrame) -> Dict[str, Any]:
    """
    Render the filter form in the sidebar.
    
    Args:
        df: DataFrame with listing data
        
    Returns:
        Dictionary with filter criteria and button states
    """
    st.markdown("---")
    st.markdown("### 🎚️ Filters")
    
    # Get filter ranges
    filter_ranges = get_filter_ranges(df)
    
    # Wrap filters in a form to prevent auto-rerun
    with st.form("filter_form"):
        # Initialize filter criteria dictionary
        filter_criteria = {}
        
        # Filter: Min 30-day booked
        filter_criteria['min_30_day_booked'] = st.number_input(
            "Min 30-Day Booked",
            min_value=0,
            max_value=30,
            value=15,
            step=1
        )
        
        # Filter: Min 30-60 day booked
        if '60_day_booked' in filter_ranges:
            filter_criteria['min_60_day_booked'] = st.number_input(
                "Min 30-60 Day Booked",
                min_value=0,
                max_value=30,
                value=0,
                step=1
            )
        
        # Filter: Max missing months
        filter_criteria['max_missing_months'] = st.number_input(
            "Max Missing Review Months in 2025",
            min_value=0,
            max_value=12,
            value=0,
            step=1
        )
        
        # Filter: Bedrooms
        if 'Bedroom_count' in df.columns:
            col_bed1, col_bed2 = st.columns([3, 1])
            with col_bed1:
                filter_criteria['bedroom_count'] = st.number_input(
                    "Bedrooms",
                    min_value=0,
                    max_value=int(df['Bedroom_count'].max()) if not df['Bedroom_count'].isna().all() else 10,
                    value=0,
                    step=1,
                    key="bedroom_input"
                )
            with col_bed2:
                st.markdown("<br>", unsafe_allow_html=True)  # Add spacing
                filter_criteria['bedroom_gte'] = st.checkbox(
                    "≥",
                    value=True,
                    key="bedroom_gte",
                    help="Greater than or equal"
                )
        
        # Filter: Bathrooms
        if 'Bath_count' in df.columns:
            col_bath1, col_bath2 = st.columns([3, 1])
            with col_bath1:
                filter_criteria['bathroom_count'] = st.number_input(
                    "Bathrooms",
                    min_value=0,
                    max_value=int(df['Bath_count'].max()) if not df['Bath_count'].isna().all() else 10,
                    value=0,
                    step=1,
                    key="bathroom_input"
                )
            with col_bath2:
                st.markdown("<br>", unsafe_allow_html=True)  # Add spacing
                filter_criteria['bathroom_gte'] = st.checkbox(
                    "≥",
                    value=True,
                    key="bathroom_gte",
                    help="Greater than or equal"
                )
        
        # Filter: Only 75% rule
        filter_criteria['only_75_rule_passed'] = st.checkbox(
            "Only 75% Rule",
            value=False
        )
        
        # Filter: Grid selection
        if 'Grid_index' in df.columns:
            unique_grids = sorted(df['Grid_index'].dropna().unique())
            if len(unique_grids) > 0:
                selected_grids = st.multiselect(
                    "Select Grids",
                    options=unique_grids,
                    default=[]
                )
                filter_criteria['selected_grids'] = selected_grids
        
        # Submit buttons
        col1, col2 = st.columns(2)
        with col1:
            apply_clicked = st.form_submit_button("Apply", use_container_width=True)
        with col2:
            reset_clicked = st.form_submit_button("Reset", use_container_width=True)
    
    return {
        'criteria': filter_criteria,
        'apply_clicked': apply_clicked,
        'reset_clicked': reset_clicked
    }


def render_welcome_screen(selected_city: str, selected_state: str):
    """
    Render the welcome screen when no data is loaded.
    
    Args:
        selected_city: Currently selected city
        selected_state: Currently selected state
    """
    # Show appropriate message based on state
    if 'df' in st.session_state:
        # Data exists but doesn't match selected location
        st.info(f"📍 Click 'Load Data' to load listings for {selected_city}, {selected_state}")
    else:
        # No data loaded yet
        st.info("👈 Select a location and click 'Load Data' to get started")
    
    st.markdown("### 📋 Data Format")
    st.markdown("""
    Your CSV files should contain:
    - `Room_id` - Listing ID
    - `Latitude` / `Longitude` - GPS coordinates
    - `Next_30_days_booked_days` - Days booked (0-30)
    - `75_rule_met` - Boolean (True/False)
    - Optional: Grid coordinates in separate file
    """)


def render_filter_count(num_passing: int, num_failing: int):
    """
    Render the filter count in the sidebar.
    
    Args:
        num_passing: Number of listings passing filters
        num_failing: Number of listings failing filters
    """
    st.markdown("---")
    st.caption(f"🔴 {num_passing:,} pass | 🔵 {num_failing:,} fail")

