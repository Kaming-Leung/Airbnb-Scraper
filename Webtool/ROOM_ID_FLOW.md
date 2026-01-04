# 🔄 Room ID Flow: From Click to Display

## Overview

This document explains exactly how a Room ID is captured from a map click, stored, and displayed in the "📋 Selected Listing Details" section.

---

## 🎯 Complete Flow

```
User clicks marker
       ↓
PyDeck captures click event with layer ID and object data
       ↓
Streamlit reruns app with event data in memory
       ↓
get_selected_listing() extracts Room ID from event
       ↓
Room ID stored in st.session_state['clicked_room_id']
       ↓
render_listing_detail_panel() displays full details
       ↓
User can see and copy Room ID in detail panel
```

---

## 📦 Detailed Step-by-Step

### Step 1: User Clicks Marker

**Where**: User interaction with PyDeck map  
**File**: `app.py` line 208-213

```python
event = render_deck_map_with_click_handling(
    df=filtered_df,
    grid_df=grid_df,
    show_grids=show_grids,
    location=location
)
```

**What happens**: 
- User clicks a red or blue marker on the map
- PyDeck's `on_select="rerun"` triggers a Streamlit rerun
- The click event data is passed to the `event` variable

---

### Step 2: Event Structure

**Where**: PyDeck layer configuration  
**File**: `utils/deck_map_renderer.py` line 79-92

```python
scatterplot_layer = pdk.Layer(
    'ScatterplotLayer',
    data=map_data,
    id='listings',  # ← Critical! This is the layer ID
    get_position=['Longitude', 'Latitude'],
    ...
    pickable=True,  # ← Enables clicking
)
```

**Event structure returned**:
```python
{
    "selection": {
        "indices": {
            "listings": [5]  # Index of clicked point in the data
        },
        "objects": {
            "listings": [  # ← Organized by layer ID!
                {
                    "Room_id": 12345,  # ← The Room ID we want!
                    "Rating": 4.8,
                    "Review_count": 123,
                    "Next_30_days_booked_days": 22,
                    "passes_current_filter": True,
                    ...
                }
            ]
        }
    }
}
```

**Key insight**: 
- The event contains the **complete object data** for the clicked point
- It's organized by **layer ID** (`'listings'`)
- The Room ID is directly accessible in the object

---

### Step 3: Extract Room ID from Event

**Where**: Click event processing  
**File**: `app.py` line 232-235

```python
# Extract selected listing from click event
selected_listing = get_selected_listing(event, df)

if selected_listing is not None:
    # Store Room ID in session state for reference
    room_id = selected_listing.get('Room_id')
```

**What `get_selected_listing()` does**:

**File**: `utils/deck_map_renderer.py` line 271-331

```python
def get_selected_listing(event: Optional[dict], df: pd.DataFrame) -> Optional[pd.Series]:
    """Extract selected listing from PyDeck click event."""
    
    # 1. Check if event exists
    if not event or not event.get('selection'):
        return None
    
    # 2. Get objects from selection
    selection = event['selection']
    objects = selection['objects']
    
    # 3. Access the 'listings' layer
    if 'listings' not in objects:
        return None
    
    listings_objects = objects['listings']
    
    # 4. Get first selected object
    selected_obj = listings_objects[0]
    
    # 5. Extract Room_id
    room_id = selected_obj.get('Room_id')  # ← HERE!
    
    # 6. Find matching row in full DataFrame
    matching_rows = df[df['Room_id'] == room_id]
    
    # 7. Return the full listing data
    return matching_rows.iloc[0]
```

**Key operations**:
1. ✅ Validates event structure
2. ✅ Accesses `objects['listings']` using the layer ID
3. ✅ Extracts `Room_id` from the clicked object
4. ✅ Looks up the full listing in the DataFrame
5. ✅ Returns complete listing data as a Pandas Series

---

### Step 4: Store Room ID in Session State

**Where**: After successful extraction  
**File**: `app.py` line 236-238

```python
# Store Room ID in session state for reference
room_id = selected_listing.get('Room_id')
st.session_state['clicked_room_id'] = room_id

print(f"✅ Successfully extracted Room ID: {room_id} from click event")

st.success(f"✅ Clicked on Room #{room_id} from map")
```

**Why store in session_state?**
- ✅ **Persistence**: Room ID survives across Streamlit reruns
- ✅ **Reference**: Can check last clicked Room ID
- ✅ **Debugging**: Easy to inspect what was clicked
- ✅ **Future use**: Can be used for comparison, history, etc.

