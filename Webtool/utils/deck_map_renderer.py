# ============================================================================
# PyDeck Map Renderer Module
# ============================================================================
"""
High-performance map rendering using PyDeck/deck.gl for 5k-15k points.
Replaces Folium for better performance.
"""

import pydeck as pdk
import pandas as pd
import streamlit as st
from typing import Optional, Tuple


def create_deck_map(
    df: pd.DataFrame,
    grid_df: Optional[pd.DataFrame] = None,
    show_grids: bool = False,
    center: Optional[Tuple[float, float]] = None,
    zoom: int = 11,
    map_style: str = 'road'
) -> pdk.Deck:
    """
    Create a PyDeck map with ScatterplotLayer for listings.
    
    Args:
        df: DataFrame with listing data and 'passes_current_filter' column
        grid_df: Optional DataFrame with grid boundaries
        show_grids: Whether to show grid overlay
        center: Optional (lat, lon) tuple for map center
        zoom: Initial zoom level
        map_style: Map style ('road' [default, Google Maps-like], 'carto', 'carto-dark', 'light', 'dark')
        
    Returns:
        pdk.Deck object ready for rendering
    """
    
    # Validate required columns
    required_cols = ['Latitude', 'Longitude', 'Room_id']
    missing = [col for col in required_cols if col not in df.columns]
    if missing:
        raise ValueError(f"Missing required columns: {missing}")
    
    # Calculate map center if not provided
    if center is None:
        center = (
            df['Latitude'].mean(),
            df['Longitude'].mean()
        )
    
    # Prepare data for deck.gl (only necessary columns for performance)
    map_data = df[[
        'Latitude', 'Longitude', 'Room_id',
        'passes_current_filter',
        'Rating', 'Review_count',
        'Next_30_days_booked_days', 'Next_30_to_60_days_booked_days',
        '75_rule_met', '55_rule_met'
    ]].copy()
    
    # Ensure Room_id is string for safe comparison (no precision issues)
    map_data['Room_id'] = map_data['Room_id'].astype(str)
    
    # Add optional columns if they exist
    for col in ['Bedroom_count', 'Bath_count', 'Guest_count', 'Is_superhost']:
        if col in df.columns:
            map_data[col] = df[col]
    
    # Convert boolean to int for color calculation
    map_data['filter_pass_int'] = map_data['passes_current_filter'].astype(int)
    
    # Define color function: red for pass, blue for fail
    # Using list format [R, G, B, A] for deck.gl
    def get_color(row):
        if row['passes_current_filter']:
            return [255, 0, 0, 180]  # Red with transparency
        else:
            return [0, 90, 255, 120]  # Blue with transparency
    
    map_data['color'] = map_data.apply(get_color, axis=1)
    
    # Create ScatterplotLayer
    scatterplot_layer = pdk.Layer(
        'ScatterplotLayer',
        data=map_data,
        id='listings',  # Required for on_select to work!
        get_position=['Longitude', 'Latitude'],
        get_fill_color='color',
        get_radius=50,  # Radius in meters
        radius_min_pixels=4,
        radius_max_pixels=20,
        pickable=True,
        auto_highlight=True,
        highlight_color=[255, 255, 255, 100],
        opacity=0.8
    )
    
    layers = [scatterplot_layer]
    
    # Add grid overlay if requested
    if show_grids and grid_df is not None:
        grid_layer = create_grid_layer(grid_df)
        if grid_layer:
            layers.insert(0, grid_layer)  # Add grids below points
    
    # Define tooltip
    tooltip = {
        "html": """
        <div style="background: white; padding: 10px; border-radius: 5px; box-shadow: 0 2px 4px rgba(0,0,0,0.2);">
            <div style="font-size: 14px; font-weight: bold; margin-bottom: 5px;">
                Room #{Room_id}
            </div>
            <div style="font-size: 12px; color: #555;">
                ⭐ {Rating} | 💬 {Review_count} reviews<br/>
                📅 30d: {Next_30_days_booked_days} | 60d: {Next_30_to_60_days_booked_days}<br/>
                🏠 {Bedroom_count} bed | 🚿 {Bath_count} bath<br/>
                ✅ 75%: {75_rule_met} | 55%: {55_rule_met}
            </div>
        </div>
        """,
        "style": {
            "backgroundColor": "transparent",
            "color": "black"
        }
    }
    
    # Create view state
    view_state = pdk.ViewState(
        latitude=center[0],
        longitude=center[1],
        zoom=zoom,
        pitch=0,
        bearing=0
    )
    
    # Map style options (free, no API key required)
    # Using Carto Voyager for Google Maps-like appearance
    map_styles = {
        'road': 'https://basemaps.cartocdn.com/gl/voyager-gl-style/style.json',  # Google Maps-like
        'carto': 'https://basemaps.cartocdn.com/gl/positron-gl-style/style.json',  # Minimal light
        'carto-dark': 'https://basemaps.cartocdn.com/gl/dark-matter-gl-style/style.json',
        'carto-voyager': 'https://basemaps.cartocdn.com/gl/voyager-gl-style/style.json',
        'light': 'light',  # Fallback to PyDeck's basic light style
        'dark': 'dark'     # Fallback to PyDeck's basic dark style
    }
    
    # Get map style URL
    style_url = map_styles.get(map_style, map_styles['road'])
    
    # Create deck
    deck = pdk.Deck(
        layers=layers,
        initial_view_state=view_state,
        tooltip=tooltip,
        map_style=style_url,
        height=800
    )
    
    return deck


