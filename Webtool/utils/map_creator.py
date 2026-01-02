# ============================================================================
# Map Creator Module
# ============================================================================
"""
Functions to create interactive Folium maps for the dashboard
"""

import ast
import folium
import folium.plugins
import pandas as pd
from typing import Optional


def format_review_table(review_data: dict) -> str:
    """
    Format review count data as an HTML table.
    
    Args:
        review_data: {'2024': [1,0,0,...], '2025': [...]}
        
    Returns:
        HTML string with formatted table
    """
    if not review_data or not isinstance(review_data, dict):
        return "<p style='color: #6c757d; font-style: italic;'>No review data available</p>"
    
    # Month names
    months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 
                'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
    
    # Start table HTML
    html = """
    <div style="margin-top: 10px; border-top: 2px solid #3498db; padding-top: 10px;">
        <h5 style="margin: 5px 0 8px 0; color: #2c3e50;">📊 Number of Reviews by Month</h5>
        <div style="overflow-x: auto;">
            <table style="width: 100%; border-collapse: collapse; font-size: 10px;">
                <thead>
                    <tr style="background-color: #3498db; color: white;">
                        <th style="padding: 4px; border: 1px solid #2980b9; font-weight: bold;">Year</th>
    """
    
    # Add month headers
    for month in months:
        html += f'<th style="padding: 4px; border: 1px solid #2980b9; font-weight: bold;">{month}</th>'
    
    html += """
                    </tr>
                </thead>
                <tbody>
    """
    
    # Sort years in descending order (most recent first)
    sorted_years = sorted(review_data.keys(), reverse=True)
    
    # Add row for each year
    for year in sorted_years:
        reviews = review_data[year]
        html += f"""
                    <tr>
                        <td style="padding: 4px; border: 1px solid #ddd; font-weight: bold; background-color: #ecf0f1;">{year}</td>
        """
        
        # Add cell for each month
        for count in reviews:
            # Color code based on activity
            if count == 0:
                bg_color = '#f8f9fa'  # Light gray
                text_color = '#6c757d'
            elif count <= 2:
                bg_color = '#fff3cd'  # Light yellow
                text_color = '#856404'
            else:  # >= 3
                bg_color = '#d4edda'  # Light green
                text_color = '#155724'
            
            html += f"""
                        <td style="padding: 4px; border: 1px solid #ddd; 
                                    background-color: {bg_color}; color: {text_color};
                                    text-align: center; font-weight: bold;">
                            {count}
                        </td>
            """
        
        html += """
                    </tr>
        """
    
    html += """
                </tbody>
            </table>
        </div>
        <div style="margin-top: 5px; font-size: 9px; color: #6c757d;">
            <span style="color: #155724;">🟢 ≥3</span> | 
            <span style="color: #856404;">🟡 1-2</span> | 
            <span style="color: #6c757d;">⚪ 0</span> reviews
        </div>
    </div>
    """
    
    return html


def create_base_map(
    df: pd.DataFrame, 
    zoom_start: int = 12, 
    grid_df: Optional[pd.DataFrame] = None,
    custom_center: Optional[tuple] = None,
    custom_zoom: Optional[int] = None
) -> folium.Map:
    """
    Create a base Folium map centered on the data.
    
    Args:
        df: DataFrame with Latitude and Longitude columns (can be empty)
        zoom_start: Initial zoom level (used if custom_zoom not provided)
        grid_df: Optional grid DataFrame to use for centering if df is empty
        custom_center: Optional (lat, lon) tuple to override automatic centering
        custom_zoom: Optional zoom level to override zoom_start
        
    Returns:
        Folium Map object
    """
    # Use custom zoom if provided
    if custom_zoom is not None:
        zoom_start = custom_zoom
    
    # Use custom center if provided
    if custom_center is not None:
        center_lat, center_lon = custom_center
    else:
        # Calculate center automatically
        if len(df) == 0:
            # Try to use grid_df for centering
            if grid_df is not None and len(grid_df) > 0:
                center_lat = (grid_df['ne_lat'].max() + grid_df['sw_lat'].min()) / 2
                center_lon = (grid_df['ne_long'].max() + grid_df['sw_long'].min()) / 2
            else:
                # Use default location (US center)
                center_lat = 39.8283
                center_lon = -98.5795
                zoom_start = 4
        else:
            # Calculate center point from data
            center_lat = (df['Latitude'].max() + df['Latitude'].min()) / 2
            center_lon = (df['Longitude'].max() + df['Longitude'].min()) / 2
    
    # Create map
    m = folium.Map(
        location=[center_lat, center_lon],
        zoom_start=zoom_start,
        tiles='OpenStreetMap'
    )
    
    return m


