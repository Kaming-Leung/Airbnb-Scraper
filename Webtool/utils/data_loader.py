# ============================================================================
# Data Loader Module
# ============================================================================
"""
Functions to load and validate enrichment data from CSV files
"""

import pandas as pd
import streamlit as st
from pathlib import Path
from typing import Optional, Tuple


def load_enrichment_data(file_path: str) -> Optional[pd.DataFrame]:
    """
    Load enrichment data from CSV or Excel file.
    
    Args:
        file_path: Path to the CSV or Excel file
        
    Returns:
        DataFrame with enrichment data, or None if loading fails
    """
    try:
        # Determine file type and load accordingly
        if file_path.endswith('.csv'):
            df = pd.read_csv(file_path)
        elif file_path.endswith(('.xlsx', '.xls')):
            df = pd.read_excel(file_path)
        else:
            st.error(f"Unsupported file format: {file_path}")
            return None
        
        return df
    
    except FileNotFoundError:
        st.error(f"File not found: {file_path}")
        return None
    except Exception as e:
        st.error(f"Error loading data: {str(e)}")
        return None


def validate_enrichment_data(df: pd.DataFrame) -> Tuple[bool, str]:
    """
    Validate that the DataFrame has required columns for the dashboard.
    
    Args:
        df: DataFrame to validate
        
    Returns:
        (is_valid, message)
    """
    required_columns = [
        'Room_id',
        'Latitude',
        'Longitude',
        'Next_30_days_booked_days',
        'Next_30_to_60_days_booked_days',
        'Total_missing_review_months_this_year',
        'Total_missing_review_months_last_year',
        '75_rule_met'
    ]
    
    missing_columns = [col for col in required_columns if col not in df.columns]
    
    if missing_columns:
        return False, f"Missing required columns: {', '.join(missing_columns)}"
    
    # Check for NaN values in critical columns
    critical_columns = ['Room_id', 'Latitude', 'Longitude']
    for col in critical_columns:
        if df[col].isna().any():
            return False, f"Column '{col}' contains missing values"
    
    return True, "Data validation passed"


def get_data_summary(df: pd.DataFrame) -> dict:
    """
    Generate summary statistics for the loaded data.
    
    Args:
        df: DataFrame with enrichment data
        
    Returns:
        Dictionary with summary statistics
    """
    summary = {
        'total_listings': len(df),
        'unique_grids': df['Grid_index'].nunique() if 'Grid_index' in df.columns else 'N/A',
        'passed_75_rule': df['75_rule_met'].sum() if '75_rule_met' in df.columns else 0,
        'passed_75_pct': (df['75_rule_met'].sum() / len(df) * 100) if '75_rule_met' in df.columns else 0,
    }
    
    # Add optional fields if available
    if 'Next_30_days_booked_days' in df.columns:
        summary['avg_30_day_booked'] = df['Next_30_days_booked_days'].mean()
    
    if 'Next_30_to_60_days_booked_days' in df.columns:
        summary['avg_60_day_booked'] = df['Next_30_to_60_days_booked_days'].mean()
    
    return summary


def discover_csv_files(data_dir: str = "data") -> list:
    """
    Discover all CSV and Excel files in the data directory.
    
    Args:
        data_dir: Directory to search for data files
        
    Returns:
        List of file paths
    """
    data_path = Path(data_dir)
    
    if not data_path.exists():
        return []
    
    # Find all CSV and Excel files
    csv_files = list(data_path.glob("*.csv"))
    excel_files = list(data_path.glob("*.xlsx"))
    excel_files.extend(list(data_path.glob("*.xls")))
    
    all_files = csv_files + excel_files
    
    return [str(f) for f in sorted(all_files)]


def format_column_names(df: pd.DataFrame) -> pd.DataFrame:
    """
    Standardize column names if needed (handle variations).
    
    Args:
        df: DataFrame with potentially inconsistent column names
        
    Returns:
        DataFrame with standardized column names
    """
    # Create a copy to avoid modifying original
    df = df.copy()
    
    # Handle common variations
    column_mapping = {
        'room_id': 'Room_id',
        'latitude': 'Latitude',
        'longitude': 'Longitude',
        'Latitiude': 'Latitude',
        'next_30_days_booked_days': 'Next_30_days_booked_days',
        'next_30_to_60_days_booked_days': 'Next_30_to_60_days_booked_days',
        'total_missing_review_months_this_year': 'Total_missing_review_months_this_year',
        'total_missing_review_months_last_year': 'Total_missing_review_months_last_year',
        '75_rule_met': '75_rule_met',
        '55_rule_met': '55_rule_met',
        'rating': 'Rating',
        'review_count': 'Review_count',
        'grid_index': 'Grid_index',
    }
    
    # Apply mapping (case-insensitive)
    df.columns = [column_mapping.get(col.lower(), col) for col in df.columns]
    
    return df


def load_grid_coordinates(file_path: str) -> Optional[pd.DataFrame]:
    """
    Load grid coordinate data from CSV or Excel file.
    
    Args:
        file_path: Path to the grid coordinates file
        
    Returns:
        DataFrame with grid coordinates, or None if loading fails
    """
    try:
        # Load file
        if file_path.endswith('.csv'):
            df = pd.read_csv(file_path)
        elif file_path.endswith(('.xlsx', '.xls')):
            df = pd.read_excel(file_path)
        else:
            st.error(f"Unsupported file format: {file_path}")
            return None
        
        return df
    
    except FileNotFoundError:
        st.error(f"Grid file not found: {file_path}")
        return None
    except Exception as e:
        st.error(f"Error loading grid data: {str(e)}")
        return None


def validate_grid_coordinates(df: pd.DataFrame) -> Tuple[bool, str]:
    """
    Validate that the DataFrame has required columns for grid coordinates.
    
    Args:
        df: DataFrame to validate
        
    Returns:
        (is_valid, message)
    """
    required_columns = ['grid_id', 'ne_lat', 'ne_long', 'sw_lat', 'sw_long']
    
    missing_columns = [col for col in required_columns if col not in df.columns]
    
    if missing_columns:
        return False, f"Missing required columns: {', '.join(missing_columns)}"
    
    # Check for NaN values in critical columns
    for col in required_columns:
        if df[col].isna().any():
            return False, f"Column '{col}' contains missing values"
    
    return True, "Grid data validation passed"


def preprocess_review_data(df: pd.DataFrame) -> pd.DataFrame:
    """
    Pre-parse review data from string to dictionary format.
    
    This is a one-time preprocessing step that significantly speeds up
    map rendering by avoiding repeated ast.literal_eval() calls.
    
    Args:
        df: DataFrame with 'Review_count_by_year_and_month' column
        
    Returns:
        DataFrame with added 'review_data_parsed' column
    """
    import ast
    
    if 'Review_count_by_year_and_month' not in df.columns:
        return df
    
    def safe_parse_review_data(value):
        """Safely parse review data string to dictionary"""
        if pd.isna(value):
            return {}
        if isinstance(value, dict):
            return value  # Already parsed
        if isinstance(value, str):
            try:
                return ast.literal_eval(value)
            except (ValueError, SyntaxError):
                return {}
        return {}
    
    # Pre-parse all review data (this happens once during load)
    df['review_data_parsed'] = df['Review_count_by_year_and_month'].apply(safe_parse_review_data)
    
    return df