**Session state key**: `st.session_state['clicked_room_id']`

---

### Step 5: Display in "📋 Selected Listing Details" Section

**Where**: Detail panel header  
**File**: `app.py` line 223-225

```python
st.markdown("---")
st.markdown("### 📋 Selected Listing Details")  # ← Section header

st.success(f"✅ Clicked on Room #{room_id} from map")  # ← Confirmation
```

**Then**: Full details rendered  
**File**: `app.py` line 244

```python
# Render detail panel for selected listing
render_listing_detail_panel(selected_listing)
```

**What's displayed**:

**File**: `utils/listing_details.py` line 80-99

```python
def render_listing_detail_panel(selected_row: pd.Series):
    # Header with Room ID and link
    room_id = selected_row.get('Room_id', 'Unknown')
    listing_url = selected_row.get('Listing_url', f"https://www.airbnb.com.sg/rooms/{room_id}")
    
    col1, col2 = st.columns([2, 1])
    with col1:
        st.markdown(f"**Room #{room_id}**")  # ← Room ID displayed here!
    with col2:
        st.markdown(f"[🔗 View Listing]({listing_url})")
    
    # ... then status badges, metrics, review heatmap, etc.
```

**User sees**:
```
┌─────────────────────────────────────────────────────────┐
│ ### 📋 Selected Listing Details                         │
│                                                          │
│ ✅ Clicked on Room #12345 from map                      │
│                                                          │
│ **Room #12345**              [🔗 View Listing]          │
│                                                          │
│ #### Status                                             │
│ ✅ Passes Filter  ✅ 75% Rule  ✅ 55% Rule  ⭐ Superhost│
│                                                          │
│ #### Key Metrics                                        │
│ Rating: 4.8  Reviews: 123  30d Booked: 22  ...         │
│                                                          │
│ #### Review Activity Heatmap                            │
│ [Color-coded table with monthly review counts]         │
└─────────────────────────────────────────────────────────┘
```

**Room ID is displayed in**:
1. ✅ Success message: "Clicked on Room #12345"
2. ✅ Header: "Room #12345"
3. ✅ URL link: Constructed using the Room ID
4. ✅ All text is **selectable and copyable**

---

## 🔍 Debug Output

**Console output when clicking a marker**:

```
📍 Click Event Received: {
    'indices': {'listings': [5]}, 
    'objects': {'listings': [{'Room_id': 12345, ...}]}
}
✅ Successfully extracted Room ID: 12345 from click event
```

**How to view debug output**:
1. Start Streamlit app: `streamlit run app.py`
2. Click on any marker
3. Check the **terminal** where Streamlit is running
4. You'll see the debug output with Room ID

---

## 🎛️ State Management

### Session State Variables

| Key | Type | Purpose | Set When | Accessed When |
|-----|------|---------|----------|---------------|
| `clicked_room_id` | int | Stores last clicked Room ID | Marker clicked | Fallback display, debugging |

### State Lifecycle

```
App starts → clicked_room_id not in session_state
       ↓
User clicks marker → clicked_room_id = 12345
       ↓
User clicks another marker → clicked_room_id = 67890 (updated)
       ↓
User changes filters → clicked_room_id = 67890 (preserved)
       ↓
User clicks "Reset Filters" → clicked_room_id = 67890 (preserved)
```

**Note**: The Room ID persists across filter changes and reruns!

---

## 🧪 Testing the Flow

### Test 1: Click and Verify Room ID

1. Start app: `streamlit run app.py`
2. Load data for a city
3. Click any marker on the map
4. **Expected output**:
   - Terminal: `✅ Successfully extracted Room ID: XXXXX from click event`
   - UI: Green success box: "✅ Clicked on Room #XXXXX from map"
   - UI: Detail panel header: "**Room #XXXXX**"

### Test 2: Verify Room ID in Session State

Add this debug line in `app.py` after line 238:

```python
st.write(f"🔍 Debug: clicked_room_id in session_state = {st.session_state.get('clicked_room_id', 'Not set')}")
```

**Expected**: You'll see the Room ID displayed on the page.

### Test 3: Copy Room ID

1. Click a marker
2. In the detail panel, click and drag to select "Room #XXXXX"
3. Press `Cmd+C` (Mac) or `Ctrl+C` (Windows)
4. Paste somewhere: `Cmd+V` / `Ctrl+V`
5. **Expected**: The Room ID is copied successfully

