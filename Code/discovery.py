"""
Airbnb Listing Discovery Module
================================

Robust, coverage-first discovery system that prevents missing listings through:
- Adaptive quadtree subdivision for dense regions
- Multi-pass discovery with varied parameters
- Retry logic with exponential backoff
- Deterministic search parameters
- User-agent rotation to avoid detection
- Complete caching and resumability

Key Anti-Detection Features:
- Rotates through 12 realistic browser user-agents
- Conservative rate limiting (default: 20 req/min)
- Random jitter in retry delays
- Stable, deterministic search parameters

Author: Enhanced for completeness
Date: 2025-12-21
"""

import json
import time
import os
import random
from datetime import date, timedelta
from typing import List, Dict, Tuple, Set, Optional
from dataclasses import dataclass, asdict
import logging
from pathlib import Path

import pyairbnb
from pyairbnb import search_all


# ============================================================================
# USER AGENTS FOR ROTATION
# ============================================================================

# Pool of realistic browser user agents to rotate through
# This helps avoid detection by making requests look like different browsers
USER_AGENTS = [
    # Chrome on Windows
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
    
    # Chrome on Mac
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
    
    # Firefox on Windows
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:120.0) Gecko/20100101 Firefox/120.0",
    
    # Firefox on Mac
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:121.0) Gecko/20100101 Firefox/121.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:120.0) Gecko/20100101 Firefox/120.0",
    
    # Safari on Mac
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Safari/605.1.15",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Safari/605.1.15",
    
    # Edge on Windows
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 Edg/120.0.0.0",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36 Edg/119.0.0.0",
]


# ============================================================================
# CONFIGURATION
# ============================================================================

@dataclass
class DiscoveryConfig:
    """Configuration for discovery process"""
    
    # Rate limiting
    requests_per_minute: int = 20  # Conservative rate limit
    retry_delay_base: float = 2.0  # Base delay for exponential backoff
    max_retries: int = 3
    
    # Subdivision strategy
    max_results_before_subdivide: int = 280  # Airbnb often caps ~300
    min_bbox_size_degrees: float = 0.001  # ~100m, stop subdividing below this
    max_subdivision_depth: int = 4  # Prevent infinite recursion
    
    # Multi-pass strategy
    num_discovery_passes: int = 3  # Multiple passes to catch rotation
    use_blank_dates: bool = True  # If True, ALL passes use blank dates
    base_checkin_days_ahead: int = 14  # Start date for search (only if use_blank_dates=False)
    checkin_night_count: int = 2  # 2-night stays (only if use_blank_dates=False)
    alternate_checkin_offsets: List[Optional[int]] = None  # Date offsets; None in list = blank dates for that pass
    alternate_stay_nights: List[Optional[int]] = None  # Stay length variations; None = use checkin_night_count
    alternate_zoom_values: List[int] = None  # Zoom level variations; None = use default 15
    
    # Search parameters
    price_min: int = 300
    price_max: int = 10000
    currency: str = "USD"
    adults: int = 1
    
    # User-agent rotation (anti-detection)
    rotate_user_agents: bool = True  # Randomly rotate user agents per request
    custom_user_agents: List[str] = None  # Optional custom user agent pool
    
    # Caching
    cache_dir: str = "Data/discovery_cache"  # Override this with region-specific path
    enable_cache: bool = True
    
    # Instrumentation
    log_level: str = "INFO"
    stats_file: str = "Data/discovery_stats.json"  # Override this with region-specific path
    log_to_file: bool = True  # Log to file instead of console
    log_dir: str = "Discovery-Search-Logs"  # Directory for log files
    
    def __post_init__(self):
        if self.alternate_checkin_offsets is None:
            # Default: try +14 days, +21 days, +30 days (only used if use_blank_dates=False)
            self.alternate_checkin_offsets = [14, 21, 30]
        
        if self.alternate_stay_nights is None:
            # Default: try different stay lengths to catch minimum night requirements
            self.alternate_stay_nights = [1, 2, 3, 7]
        
        if self.alternate_zoom_values is None:
            # Default: try different zoom levels (13=zoomed out, 16=zoomed in)
            self.alternate_zoom_values = [14, 15, 16]
        
        # Warn if using specific dates (not recommended for discovery)
        if not self.use_blank_dates:
            import warnings
            warnings.warn(
                "⚠️  Using specific dates for discovery may miss listings that are booked on those dates. "
                "Consider setting use_blank_dates=True for complete discovery.",
                UserWarning
            )