def add_listings_to_map(
    m: folium.Map,
    df: pd.DataFrame,
    color_column: Optional[str] = None,
    color_map: Optional[dict] = None
) -> folium.Map:
    """
    Add listing markers to the map.
    
    Args:
        m: Folium Map object
        df: DataFrame with listing data
        color_column: Column to use for coloring (e.g., '75_rule_met')
        color_map: Dictionary mapping values to colors
        
    Returns:
        Updated Folium Map object
    """
    # Default color mapping
    if color_map is None:
        color_map = {
            True: {'color': 'red', 'fillColor': 'red', 'border': 'darkred'},
            False: {'color': 'blue', 'fillColor': 'blue', 'border': 'darkblue'}
        }
    
    # Add each listing as a circle marker
    # Use itertuples() for faster iteration (2-5x faster than iterrows)
    for listing in df.itertuples():
        # Extract listing information
        room_id = listing.Room_id
        lat = listing.Latitude
        lon = listing.Longitude
        
        # Determine color
        if color_column and hasattr(listing, color_column):
            color_value = getattr(listing, color_column)
            colors = color_map.get(color_value, color_map.get(False))
        else:
            colors = color_map.get(False)  # Default to blue
        
        # Get optional fields (use getattr with default for missing columns)
        rating = getattr(listing, 'Rating', 'N/A')
        review_count = getattr(listing, 'Review_count', 'N/A')
        next_30_days = getattr(listing, 'Next_30_days_booked_days', 'N/A')
        next_60_days = getattr(listing, 'Next_30_to_60_days_booked_days', 'N/A')
        missing_months = getattr(listing, 'Total_missing_review_months_this_year', 'N/A')
        met_75_rule = getattr(listing, '_75_rule_met', False)  # Note: 75_rule_met becomes _75_rule_met in namedtuple
        passes_filter = getattr(listing, 'passes_current_filter', True)
        
        # Get property details for tooltip
        guest_count = getattr(listing, 'Guest_count', getattr(listing, 'Guests', 'N/A'))
        bedroom_count = getattr(listing, 'Bedroom_count', 'N/A')
        bath_count = getattr(listing, 'Bath_count', 'N/A')
        
        # Get review activity data and format as table
        # Use pre-parsed data if available (much faster!)
        if hasattr(listing, 'review_data_parsed'):
            review_data = getattr(listing, 'review_data_parsed', {})
        else:
            # Fallback to parsing if not pre-processed (backward compatibility)
            review_data = getattr(listing, 'Review_count_by_year_and_month', {})
            if pd.notna(review_data) and isinstance(review_data, str):
                try:
                    review_data = ast.literal_eval(review_data)
                except:
                    review_data = {}
            elif pd.isna(review_data) or not isinstance(review_data, dict):
                review_data = {}
        
        review_table_html = format_review_table(review_data)
        
        # Create filter status text (if filter column exists)
        if hasattr(listing, 'passes_current_filter'):
            if passes_filter:
                filter_status_text = '✅ Passes Current Filter'
                filter_status_color = '#27ae60'
            else:
                filter_status_text = '❌ Does NOT Pass Current Filter'
                filter_status_color = '#95a5a6'
        else:
            filter_status_text = None
            filter_status_color = None
        
        # Create 75% rule status text
        if met_75_rule:
            rule_status_text = '✅ Passes 75% Rule'
            rule_status_color = '#27ae60'
        else:
            rule_status_text = '❌ Does NOT Pass 75% Rule'
            rule_status_color = '#e74c3c'
        
        # Create popup HTML
        # Build status badges HTML
        status_badges_html = ""
        if filter_status_text:
            status_badges_html += f"""
            <div style="background-color: {filter_status_color}; color: white; padding: 5px; margin: 5px 0; border-radius: 3px; text-align: center;">
                <strong>{filter_status_text}</strong>
            </div>
            """
        status_badges_html += f"""
            <div style="background-color: {rule_status_color}; color: white; padding: 5px; margin: 5px 0; border-radius: 3px; text-align: center;">
                <strong>{rule_status_text}</strong>
            </div>
            """
        
        popup_html = f"""
        <div style="font-family: Arial; font-size: 12px; min-width: 450px; max-width: 500px;">
            <h4 style="margin: 5px 0; color: {colors['border']};">Listing {room_id}</h4>
            {status_badges_html}
            <table style="width: 100%; border-collapse: collapse;">
                <tr style="border-bottom: 1px solid #ddd;">
                    <td style="padding: 3px; font-weight: bold;">Room ID:</td>
                    <td style="padding: 3px;">{room_id}</td>
                </tr>
                <tr style="border-bottom: 1px solid #ddd;">
                    <td style="padding: 3px; font-weight: bold;">Next 30 days booked:</td>
                    <td style="padding: 3px;">{next_30_days} days</td>
                </tr>
                <tr style="border-bottom: 1px solid #ddd;">
                    <td style="padding: 3px; font-weight: bold;">Next 31-60 days booked:</td>
                    <td style="padding: 3px;">{next_60_days} days</td>
                </tr>
                <tr style="border-bottom: 1px solid #ddd;">
                    <td style="padding: 3px; font-weight: bold;">Missing months (this year):</td>
                    <td style="padding: 3px;">{missing_months}</td>
                </tr>
                <tr style="border-bottom: 1px solid #ddd;">
                    <td style="padding: 3px; font-weight: bold;">Guests:</td>
                    <td style="padding: 3px;">{guest_count}</td>
                </tr>
                <tr style="border-bottom: 1px solid #ddd;">
                    <td style="padding: 3px; font-weight: bold;">Bedrooms:</td>
                    <td style="padding: 3px;">{bedroom_count}</td>
                </tr>
                <tr style="border-bottom: 1px solid #ddd;">
                    <td style="padding: 3px; font-weight: bold;">Bathrooms:</td>
                    <td style="padding: 3px;">{bath_count}</td>
                </tr>
                <tr style="border-bottom: 1px solid #ddd;">
                    <td style="padding: 3px; font-weight: bold;">Rating:</td>
                    <td style="padding: 3px;">{rating} ⭐</td>
                </tr>
                <tr style="border-bottom: 1px solid #ddd;">
                    <td style="padding: 3px; font-weight: bold;">Review count:</td>
                    <td style="padding: 3px;">{review_count}</td>
                </tr>
                <tr style="border-bottom: 1px solid #ddd;">
                    <td style="padding: 3px; font-weight: bold;">Coordinates:</td>
                    <td style="padding: 3px;">{lat:.5f}, {lon:.5f}</td>
                </tr>
                <tr>
                    <td style="padding: 3px; font-weight: bold;">Link:</td>
                    <td style="padding: 3px;"><a href="https://www.airbnb.com/rooms/{room_id}" target="_blank">View Listing</a></td>
                </tr>
            </table>
            
            {review_table_html}
        </div>
        """
        
        # Create tooltip with property details
        tooltip_text = f"Listing {room_id} | {guest_count} guests | {bedroom_count} bed | {bath_count} bath"
        
        # Add circle marker
        folium.CircleMarker(
            location=[lat, lon],
            radius=6,
            color=colors['border'],
            fill=True,
            fillColor=colors['fillColor'],
            fillOpacity=0.8,
            weight=2,
            popup=folium.Popup(popup_html, max_width=550),
            tooltip=tooltip_text
        ).add_to(m)
    
    return m


