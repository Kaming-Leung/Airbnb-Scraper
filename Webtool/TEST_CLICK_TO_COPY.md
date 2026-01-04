# 🧪 Test Click-to-Copy Functionality

## What Should Happen

With Streamlit 1.52.2, the `on_select` callback should work perfectly. Here's what to expect:

### Current Workflow:

1. **Hover over a marker** → Tooltip appears (shows Room ID but **text is NOT selectable**)
2. **Click on the marker** → Detail panel appears below the map
3. **In the detail panel** → Room ID and all info is shown in **selectable text format**
4. **Select and copy** → You can now copy the Room ID from the detail panel

---

## 🎯 Testing Steps

### Step 1: Start Your Streamlit App
```bash
cd /Users/kamingleung/Development/TryOut/Airbnb-Search/Webtool
streamlit run app.py
```

### Step 2: Load Data
- Select a **State** and **City** from the sidebar
- Click **"Load Data"** button

### Step 3: Test Click Functionality
1. **Hover** over any red or blue marker on the map
   - You'll see a tooltip with Room ID
   - Moving your mouse away will make it disappear (expected behavior)

2. **Click** on any marker
   - Look below the map for a detail panel
   - The panel should show all listing details
   - The Room ID should be displayed as **selectable text**

3. **Copy the Room ID**
   - Click and drag to select the Room ID text
   - Press `Cmd+C` (Mac) or `Ctrl+C` (Windows)
   - ✅ Success! You've copied the Room ID

---

## 🐛 Troubleshooting

### If clicking doesn't work:

1. **Check the terminal/browser console** for error messages

2. **Verify your layer has an `id`**:
   According to the [Streamlit docs](https://docs.streamlit.io/develop/api-reference/charts/st.pydeck_chart):
   > "If on_select is not 'ignore', all layers must have a declared id to keep the chart stateful across reruns."

   Check `utils/deck_map_renderer.py` - the ScatterplotLayer should have:
   ```python
   pdk.Layer(
       "ScatterplotLayer",
       data=listings_data,
       id="listings",  # ← This is required!
       ...
   )
   ```

3. **Check the event output**:
   Add this debug line in `app.py` after the `st.pydeck_chart` call:
   ```python
   st.write("Debug event:", event)
   ```
   
   When you click a marker, you should see:
   ```python
   {
       "selection": {
           "indices": {"listings": [5]},
           "objects": {"listings": [{...}]}
       }
   }
   ```

---

## ✅ Expected Behavior Summary

| Action | Tooltip | Detail Panel |
|--------|---------|--------------|
| **Hover over marker** | Shows (not selectable) | Not visible |
| **Move mouse away** | Disappears | Not visible |
| **Click marker** | May briefly show | Appears below map ✅ |
| **Select text in panel** | N/A | **Works!** ✅ |
| **Copy Room ID** | Can't | **Can!** ✅ |

---

## 🎓 Why Tooltips Can't Be Selectable

This is a **deck.gl (PyDeck's underlying library) limitation**, not a Streamlit issue:

- Tooltips are rendered as **temporary overlays** on the map canvas
- They're **designed to disappear** when the mouse leaves the marker area
- They're **not part of the DOM** in a way that allows text selection
- This is true for **all** deck.gl applications, not just Streamlit

### The Solution:
Use the **detail panel** (which appears on click) to copy Room IDs. This panel:
- ✅ Stays visible until you click elsewhere
- ✅ Contains fully selectable text
- ✅ Can be copied with standard keyboard shortcuts
- ✅ Shows all listing details, not just Room ID

---

## 📊 Comparison: Tooltip vs. Detail Panel

```
╔════════════════════════════════════════════════════════════╗
║ TOOLTIP (on hover)                                         ║
║ ─────────────────────────────────────────────────────────  ║
║ • Appears on hover                                         ║
║ • Disappears when mouse moves                              ║
║ • Text is NOT selectable                                   ║
║ • Good for: Quick preview                                  ║
║ • Bad for: Copying text                                    ║
╚════════════════════════════════════════════════════════════╝

╔════════════════════════════════════════════════════════════╗
║ DETAIL PANEL (on click)                                    ║
║ ─────────────────────────────────────────────────────────  ║
║ • Appears on click                                         ║
║ • Stays visible until dismissed                            ║
║ • Text IS selectable ✅                                    ║
║ • Good for: Copying data, viewing full details             ║
║ • Good for: Your use case! ✅                              ║
╚════════════════════════════════════════════════════════════╝
```

---

## 🎯 Bottom Line

**You don't need to change anything!** Your app already has the best possible solution:

1. **Tooltips** for quick preview (hover)
2. **Click + Detail Panel** for copying Room IDs and viewing full info

Just **click** instead of trying to copy from the tooltip, and you'll be able to select and copy the Room ID from the detail panel.

---

**Need more help?** Let me know if clicking on markers doesn't trigger the detail panel!

