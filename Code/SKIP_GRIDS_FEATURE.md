# Skip Grids Feature

## Overview
The discovery system now supports skipping specific grids during the search process. This is useful for:
- Skipping grids that have errors or issues
- Re-running discovery while avoiding already-processed grids
- Testing with a subset of grids

## How to Use

### In Your Notebook

Update your discovery cell to include the `skip_grids` parameter:

```python
# ============================================================================
# OPTION A: USE IMPROVED DISCOVERY SYSTEM (RECOMMENDED)
# ============================================================================

from discovery import discover_all_grids, DiscoveryConfig, BBox, AirbnbDiscoveryEngine

# ⏭️ SKIP SPECIFIC GRIDS (OPTIONAL)
# Add grid IDs you want to skip here (e.g., grids with errors or already processed)
# Leave empty [] to process all grids
skip_grids = []  # Example: [1, 5, 10, 25] to skip those grids

# Configure discovery parameters
discovery_config = DiscoveryConfig(
    # Rate limiting (conservative to avoid bans)
    requests_per_minute=10,
    
    # Subdivision strategy
    max_results_before_subdivide=280,
    min_bbox_size_degrees=0.001,
    max_subdivision_depth=4,
    
    # Multi-pass strategy
    num_discovery_passes = 30,
    use_blank_dates=False,
    
    alternate_checkin_offsets=[None, 3, 7, 14, 30, 60, 90],
    alternate_stay_nights=[1, 2, 3],
    alternate_zoom_values=[14, 15, 16],

    # User-agent rotation
    rotate_user_agents=True,
    
    # Search parameters
    price_min=250,
    price_max=10000,
    currency="USD",
    
    # Caching
    cache_dir=f"Data/{region_name}/discovery_cache",
    enable_cache=False,
    
    # Logging (to prevent notebook lag)
    log_to_file=True,
    log_dir="Discovery-Search-Logs",
    log_level="INFO",
    
    # Stats
    stats_file=f"Data/{region_name}/discovery_stats.json",
)

print("🔍 Starting improved discovery system...")
print(f"Region: {region_name}")
print(f"Grid cells to search: {len(gird_coords_df)}")
if len(skip_grids) > 0:
    print(f"⏭️  Grids to skip: {skip_grids}")
    print(f"Grids to process: {len(gird_coords_df) - len(skip_grids)}")
print(f"Discovery passes per cell: {discovery_config.num_discovery_passes}")
print(f"📝 Detailed logs will be saved to: {discovery_config.log_dir}/")
print("=" * 70)

# Run discovery with skip list
discovered_listings, engine = discover_all_grids(
    gird_coords_df, 
    region_name, 
    discovery_config,
    skip_grids=skip_grids  # ⭐ NEW: Pass the skip list
)

print(f"\n✅ Discovery complete!")
print(f"📊 Total unique listings: {len(discovered_listings)}")
print(f"📁 Saved to: Data/{region_name}/discovered_listings.json")
print(f"📈 Stats saved to: {discovery_config.stats_file}")

# Convert for enrichment
all_results = [listing.raw_data for listing in discovered_listings.values()]
print(f"\n✓ Ready for enrichment pipeline with {len(all_results)} listings")
```

## Examples

### Example 1: Skip a Few Grids
```python
# Skip grids 1, 5, and 10 (maybe they have errors or are already done)
skip_grids = [1, 5, 10]
```

**Output:**
```
🔍 Starting improved discovery system...
Region: Chicago
Grid cells to search: 30
⏭️  Grids to skip: [1, 5, 10]
Grids to process: 27
...
⏭️  Skipping grid 1 (in skip list)
📍 Processing grid 2 of 30...
...
⏭️  Skipping grid 5 (in skip list)
...

GRID PROCESSING SUMMARY
======================================================================
Total grids in file: 30
Grids processed: 27
Grids skipped: 3 [1, 5, 10]
======================================================================
```

### Example 2: Process Only a Range (Skip the Rest)
```python
# Process only grids 1-10, skip everything else
all_grids = set(range(1, 86))  # All grids from 1 to 85
grids_to_process = set(range(1, 11))  # Only grids 1-10
skip_grids = list(all_grids - grids_to_process)
```

### Example 3: Resume After Error
```python
# If your process crashed on grid 15, skip 1-14 to continue from 15
skip_grids = list(range(1, 15))  # Skip grids 1-14
```

### Example 4: Process All Grids (Default)
```python
# Leave empty to process all grids
skip_grids = []
```

## What Gets Skipped

When a grid is skipped:
- ✅ It's logged in the console and log file
- ✅ No API calls are made for that grid
- ✅ No data files are created for that grid
- ✅ The final summary shows how many grids were skipped

## Tips

1. **After an error run**: Check the log file to see which grid failed, then add it to `skip_grids` and re-run
2. **Testing**: Use `skip_grids` to process just 2-3 grids first to test your configuration
3. **Batching**: Process grids in batches by changing the skip list between runs

## Technical Details

- The skip check happens BEFORE any API calls, so skipped grids consume no API quota
- Skipped grids won't appear in the final `discovered_listings.json`
- The function accepts `skip_grids` as an optional parameter (defaults to `[]` if not provided)
- Grid IDs are checked using `grid_id in skip_grids`, so order doesn't matter

