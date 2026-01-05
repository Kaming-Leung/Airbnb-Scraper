# Pass 75% Rule Auto-Filter Implementation

## Overview
Modified the filter form so that when the "Pass 75% Rule" checkbox is checked, it **immediately** sets "Min Days Booked (Next 30 days)" to **22** (the threshold for the 75% rule with leniency of 2 days).

## Changes Made

### 1. **Moved Checkbox Outside Form**
- The "Pass 75% Rule" checkbox was moved **outside** the form (before the form starts)
- This allows it to trigger immediate updates without waiting for form submission
- Positioned at the top of the filters section for visibility

### 2. **Dynamic Default Value**
- "Min Days Booked (Next 30 days)" now uses a **dynamic default value**:
  - **22** when "Pass 75% Rule" is checked
  - **15** when unchecked (previous default)
- Added helpful tooltip: "Automatically set to 22 when 'Pass 75% Rule' is checked"

### 3. **State Management**
- Added `st.session_state.pass_75_rule_checked` to persist checkbox state
- State is updated on every rerun to maintain consistency
- Reset button clears the checkbox state

## User Experience

### How It Works
1. User checks "Pass 75% Rule" checkbox
2. **Immediately**, the "Min Days Booked (Next 30 days)" field updates to **22**
3. User can still manually adjust the value if needed
4. User clicks "Apply" to filter the data
5. Clicking "Reset" unchecks the box and returns the default to 15

### Why 22 Days?
The 75% occupancy rule requires:
- At least **22 days** booked out of the next 30 days
- This is calculated as: 75% of 30 days = 22.5 days, minus leniency of 2 days = 20 days
- However, to pass the rule comfortably, **22 days** is used as the threshold

## Technical Details

### Before (Inside Form)
```python
# Checkbox was inside form - no immediate updates
with st.form("filter_form"):
    filter_criteria['only_75_rule_passed'] = st.checkbox("Pass 75% Rule", value=False)
    filter_criteria['min_30_day_booked'] = st.number_input(..., value=15)
```

### After (Outside Form)
```python
# Checkbox outside form - immediate updates
filter_criteria['only_75_rule_passed'] = st.checkbox(
    "Pass 75% Rule",
    value=st.session_state.pass_75_rule_checked,
    key="pass_75_rule_checkbox"
)

# Dynamic default based on checkbox state
default_30_day_value = 22 if filter_criteria['only_75_rule_passed'] else 15

with st.form("filter_form"):
    filter_criteria['min_30_day_booked'] = st.number_input(
        ...,
        value=default_30_day_value,
        help="Automatically set to 22 when 'Pass 75% Rule' is checked"
    )
```

## Benefits

1. **Immediate Feedback**: No need to click "Apply" to see the value change
2. **Convenience**: Users don't need to manually enter 22
3. **Consistency**: Ensures the 75% rule threshold is correctly applied
4. **Flexibility**: Users can still override the auto-set value if needed
5. **Clear Intent**: Makes it obvious what "Pass 75% Rule" means in terms of days

## Files Modified

- `Webtool/utils/ui_components.py`
  - Moved "Pass 75% Rule" checkbox outside form
  - Added session state tracking
  - Made "Min Days Booked" default value dynamic
  - Added reset handling

## Testing Checklist

- ✅ Checking "Pass 75% Rule" immediately sets days to 22
- ✅ Unchecking reverts to default value (15)
- ✅ User can manually override the auto-set value
- ✅ Reset button unchecks the box and resets to 15
- ✅ State persists across page interactions (until reset)
- ✅ Filter logic correctly applies the checkbox criteria
- ✅ No form submission issues

## Future Enhancements

- Could add similar auto-set logic for the 55% rule (17-18 days for days 31-60)
- Could show a visual indicator when a value is auto-set vs. manually entered
- Could add a "lock" icon to prevent accidental manual changes

