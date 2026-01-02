# ============================================================================
# Filter Module
# ============================================================================
"""
Functions to filter listing data based on user criteria
"""

import pandas as pd
from typing import Dict, Any


def apply_filters(df: pd.DataFrame, filter_criteria: Dict[str, Any]) -> pd.DataFrame:
    """
    Apply filter criteria to the DataFrame by adding a 'passes_current_filter' column.
    
    Instead of removing rows, this marks each listing as passing or failing the filters.
    This allows the map to show all listings with different colors.
    
    Args:
        df: DataFrame with listing data
        filter_criteria: Dictionary of filter parameters
        
    Returns:
        Full DataFrame with added 'passes_current_filter' column (True/False)
    """
    result_df = df.copy()
    
    # Start with all listings passing (True)
    mask = pd.Series(True, index=result_df.index)
    
    # Apply each filter condition to the mask
    
    # Filter by Next 30 days booked
    if 'min_30_day_booked' in filter_criteria and 'Next_30_days_booked_days' in result_df.columns:
        min_val = filter_criteria['min_30_day_booked']
        if min_val > 0:  # Only apply if value is greater than 0
            mask &= (result_df['Next_30_days_booked_days'] >= min_val)
    
    # Filter by Next 31-60 days booked
    if 'min_60_day_booked' in filter_criteria and 'Next_30_to_60_days_booked_days' in result_df.columns:
        min_val = filter_criteria['min_60_day_booked']
        if min_val > 0:  # Only apply if value is greater than 0
            mask &= (result_df['Next_30_to_60_days_booked_days'] >= min_val)
    
    # Filter by missing review months this year
    if 'max_missing_months' in filter_criteria and 'Total_missing_review_months_this_year' in result_df.columns:
        max_val = filter_criteria['max_missing_months']
        if max_val < 12:  # Only apply if not the maximum (12)
            mask &= (result_df['Total_missing_review_months_this_year'] <= max_val)
    
    # Filter by 75% rule
    if 'only_75_rule_passed' in filter_criteria and filter_criteria['only_75_rule_passed']:
        if '75_rule_met' in result_df.columns:
            mask &= (result_df['75_rule_met'] == True)
    
    # Filter by rating (Phase 4)
    if 'min_rating' in filter_criteria and 'Rating' in result_df.columns:
        min_val = filter_criteria['min_rating']
        if min_val > 0:  # Only apply if value is greater than 0
            mask &= (result_df['Rating'] >= min_val)
    
    # Filter by review count (Phase 4)
    if 'min_review_count' in filter_criteria and 'Review_count' in result_df.columns:
        min_val = filter_criteria['min_review_count']
        if min_val > 0:  # Only apply if value is greater than 0
            mask &= (result_df['Review_count'] >= min_val)
    
    # Filter by grid IDs (Phase 4)
    if 'selected_grids' in filter_criteria and filter_criteria['selected_grids']:
        if 'Grid_index' in result_df.columns:
            selected_grids = filter_criteria['selected_grids']
            if len(selected_grids) > 0:  # Only apply if grids are selected
                mask &= result_df['Grid_index'].isin(selected_grids)
    
    # Filter by superhost status (Phase 4)
    if 'only_superhosts' in filter_criteria and filter_criteria['only_superhosts']:
        if 'Is_superhost' in result_df.columns:
            mask &= (result_df['Is_superhost'] == True)
    
    # Filter by 55% rule (Phase 4)
    if 'only_55_rule_passed' in filter_criteria and filter_criteria['only_55_rule_passed']:
        if '55_rule_met' in result_df.columns:
            mask &= (result_df['55_rule_met'] == True)
    
    # Filter by bedroom count
    if 'bedroom_count' in filter_criteria and 'Bedroom_count' in result_df.columns:
        bedroom_val = filter_criteria['bedroom_count']
        if bedroom_val > 0:  # Only apply if value is greater than 0
            bedroom_gte = filter_criteria.get('bedroom_gte', True)  # Default to >= if not specified
            if bedroom_gte:
                # Greater than or equal to
                mask &= (result_df['Bedroom_count'] >= bedroom_val)
            else:
                # Exactly equal to
                mask &= (result_df['Bedroom_count'] == bedroom_val)
    
    # Filter by bathroom count
    if 'bathroom_count' in filter_criteria and 'Bath_count' in result_df.columns:
        bathroom_val = filter_criteria['bathroom_count']
        if bathroom_val > 0:  # Only apply if value is greater than 0
            bathroom_gte = filter_criteria.get('bathroom_gte', True)  # Default to >= if not specified
            if bathroom_gte:
                # Greater than or equal to
                mask &= (result_df['Bath_count'] >= bathroom_val)
            else:
                # Exactly equal to
                mask &= (result_df['Bath_count'] == bathroom_val)
    
    # Add the filter result as a new column
    result_df['passes_current_filter'] = mask
    
    return result_df




