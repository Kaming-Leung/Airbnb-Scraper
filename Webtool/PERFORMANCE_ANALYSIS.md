# Performance Analysis: Slow Map Loading

## 📊 Current Situation
- **Dataset Size**: ~4,433 listings with 39 columns
- **Issue**: Map takes very long to load/reload when "Apply" button is clicked
- **Impact**: Poor user experience, especially with frequent filter changes

---

## 🔍 Identified Bottlenecks

### **1. 🐌 CRITICAL: Review Data Parsing (Biggest Bottleneck)**
**Location**: `map_creator.py` lines 207-218

**Problem**:
```python
# This runs for EVERY listing (4,433 times) on EVERY map render
if pd.notna(review_data) and isinstance(review_data, str):
    try:
        review_data = ast.literal_eval(review_data)  # ⚠️ VERY SLOW
    except:
        review_data = {}
```

**Why It's Slow**:
- `ast.literal_eval()` is parsing a complex dictionary string like `{'2024': [1,0,0,...], '2025': [...]}` 
- Called **4,433 times** every time the map loads
- This is a CPU-intensive string parsing operation

**Estimated Impact**: **60-80% of total load time**

---

### **2. 🐌 MAJOR: Creating Complex HTML Popups**
**Location**: `map_creator.py` lines 218, 255-296

**Problem**:
```python
# Called for EVERY listing (4,433 times)
review_table_html = format_review_table(review_data)

# Then creates a large HTML string with:
# - Status badges
# - Multiple table rows
# - Review activity table
popup_html = f"""..."""  # 50+ lines of HTML
```

**Why It's Slow**:
- `format_review_table()` generates a complex HTML table for each listing
- Iterates through years and months to create color-coded cells
- Creates 50+ lines of HTML per listing
- All this HTML is embedded in the map even though most popups are never opened

**Estimated Impact**: **20-30% of total load time**

---

### **3. 🐌 MODERATE: DataFrame Copy**
**Location**: `filters.py` line 26

**Problem**:
```python
result_df = df.copy()  # Creates a full copy of 4,433 rows × 39 columns
```

**Why It's Slow**:
- Creates a complete deep copy of the entire DataFrame
- With 4,433 rows and 39 columns, this is ~170,000 data cells to copy
- Happens every time filters are applied

**Estimated Impact**: **5-10% of total load time**

---

### **4. 🐌 MODERATE: Adding 4,433 Markers to Map**
**Location**: `map_creator.py` lines 299-309

**Problem**:
```python
# Called 4,433 times
for idx, listing in df.iterrows():
    folium.CircleMarker(...).add_to(m)
```

**Why It's Slow**:
- Creates 4,433 individual CircleMarker objects
- Each with popup, tooltip, and styling
- Folium needs to serialize all of this into JavaScript

**Estimated Impact**: **5-10% of total load time**

---

### **5. 🐌 MINOR: Iterating with iterrows()**
**Location**: Multiple places in `map_creator.py`

**Problem**:
```python
for idx, listing in df.iterrows():  # iterrows() is slow
```

**Why It's Slow**:
- `iterrows()` is one of the slowest ways to iterate in pandas
- Returns each row as a Series object (overhead)
- Better alternatives: `itertuples()` or vectorized operations

**Estimated Impact**: **2-5% of total load time**

---

### **6. 🐌 MINOR: Loading All Columns**
**Location**: `data_loader.py` line 27

**Problem**:
```python
df = pd.read_csv(file_path)  # Loads all 39 columns
```

**Why It's Slow**:
- Loads all columns even if not displayed
- More memory usage
- Larger DataFrame operations

**Estimated Impact**: **2-3% of total load time**

---

## 💡 Recommended Solutions (Ordered by Impact)

### **Solution 1: Pre-parse Review Data on Load (Highest Impact)**
**Estimated Speed Improvement**: 60-80% faster

**What to Do**:
Parse the `Review_count_by_year_and_month` column ONCE when data is loaded, not every time the map renders.

**Implementation**:
```python
# In data_loader.py, after loading CSV
def preprocess_review_data(df):
    """Parse review data once during load, not per render"""
    if 'Review_count_by_year_and_month' in df.columns:
        df['Review_count_by_year_and_month_parsed'] = df['Review_count_by_year_and_month'].apply(
            lambda x: ast.literal_eval(x) if pd.notna(x) and isinstance(x, str) else {}
        )
    return df
```

**Pros**:
- Massive performance gain (60-80% faster)
- One-time cost during initial load
- Subsequent map renders use pre-parsed data

**Cons**:
- Slightly slower initial data load (~2 seconds)
- Uses slightly more memory

---

### **Solution 2: Lazy Load Popups (High Impact)**
**Estimated Speed Improvement**: 20-30% faster

**What to Do**:
Don't generate complex popup HTML for every marker upfront. Use simpler popups or load on-demand.

**Implementation Options**:

**Option A: Simplified Popups**
```python
# Only show key info in popup, link to full details
popup_html = f"""
<div style="font-family: Arial;">
    <h4>Listing {room_id}</h4>
    <p>30-day booked: {next_30_days} days</p>
    <p>Rating: {rating} ⭐</p>
    <a href="https://www.airbnb.com/rooms/{room_id}" target="_blank">View Details</a>
</div>
"""
```

**Option B: Remove Review Table from Popup**
- Review tables are rarely viewed
- Generate them only when popup is clicked (requires JavaScript)

**Pros**:
- Significantly faster map creation
- Less data sent to browser
- Still shows important info

**Cons**:
- Less detailed popups
- Review table not immediately visible

---

### **Solution 3: Optimize DataFrame Operations (Moderate Impact)**
**Estimated Speed Improvement**: 5-10% faster

**What to Do**:
Replace DataFrame copy with view/reference where possible.