def create_grid_layer(grid_df: pd.DataFrame) -> Optional[pdk.Layer]:
    """
    Create a PolygonLayer for grid overlay.
    
    Args:
        grid_df: DataFrame with ne_lat, ne_long, sw_lat, sw_long columns
        
    Returns:
        pdk.Layer or None if grid data is invalid
    """
    required_cols = ['ne_lat', 'ne_long', 'sw_lat', 'sw_long']
    if not all(col in grid_df.columns for col in required_cols):
        return None
    
    # Convert grid rectangles to polygon coordinates
    polygons = []
    for _, row in grid_df.iterrows():
        # Create rectangle as polygon [SW, SE, NE, NW, SW]
        polygon = [
            [row['sw_long'], row['sw_lat']],  # SW
            [row['ne_long'], row['sw_lat']],  # SE
            [row['ne_long'], row['ne_lat']],  # NE
            [row['sw_long'], row['ne_lat']],  # NW
            [row['sw_long'], row['sw_lat']]   # Close polygon
        ]
        polygons.append({
            'polygon': polygon,
            'grid_id': row.get('grid_id', 'N/A')
        })
    
    grid_data = pd.DataFrame(polygons)
    
    # Create PolygonLayer
    grid_layer = pdk.Layer(
        'PolygonLayer',
        data=grid_data,
        id='grids',  # Required for on_select to work with multiple layers
        get_polygon='polygon',
        get_fill_color=[0, 90, 255, 30],  # Light blue with transparency
        get_line_color=[0, 90, 255, 150],  # Blue border
        line_width_min_pixels=1,
        pickable=True,
        auto_highlight=False
    )
    
    return grid_layer


