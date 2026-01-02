# ============================================================================
# State and City Management Module
# ============================================================================
"""
Functions for discovering and managing state/city data structure.
"""

from pathlib import Path
from typing import Dict, List, Tuple, Optional


def discover_state_city_structure() -> Dict[str, List[str]]:
    """
    Discover states and cities from data/States folder structure.
    
    Returns:
        Dictionary mapping state names to lists of city names
        Example: {'California': ['Sacramento', 'San Francisco'], ...}
    """
    states_dir = Path("data/States")
    structure = {}
    
    if not states_dir.exists():
        return structure
    
    # Iterate through state folders
    for state_path in sorted(states_dir.iterdir()):
        if state_path.is_dir():
            state_name = state_path.name
            cities = []
            
            # Iterate through city folders within each state
            for city_path in sorted(state_path.iterdir()):
                if city_path.is_dir():
                    cities.append(city_path.name)
            
            if cities:  # Only add state if it has cities
                structure[state_name] = cities
    
    return structure


def load_city_data(state: str, city: str) -> Tuple[Optional[str], Optional[str]]:
    """
    Load listing and grid data file paths for a specific state/city.
    
    Args:
        state: State name
        city: City name
        
    Returns:
        Tuple of (listing_file_path, grid_file_path)
        Returns (None, None) if city folder doesn't exist
    """
    city_path = Path(f"data/States/{state}/{city}")
    
    if not city_path.exists():
        return None, None
    
    # Find listing CSV and grid CSV
    listing_file = None
    grid_file = None
    
    for file in city_path.glob("*.csv"):
        if 'listings' in file.name.lower():
            listing_file = str(file)
        elif 'grid' in file.name.lower():
            grid_file = str(file)
    
    return listing_file, grid_file


def check_location_match(selected_state: str, selected_city: str) -> bool:
    """
    Check if loaded data matches the currently selected location.
    
    Args:
        selected_state: Currently selected state
        selected_city: Currently selected city
        
    Returns:
        True if data is loaded and matches selected location
    """
    import streamlit as st
    
    return (
        'df' in st.session_state and 
        'loaded_state' in st.session_state and 
        'loaded_city' in st.session_state and
        st.session_state['loaded_state'] == selected_state and
        st.session_state['loaded_city'] == selected_city
    )