# ============================================================================
# DATA MODELS
# ============================================================================

@dataclass
class BBox:
    """Bounding box representation"""
    ne_lat: float
    ne_long: float
    sw_lat: float
    sw_long: float
    grid_id: Optional[int] = None
    depth: int = 0
    parent_id: Optional[str] = None
    
    @property
    def id(self) -> str:
        """Unique identifier for this bbox"""
        return f"{self.sw_lat:.6f}_{self.sw_long:.6f}_{self.ne_lat:.6f}_{self.ne_long:.6f}"
    
    @property
    def center(self) -> Tuple[float, float]:
        """Center point (lat, lon)"""
        return (
            (self.ne_lat + self.sw_lat) / 2,
            (self.ne_long + self.sw_long) / 2
        )
    
    @property
    def size(self) -> float:
        """Max dimension in degrees"""
        lat_span = abs(self.ne_lat - self.sw_lat)
        lon_span = abs(self.ne_long - self.sw_long)
        return max(lat_span, lon_span)
    
    def subdivide(self) -> List['BBox']:
        """Subdivide into 4 quadrants (quadtree)"""
        center_lat, center_lon = self.center
        
        return [
            # NE quadrant
            BBox(self.ne_lat, self.ne_long, center_lat, center_lon,
                 grid_id=self.grid_id, depth=self.depth + 1, parent_id=self.id),
            # NW quadrant
            BBox(self.ne_lat, center_lon, center_lat, self.sw_long,
                 grid_id=self.grid_id, depth=self.depth + 1, parent_id=self.id),
            # SE quadrant
            BBox(center_lat, self.ne_long, self.sw_lat, center_lon,
                 grid_id=self.grid_id, depth=self.depth + 1, parent_id=self.id),
            # SW quadrant
            BBox(center_lat, center_lon, self.sw_lat, self.sw_long,
                 grid_id=self.grid_id, depth=self.depth + 1, parent_id=self.id),
        ]


@dataclass
class DiscoveredListing:
    """Minimal listing metadata from discovery phase"""
    room_id: int
    latitude: float
    longitude: float
    grid_id_assigned: Optional[int]  # After verification
    grid_id_source: Optional[int]  # Original grid searched
    bbox_id: str
    pass_id: int
    discovered_at: str  # ISO timestamp
    raw_data: Dict  # Full response from Airbnb


@dataclass
class SearchStats:
    """Statistics for a single search call"""
    bbox_id: str
    pass_id: int
    results_count: int
    subdivided: bool
    retry_count: int
    duration_seconds: float
    timestamp: str


# ============================================================================
# DISCOVERY ENGINE
# ============================================================================

