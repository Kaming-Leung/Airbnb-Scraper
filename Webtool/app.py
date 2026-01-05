# ============================================================================
# Streamlit Airbnb Dashboard - Main Application (Refactored)
# ============================================================================
"""
Interactive dashboard for analyzing Airbnb enrichment data.

Usage:
    streamlit run app.py
"""

import streamlit as st
import pandas as pd

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

# # Custom CSS for dataframe hover highlighting
# st.markdown("""
# <style>
#     /* Light blue hover for dataframe rows */
#     .stDataFrame tbody tr:hover {
#         background-color: #E3F2FD !important;  /* Light blue */
#     }
    
#     /* Also apply to the cells within the hovered row */
#     .stDataFrame tbody tr:hover td {
#         background-color: #E3F2FD !important;  /* Light blue */
#     }
# </style>
# """, unsafe_allow_html=True)


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
    
    tab1, tab2, tab3 = st.tabs(["📍 Map", "📊 Table", "🛏️ Bed/Bath Analysis"])
    
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
        st.markdown("### 📋 Selected Listing Details")
        
        # Debug output
        if event:
            selection = event.get('selection', {})
            if selection and 'objects' in selection and 'listings' in selection.get('objects', {}):
                clicked_objects = selection['objects']['listings']
        
        # Check if we can use click events (Streamlit >= 1.33)
        if event is not None:
            
            # Extract selected listing from click event
            # CRITICAL: Search in filtered_df (same data used to create the map!)
            selected_listing = get_selected_listing(event, filtered_df)
            
            if selected_listing is not None:
                # Store Room ID in session state for reference
                room_id = selected_listing.get('Room_id')
                st.session_state['clicked_room_id'] = room_id
                                
                st.success(f"✅ Clicked on Room #{room_id} from map")
                
                # Render detail panel for selected listing
                render_listing_detail_panel(selected_listing)
            else:
                # Failed to extract or match listing
                print("❌ get_selected_listing returned None - listing not found or event invalid")
                
                st.error("⚠️ Could not load details for the clicked listing. Please try clicking again.")
                st.warning("💡 **Tip**: If this keeps happening, try resetting filters or reloading the data.")
                
                # Check if we have a previously clicked Room ID
                if 'clicked_room_id' in st.session_state:
                    prev_room_id = st.session_state['clicked_room_id']
                    st.info(f"💡 Last successfully selected: Room #{prev_room_id}")
                
                # Show debug info
                with st.expander("🔧 Debug Information"):
                    if event and 'selection' in event:
                        sel_objects = event.get('selection', {}).get('objects', {}).get('listings', [])
                        if sel_objects:
                            clicked_room_id = sel_objects[0].get('Room_id')
                            st.write(f"**Clicked Room_id**: {clicked_room_id}")
                    
                    st.write(f"**Total rows in full dataset**: {len(df)}")
                    st.write(f"**Filtered rows displayed on map**: {len(filtered_df)}")
                    
                    if 'Room_id' in filtered_df.columns:
                        st.write(f"**Room_id column type**: {filtered_df['Room_id'].dtype}")
                        st.write(f"**Sample Room_ids from map data**: {filtered_df['Room_id'].head(5).tolist()}")
                    
                    st.write("**Full event data**:", event)
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
    # TAB 2: Table View
    # ========================================================================
    
    with tab2:
        st.markdown("## 📊 Data Table")
        
        # Get filtered data (respecting current filters)
        table_df = filtered_df[filtered_df['passes_current_filter'] == True].copy()

        table_df = table_df[['Listing_url', 'Next_30_days_booked_days', 'Next_30_to_60_days_booked_days', '75_rule_met', '55_rule_met', 'Rating', 'Review_count', 'Guest_count', 'Bedroom_count', 'Bath_count', 'Is_superhost']]
        table_df.reset_index(drop=True, inplace=True)
        
        # Pagination settings
        ROWS_PER_PAGE = 70
        total_rows = len(table_df)
        total_pages = (total_rows + ROWS_PER_PAGE - 1) // ROWS_PER_PAGE  # Ceiling division
        
        # Initialize pagination state
        if 'table_page' not in st.session_state:
            st.session_state.table_page = 1
        
        # Ensure current page is within valid range
        if st.session_state.table_page > total_pages and total_pages > 0:
            st.session_state.table_page = total_pages
        if st.session_state.table_page < 1:
            st.session_state.table_page = 1
        
        # Display summary info
        col1, col2, col3 = st.columns([2, 2, 3])
        
        with col1:
            st.metric("Total Rows", f"{total_rows:,}")
        
        with col2:
            st.metric("Total Columns", len(table_df.columns))
        
        with col3:
            if total_pages > 1:
                st.info(f"📄 Page {st.session_state.table_page} of {total_pages}")
            else:
                st.info(f"📄 Showing all rows")
        
        # Calculate start and end indices for current page
        start_idx = (st.session_state.table_page - 1) * ROWS_PER_PAGE
        end_idx = min(start_idx + ROWS_PER_PAGE, total_rows)
        
        # Get current page data
        if total_rows > 0:
            current_page_df = table_df.iloc[start_idx:end_idx]
            
            st.caption(f"Showing rows {start_idx + 1} to {end_idx} of {total_rows:,}")
            
            # Display table with horizontal scrolling and sticky headers
            st.dataframe(
                current_page_df,
                width='stretch',  # Full width with horizontal scroll
                height=600,  # Fixed height enables vertical scroll with sticky headers
                hide_index=False,  # Hide row index
                column_config={
                    "Listing_url": st.column_config.LinkColumn(
                        "Listing URL",
                        help="Click to open listing on Airbnb",
                        display_text="🔗 View Listing"
                    )
                }
            )
        else:
            st.warning("⚠️ No data to display. Adjust your filters to see results.")
        
        # Pagination controls (only show if more than one page)
        if total_pages > 1:
            st.markdown("---")
            
            col1, col2, col3, col4, col5 = st.columns([1, 1, 2, 1, 1])
            
            with col1:
                if st.button("⏮️ First", disabled=(st.session_state.table_page == 1)):
                    st.session_state.table_page = 1
                    st.rerun()
            
            with col2:
                if st.button("◀️ Previous", disabled=(st.session_state.table_page == 1)):
                    st.session_state.table_page -= 1
                    st.rerun()
            
            with col3:
                # Page input for direct navigation
                page_input = st.number_input(
                    "Go to page:",
                    min_value=1,
                    max_value=total_pages,
                    value=st.session_state.table_page,
                    step=1,
                    key="page_input"
                )
                if page_input != st.session_state.table_page:
                    st.session_state.table_page = page_input
                    st.rerun()
            
            with col4:
                if st.button("Next ▶️", disabled=(st.session_state.table_page == total_pages)):
                    st.session_state.table_page += 1
                    st.rerun()
            
            with col5:
                if st.button("Last ⏭️", disabled=(st.session_state.table_page == total_pages)):
                    st.session_state.table_page = total_pages
                    st.rerun()
    
    # ========================================================================
    # TAB 3: Bed/Bath Analysis
    # ========================================================================
    
    with tab3:
        st.markdown("## 🛏️ Bedroom & Bathroom Analysis")

        df_filter_true = filtered_df[filtered_df['passes_current_filter'] == True]
        
        # Check if required columns exist
        if 'Bedroom_count' not in df.columns or 'Bath_count' not in df.columns:
            st.warning("⚠️ Bedroom or Bathroom data not available in this dataset")
        else:
            # ================================================================
            # BEDROOM ANALYSIS
            # ================================================================
            st.markdown("### 🛏️ Bedroom Distribution")
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("#### Filtered Listings")
                st.caption(f"Showing {len(filtered_df):,} listings that match filter criteria")
                
                # Calculate bedroom distribution for filtered data
                bedroom_filtered = df_filter_true['Bedroom_count'].value_counts().sort_index()
                bedroom_filtered_df = pd.DataFrame({
                    'Bedrooms': bedroom_filtered.index,
                    'Count': bedroom_filtered.values
                })
                
                st.dataframe(
                    bedroom_filtered_df,
                    width='stretch',
                    hide_index=True
                )
                
                # Summary stats
                st.caption(f"📊 **Total filtered listings**: {len(df_filter_true):,}")
                st.caption(f"📊 **Most common**: {bedroom_filtered.idxmax()} bedroom(s) ({bedroom_filtered.max():,} listings)")
            
            with col2:
                st.markdown("#### All Listings in Area")
                st.caption(f"Showing all {len(df):,} listings in the dataset")
                
                # Calculate bedroom distribution for all data
                bedroom_all = df['Bedroom_count'].value_counts().sort_index()
                bedroom_all_df = pd.DataFrame({
                    'Bedrooms': bedroom_all.index,
                    'Count': bedroom_all.values
                })
                
                st.dataframe(
                    bedroom_all_df,
                    width='stretch',
                    hide_index=True
                )
                
                # Summary stats
                st.caption(f"📊 **Total area listings**: {len(df):,}")
                st.caption(f"📊 **Most common**: {bedroom_all.idxmax()} bedroom(s) ({bedroom_all.max():,} listings)")
            
            st.markdown("---")
            
            # ================================================================
            # BATHROOM ANALYSIS
            # ================================================================
            st.markdown("### 🚿 Bathroom Distribution")
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("#### Filtered Listings")
                st.caption(f"Showing {len(df_filter_true):,} listings that match filter criteria")
                
                # Calculate bathroom distribution for filtered data
                bathroom_filtered = df_filter_true['Bath_count'].value_counts().sort_index()
                bathroom_filtered_df = pd.DataFrame({
                    'Bathrooms': bathroom_filtered.index,
                    'Count': bathroom_filtered.values
                })
                
                st.dataframe(
                    bathroom_filtered_df,
                    width='stretch',
                    hide_index=True
                )
                
                # Summary stats
                st.caption(f"📊 **Total filtered listings**: {len(filtered_df):,}")
                st.caption(f"📊 **Most common**: {bathroom_filtered.idxmax()} bathroom(s) ({bathroom_filtered.max():,} listings)")
            
            with col2:
                st.markdown("#### All Listings in Area")
                st.caption(f"Showing all {len(df):,} listings in the dataset")
                
                # Calculate bathroom distribution for all data
                bathroom_all = df['Bath_count'].value_counts().sort_index()
                bathroom_all_df = pd.DataFrame({
                    'Bathrooms': bathroom_all.index,
                    'Count': bathroom_all.values
                })
                
                st.dataframe(
                    bathroom_all_df,
                    width='stretch',
                    hide_index=True
                )
                
                # Summary stats
                st.caption(f"📊 **Total area listings**: {len(df):,}")
                st.caption(f"📊 **Most common**: {bathroom_all.idxmax()} bathroom(s) ({bathroom_all.max():,} listings)")
            
            st.markdown("---")
            
            # ================================================================
            # BEDROOM x BATHROOM CROSS-TABULATION
            # ================================================================
            st.markdown("### 🛏️🚿 Bedroom × Bathroom Combination")
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("#### Filtered Listings")
                st.caption(f"Showing {len(df_filter_true):,} listings that match filter criteria")
                
                # Create cross-tabulation for filtered data
                crosstab_filtered = pd.crosstab(
                    df_filter_true['Bedroom_count'], 
                    df_filter_true['Bath_count'],
                    margins=True,
                    margins_name='Total'
                )
                crosstab_filtered.index.name = 'Bedrooms \\ Bathrooms'
                
                # Convert index and columns to strings to avoid type conversion warnings
                crosstab_filtered.index = crosstab_filtered.index.astype(str)
                crosstab_filtered.columns = crosstab_filtered.columns.astype(str)
                
                st.dataframe(
                    crosstab_filtered,
                    width='stretch'
                )
                
                # Find most common combination
                combo_filtered = df_filter_true.groupby(['Bedroom_count', 'Bath_count']).size()
                if len(combo_filtered) > 0:
                    most_common = combo_filtered.idxmax()
                    st.caption(f"📊 **Most common**: {most_common[0]} bed, {most_common[1]} bath ({combo_filtered.max():,} listings)")
            
            with col2:
                st.markdown("#### All Listings in Area")
                st.caption(f"Showing all {len(df):,} listings in the dataset")
                
                # Create cross-tabulation for all data
                crosstab_all = pd.crosstab(
                    df['Bedroom_count'], 
                    df['Bath_count'],
                    margins=True,
                    margins_name='Total'
                )
                crosstab_all.index.name = 'Bedrooms \\ Bathrooms'
                
                # Convert index and columns to strings to avoid type conversion warnings
                crosstab_all.index = crosstab_all.index.astype(str)
                crosstab_all.columns = crosstab_all.columns.astype(str)
                
                st.dataframe(
                    crosstab_all,
                    width='stretch'
                )
                
                # Find most common combination
                combo_all = df.groupby(['Bedroom_count', 'Bath_count']).size()
                if len(combo_all) > 0:
                    most_common = combo_all.idxmax()
                    st.caption(f"📊 **Most common**: {most_common[0]} bed, {most_common[1]} bath ({combo_all.max():,} listings)")

        
    
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

