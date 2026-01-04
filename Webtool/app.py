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
from utils.deck_map_renderer import render_deck_map_with_click_handling, get_selected_listing
from utils.listing_details import render_listing_detail_panel, render_empty_detail_panel


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
    
    # ========================================================================
    # Create Tabs
    # ========================================================================
    
    tab1, tab2 = st.tabs(["📍 Map", "🛏️ Bed/Bath Analysis"])
    
    # ========================================================================
    # TAB 1: Map
    # ========================================================================
    
    with tab1:
        # Show grids checkbox
        show_grids = False
        if grid_df is not None:
            show_grids = st.checkbox("Show Grids", value=True)
        
        # Render PyDeck Map with click handling
        event = render_deck_map_with_click_handling(
            df=filtered_df,
            grid_df=grid_df,
            show_grids=show_grids,
            location=location
        )
        
        # Show caption
        st.caption(f"🔴 {num_passing:,} pass | 🔵 {num_failing:,} fail | Total: {len(df):,}")
        
        # ====================================================================
        # Listing Detail Panel (below map)
        # ====================================================================
        
        st.markdown("---")

        
        # Check if we can use click events (Streamlit >= 1.33)
        if event is not None:
            # Extract selected listing from click event
            selected_listing = get_selected_listing(event, df)
            
            if selected_listing is not None:
                # Render detail panel for selected listing
                render_listing_detail_panel(selected_listing)
            else:
                # Show placeholder
                render_empty_detail_panel()
        else:
            # ====================================================================
            # WORKAROUND for Streamlit < 1.33: Manual Room ID Selection
            # ====================================================================
            st.markdown("### 📋 View Listing Details")
            
            # Get list of Room IDs from FILTERED data (sorted)
            available_room_ids = sorted(filtered_df['Room_id'].unique())
            
            st.markdown(f"**📊 {len(available_room_ids)} listings available** (based on current filters)")
            
            col1, col2 = st.columns([3, 1])
            
            with col1:
                # Manual selection with search
                selected_room_id = st.selectbox(
                    "Select Room ID:",
                    options=available_room_ids,
                    index=0,
                    key="manual_room_selector",
                    help="Select a Room ID from the dropdown to view details"
                )
            
            with col2:
                st.markdown("<br>", unsafe_allow_html=True)
                show_button = st.button("Show Details", type="primary")
            
            # Auto-show details when button clicked OR if already showing
            if show_button:
                st.session_state['show_details'] = True
                st.session_state['selected_room_id'] = selected_room_id
            
            # Show details
            if st.session_state.get('show_details', False):
                selected_room_id = st.session_state.get('selected_room_id', available_room_ids[0])
                
                # Update to current selection if changed
                if selected_room_id != st.session_state.get('last_selected_room_id'):
                    st.session_state['last_selected_room_id'] = selected_room_id
                
                # Find the listing in the full dataset (not filtered, to get all data)
                matching_rows = df[df['Room_id'] == selected_room_id]
                if not matching_rows.empty:
                    selected_listing = matching_rows.iloc[0]
                    st.markdown("---")
                    render_listing_detail_panel(selected_listing)
                else:
                    st.error(f"Room ID {selected_room_id} not found")
            else:
                st.markdown("---")
                st.caption("👆 Select a Room ID from the dropdown above and click **'Show Details'** to view full information")
    
    # ========================================================================
    # TAB 2: Bed/Bath Analysis
    # ========================================================================
    
    with tab2:
        st.info("🚧 Bed/Bath Analysis - Coming soon")
        st.write("This tab will show detailed analysis of bedrooms and bathrooms.")
    
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

