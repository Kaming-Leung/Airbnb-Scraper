# 🏠 Airbnb Analytics Dashboard

Interactive web dashboard for analyzing Airbnb enrichment data with map visualizations and filters.

---

## 📋 Table of Contents

- [Features](#-features)
- [Installation](#-installation)
- [Quick Start](#-quick-start)
- [Usage Guide](#-usage-guide)
- [Data Format](#-data-format)
- [Troubleshooting](#-troubleshooting)

---

## ✨ Features

### ✅ Phase 1 & 2 (Implemented)

- **📁 Data Loading**
  - Load CSV or Excel files
  - Auto-detect files in `data/` folder
  - File upload option
  - Data validation

- **📊 Summary Statistics**
  - Total listings count
  - Unique grids count
  - Pass/fail 75% rule breakdown
  - Average ratings and booking metrics

- **🗺️ Interactive Map**
  - Color-coded listings (red = pass 75% rule, blue = fail)
  - Clickable markers with detailed info
  - Zoom and pan controls
  - Fullscreen mode

### ⏳ Coming Soon (Phases 3-7)

- Filter system (sliders for all criteria)
- Data table with sorting
- Export filtered results
- Multi-region support
- Advanced analytics

---

## 🚀 Installation

### Prerequisites

- Python 3.8 or higher
- pip package manager

### Step 1: Install Dependencies

```bash
cd Webtool
pip install -r requirements.txt
```

**Required packages:**
- `streamlit` - Web framework
- `streamlit-folium` - Map integration
- `pandas` - Data processing
- `folium` - Interactive maps
- `openpyxl` - Excel support

### Step 2: Prepare Your Data

Place your enrichment CSV/Excel files in the `data/` folder:

```
Webtool/
├── data/
│   ├── chicago_enriched.csv
│   ├── napa_enriched.csv
│   └── your_data.xlsx
```

---

## 🎯 Quick Start

### Run the Dashboard

```bash
streamlit run app.py
```

The dashboard will open in your browser at `http://localhost:8501`

### First-Time Setup

1. **Load Data**: Click the sidebar to select a file
2. **Click "Load Data"**: Wait for validation
3. **Explore Map**: Interact with the map (click dots for details)
4. **View Stats**: Check summary statistics at the top

---

## 📖 Usage Guide

### Loading Data

**Option 1: Select from data/ folder**
- Files in `data/` folder are auto-detected
- Choose from dropdown in sidebar
- Click "🔄 Load Data"

**Option 2: Upload a file**
- Use the file uploader in sidebar
- Supports CSV, XLSX, XLS
- File is temporarily saved and loaded

### Navigating the Map

- **Zoom**: Scroll wheel or +/- buttons
- **Pan**: Click and drag
- **Click Dots**: View listing details
- **Fullscreen**: Click fullscreen button (top-right of map)

### Understanding Colors

- 🔴 **Red Dots**: Listings that PASS 75% rule
- 🔵 **Blue Dots**: Listings that FAIL 75% rule

### Popup Information

Click any dot to see:
- Room ID and Airbnb link
- Days booked (30-day and 31-60 day windows)
- Missing review months
- Rating and review count
- Coordinates

---

## 📄 Data Format

### Required Columns

Your CSV/Excel file **must** have these columns:

| Column Name | Type | Description |
|-------------|------|-------------|
| `Room_id` | int | Unique listing ID |
| `Latitude` | float | Listing latitude |
| `Longitude` | float | Listing longitude |
| `Next_30_days_booked_days` | int | Days booked in next 30 days |
| `75_rule_met` | bool | Whether listing passes 75% rule |

### Optional Columns

These enhance the dashboard but aren't required:

| Column Name | Type | Description |
|-------------|------|-------------|
| `Next_30_to_60_days_booked_days` | int | Days booked in days 31-60 |
| `Total_missing_review_months_this_year` | int | Missing review months (current year) |
| `Total_missing_review_months_last_year` | int | Missing review months (last year) |
| `Rating` | float | Overall rating (0-5) |
| `Review_count` | int | Total number of reviews |
| `Grid_index` | int | Grid cell identifier |

### Sample Data

```csv
Room_id,Latitude,Longitude,Next_30_days_booked_days,75_rule_met,Rating,Review_count
1234567,41.8781,-87.6298,25,True,4.9,156
2345678,41.8800,-87.6250,18,False,4.5,89
3456789,41.8750,-87.6350,22,True,4.8,234
```

### Column Name Variations

The dashboard automatically handles these variations:
- `room_id` → `Room_id`
- `latitude` / `Latitiude` → `Latitude`
- `longitude` → `Longitude`
- Case-insensitive matching

---

## 🛠️ Troubleshooting

### Common Issues

#### "No data files found in data/ folder"

**Solution:** Place CSV/Excel files in `Webtool/data/` folder

```bash
cd Webtool
ls data/  # Should show your files
```

#### "Data validation failed: Missing required columns"

**Solution:** Check that your CSV has all required columns:
- `Room_id`
- `Latitude`
- `Longitude`
- `Next_30_days_booked_days`
- `75_rule_met`

#### "Error loading data"

**Solutions:**
1. Check file format (CSV or Excel)
2. Ensure no corrupted data
3. Verify column names match expected format
4. Try opening file in Excel/pandas to confirm it's valid

#### Map doesn't display

**Solutions:**
1. Check that `Latitude` and `Longitude` columns exist
2. Verify coordinates are valid (not NaN or 0)
3. Ensure `streamlit-folium` is installed: `pip install streamlit-folium`

#### Port already in use

**Solution:** Stop other Streamlit apps or use a different port:

```bash
streamlit run app.py --server.port 8502
```

---

## 📂 File Structure

```
Webtool/
├── app.py                      # Main Streamlit application
├── requirements.txt            # Python dependencies
├── README.md                   # This file
├── data/                       # Data folder (put CSVs here)
│   └── .gitkeep
└── utils/                      # Utility modules
    ├── __init__.py
    ├── data_loader.py          # Data loading and validation
    └── map_creator.py          # Map creation functions
```

---

## 🔄 Next Steps

### Phase 3: Filter System (Coming Next)

- Interactive sliders for filtering
- Min 30-day booked days
- Min 31-60 booked days
- Max missing review months
- Real-time map updates

### Phase 4: Additional Filters

- Min rating filter
- Min review count filter
- Grid ID multiselect

### Phase 5: Data Export

- Download filtered results as CSV
- Download as Excel
- Sortable data table

---

## 💡 Tips

1. **Large datasets**: The map may be slow with 1000+ listings. Use filters (coming in Phase 3) to reduce displayed points.

2. **Multiple regions**: Currently loads one file at a time. Phase 6 will add region switching.

3. **Grid boundaries**: Grid visualization requires separate grid coordinate files (Phase 6).

4. **Performance**: Keep CSV files under 50MB for best performance. Split large datasets by region.

---

## 🆘 Support

If you encounter issues:

1. Check this README's troubleshooting section
2. Verify your data format matches the requirements
3. Ensure all dependencies are installed
4. Check the terminal for error messages

---

## 📊 Current Implementation Status

| Phase | Status | Features |
|-------|--------|----------|
| Phase 1 | ✅ Done | Data loading, validation, summary stats |
| Phase 2 | ✅ Done | Interactive map with listings |
| Phase 3 | ⏳ Pending | Filter system |
| Phase 4 | ⏳ Pending | Additional filters |
| Phase 5 | ⏳ Pending | Data export |
| Phase 6 | ⏳ Pending | Multi-region support |
| Phase 7 | ⏳ Pending | Polish and enhancements |

---

**Last Updated:** Phase 1 & 2 Complete
**Version:** 1.0.0