def add_grids_to_map(
    m: folium.Map,
    grid_df: pd.DataFrame,
    summary_df: pd.DataFrame
) -> folium.Map:
    """
    Add grid rectangles to the map.
    
    Args:
        m: Folium Map object
        grid_df: DataFrame with grid coordinates
        summary_df: DataFrame with listing data (to calculate grid stats, can be empty)
        
    Returns:
        Updated Folium Map object
    """
    # Use itertuples() for faster iteration
    for row in grid_df.itertuples():
        grid_id = row.grid_id
        
        # Define rectangle bounds
        bounds = [
            [row.sw_lat, row.sw_long],
            [row.ne_lat, row.ne_long]
        ]
        
        # Count listings within this grid (handle empty summary_df)
        if len(summary_df) > 0:
            listings_in_grid = summary_df[
                (summary_df['Latitude'] >= row.sw_lat) & 
                (summary_df['Latitude'] <= row.ne_lat) & 
                (summary_df['Longitude'] >= row.sw_long) & 
                (summary_df['Longitude'] <= row.ne_long)
            ]
        else:
            listings_in_grid = pd.DataFrame()
        
        num_listings = len(listings_in_grid)
        
        # Calculate stats (handle empty dataframe)
        if num_listings > 0 and '75_rule_met' in listings_in_grid.columns:
            num_passed_75 = listings_in_grid['75_rule_met'].sum()
        else:
            num_passed_75 = 0
        
        num_failed_75 = num_listings - num_passed_75
        
        # Calculate other stats
        if num_listings > 0:
            avg_rating = listings_in_grid['Rating'].mean() if 'Rating' in listings_in_grid.columns else 0
            avg_booked_days = listings_in_grid['Next_30_days_booked_days'].mean() if 'Next_30_days_booked_days' in listings_in_grid.columns else 0
        else:
            avg_rating = 0
            avg_booked_days = 0
        
        # Create popup
        grid_popup_html = f"""
        <div style="font-family: Arial; font-size: 12px; min-width: 250px;">
            <h3 style="margin: 5px 0; color: #2c3e50; border-bottom: 2px solid #3498db; padding-bottom: 5px;">
                📍 Grid {int(grid_id)}
            </h3>
            <table style="width: 100%; border-collapse: collapse; margin-top: 10px;">
                <tr style="background-color: #ecf0f1;">
                    <td style="padding: 5px; font-weight: bold;">Total Listings:</td>
                    <td style="padding: 5px; text-align: right;"><strong>{num_listings}</strong></td>
                </tr>
                <tr>
                    <td style="padding: 5px; font-weight: bold;">✅ Pass 75% Rule:</td>
                    <td style="padding: 5px; text-align: right; color: #27ae60;"><strong>{num_passed_75}</strong></td>
                </tr>
                <tr style="background-color: #ecf0f1;">
                    <td style="padding: 5px; font-weight: bold;">❌ Fail 75% Rule:</td>
                    <td style="padding: 5px; text-align: right; color: #e74c3c;"><strong>{num_failed_75}</strong></td>
                </tr>
                <tr>
                    <td style="padding: 5px; font-weight: bold;">⭐ Avg Rating:</td>
                    <td style="padding: 5px; text-align: right;">{avg_rating:.2f}</td>
                </tr>
                <tr style="background-color: #ecf0f1;">
                    <td style="padding: 5px; font-weight: bold;">📅 Avg Days Booked:</td>
                    <td style="padding: 5px; text-align: right;">{avg_booked_days:.1f} / 30</td>
                </tr>
            </table>
        </div>
        """
        
        # Add rectangle
        folium.Rectangle(
            bounds=bounds,
            color='blue',
            fill=True,
            fillColor='blue',
            fillOpacity=0.15,
            weight=2,
            popup=folium.Popup(grid_popup_html, max_width=300),
            tooltip=f"Grid {grid_id}: {num_listings} listings"
        ).add_to(m)
        
        # Add grid label
        center_lat_grid = (row.ne_lat + row.sw_lat) / 2
        center_lon_grid = (row.ne_long + row.sw_long) / 2
        
        folium.Marker(
            location=[center_lat_grid, center_lon_grid],
            icon=folium.DivIcon(html=f"""
                <div style="
                    font-size: 12px;
                    font-weight: bold;
                    color: #1e3a8a;
                    text-align: center;
                    text-shadow: 1px 1px 2px white, -1px -1px 2px white;
                ">
                    {int(grid_id)}
                </div>
            """)
        ).add_to(m)
    
    return m


