# Bedroom & Bathroom Filters

## Overview
Added two new filter inputs to the dashboard that allow filtering listings by number of bedrooms and bathrooms.

## Features

### 1. **Bedroom Filter**
- **Column**: `Bedroom_count`
- **Input Type**: Number input (0 to max bedrooms in dataset)
- **Toggle Checkbox**: ≥ symbol
  - **Checked (default)**: Filter for listings with **≥** (greater than or equal to) the specified number of bedrooms
  - **Unchecked**: Filter for listings with **exactly** the specified number of bedrooms

### 2. **Bathroom Filter**
- **Column**: `Bath_count`
- **Input Type**: Number input (0 to max bathrooms in dataset)
- **Toggle Checkbox**: ≥ symbol
  - **Checked (default)**: Filter for listings with **≥** (greater than or equal to) the specified number of bathrooms
  - **Unchecked**: Filter for listings with **exactly** the specified number of bathrooms

## How It Works

### UI Layout
Both filters use a two-column layout:
- **Left column (wider)**: Number input field
- **Right column (narrow)**: Checkbox with ≥ symbol

### Filter Behavior
- **Default Value**: 0 (no filter applied)
- **When Value = 0**: Filter is not applied, all listings are included
- **When Value > 0**: Filter is applied based on checkbox state

### Apply Button
All filters (including bedrooms and bathrooms) are wrapped in a form. Changes only take effect when the **"Apply"** button is clicked.

## Examples

### Example 1: Find Listings with 3+ Bedrooms
```
Bedrooms: 3
≥ Checkbox: ✅ Checked
Result: Shows listings with 3, 4, 5, or more bedrooms
```

### Example 2: Find Listings with Exactly 2 Bedrooms
```
Bedrooms: 2
≥ Checkbox: ☐ Unchecked
Result: Shows only listings with exactly 2 bedrooms
```

### Example 3: Find Listings with 2+ Bathrooms AND Exactly 3 Bedrooms
```
Bedrooms: 3
≥ Checkbox: ☐ Unchecked

Bathrooms: 2
≥ Checkbox: ✅ Checked

Result: Shows listings with exactly 3 bedrooms AND 2 or more bathrooms
```

### Example 4: No Bedroom/Bathroom Filtering
```
Bedrooms: 0
Bathrooms: 0
Result: All listings shown (no bedroom/bathroom filter applied)
```

## Visual Indicators

### On the Map
- 🔴 **Red dots**: Listings that **pass** all current filters
- 🔵 **Blue dots**: Listings that **fail** one or more filters

### In the Sidebar
- At the bottom of the sidebar, you'll see:
  ```
  🔴 X pass | 🔵 Y fail
  ```
  Where X is the number passing filters and Y is the number failing.

## Technical Details

### Files Modified
1. **`utils/ui_components.py`**:
   - Added bedroom and bathroom input fields in `render_filter_form()`
   - Used two-column layout for compact display
   - Added tooltips to explain checkbox behavior

2. **`utils/filters.py`**:
   - Updated `apply_filters()` to handle bedroom/bathroom filtering
   - Added logic for both >= and == comparisons
   - Only applies filter when value > 0
   - Updated `get_filter_ranges()` to include bedroom/bathroom ranges

### Filter Logic
```python
# Bedroom filter logic
if bedroom_count > 0:
    if bedroom_gte:  # Checkbox is checked
        mask &= (df['Bedroom_count'] >= bedroom_count)
    else:  # Checkbox is unchecked
        mask &= (df['Bedroom_count'] == bedroom_count)

# Same logic for bathrooms
```

### Data Requirements
For these filters to appear in the UI, your CSV files must contain:
- `Bedroom_count` column (for bedroom filter)
- `Bath_count` column (for bathroom filter)

If either column is missing, that filter will not be displayed.

## Tips

1. **Use >= for broad searches**: Keep the checkbox checked when you want "at least X bedrooms/bathrooms"
2. **Use == for specific needs**: Uncheck the box when you need exactly X bedrooms/bathrooms
3. **Combine with other filters**: These filters work alongside all other filters (30-day booked, 75% rule, etc.)
4. **Set to 0 to disable**: If you don't want to filter by bedrooms or bathrooms, leave the value at 0
5. **Remember to click Apply**: Changes only take effect when you click the "Apply" button

## Common Use Cases

### Find Large Properties
```
Bedrooms: 4
≥ Checkbox: ✅ Checked
Bathrooms: 3
≥ Checkbox: ✅ Checked
```
*Shows listings with 4+ bedrooms and 3+ bathrooms*

### Find Studio Apartments
```
Bedrooms: 0
≥ Checkbox: ☐ Unchecked
```
*Shows only listings with 0 bedrooms (studios)*

### Find Standard 2BR/2BA Units
```
Bedrooms: 2
≥ Checkbox: ☐ Unchecked
Bathrooms: 2
≥ Checkbox: ☐ Unchecked
```
*Shows only listings with exactly 2 bedrooms and 2 bathrooms*

### Find Luxury Properties
```
Bedrooms: 5
≥ Checkbox: ✅ Checked
Bathrooms: 4
≥ Checkbox: ✅ Checked
Min 30-Day Booked: 20
Only 75% Rule: ✅ Checked
```
*Shows high-performing luxury properties with 5+ bedrooms and 4+ bathrooms*

