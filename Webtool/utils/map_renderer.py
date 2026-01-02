# ============================================================================
# Map Rendering Module
# ============================================================================
"""
Functions for rendering and managing the Folium map in Streamlit.
"""

import streamlit as st
import pandas as pd
import hashlib
import json
from streamlit_folium import st_folium
from .map_creator import create_map_with_listings


def generate_map_hash(filter_criteria: dict, show_grids: bool, location: str) -> str:
    """
    Generate a unique hash for the current map state.
    
    Args:
        filter_criteria: Dictionary of filter parameters
        show_grids: Whether grids are shown
        location: Current location string
        
    Returns:
        8-character hash string
    """
    filter_state = {
        'filter_criteria': filter_criteria,
        'show_grids': show_grids,
        'location': location
    }
    return hashlib.md5(
        json.dumps(filter_state, sort_keys=True, default=str).encode()
    ).hexdigest()[:8]


def render_map(
    filtered_df: pd.DataFrame,
    original_df: pd.DataFrame,
    grid_df: pd.DataFrame,
    show_grids: bool,
    filter_criteria: dict,
    location: str
):
    """
    Render the interactive Folium map with smart caching.
    
    Only recreates the map when filters change, not on zoom/pan interactions.
    
    Args:
        filtered_df: DataFrame with filtered listings
        original_df: Original unfiltered DataFrame
        grid_df: DataFrame with grid coordinates (optional)
        show_grids: Whether to show grids
        filter_criteria: Dictionary of filter parameters
        location: Current location string
    """
    # Generate hash for current state
    filter_hash = generate_map_hash(filter_criteria, show_grids, location)
    
    # Initialize map state in session
    if 'map_filter_hash' not in st.session_state:
        st.session_state['map_filter_hash'] = None
        st.session_state['map_html'] = None
    
    # Only create map if filters changed (not on map interactions)
    try:
        if st.session_state['map_filter_hash'] != filter_hash:
            with st.spinner("🗺️ Generating interactive map..."):
                m = create_map_with_listings(
                    df=filtered_df,
                    grid_df=grid_df if show_grids else None,
                    show_grids=show_grids,
                    color_column='passes_current_filter',
                    original_df=original_df
                )
                
                # Store map and hash in session state
                st.session_state['map_html'] = m._repr_html_()
                st.session_state['map_filter_hash'] = filter_hash
                st.session_state['current_map_object'] = m
        
        # Display the map (reuse from session state)
        # This prevents recreation on zoom/pan interactions
        map_data = st_folium(
            st.session_state['current_map_object'],
            width=1800,
            height=800,
            returned_objects=[]  # Don't return zoom/center to avoid triggering reruns
        )
        
        return True  # Successfully rendered
        
    except Exception as e:
        st.error(f"Error creating map: {str(e)}")
        import traceback
        st.code(traceback.format_exc())
        return False  # Failed to render


def render_map_caption(num_passing: int, num_failing: int, total: int):
    """
    Render the caption below the map showing listing counts.
    
    Args:
        num_passing: Number of listings passing filters
        num_failing: Number of listings failing filters
        total: Total number of listings
    """
    if num_passing > 0:
        st.caption(
            f"🔴 {num_passing:,} listings pass filter | "
            f"🔵 {num_failing:,} listings fail filter | "
            f"Total: {total:,}"
        )
    else:
        st.caption(f"🔵 All {total:,} listings fail current filters")

