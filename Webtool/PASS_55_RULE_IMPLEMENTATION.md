# Pass 55% Rule Implementation

## Overview
Added a new "Pass 55% Rule" checkbox that **automatically** sets "Min Days Booked (Next 30-60 days)" to **17** (the threshold for the 55% rule with leniency).

This complements the existing "Pass 75% Rule" checkbox and follows the same immediate-update pattern.

## Changes Made

### 1. **New Checkbox Added**
- "Pass 55% Rule" checkbox positioned right after "Pass 75% Rule"
- Located **outside** the form for immediate updates
- Uses session state to persist checkbox state

### 2. **Dynamic Default Value**
- "Min Days Booked (Next 30-60 days)" now uses a **dynamic default value**:
  - **17** when "Pass 55% Rule" is checked
  - **0** when unchecked (previous default)
- Added helpful tooltip: "Automatically set to 17 when 'Pass 55% Rule' is checked"

### 3. **Filter Logic Integration**
- Added filter logic in `filters.py` to respect the `only_55_rule_passed` criterion
- Filters by the `55_rule_met` column when checkbox is checked
- Uses same pattern as the 75% rule filter

### 4. **State Management**
- Added `st.session_state.pass_55_rule_checked` to persist checkbox state
- State is updated on every rerun
- Reset button clears both 75% and 55% checkbox states

## User Experience

### How It Works
1. User checks "Pass 55% Rule" checkbox
2. **Immediately**, the "Min Days Booked (Next 30-60 days)" field updates to **17**
3. User can still manually adjust the value if needed
4. User clicks "Apply" to filter the data
5. Filter respects both the numeric threshold AND the `55_rule_met` column
6. Clicking "Reset" unchecks the box and returns the default to 0

### Why 17 Days?
The 55% occupancy rule requires:
- At least **17 days** booked out of 30 days (days 31-60)
- This is calculated as: 55% of 30 days = 16.5 days, minus leniency of 2 days = ~15 days
- However, to pass the rule comfortably, **17 days** is used as the threshold

### Combined Use
Both checkboxes can be used together:
- "Pass 75% Rule" → Sets "Next 30 days" to 22
- "Pass 55% Rule" → Sets "Next 30-60 days" to 17
- This ensures listings pass **both** occupancy rules

## Technical Details

### Checkbox Implementation (Outside Form)
```python
# "Pass 55% Rule" checkbox OUTSIDE form for immediate effect
if 'pass_55_rule_checked' not in st.session_state:
    st.session_state.pass_55_rule_checked = False

filter_criteria['only_55_rule_passed'] = st.checkbox(
    "Pass 55% Rule",
    value=st.session_state.pass_55_rule_checked,
    key="pass_55_rule_checkbox"
)

# Update session state
st.session_state.pass_55_rule_checked = filter_criteria['only_55_rule_passed']

# Dynamic default based on checkbox state
default_60_day_value = 17 if filter_criteria['only_55_rule_passed'] else 0
```

### Number Input with Dynamic Default
```python
filter_criteria['min_60_day_booked'] = st.number_input(
    "Min Days Booked (Next 30-60 days)",
    min_value=0,
    max_value=30,
    value=default_60_day_value,  # Dynamic: 17 or 0
    step=1,
    help="Automatically set to 17 when 'Pass 55% Rule' is checked"
)
```

### Filter Logic
```python
# Filter by 55% rule
if 'only_55_rule_passed' in filter_criteria and filter_criteria['only_55_rule_passed']:
    if '55_rule_met' in result_df.columns:
        mask &= (result_df['55_rule_met'] == True)
```

### Reset Handling
```python
# Handle reset: clear both checkbox states
if reset_clicked:
    st.session_state.pass_75_rule_checked = False
    st.session_state.pass_55_rule_checked = False
```

## Files Modified

1. **`Webtool/utils/ui_components.py`**
   - Added "Pass 55% Rule" checkbox outside form
   - Added session state tracking (`pass_55_rule_checked`)
   - Made "Min Days Booked (Next 30-60 days)" default value dynamic
   - Added reset handling for 55% checkbox

2. **`Webtool/utils/filters.py`**
   - Added filter logic for `only_55_rule_passed` criterion
   - Filters by `55_rule_met` column when checkbox is checked

## Benefits

1. **Immediate Feedback**: No need to click "Apply" to see the value change
2. **Convenience**: Users don't need to manually enter 17
3. **Consistency**: Ensures the 55% rule threshold is correctly applied
4. **Flexibility**: Users can still override the auto-set value
5. **Clear Intent**: Makes it obvious what "Pass 55% Rule" means
6. **Comprehensive Filtering**: Works alongside the 75% rule for multi-criteria filtering

## UI Layout

The filter section now shows (from top to bottom):
```
🎚️ Filters
  ☐ Pass 75% Rule
  ☐ Pass 55% Rule
  
  [Apply] [Reset]
  ──────────────
  Min Days Booked (Next 30 days): [22 or 15]
  Min Days Booked (Next 30-60 days): [17 or 0]
  ...
```

## Testing Checklist

- ✅ Checking "Pass 55% Rule" immediately sets days to 17
- ✅ Unchecking reverts to default value (0)
- ✅ User can manually override the auto-set value
- ✅ Reset button unchecks both 75% and 55% boxes
- ✅ State persists across page interactions (until reset)
- ✅ Filter logic correctly applies the `55_rule_met` column filter
- ✅ Both checkboxes can be used simultaneously
- ✅ No form submission issues
- ✅ Works when `55_rule_met` column is missing (graceful handling)

## Example Use Cases

### Use Case 1: High-Performance Listings Only
- Check "Pass 75% Rule" → 22 days (next 30)
- Check "Pass 55% Rule" → 17 days (next 30-60)
- Result: Only listings that pass both occupancy thresholds

### Use Case 2: Near-Future Occupancy Focus
- Check "Pass 75% Rule" → 22 days
- Leave "Pass 55% Rule" unchecked → 0 days
- Result: Focus on listings with high near-term bookings

### Use Case 3: Long-Term Occupancy Focus
- Leave "Pass 75% Rule" unchecked → 15 days
- Check "Pass 55% Rule" → 17 days
- Result: Listings with moderate near-term but strong long-term bookings

### Use Case 4: Custom Thresholds
- Check both boxes to get defaults
- Manually adjust to custom values (e.g., 20 and 15)
- Result: Fine-tuned occupancy filtering

## Future Enhancements

- Could add visual indicators showing which values are auto-set vs. manual
- Could add a "Both Rules" preset button that checks both boxes at once
- Could show a summary: "X listings pass 75% rule, Y pass 55% rule, Z pass both"
- Could add configurable thresholds (let users define what "pass" means)

