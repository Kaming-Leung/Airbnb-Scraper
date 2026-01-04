# ============================================================================
# Year Filter Helper Module
# ============================================================================
"""
Helper functions for managing multiple year-based review filters.
"""

import pandas as pd
from typing import List, Dict, Any


def get_available_years(df: pd.DataFrame) -> List[int]:
    """
    Extract all unique years from DataFrame attributes or precomputed columns.
    
    This is optimized to use precomputed year data when available,
    falling back to scanning review_data_parsed if needed.
    
    Args:
        df: DataFrame with 'review_data_parsed' column or precomputed year columns
        
    Returns:
        List of years (sorted, most recent first)
    """
    # Try to use precomputed years from DataFrame attributes (fastest)
    if hasattr(df, 'attrs') and 'available_years' in df.attrs:
        year_strings = df.attrs['available_years']
        return [int(y) for y in year_strings]
    
    # Try to extract from precomputed columns (fast)
    year_cols = [col for col in df.columns if col.startswith('missing_reviews_')]
    if year_cols:
        years = []
        for col in year_cols:
            year_str = col.replace('missing_reviews_', '')
            try:
                years.append(int(year_str))
            except:
                continue
        if years:
            return sorted(years, reverse=True)
    
    # Fallback: scan review_data_parsed (slower)
    years = set()
    
    if 'review_data_parsed' in df.columns:
        for data in df['review_data_parsed'].dropna():
            if isinstance(data, dict):
                years.update(data.keys())
    
    # Convert to integers and filter valid years
    valid_years = []
    for year in years:
        try:
            year_int = int(year)
            if 2000 <= year_int <= 2030:  # Reasonable range
                valid_years.append(year_int)
        except:
            continue
    
    return sorted(valid_years, reverse=True)  # Most recent first


def count_missing_months_for_year(review_data: Any, year: str) -> int:
    """
    Count the number of missing review months (zeros) for a specific year.
    
    Args:
        review_data: Pre-parsed review data dictionary
        year: Year as string (e.g., '2025')
        
    Returns:
        Number of months with 0 reviews (0-12)
    """
    if not isinstance(review_data, dict):
        return 12  # No data = all months missing
    
    year_data = review_data.get(year, [])
    if not year_data:
        return 12  # Year not in data = all months missing
    
    return year_data.count(0)  # Count zeros


def apply_multiple_year_filters(df: pd.DataFrame, year_filters: List[Dict[str, Any]]) -> pd.Series:
    """
    Apply multiple year-based missing review month filters using VECTORIZED operations.
    
    This function uses precomputed 'missing_reviews_{year}' columns for 10-100x
    speed improvement vs the old .apply() approach. Falls back to .apply() if
    precomputed columns are not available.
    
    Args:
        df: DataFrame with precomputed 'missing_reviews_{year}' columns
        year_filters: List of filter dicts, each containing:
            - 'year': int (e.g., 2025)
            - 'max_missing': int (0-12)
            - 'enabled': bool (whether to apply this filter)
    
    Returns:
        Boolean mask for filtering
    """
    if not year_filters:
        return pd.Series([True] * len(df), index=df.index)
    
    # Start with all True
    mask = pd.Series([True] * len(df), index=df.index)
    
    # Apply each enabled filter (AND logic)
    for year_filter in year_filters:
        if not year_filter.get('enabled', True):
            continue  # Skip disabled filters
        
        year = str(year_filter['year'])
        max_missing = year_filter['max_missing']
        
        # Try to use precomputed column (VECTORIZED - fast!)
        precomputed_col = f'missing_reviews_{year}'
        
        if precomputed_col in df.columns:
            # VECTORIZED: Direct column comparison (10-100x faster)
            mask = mask & (df[precomputed_col] <= max_missing)
        else:
            # Fallback: Use .apply() if precomputed column doesn't exist
            # (This should only happen if data loading didn't precompute columns)
            if 'review_data_parsed' in df.columns:
                missing_counts = df['review_data_parsed'].apply(
                    lambda data: count_missing_months_for_year(data, year)
                )
                mask = mask & (missing_counts <= max_missing)
    
    return mask


def get_default_year_filters(available_years: List[int]) -> List[Dict[str, Any]]:
    """
    Get default year filters (current year and last year).
    
    Args:
        available_years: List of available years from data
        
    Returns:
        List of default filter configurations
    """
    if not available_years:
        return []
    
    # Default: Show up to 3 most recent years
    default_filters = []
    
    for i, year in enumerate(available_years[:3]):
        default_filters.append({
            'year': year,
            'max_missing': 0 if i == 0 else 3,  # Stricter for current year
            'enabled': i < 2  # Only enable first 2 by default
        })
    
    return default_filters