def get_filter_summary(original_df: pd.DataFrame, filtered_df: pd.DataFrame) -> Dict[str, Any]:
    """
    Generate summary statistics comparing original and filtered data.
    
    Args:
        original_df: Original unfiltered DataFrame
        filtered_df: DataFrame with 'passes_current_filter' column
        
    Returns:
        Dictionary with summary statistics
    """
    total_original = len(original_df)
    
    # Get only the rows that pass the filter
    if 'passes_current_filter' in filtered_df.columns:
        passing_rows = filtered_df[filtered_df['passes_current_filter'] == True]
        total_filtered = len(passing_rows)
    else:
        passing_rows = filtered_df
        total_filtered = len(filtered_df)
    
    percentage = (total_filtered / total_original * 100) if total_original > 0 else 0
    
    summary = {
        'total_original': total_original,
        'total_filtered': total_filtered,
        'percentage': percentage,
        'filtered_out': total_original - total_filtered,
    }
    
    # Compare pass rates for 75% rule
    if '75_rule_met' in filtered_df.columns:
        original_passed = original_df['75_rule_met'].sum()
        filtered_passed = passing_rows['75_rule_met'].sum() if len(passing_rows) > 0 else 0
        
        summary['original_passed_75'] = original_passed
        summary['filtered_passed_75'] = filtered_passed
        summary['original_passed_75_pct'] = (original_passed / total_original * 100) if total_original > 0 else 0
        summary['filtered_passed_75_pct'] = (filtered_passed / total_filtered * 100) if total_filtered > 0 else 0
    
    # Compare pass rates for 55% rule (Phase 4)
    if '55_rule_met' in filtered_df.columns:
        original_passed_55 = original_df['55_rule_met'].sum()
        filtered_passed_55 = passing_rows['55_rule_met'].sum() if len(passing_rows) > 0 else 0
        
        summary['original_passed_55'] = original_passed_55
        summary['filtered_passed_55'] = filtered_passed_55
        summary['original_passed_55_pct'] = (original_passed_55 / total_original * 100) if total_original > 0 else 0
        summary['filtered_passed_55_pct'] = (filtered_passed_55 / total_filtered * 100) if total_filtered > 0 else 0
    
    # Compare average metrics
    if 'Next_30_days_booked_days' in filtered_df.columns and len(passing_rows) > 0:
        summary['avg_30_day_booked'] = passing_rows['Next_30_days_booked_days'].mean()
        summary['original_avg_30_day'] = original_df['Next_30_days_booked_days'].mean()
    
    if 'Next_30_to_60_days_booked_days' in filtered_df.columns and len(passing_rows) > 0:
        summary['avg_60_day_booked'] = passing_rows['Next_30_to_60_days_booked_days'].mean()
        summary['original_avg_60_day'] = original_df['Next_30_to_60_days_booked_days'].mean()
    
    if 'Rating' in filtered_df.columns and len(passing_rows) > 0:
        summary['avg_rating'] = passing_rows['Rating'].mean()
        summary['original_avg_rating'] = original_df['Rating'].mean()
    
    if 'Review_count' in filtered_df.columns and len(passing_rows) > 0:
        summary['avg_review_count'] = passing_rows['Review_count'].mean()
        summary['original_avg_review_count'] = original_df['Review_count'].mean()
    
    # Superhost statistics (Phase 4)
    if 'Is_superhost' in filtered_df.columns and len(passing_rows) > 0:
        superhosts_filtered = passing_rows['Is_superhost'].sum()
        superhosts_original = original_df['Is_superhost'].sum()
        summary['superhosts_count'] = superhosts_filtered
        summary['superhosts_pct'] = (superhosts_filtered / total_filtered * 100) if total_filtered > 0 else 0
        summary['original_superhosts_pct'] = (superhosts_original / total_original * 100) if total_original > 0 else 0
    
    return summary




def get_filter_ranges(df: pd.DataFrame) -> Dict[str, tuple]:
    """
    Get min/max ranges for filterable columns.
    
    Args:
        df: DataFrame with listing data
        
    Returns:
        Dictionary mapping column names to (min, max) tuples
    """
    ranges = {}
    
    if 'Next_30_days_booked_days' in df.columns:
        ranges['30_day_booked'] = (
            int(df['Next_30_days_booked_days'].min()),
            int(df['Next_30_days_booked_days'].max())
        )
    
    if 'Next_30_to_60_days_booked_days' in df.columns:
        ranges['60_day_booked'] = (
            int(df['Next_30_to_60_days_booked_days'].min()),
            int(df['Next_30_to_60_days_booked_days'].max())
        )
    
    if 'Total_missing_review_months_this_year' in df.columns:
        ranges['missing_months'] = (
            int(df['Total_missing_review_months_this_year'].min()),
            int(df['Total_missing_review_months_this_year'].max())
        )
    
    if 'Rating' in df.columns:
        ranges['rating'] = (
            float(df['Rating'].min()),
            float(df['Rating'].max())
        )
    
    if 'Review_count' in df.columns:
        ranges['review_count'] = (
            int(df['Review_count'].min()),
            int(df['Review_count'].max())
        )
    
    if 'Bedroom_count' in df.columns:
        ranges['bedroom_count'] = (
            int(df['Bedroom_count'].min()),
            int(df['Bedroom_count'].max())
        )
    
    if 'Bath_count' in df.columns:
        ranges['bathroom_count'] = (
            int(df['Bath_count'].min()),
            int(df['Bath_count'].max())
        )
    
    return ranges




def validate_filter_criteria(filter_criteria: Dict[str, Any], ranges: Dict[str, tuple]) -> bool:
    """
    Validate that filter criteria are within acceptable ranges.
    
    Args:
        filter_criteria: Dictionary of filter parameters
        ranges: Dictionary of valid ranges for each filter
        
    Returns:
        True if all criteria are valid
    """
    # Check 30-day booked range
    if 'min_30_day_booked' in filter_criteria and '30_day_booked' in ranges:
        min_val, max_val = ranges['30_day_booked']
        if not (min_val <= filter_criteria['min_30_day_booked'] <= max_val):
            return False
    
    # Check 60-day booked range
    if 'min_60_day_booked' in filter_criteria and '60_day_booked' in ranges:
        min_val, max_val = ranges['60_day_booked']
        if not (min_val <= filter_criteria['min_60_day_booked'] <= max_val):
            return False
    
    # Check missing months range
    if 'max_missing_months' in filter_criteria and 'missing_months' in ranges:
        min_val, max_val = ranges['missing_months']
        if not (min_val <= filter_criteria['max_missing_months'] <= max_val):
            return False
    
    return True