class AirbnbDiscoveryEngine:
    """
    Main discovery engine with coverage-first strategy
    """
    
    def __init__(self, config: DiscoveryConfig, grid_coords_df=None):
        self.config = config
        self.grid_coords_df = grid_coords_df
        
        # Setup logging
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(getattr(logging, config.log_level))
        
        # Clear any existing handlers to avoid duplicates
        self.logger.handlers = []
        
        if config.log_to_file:
            # Create log directory
            os.makedirs(config.log_dir, exist_ok=True)
            
            # Generate timestamped log filename
            timestamp = time.strftime("%Y%m%d_%H%M%S")
            log_filename = f"discovery_search_{timestamp}.log"
            log_path = os.path.join(config.log_dir, log_filename)
            
            # Setup file handler
            file_handler = logging.FileHandler(log_path, encoding='utf-8')
            file_handler.setLevel(getattr(logging, config.log_level))
            
            # Setup formatter
            formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            file_handler.setFormatter(formatter)
            
            self.logger.addHandler(file_handler)
            self.logger.info(f"Logging initialized to file: {log_path}")
            
            # Store log path for user reference
            self.log_file_path = log_path
        else:
            # Console logging
            console_handler = logging.StreamHandler()
            console_handler.setLevel(getattr(logging, config.log_level))
            formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            console_handler.setFormatter(formatter)
            self.logger.addHandler(console_handler)
            self.log_file_path = None
        
        # Statistics tracking
        self.stats: List[SearchStats] = []
        self.discovered_listings: Dict[int, DiscoveredListing] = {}  # room_id -> listing
        
        # Rate limiting
        self.last_request_time = 0.0
        self.request_count = 0
        
        # Setup user-agent pool
        if self.config.rotate_user_agents:
            self.user_agent_pool = self.config.custom_user_agents if self.config.custom_user_agents else USER_AGENTS
            self.logger.info(f"User-agent rotation enabled with {len(self.user_agent_pool)} agents")
        else:
            self.user_agent_pool = None
        
        # Setup cache
        if self.config.enable_cache:
            os.makedirs(self.config.cache_dir, exist_ok=True)
    
    def _get_random_user_agent(self) -> Optional[str]:
        """
        Get a random user agent from the pool.
        
        Returns None if user-agent rotation is disabled.
        """
        if not self.config.rotate_user_agents or not self.user_agent_pool:
            return None
        return random.choice(self.user_agent_pool)
    
    def _rate_limit(self):
        """Enforce rate limiting"""
        min_interval = 60.0 / self.config.requests_per_minute
        elapsed = time.time() - self.last_request_time
        
        if elapsed < min_interval:
            sleep_time = min_interval - elapsed
            self.logger.debug(f"Rate limiting: sleeping {sleep_time:.2f}s")
            time.sleep(sleep_time)
        
        self.last_request_time = time.time()
        self.request_count += 1
    
    def _get_search_dates(self, pass_id: int) -> Tuple[str, str]:
        """
        Generate check-in/check-out dates for a pass.
        
        Three strategies:
        1. All blank (use_blank_dates=True): Every pass uses blank dates
           - Simple but all passes are identical (no multi-pass benefit)
        
        2. All specific dates (use_blank_dates=False): Every pass uses dates from alternate_checkin_offsets
           - Good for catching date-specific availability
           - But may miss listings booked on searched dates
        
        3. Hybrid (RECOMMENDED): Mix blank and specific dates
           - Set use_blank_dates=False
           - Include None in alternate_checkin_offsets: [None, 14, 30, 60]
           - Pass with None uses blank dates, others use specific dates
           - Best of both worlds!
        """
        if self.config.use_blank_dates:
            # Strategy 1: All passes use blank dates
            return "", ""
        
        # Strategy 2 & 3: Use alternate_checkin_offsets
        if not self.config.alternate_checkin_offsets:
            # Fallback if empty
            return "", ""
        
        offset = self.config.alternate_checkin_offsets[pass_id % len(self.config.alternate_checkin_offsets)]
        
        # If offset is None, use blank dates (Strategy 3: Hybrid)
        if offset is None:
            return "", ""
        
        # Otherwise use specific dates (Strategy 2 or 3)
        today = date.today()
        checkin = today + timedelta(days=offset)
        
        # Use dynamic stay length for this pass
        stay_nights = self._get_stay_nights(pass_id)
        checkout = checkin + timedelta(days=stay_nights)
        
        return checkin.strftime("%Y-%m-%d"), checkout.strftime("%Y-%m-%d")
    
    def _get_stay_nights(self, pass_id: int) -> int:
        """
        Get the number of nights for this pass to catch minimum stay requirements.
        
        Why vary stay length?
        - Listings with 3-night minimum won't show up in 2-night searches
        - Listings with 7-night minimum won't show up in 2-3 night searches
        - Weekly/monthly rentals have different visibility
        
        Strategy: Cycle through [1, 2, 3, 7] nights to catch all requirements
        """
        if not self.config.alternate_stay_nights:
            return self.config.checkin_night_count  # Fallback to default
        
        stay_nights = self.config.alternate_stay_nights[pass_id % len(self.config.alternate_stay_nights)]
        
        # If None in list, use default
        if stay_nights is None:
            return self.config.checkin_night_count
        
        return stay_nights
    
    def _get_zoom_value(self, pass_id: int) -> int:
        """
        Get the zoom level for this pass to catch different map tile results.
        
        Why vary zoom?
        - Airbnb uses map tiles at different zoom levels
        - Different zoom levels may return different listings
        - 13 = zoomed out (broader area, fewer details)
        - 15 = default (balanced)
        - 16 = zoomed in (more precise, more details)
        
        Strategy: Cycle through [14, 15, 16] to catch all map tile variations
        """
        if not self.config.alternate_zoom_values:
            return 15  # Default zoom
        
        return self.config.alternate_zoom_values[pass_id % len(self.config.alternate_zoom_values)]
    
    def _search_with_retry(
        self,
        bbox: BBox,
        pass_id: int
    ) -> Tuple[List[Dict], SearchStats]:
        """
        Execute a single search with retry logic and error detection.
        
        Returns:
            (results, stats)
        """
        check_in, check_out = self._get_search_dates(pass_id)
        stay_nights = self._get_stay_nights(pass_id)
        zoom_value = self._get_zoom_value(pass_id)
        
        start_time = time.time()
        retry_count = 0
        last_error = None
        
        for attempt in range(self.config.max_retries + 1):
            try:
                self._rate_limit()
                
                # Get random user agent for this request
                user_agent = self._get_random_user_agent()
                
                date_str = "NO DATES (all listings)" if check_in == "" else f"{check_in} to {check_out} ({stay_nights}n)"
                self.logger.debug(
                    f"Search bbox={bbox.id[:20]}... pass={pass_id} "
                    f"dates={date_str} zoom={zoom_value} attempt={attempt}"
                )
                
                if user_agent:
                    self.logger.debug(f"Using user-agent: {user_agent[:50]}...")
                
                # Apply user-agent to pyairbnb session if rotation is enabled
                if user_agent and hasattr(pyairbnb, 'session'):
                    # If pyairbnb exposes a session object, update its headers
                    pyairbnb.session.headers.update({'User-Agent': user_agent})
                
                results = search_all(
                    check_in=check_in,
                    check_out=check_out,
                    ne_lat=bbox.ne_lat,
                    ne_long=bbox.ne_long,
                    sw_lat=bbox.sw_lat,
                    sw_long=bbox.sw_long,
                    zoom_value=zoom_value,  # Dynamic zoom based on pass
                    price_min=self.config.price_min,
                    price_max=self.config.price_max,
                    currency=self.config.currency
                )
                
                # Detect suspicious/incomplete responses
                if results is None:
                    raise ValueError("search_all returned None")
                
                # Success
                duration = time.time() - start_time
                stats = SearchStats(
                    bbox_id=bbox.id,
                    pass_id=pass_id,
                    results_count=len(results),
                    subdivided=False,
                    retry_count=retry_count,
                    duration_seconds=duration,
                    timestamp=time.strftime("%Y-%m-%d %H:%M:%S")
                )
                
                return results, stats
                
            except Exception as e:
                last_error = e
                retry_count += 1
                
                if attempt < self.config.max_retries:
                    # Exponential backoff with jitter
                    delay = self.config.retry_delay_base * (2 ** attempt)
                    jitter = delay * 0.2 * (time.time() % 1.0)  # 0-20% jitter
                    total_delay = delay + jitter
                    
                    self.logger.warning(
                        f"Search failed (attempt {attempt + 1}), "
                        f"retrying in {total_delay:.1f}s: {e}"
                    )
                    time.sleep(total_delay)
                else:
                    self.logger.error(
                        f"Search failed after {self.config.max_retries + 1} attempts: {e}"
                    )
        
        # All retries exhausted
        duration = time.time() - start_time
        stats = SearchStats(
            bbox_id=bbox.id,
            pass_id=pass_id,
            results_count=0,
            subdivided=False,
            retry_count=retry_count,
            duration_seconds=duration,
            timestamp=time.strftime("%Y-%m-%d %H:%M:%S")
        )
        
        return [], stats
    
    def _should_subdivide(self, bbox: BBox, results_count: int) -> bool:
        """
        Decide if a bbox should be subdivided.
        
        Subdivision occurs when:
        - Result count suggests capping/truncation
        - Bbox is large enough to subdivide
        - Not too deep already
        """
        if bbox.depth >= self.config.max_subdivision_depth:
            self.logger.debug(f"Max depth reached for {bbox.id}")
            return False
        
        if bbox.size < self.config.min_bbox_size_degrees:
            self.logger.debug(f"Min size reached for {bbox.id}")
            return False
        
        if results_count >= self.config.max_results_before_subdivide:
            self.logger.info(
                f"Subdividing bbox {bbox.id[:20]}... (depth={bbox.depth}) "
                f"due to high count: {results_count}"
            )
            return True
        
        return False
    
    def _search_bbox_recursive(
        self,
        bbox: BBox,
        pass_id: int
    ) -> Set[int]:
        """
        Recursively search a bbox with adaptive subdivision.
        
        Returns:
            Set of room_ids discovered
        """
        results, stats = self._search_with_retry(bbox, pass_id)
        self.stats.append(stats)
        
        # Extract room IDs from results
        room_ids = set()
        for result in results:
            room_id = result.get('room_id')
            if room_id:
                room_ids.add(room_id)
                
                # Store discovered listing (will be deduplicated later)
                if room_id not in self.discovered_listings:
                    coords = result.get('coordinates', {})
                    self.discovered_listings[room_id] = DiscoveredListing(
                        room_id=room_id,
                        latitude=coords.get('latitude', 0.0),
                        longitude=coords.get('longitud', 0.0),  # Note: typo in pyairbnb
                        grid_id_assigned=None,  # Will be verified later
                        grid_id_source=bbox.grid_id,
                        bbox_id=bbox.id,
                        pass_id=pass_id,
                        discovered_at=time.strftime("%Y-%m-%d %H:%M:%S"),
                        raw_data=result
                    )
        
        # Decide if we should subdivide
        if self._should_subdivide(bbox, len(results)):
            self.logger.info(
                f"Subdividing into 4 quadrants (depth {bbox.depth} -> {bbox.depth + 1})"
            )
            
            sub_bboxes = bbox.subdivide()
            stats.subdivided = True
            
            # Search each sub-bbox
            for sub_bbox in sub_bboxes:
                sub_room_ids = self._search_bbox_recursive(sub_bbox, pass_id)
                room_ids.update(sub_room_ids)
        
        return room_ids
    
    def discover_grid(self, bbox: BBox) -> Set[int]:
        """
        Discover all listings in a grid cell using multi-pass + subdivision.
        
        Returns:
            Set of unique room_ids discovered
        """
        self.logger.info(
            f"Starting discovery for grid_id={bbox.grid_id} "
            f"({self.config.num_discovery_passes} passes)"
        )
        
        all_room_ids = set()
        
        # Multi-pass discovery
        for pass_id in range(self.config.num_discovery_passes):
            self.logger.info(f"  Pass {pass_id + 1}/{self.config.num_discovery_passes}")
            
            # Check cache
            if self.config.enable_cache:
                cached_ids = self._load_cache(bbox, pass_id)
                if cached_ids is not None:
                    self.logger.info(f"    Loaded {len(cached_ids)} IDs from cache")
                    all_room_ids.update(cached_ids)
                    continue
            
            # Perform search (with potential subdivision)
            pass_room_ids = self._search_bbox_recursive(bbox, pass_id)
            
            # Calculate new IDs BEFORE updating the set
            new_ids_this_pass = pass_room_ids - all_room_ids
            all_room_ids.update(pass_room_ids)
            
            self.logger.info(
                f"    Found {len(pass_room_ids)} listings "
                f"(+{len(new_ids_this_pass)} new this pass)"
            )
            
            # Save to cache
            if self.config.enable_cache:
                self._save_cache(bbox, pass_id, pass_room_ids)
        
        self.logger.info(
            f"Completed grid_id={bbox.grid_id}: {len(all_room_ids)} unique listings"
        )
        
        return all_room_ids
    
    def _load_cache(self, bbox: BBox, pass_id: int) -> Optional[Set[int]]:
        """Load cached room IDs for a bbox + pass"""
        cache_file = os.path.join(
            self.config.cache_dir,
            f"grid_{bbox.grid_id}_pass_{pass_id}.json"
        )
        
        if not os.path.exists(cache_file):
            return None
        
        try:
            with open(cache_file, 'r') as f:
                data = json.load(f)
                return set(data.get('room_ids', []))
        except Exception as e:
            self.logger.warning(f"Failed to load cache {cache_file}: {e}")
            return None
    
    def _save_cache(self, bbox: BBox, pass_id: int, room_ids: Set[int]):
        """Save room IDs to cache"""
        cache_file = os.path.join(
            self.config.cache_dir,
            f"grid_{bbox.grid_id}_pass_{pass_id}.json"
        )
        
        try:
            with open(cache_file, 'w') as f:
                json.dump({
                    'grid_id': bbox.grid_id,
                    'pass_id': pass_id,
                    'bbox': asdict(bbox),
                    'room_ids': list(room_ids),
                    'count': len(room_ids),
                    'timestamp': time.strftime("%Y-%m-%d %H:%M:%S")
                }, f, indent=2)
        except Exception as e:
            self.logger.warning(f"Failed to save cache {cache_file}: {e}")
    
    def verify_coordinates(self, grid_coords_df) -> Dict[int, DiscoveredListing]:
        """
        Verify and assign correct grid_id to all discovered listings.
        
        Uses find_grid_for_coordinate logic but doesn't discard mismatches.
        """
        self.logger.info("Verifying coordinates for all discovered listings...")
        
        verified_count = 0
        reassigned_count = 0
        outside_grid_count = 0
        
        for room_id, listing in self.discovered_listings.items():
            # Find which grid this listing actually belongs to
            verified_grid = self._find_grid_for_coordinate(
                listing.latitude,
                listing.longitude,
                grid_coords_df
            )
            
            listing.grid_id_assigned = verified_grid
            
            if verified_grid is not None:
                verified_count += 1
                
                if verified_grid != listing.grid_id_source:
                    reassigned_count += 1
                    self.logger.debug(
                        f"Listing {room_id} reassigned: "
                        f"grid {listing.grid_id_source} -> {verified_grid}"
                    )
            else:
                outside_grid_count += 1
                listing.grid_id_assigned = -1  # Tag as outside any grid
                self.logger.debug(
                    f"Listing {room_id} outside all grids: "
                    f"({listing.latitude}, {listing.longitude})"
                )
        
        self.logger.info(
            f"Coordinate verification complete: "
            f"{verified_count} in-grid, {reassigned_count} reassigned, "
            f"{outside_grid_count} outside-grid"
        )
        
        return self.discovered_listings
    
    def _find_grid_for_coordinate(self, lat: float, lon: float, grid_coords_df) -> Optional[int]:
        """Find which grid cell contains this coordinate"""
        if grid_coords_df is None:
            return None
        
        match = grid_coords_df[
            (grid_coords_df['sw_lat'] <= lat) & (lat <= grid_coords_df['ne_lat']) &
            (grid_coords_df['sw_long'] <= lon) & (lon <= grid_coords_df['ne_long'])
        ]
        
        if not match.empty:
            return int(match.iloc[0]['grid_id'])
        
        return None
    
    def save_discoveries(self, output_path: str):
        """Save all discovered listings to JSON"""
        self.logger.info(f"Saving {len(self.discovered_listings)} listings to {output_path}")
        
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump({
                'total_unique_listings': len(self.discovered_listings),
                'discovery_timestamp': time.strftime("%Y-%m-%d %H:%M:%S"),
                'config': asdict(self.config),
                'listings': {
                    room_id: asdict(listing)
                    for room_id, listing in self.discovered_listings.items()
                }
            }, f, indent=2, ensure_ascii=False)
    
    def save_grid_results(self, grid_id: int, region_name: str):
        """
        Save results for a specific grid to segmented files.
        
        Creates files in Data/{region_name}/Segmented-Data/ folder:
        - discovered_listings_grid_{grid_id}_{datetime}.json
        - discovery_stats_grid_{grid_id}_{datetime}.json
        
        Args:
            grid_id: ID of the grid to save
            region_name: Name of the region (for folder structure)
        """
        # Create segmented data folder
        segmented_dir = f"Data/{region_name}/Segmented-Data"
        os.makedirs(segmented_dir, exist_ok=True)
        
        # Generate timestamp for filename
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        
        # Filter listings for this specific grid
        grid_listings = {
            room_id: listing
            for room_id, listing in self.discovered_listings.items()
            if listing.grid_id_source == grid_id or listing.grid_id_assigned == grid_id
        }
        
        # Save listings file
        listings_file = os.path.join(
            segmented_dir,
            f"discovered_listings_grid_{grid_id}_{timestamp}.json"
        )
        
        with open(listings_file, 'w', encoding='utf-8') as f:
            json.dump({
                'grid_id': grid_id,
                'total_listings': len(grid_listings),
                'discovery_timestamp': time.strftime("%Y-%m-%d %H:%M:%S"),
                'listings': {
                    room_id: asdict(listing)
                    for room_id, listing in grid_listings.items()
                }
            }, f, indent=2, ensure_ascii=False)
        
        # Save stats file for this grid
        grid_stats = [s for s in self.stats if str(s.bbox_id).startswith(f"{grid_id}")]
        
        stats_file = os.path.join(
            segmented_dir,
            f"discovery_stats_grid_{grid_id}_{timestamp}.json"
        )
        
        with open(stats_file, 'w', encoding='utf-8') as f:
            json.dump({
                'grid_id': grid_id,
                'total_searches': len(grid_stats),
                'total_listings': len(grid_listings),
                'discovery_timestamp': time.strftime("%Y-%m-%d %H:%M:%S"),
                'stats': [asdict(s) for s in grid_stats]
            }, f, indent=2)
        
        self.logger.info(
            f"✓ Saved grid {grid_id} results: {len(grid_listings)} listings "
            f"to {segmented_dir}/"
        )
    
    def generate_stats_report(self) -> Dict:
        """Generate comprehensive statistics report"""
        report = {
            'summary': {
                'total_unique_listings': len(self.discovered_listings),
                'total_searches': len(self.stats),
                'total_requests': self.request_count,
            },
            'by_grid': {},
            'subdivision_stats': {
                'total_subdivisions': sum(1 for s in self.stats if s.subdivided),
                'searches_by_depth': {},
            },
            'multi_pass_gains': {},
            'retries': {
                'total_retries': sum(s.retry_count for s in self.stats),
                'failed_searches': sum(1 for s in self.stats if s.results_count == 0 and s.retry_count > 0),
            }
        }
        
        # Per-grid stats
        for room_id, listing in self.discovered_listings.items():
            grid_id = listing.grid_id_assigned or listing.grid_id_source or -1
            
            if grid_id not in report['by_grid']:
                report['by_grid'][grid_id] = {
                    'unique_listings': 0,
                    'listings_by_pass': {}
                }
            
            report['by_grid'][grid_id]['unique_listings'] += 1
            
            pass_id = listing.pass_id
            if pass_id not in report['by_grid'][grid_id]['listings_by_pass']:
                report['by_grid'][grid_id]['listings_by_pass'][pass_id] = 0
            report['by_grid'][grid_id]['listings_by_pass'][pass_id] += 1
        
        # Save report
        if self.config.stats_file:
            os.makedirs(os.path.dirname(self.config.stats_file), exist_ok=True)
            with open(self.config.stats_file, 'w') as f:
                json.dump(report, f, indent=2)
        
        return report
    
    def print_stats_summary(self):
        """Print human-readable stats summary"""
        report = self.generate_stats_report()
        
        print("\n" + "=" * 70)
        print("DISCOVERY STATISTICS SUMMARY")
        print("=" * 70)
        print(f"Total unique listings discovered: {report['summary']['total_unique_listings']}")
        print(f"Total search API calls: {report['summary']['total_searches']}")
        print(f"Total subdivisions triggered: {report['subdivision_stats']['total_subdivisions']}")
        print(f"Total retries: {report['retries']['total_retries']}")
        print(f"Failed searches: {report['retries']['failed_searches']}")
        print()
        print("Listings by Grid:")
        for grid_id, stats in sorted(report['by_grid'].items()):
            print(f"  Grid {grid_id}: {stats['unique_listings']} listings")
            if len(stats['listings_by_pass']) > 1:
                print(f"    Multi-pass breakdown: {stats['listings_by_pass']}")
        print("=" * 70 + "\n")