def render_deck_map_with_click_handling(
    df: pd.DataFrame,
    grid_df: Optional[pd.DataFrame] = None,
    show_grids: bool = False,
    location: str = "Unknown"
) -> Optional[dict]:
    """
    Render PyDeck map and handle click/hover events.
    
    Args:
        df: Filtered DataFrame with 'passes_current_filter' column
        grid_df: Optional grid coordinates
        show_grids: Whether to show grid overlay
        location: Location name for display
        
    Returns:
        Click event data or None (None for older Streamlit versions)
    """
    
    if df.empty:
        st.warning("No data to display on map")
        return None
    
    # Create deck map
    try:
        deck = create_deck_map(
            df=df,
            grid_df=grid_df,
            show_grids=show_grids
        )
        
        # Render with Streamlit
        # Try new API (Streamlit >= 1.33) with on_select, fall back to basic rendering
        try:
            # New API with click handling
            event = st.pydeck_chart(
                deck,
                width='stretch',  # Replaced use_container_width (deprecated)
                on_select="rerun",
                selection_mode="single-object"
            )
            
            # Check if selection data is actually populated
            # Streamlit 1.29 accepts on_select but returns empty selection
            if event and event.get('selection'):
                selection = event['selection']
                objects = selection.get('objects', {})
                # If objects is an empty dict or empty list, click handling doesn't work
                if not objects or (isinstance(objects, dict) and len(objects) == 0):
                    # Selection data is empty - click handling not supported
                    return None
            
            return event
        except TypeError:
            # Older Streamlit version - basic rendering without click handling
            st.pydeck_chart(deck, width='stretch')  # Replaced use_container_width (deprecated)
            return None
        
    except Exception as e:
        st.error(f"Error creating map: {str(e)}")
        import traceback
        st.code(traceback.format_exc())
        return None




def get_selected_listing(event: Optional[dict], df: pd.DataFrame) -> Optional[pd.Series]:
    """
    Extract selected listing from PyDeck click event.
    
    Args:
        event: PyDeck selection event data
        df: Full DataFrame to look up selected listing
        
    Returns:
        Selected listing as Series or None
    """
    if not event or not event.get('selection'):
        return None
    
    try:
        # Extract object from selection
        selection = event['selection']
        if not selection or 'objects' not in selection:
            return None
        
        objects = selection['objects']
        
        # Check if objects is valid (Streamlit < 1.33 returns empty dict {})
        if not objects:
            return None
        
        # Objects is a dict organized by layer id: {"listings": [...], "grids": [...]}
        if not isinstance(objects, dict):
            return None
        
        # Empty dict means no selection (Streamlit 1.29 behavior)
        if len(objects) == 0:
            return None
        
        # Get objects from the 'listings' layer
        if 'listings' not in objects:
            return None
        
        listings_objects = objects['listings']
        if not isinstance(listings_objects, list) or len(listings_objects) == 0:
            return None
        
        # Get first selected object
        selected_obj = listings_objects[0]
        
        # Extract Room_id
        room_id = selected_obj.get('Room_id')
        if room_id is None:
            print("❌ Error: Room_id is None in selected object")
            return None
        
        
        # Convert to string for safe comparison (no precision issues)
        try:
            room_id = str(room_id)
        except (ValueError, TypeError) as e:
            print(f"❌ Error converting Room_id to string: {e}")
            return None
        
        # Check if Room_id column exists and its type
        if 'Room_id' not in df.columns:
            print("❌ Error: 'Room_id' column not found in DataFrame")
            return None
                
        # Ensure DataFrame Room_id is also string for consistent comparison
        if df['Room_id'].dtype != 'object':  # 'object' is pandas dtype for strings
            df = df.copy()
            df['Room_id'] = df['Room_id'].astype(str)
        
        
        # Find matching row in dataframe
        matching_rows = df[df['Room_id'] == room_id]
        
        
        if matching_rows.empty:
            # Check if Room_id exists with any whitespace issues
            if room_id.strip() != room_id:
                print(f"⚠️ Warning: Room_id has leading/trailing whitespace!")
            return None
        
        return matching_rows.iloc[0]
        
    except Exception as e:
        # Don't show warning for empty selection (expected behavior)
        import traceback
        print(f"Debug: Error extracting selected listing: {str(e)}")
        print(f"Debug: Event structure: {event}")
        print(f"Debug: Traceback: {traceback.format_exc()}")
        return None

