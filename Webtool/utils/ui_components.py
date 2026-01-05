# ============================================================================
# UI Components Module
# ============================================================================
"""
Reusable UI components for the Streamlit dashboard.
"""

import streamlit as st
import pandas as pd
from typing import Dict, Any, List
from .filters import get_filter_ranges
from .year_filter_helper import get_available_years, get_default_year_filters


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


def render_year_filters(df: pd.DataFrame) -> List[Dict[str, Any]]:
    """
    Render multiple year-based missing review month filters.
    
    Args:
        df: DataFrame with listing data
        
    Returns:
        List of year filter configurations
    """
    # Get available years from data
    available_years = get_available_years(df)
    
    if not available_years:
        st.caption("_No review data available_")
        return []
    
    # Initialize with default filters if not in session state
    if 'year_filter_count' not in st.session_state:
        st.session_state['year_filter_count'] = min(3, len(available_years))
    
    st.markdown("**Missing Review Months by Year**")
    
    year_filters = []
    
    # Render each year filter
    num_filters = st.session_state['year_filter_count']
    
    for i in range(num_filters):
        # Create three columns: checkbox, year, max_missing
        col1, col2, col3 = st.columns([0.5, 1.2, 1.2])
        
        with col1:
            enabled = st.checkbox(
                "✓",
                value=False,  # Disabled by default
                key=f"year_filter_enabled_{i}",
                label_visibility="collapsed",
                help="Enable this filter"
            )
        
        with col2:
            year = st.selectbox(
                "Year",
                options=available_years,
                index=min(i, len(available_years) - 1),
                key=f"year_filter_year_{i}",
                label_visibility="collapsed"
            )
        
        with col3:
            max_missing = st.number_input(
                "Max Missing",
                min_value=0,
                max_value=12,
                value = 0,
                # value=0 if i == 0 else 3,
                step=1,
                key=f"year_filter_max_{i}",
                label_visibility="collapsed"
            )
        
        year_filters.append({
            'year': year,
            'max_missing': max_missing,
            'enabled': enabled
        })
    
    return year_filters


def render_year_filter_buttons(df: pd.DataFrame):
    """
    Render add/remove buttons for year filters OUTSIDE the form.
    This prevents the buttons from triggering form submission.
    
    Args:
        df: DataFrame with listing data
    """
    # Get available years to check max limit
    available_years = get_available_years(df)
    
    if not available_years:
        return
    
    # Add/Remove buttons (OUTSIDE form)
    col_add, col_remove = st.columns(2)
    
    with col_add:
        if st.button("➕", help="Add year filter", use_container_width=True, key="add_year_filter"):
            if st.session_state.get('year_filter_count', 1) < len(available_years):
                st.session_state['year_filter_count'] = st.session_state.get('year_filter_count', 1) + 1
                st.rerun()
    
    with col_remove:
        if st.button("➖", help="Remove last filter", use_container_width=True, key="remove_year_filter"):
            if st.session_state.get('year_filter_count', 1) > 1:
                st.session_state['year_filter_count'] = st.session_state.get('year_filter_count', 1) - 1
                st.rerun()


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
    
    # Initialize filter criteria dictionary
    filter_criteria = {}
    
    # "Pass 75% Rule" checkbox OUTSIDE form for immediate effect
    # Initialize session state for the checkbox
    if 'pass_75_rule_checked' not in st.session_state:
        st.session_state.pass_75_rule_checked = False
    
    filter_criteria['only_75_rule_passed'] = st.checkbox(
        "Pass 75% Rule",
        value=st.session_state.pass_75_rule_checked,
        key="pass_75_rule_checkbox"
    )
    
    # Update session state
    st.session_state.pass_75_rule_checked = filter_criteria['only_75_rule_passed']
    
    # Determine default value based on checkbox state
    default_30_day_value = 22 if filter_criteria['only_75_rule_passed'] else 15
    
    # "Pass 55% Rule" checkbox OUTSIDE form for immediate effect
    # Initialize session state for the checkbox
    if 'pass_55_rule_checked' not in st.session_state:
        st.session_state.pass_55_rule_checked = False
    
    filter_criteria['only_55_rule_passed'] = st.checkbox(
        "Pass 55% Rule",
        value=st.session_state.pass_55_rule_checked,
        key="pass_55_rule_checkbox"
    )
    
    # Update session state
    st.session_state.pass_55_rule_checked = filter_criteria['only_55_rule_passed']
    
    # Determine default value based on checkbox state
    default_60_day_value = 17 if filter_criteria['only_55_rule_passed'] else 0
    
    # Wrap main filters in a form to prevent auto-rerun
    with st.form("filter_form"):
        # Submit buttons at the top
        col1, col2 = st.columns(2)
        with col1:
            apply_clicked = st.form_submit_button("Apply", use_container_width=True, type="primary")
        with col2:
            reset_clicked = st.form_submit_button("Reset", use_container_width=True)
        
        st.markdown("---")
        
        # Filter: Min 30-day booked
        filter_criteria['min_30_day_booked'] = st.number_input(
            "Min Days Booked (Next 30 days)",
            min_value=0,
            max_value=30,
            value=default_30_day_value,
            step=1,
            help="Automatically set to 22 when 'Pass 75% Rule' is checked"
        )
        
        # Filter: Min 30-60 day booked
        if '60_day_booked' in filter_ranges:
            filter_criteria['min_60_day_booked'] = st.number_input(
                "Min Days Booked (Next 30-60 days)",
                min_value=0,
                max_value=30,
                value=default_60_day_value,
                step=1,
                help="Automatically set to 17 when 'Pass 55% Rule' is checked"
            )
        
        st.markdown("---")
        
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
    
    # Year filters OUTSIDE the form so ➕/➖ buttons can be placed right after
    st.markdown("---")
    filter_criteria['year_filters'] = render_year_filters(df)
    
    # Render add/remove year filter buttons right after year filters
    render_year_filter_buttons(df)
    
    # Handle reset: clear both checkbox states
    if reset_clicked:
        st.session_state.pass_75_rule_checked = False
        st.session_state.pass_55_rule_checked = False
    
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

