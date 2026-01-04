# ============================================================================
# Listing Details Panel Module
# ============================================================================
"""
Render detailed information for a selected listing.
Only computed on-demand when a listing is clicked.
"""

import streamlit as st
import pandas as pd
from typing import Any, Optional
import ast


def format_review_heatmap(review_data: Any) -> str:
    """
    Format review count data as a color-coded table.
    
    Args:
        review_data: Dictionary with year keys and list of monthly counts
        
    Returns:
        HTML string with styled table
    """
    if not isinstance(review_data, dict) or not review_data:
        return "<p>No review data available</p>"
    
    # Sort years (most recent first)
    years = sorted(review_data.keys(), reverse=True)
    months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 
              'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
    
    # Build table HTML
    html = '<table style="width:100%; border-collapse: collapse; font-size: 11px;">'
    
    # Header row
    html += '<tr><th style="padding: 4px; border: 1px solid #ddd; background: #f0f0f0;">Year</th>'
    for month in months:
        html += f'<th style="padding: 4px; border: 1px solid #ddd; background: #f0f0f0;">{month}</th>'
    html += '</tr>'
    
    # Data rows
    for year in years:
        counts = review_data[year]
        if not isinstance(counts, list) or len(counts) != 12:
            continue
            
        html += f'<tr><td style="padding: 4px; border: 1px solid #ddd; font-weight: bold;">{year}</td>'
        
        for count in counts:
            # Color coding
            if count == 0:
                color = '#e0e0e0'  # Gray
                text_color = '#666'
            elif count <= 2:
                color = '#fff9c4'  # Yellow
                text_color = '#000'
            else:
                color = '#c8e6c9'  # Light green
                text_color = '#000'
            
            html += f'<td style="padding: 4px; border: 1px solid #ddd; background: {color}; color: {text_color}; text-align: center;">{count}</td>'
        
        html += '</tr>'
    
    html += '</table>'
    
    # Add legend
    html += '''
    <div style="margin-top: 10px; font-size: 10px;">
        <span style="background: #e0e0e0; padding: 2px 6px; margin-right: 8px;">■ 0 reviews</span>
        <span style="background: #fff9c4; padding: 2px 6px; margin-right: 8px;">■ 1-2 reviews</span>
        <span style="background: #c8e6c9; padding: 2px 6px;">■ 3+ reviews</span>
    </div>
    '''
    
    return html


def render_listing_detail_panel(selected_row: pd.Series):
    """
    Render detailed information panel for a selected listing.
    
    Args:
        selected_row: DataFrame row (Series) for the selected listing
    """
    
    # Header with Room ID and link
    room_id = selected_row.get('Room_id', 'Unknown')
    listing_url = selected_row.get('Listing_url', f"https://www.airbnb.com.sg/rooms/{room_id}")
    
    col1, col2 = st.columns([2, 1])
    with col1:
        st.markdown(f"**Room #{room_id}**")
    with col2:
        st.markdown(f"[🏠 View on Airbnb]({listing_url})")
    
    # Status badges
    st.markdown("#### Status")
    
    badge_cols = st.columns(4)
    
    with badge_cols[0]:
        passes_filter = selected_row.get('passes_current_filter', False)
        if passes_filter:
            st.success("✅ Passes Filter")
        else:
            st.info("❌ Does Not Pass the Current Filter Criteria")
    
    with badge_cols[1]:
        passes_75 = selected_row.get('75_rule_met', False)
        if passes_75:
            st.success("✅ 75% Rule")
        else:
            st.warning("❌ 75% Rule")
    
    with badge_cols[2]:
        passes_55 = selected_row.get('55_rule_met', False)
        if passes_55:
            st.success("✅ 55% Rule")
        else:
            st.warning("❌ 55% Rule")
    
    with badge_cols[3]:
        is_superhost = selected_row.get('Is_superhost', False)
        if is_superhost:
            st.success("⭐ Superhost")
    
    # Key metrics
    st.markdown("#### Key Metrics")
    
    metric_cols = st.columns(4)
    
    with metric_cols[0]:
        rating = selected_row.get('Rating', 0)
        st.metric("Rating", f"{rating:.1f}" if rating else "N/A")
    
    with metric_cols[1]:
        review_count = selected_row.get('Review_count', 0)
        st.metric("Reviews", f"{int(review_count)}" if review_count else "0")
    
    with metric_cols[2]:
        days_30 = selected_row.get('Next_30_days_booked_days', 0)
        st.metric("30d Booked", f"{int(days_30)}" if days_30 else "0")
    
    with metric_cols[3]:
        days_60 = selected_row.get('Next_30_to_60_days_booked_days', 0)
        st.metric("30-60d Booked", f"{int(days_60)}" if days_60 else "0")
    
    # Property details
    st.markdown("#### Property Details")
    
    property_cols = st.columns(4)
    
    with property_cols[0]:
        guests = selected_row.get('Guest_count', 'N/A')
        st.markdown(f"**Guests:** {guests}")
    
    with property_cols[1]:
        bedrooms = selected_row.get('Bedroom_count', 'N/A')
        st.markdown(f"**Bedrooms:** {bedrooms}")
    
    with property_cols[2]:
        bathrooms = selected_row.get('Bath_count', 'N/A')
        st.markdown(f"**Bathrooms:** {bathrooms}")
    
    # with property_cols[3]:
    #     grid = selected_row.get('Grid_index', 'N/A')
    #     st.markdown(f"**Grid:** {grid}")
    
    # Location
    st.markdown("#### Location")
    lat = selected_row.get('Latitude', 'N/A')
    lon = selected_row.get('Longitude', 'N/A')
    st.markdown(f"**Coordinates:** {lat}, {lon}")
    
    # Review activity heatmap
    st.markdown("#### 📊 Review Activity by Month")
    
    review_data = selected_row.get('review_data_parsed')
    
    # Fallback to parsing string if needed
    if review_data is None or not isinstance(review_data, dict):
        review_str = selected_row.get('Review_count_by_year_and_month')
        if review_str and isinstance(review_str, str):
            try:
                review_data = ast.literal_eval(review_str)
            except:
                review_data = None
    
    if review_data:
        heatmap_html = format_review_heatmap(review_data)
        st.markdown(heatmap_html, unsafe_allow_html=True)
    else:
        st.info("No review activity data available")
    
    # Title if available
    title = selected_row.get('Title')
    if title:
        st.markdown("#### Listing Title")
        st.markdown(f"*{title}*")


def render_empty_detail_panel():
    """
    Render placeholder when no listing is selected.
    (This function is deprecated - placeholder is now shown in app.py)
    """
    st.info("👆 Click on a marker on the map to view listing details")