# ============================================================================
# CONVENIENCE FUNCTIONS
# ============================================================================

def discover_all_grids(
    grid_coords_df,
    region_name: str,
    config: Optional[DiscoveryConfig] = None,
    save_per_grid: bool = True,
    skip_grids: Optional[List[int]] = None
) -> Tuple[Dict[int, DiscoveredListing], AirbnbDiscoveryEngine]:
    """
    High-level function to discover listings across all grids.
    
    Args:
        grid_coords_df: DataFrame with columns [grid_id, ne_lat, ne_long, sw_lat, sw_long]
        region_name: Name of the region (for folder structure)
        config: Optional custom configuration
        save_per_grid: If True, saves results after each grid to Segmented-Data folder
        skip_grids: Optional list of grid IDs to skip (e.g., [1, 5, 10])
    
    Returns:
        (discovered_listings_dict, engine_instance)
    """
    if config is None:
        config = DiscoveryConfig()
    
    if skip_grids is None:
        skip_grids = []
    
    engine = AirbnbDiscoveryEngine(config, grid_coords_df)
    
    # Log skipped grids if any
    if len(skip_grids) > 0:
        engine.logger.info(f"⏭️  Skipping {len(skip_grids)} grids: {sorted(skip_grids)}")
        print(f"⏭️  Skipping {len(skip_grids)} grids: {sorted(skip_grids)}")
    
    # Helper function for logging that works with both file and console
    def log_print(message):
        """Log to file and optionally print minimal output to notebook"""
        engine.logger.info(message)
        if config.log_to_file:
            # Only print minimal progress to notebook to avoid lag
            if "Processing grid" in message or "Discovery complete" in message or "Skipping grid" in message:
                print(message)
        else:
            print(message)
    
    # Track skipped and processed grids
    skipped_count = 0
    processed_count = 0
    
    # Process each grid
    for idx, row in grid_coords_df.iterrows():
        grid_id = int(row['grid_id'])
        
        # Check if this grid should be skipped
        if len(skip_grids) > 0 and grid_id in skip_grids:
            log_print(f"⏭️  Skipping grid {grid_id} (in skip list)")
            skipped_count += 1
            continue
        
        bbox = BBox(
            ne_lat=row['ne_lat'],
            ne_long=row['ne_long'],
            sw_lat=row['sw_lat'],
            sw_long=row['sw_long'],
            grid_id=grid_id
        )
        
        log_print(f"\n📍 Processing grid {grid_id} of {len(grid_coords_df)}...")
        
        # Discover listings for this grid
        engine.discover_grid(bbox)
        
        # Save this grid's results immediately (before moving to next grid)
        if save_per_grid:
            engine.save_grid_results(grid_id, region_name)
            log_print(f"✓ Grid {grid_id} results saved to Segmented-Data/")
        
        processed_count += 1
    
    # Verify coordinates
    engine.verify_coordinates(grid_coords_df)
    
    # Print processing summary
    print("\n" + "=" * 70)
    print("GRID PROCESSING SUMMARY")
    print("=" * 70)
    print(f"Total grids in file: {len(grid_coords_df)}")
    print(f"Grids processed: {processed_count}")
    if skipped_count > 0:
        print(f"Grids skipped: {skipped_count} {sorted(skip_grids)}")
    print("=" * 70)
    
    # Generate stats (this will still print to console for summary)
    engine.print_stats_summary()
    
    # Save combined discoveries (all grids together)
    engine.save_discoveries(f"Data/{region_name}/discovered_listings.json")
    
    # Print log file location if logging to file
    if config.log_to_file and hasattr(engine, 'log_file_path'):
        print(f"\n📝 Full detailed logs saved to: {engine.log_file_path}")
    
    return engine.discovered_listings, engine


if __name__ == "__main__":
    print("Airbnb Discovery Module")
    print("Import this module and use discover_all_grids() or AirbnbDiscoveryEngine directly")