### Test 4: Click Multiple Markers

1. Click marker A (Room #12345)
2. Verify detail panel shows Room #12345
3. Click marker B (Room #67890)
4. **Expected**: Detail panel updates to Room #67890
5. Terminal should show two extraction messages

---

## 🐛 Troubleshooting

### Issue: "No Room ID extracted"

**Possible causes**:
1. ❌ Layer missing `id='listings'`
2. ❌ Event structure changed (Streamlit version issue)
3. ❌ Marker not clickable (`pickable=False`)

**Fix**: Check `utils/deck_map_renderer.py` line 82 for `id='listings'`

### Issue: "Room ID is None"

**Possible causes**:
1. ❌ Clicked object doesn't have `Room_id` field
2. ❌ Wrong layer accessed (e.g., clicking grid instead of listing)

**Fix**: Add debug output to see what object was clicked:
```python
print(f"Clicked object data: {selected_obj}")
```

### Issue: "Detail panel doesn't update"

**Possible causes**:
1. ❌ `on_select` not set to `"rerun"`
2. ❌ Layer ID mismatch

**Fix**: Check `utils/deck_map_renderer.py` line 236 for `on_select="rerun"`

---

## 📊 Data Flow Diagram

```
┌──────────────────────────────────────────────────────────────┐
│                         USER CLICKS MARKER                    │
└──────────────────────────┬───────────────────────────────────┘
                           │
                           ▼
┌──────────────────────────────────────────────────────────────┐
│ PyDeck Layer (id='listings')                                 │
│ - pickable=True                                              │
│ - on_select="rerun"                                          │
│ Returns: event = {                                           │
│   "selection": {                                             │
│     "objects": {                                             │
│       "listings": [{"Room_id": 12345, ...}]                  │
│     }                                                         │
│   }                                                           │
│ }                                                             │
└──────────────────────────┬───────────────────────────────────┘
                           │
                           ▼
┌──────────────────────────────────────────────────────────────┐
│ get_selected_listing(event, df)                              │
│ 1. Check event exists                                        │
│ 2. Access objects['listings']                                │
│ 3. Extract Room_id = 12345                                   │
│ 4. Find matching row in df                                   │
│ 5. Return full listing data (Pandas Series)                  │
└──────────────────────────┬───────────────────────────────────┘
                           │
                           ▼
┌──────────────────────────────────────────────────────────────┐
│ app.py - Store in Session State                              │
│ room_id = selected_listing.get('Room_id')                    │
│ st.session_state['clicked_room_id'] = room_id               │
│ # room_id = 12345                                            │
└──────────────────────────┬───────────────────────────────────┘
                           │
                           ▼
┌──────────────────────────────────────────────────────────────┐
│ UI Display - "📋 Selected Listing Details"                   │
│                                                               │
│ ✅ Clicked on Room #12345 from map                           │
│                                                               │
│ **Room #12345**              [🔗 View Listing]               │
│                                                               │
│ [Status badges, metrics, review heatmap, etc.]              │
│                                                               │
│ ✅ Text is selectable and copyable                           │
└──────────────────────────────────────────────────────────────┘
```

---

## 🎓 Key Takeaways

### ✅ Room ID Flow is Working!

1. **Click captured**: PyDeck with `on_select="rerun"` triggers rerun
2. **Room ID extracted**: `get_selected_listing()` accesses `event['selection']['objects']['listings'][0]['Room_id']`
3. **Room ID stored**: `st.session_state['clicked_room_id']` preserves it
4. **Room ID displayed**: "📋 Selected Listing Details" section shows full info
5. **Room ID copyable**: All text in detail panel is selectable

### 🔑 Critical Requirements

- ✅ **Layer ID**: `id='listings'` must be set on ScatterplotLayer
- ✅ **Pickable**: `pickable=True` must be set on ScatterplotLayer
- ✅ **On Select**: `on_select="rerun"` must be set on `st.pydeck_chart`
- ✅ **Streamlit Version**: >= 1.33.0 (you have 1.52.2) ✅
- ✅ **Correct Access**: Must access `objects['listings']` not `objects[0]`

### 🎯 Result

**When you click a marker**, you will see:

1. **Terminal**: Debug output confirming Room ID extraction
2. **UI**: Green success message with Room ID
3. **UI**: Full detail panel with **selectable, copyable Room ID**
4. **Session State**: Room ID stored for reference

---

**Everything is working as designed!** 🎊