def create_map_with_listings(
    df: pd.DataFrame,
    grid_df: Optional[pd.DataFrame] = None,
    show_grids: bool = False,
    color_column: str = '75_rule_met',
    original_df: Optional[pd.DataFrame] = None,
    custom_center: Optional[tuple] = None,
    custom_zoom: Optional[int] = None
) -> folium.Map:
    """
    Create a complete map with listings and optionally grids.
    
    Args:
        df: DataFrame with listing data (possibly filtered, can be empty)
        grid_df: DataFrame with grid coordinates (optional)
        show_grids: Whether to show grid boundaries
        color_column: Column to use for coloring markers
        original_df: Original unfiltered DataFrame (for grid stats)
        custom_center: Optional (lat, lon) tuple to preserve map center
        custom_zoom: Optional zoom level to preserve zoom state
        
    Returns:
        Folium Map object
    """
    # Create base map with custom center/zoom if provided
    m = create_base_map(
        df, 
        grid_df=grid_df,
        custom_center=custom_center,
        custom_zoom=custom_zoom
    )
    
    # Add grids if requested (use original_df for stats if provided)
    if show_grids and grid_df is not None:
        stats_df = original_df if original_df is not None else df
        m = add_grids_to_map(m, grid_df, stats_df)
    
    # Add listings only if df is not empty
    if len(df) > 0:
        m = add_listings_to_map(m, df, color_column=color_column)
    
    # Add fullscreen button
    folium.plugins.Fullscreen().add_to(m)
    
    return m

