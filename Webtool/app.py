# ============================================================================
# Streamlit Airbnb Dashboard - Main Application (Refactored)
# ============================================================================
"""
Interactive dashboard for analyzing Airbnb enrichment data.

Usage:
    streamlit run app.py
"""

import streamlit as st

# Import custom modules
from utils.state_manager import (
    discover_state_city_structure,
    load_city_data,
    check_location_match
)
from utils.data_loader import (
    load_enrichment_data,
    validate_enrichment_data,
    format_column_names,
    load_grid_coordinates,
    validate_grid_coordinates,
    preprocess_review_data
)
from utils.ui_components import (
    render_location_selector,
    render_filter_form,
    render_welcome_screen,
    render_filter_count
)
from utils.filters import apply_filters, get_filter_summary
from utils.map_renderer import render_map, render_map_caption


# ============================================================================
# PAGE CONFIGURATION
# ============================================================================

st.set_page_config(
    page_title="Airbnb Analytics Dashboard",
    page_icon="🏠",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items=None
)


# ============================================================================
# DATA LOADING FUNCTIONS
# ============================================================================

def load_data_for_location(selected_state: str, selected_city: str):
    """
    Load listing and grid data for the selected location.
    
    Args:
        selected_state: Selected state name
        selected_city: Selected city name
    """
    with st.spinner(f"🔄 Loading data for {selected_city}, {selected_state}..."):
        # Get file paths
        listing_file, grid_file = load_city_data(selected_state, selected_city)
        
        if not listing_file:
            st.error(f"No listing data found for {selected_city}, {selected_state}")
            return
        
        # Load and validate listing data
        df = load_enrichment_data(listing_file)
        if df is None:
            st.error("Failed to load listing data")
            return
        
        df = format_column_names(df)
        
        # Pre-parse review data for better performance
        df = preprocess_review_data(df)
        
        is_valid, message = validate_enrichment_data(df)
        
        if not is_valid:
            st.error(f"Data validation failed: {message}")
            st.info("Required columns: Room_id, Latitude, Longitude, Next_30_days_booked_days, 75_rule_met")
            return
        
        # Store in session state
        st.session_state['df'] = df
        st.session_state['loaded_state'] = selected_state
        st.session_state['loaded_city'] = selected_city
        st.session_state['location'] = f"{selected_city}, {selected_state}"
        st.success(f"✅ Loaded {len(df):,} listings for {selected_city}, {selected_state}")
    
    # Load grid data if available
    if grid_file:
        with st.spinner("📐 Loading grid coordinates..."):
            grid_df = load_grid_coordinates(grid_file)
            if grid_df is not None:
                is_valid, message = validate_grid_coordinates(grid_df)
                if is_valid:
                    st.session_state['grid_df'] = grid_df
                    st.success(f"✅ Loaded {len(grid_df)} grids")
                else:
                    st.warning(f"Grid validation failed: {message}")
                    st.session_state['grid_df'] = None
    else:
        st.session_state['grid_df'] = None
        st.info("No grid file found for this location")


# ============================================================================
# MAIN APP
# ============================================================================

def main():
    """Main application function"""
    
    # Header
    st.title("🏠 Airbnb Analytics")
    
    # ========================================================================
    # SIDEBAR: Location Selection
    # ========================================================================
    
    with st.sidebar:
        # Discover and render location selector
        structure = discover_state_city_structure()
        selected_state, selected_city, load_clicked = render_location_selector(structure)
        
        # Early return if no structure found
        if not structure:
            return
    
    # ========================================================================
    # Load Data (if button clicked)
    # ========================================================================
    
    if load_clicked:
        load_data_for_location(selected_state, selected_city)
    
    # ========================================================================
    # Check if we have data for current location
    # ========================================================================
    
    has_data = check_location_match(selected_state, selected_city)
    
    if not has_data:
        # Show welcome screen
        render_welcome_screen(selected_city, selected_state)
        return
    
    # ========================================================================
    # Data is loaded - Show dashboard
    # ========================================================================
    
    # Get data from session state
    df = st.session_state['df']
    location = st.session_state.get('location', 'Unknown')
    grid_df = st.session_state.get('grid_df', None)
    
    # Render filters in sidebar
    with st.sidebar:
        filter_result = render_filter_form(df)
        filter_criteria = filter_result['criteria']
        reset_clicked = filter_result['reset_clicked']
        
        # Handle reset
        if reset_clicked:
            st.rerun()
    
    # Apply filters
    filtered_df = apply_filters(df, filter_criteria)
    
    # Get filter summary
    filter_summary = get_filter_summary(df, filtered_df)
    
    # Count listings passing/failing filters
    if 'passes_current_filter' in filtered_df.columns:
        num_passing = filtered_df['passes_current_filter'].sum()
        num_failing = len(filtered_df) - num_passing
    else:
        num_passing = len(filtered_df)
        num_failing = 0
    
    # Warning if no matches
    if num_passing == 0:
        st.warning("⚠️ No listings match the current filter criteria")
    
    # Show grids checkbox
    show_grids = False
    if grid_df is not None:
        show_grids = st.checkbox("Show Grids", value=True)
    
    # ========================================================================
    # Render Map
    # ========================================================================
    
    success = render_map(
        filtered_df=filtered_df,
        original_df=df,
        grid_df=grid_df,
        show_grids=show_grids,
        filter_criteria=filter_criteria,
        location=location
    )
    
    # Show caption if map rendered successfully
    if success:
        render_map_caption(num_passing, num_failing, len(df))
    
    # ========================================================================
    # Sidebar: Filter Results
    # ========================================================================
    
    with st.sidebar:
        render_filter_count(num_passing, num_failing)


# ============================================================================
# RUN APP
# ============================================================================

if __name__ == "__main__":
    main()