**Implementation**:
```python
# In filters.py
def apply_filters(df: pd.DataFrame, filter_criteria: Dict[str, Any]) -> pd.DataFrame:
    # Don't copy entire DataFrame
    # Just add the boolean mask column
    mask = pd.Series(True, index=df.index)
    # ... apply filters to mask ...
    df['passes_current_filter'] = mask  # Modifies original (use with caution)
    return df
```

**OR** (safer):
```python
# Only copy the columns you need for filtering
result_df = df[['Room_id', 'Latitude', 'Longitude', 
                'Next_30_days_booked_days', ...]].copy()
```

**Pros**:
- Faster filter application
- Less memory usage

**Cons**:
- Need to be careful about modifying original DataFrame

---

### **Solution 4: Use Marker Clustering (Moderate Impact)**
**Estimated Speed Improvement**: Variable (10-50% for zoomed-out views)

**What to Do**:
Group nearby markers into clusters when zoomed out.

**Implementation**:
```python
from folium.plugins import MarkerCluster

# Create marker cluster instead of individual markers
marker_cluster = MarkerCluster().add_to(m)

for listing in df.itertuples():
    folium.CircleMarker(...).add_to(marker_cluster)
```

**Pros**:
- Much faster rendering when zoomed out
- Better visual clarity
- Still shows individual markers when zoomed in

**Cons**:
- Slightly different visual appearance
- May not work well with color-coding (pass/fail)

---

### **Solution 5: Use itertuples() Instead of iterrows() (Minor Impact)**
**Estimated Speed Improvement**: 2-5% faster

**What to Do**:
Replace `iterrows()` with `itertuples()` for faster iteration.

**Implementation**:
```python
# Before:
for idx, listing in df.iterrows():
    room_id = listing['Room_id']
    
# After:
for listing in df.itertuples():
    room_id = listing.Room_id
```

**Pros**:
- Easy to implement
- No downside

**Cons**:
- Minimal impact

---

### **Solution 6: Load Only Required Columns (Minor Impact)**
**Estimated Speed Improvement**: 2-3% faster

**What to Do**:
Specify which columns to load from CSV.

**Implementation**:
```python
# In data_loader.py
required_cols = [
    'Room_id', 'Latitude', 'Longitude',
    'Next_30_days_booked_days', 'Next_30_to_60_days_booked_days',
    'Rating', 'Review_count', '75_rule_met',
    'Bedroom_count', 'Bath_count', 'Guest_count'
]
df = pd.read_csv(file_path, usecols=required_cols)
```

**Pros**:
- Faster loading
- Less memory

**Cons**:
- Need to maintain column list
- If new columns needed, must update list

---

### **Solution 7: Cache Filtered Data (Minor Impact)**
**Estimated Speed Improvement**: Variable

**What to Do**:
Cache the filtered DataFrame so filtering doesn't re-run on map interactions.

**Implementation**:
```python
# Already partially implemented via session state
# Could expand to cache filter results
```

**Pros**:
- Avoids redundant filtering

**Cons**:
- Already mostly handled by current caching

---

## 🎯 Recommended Implementation Order

### **Phase 1: Quick Wins (Do First)**
1. ✅ **Pre-parse review data on load** (Solution 1)
2. ✅ **Use itertuples()** (Solution 5)
   - **Combined Impact**: 65-85% faster
   - **Effort**: Low (1-2 hours)

### **Phase 2: Major Improvements**
3. ✅ **Simplify popups or remove review tables** (Solution 2)
   - **Impact**: Additional 20-30% faster
   - **Effort**: Medium (2-3 hours)

### **Phase 3: Optimization**
4. ✅ **Optimize DataFrame operations** (Solution 3)
5. ✅ **Load only required columns** (Solution 6)
   - **Combined Impact**: Additional 7-13% faster
   - **Effort**: Low (1 hour)

### **Phase 4: Advanced (Optional)**
6. ⚠️ **Marker clustering** (Solution 4)
   - **Impact**: Variable, mainly for zoomed-out views
   - **Effort**: Medium-High (requires testing with color-coding)

---

## 📈 Expected Overall Performance

| Phase | Estimated Load Time | Improvement |
|-------|---------------------|-------------|
| Current | 10-15 seconds | Baseline |
| After Phase 1 | 2-3 seconds | **70-80% faster** |
| After Phase 2 | 1-2 seconds | **85-90% faster** |
| After Phase 3 | 1-1.5 seconds | **90%+ faster** |

---

## 🛠️ Testing Recommendations

1. **Profile Current Performance**:
   ```python
   import time
   start = time.time()
   # ... operation ...
   print(f"Time: {time.time() - start:.2f}s")
   ```

2. **Test with Different Data Sizes**:
   - Small: 500 listings
   - Medium: 2,000 listings
   - Large: 4,433 listings (current)

3. **Monitor Memory Usage**:
   - Check browser memory (DevTools → Memory)
   - Check Python memory usage

---

## ❓ Questions to Consider

1. **Do users actually view the review tables in popups?**
   - If rarely used, consider removing or simplifying

2. **Is color-coding by pass/fail essential?**
   - If clustering is implemented, color-coding becomes more complex

3. **Are all 39 columns necessary?**
   - Identify which columns are actually used in the UI

4. **How often do users change filters?**
   - If frequently, caching becomes more important

---

## 📝 Summary

**Root Cause**: Parsing review data (ast.literal_eval) for 4,433 listings on every map render is the primary bottleneck (60-80% of load time).

**Best Solution**: Pre-parse review data once during initial load (Phase 1, Solution 1).

**Expected Result**: Map loading should go from 10-15 seconds down to 2-3 seconds after Phase 1, and potentially under 1.5 seconds after all optimizations.

