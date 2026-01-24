# pipeline.py
import numpy as np
from aoi import AOI
from search import SentinelSearch
from scene import SentinelScene
import os
from datetime import datetime
from config import (
    output_directory, 
    base_name, 
    band_selection,
    excluded_flags
)

# SCL (Scene Classification Layer) flag mapping - maps descriptive names to flag numbers
SCL_FLAGS = {
    "No Data": 0,
    "Saturated or defective": 1,
    "Dark area pixels": 2,
    "Cloud shadows": 3,
    "Vegetation": 4,
    "Not vegetated": 5,
    "Water": 6,
    "Unclassified": 7,
    "Cloud medium probability": 8,
    "Cloud high probability": 9,
    "Thin cirrus": 10,
    "Snow or ice": 11
}


# Sentinel-2 band mapping: (Band Code, Band Name)
BAND_MAPPING = {
    "B01": "Coastal_Aerosol",
    "B02": "Blue",
    "B03": "Green", 
    "B04": "Red",
    "B05": "Red_Edge_1",
    "B06": "Red_Edge_2",
    "B07": "Red_Edge_3",
    "B08": "NIR",
    "B09": "Narrow_NIR",
    "B09": "Water_Vapor",
    "B11": "SWIR1",
    "B12": "SWIR2",
    "SCL": "Scene_Classification",
}

# Band selections for get_data mode
# Sentinel-2 band mapping
S2_BAND_SELECTIONS = {
    "rgb_only": [("B04", "Red"), ("B03", "Green"), ("B02", "Blue")],
    "rgb_nir_swir": [("B04", "Red"), ("B03", "Green"), ("B02", "Blue"), ("B08", "NIR"), ("B11", "SWIR1"), ("B12", "SWIR2")],
    "all_bands": [
        ("B01", "Coastal_Aerosol"), ("B02", "Blue"), ("B03", "Green"), ("B04", "Red"),
        ("B05", "Red_Edge_1"), ("B06", "Red_Edge_2"), ("B07", "Red_Edge_3"),
        ("B08", "NIR"), ("B09", "Narrow_NIR"), ("B11", "SWIR1"), ("B12", "SWIR2")
    ],
}

# Landsat band mapping
L8_BAND_SELECTIONS = {
    "rgb_only": [("red", "Red"), ("green", "Green"), ("blue", "Blue")],
    "rgb_nir_swir": [("red", "Red"), ("green", "Green"), ("blue", "Blue"), ("nir08", "NIR"), ("swir16", "SWIR1"), ("swir22", "SWIR2")],
    "all_bands": [
        ("coastal", "Coastal_Aerosol"), ("blue", "Blue"), ("green", "Green"), ("red", "Red"),
        ("nir08", "NIR"), ("swir16", "SWIR1"), ("swir22", "SWIR2")
    ],
}

class Optical_Downloader:
    def __init__(
        self,
        stac_url: str,
        collection: str,
        resolution: int = 10,
        dtype: str = "float32",
        fill_value: float = 0.0,
    ):
        self.search = SentinelSearch(stac_url, collection)
        self.collection = collection
        self.resolution = resolution
        self.dtype = dtype
        self.fill_value = fill_value

    def run(self, points_list: list, date_str: str, max_cloud_tile: int = 20, 
            max_cloud_tolerance: int = 20, platform: str = "sentinel-2-l2a"):
        
        # 1) AOI + search
        aoi = AOI.from_four_points(points_list)
        print(f"[Pipeline] AOI bounds: {aoi.bounds}")
        # Use max_cloud_tile for SEARCH (candidates)
        item = self.search.find_best_item(aoi.to_geojson, date_str, max_cloud_tile=max_cloud_tile)
        
        # Extract metadata
        if isinstance(item, dict):
            item_id = item.get("id", "Unknown")
            properties = item.get("properties", {})
        else:
            item_id = getattr(item, "id", "Unknown")
            properties = getattr(item, "properties", {})
            
        # Platform-specific metadata extraction
        datetime_val = properties.get("datetime", "Unknown")
        if datetime_val != "Unknown":
            # Keep just YYYY-MM-DD for filename
            datetime_str = datetime_val[:10]
        else:
            datetime_str = "Unknown"

        cloud_cover_metadata = properties.get("eo:cloud_cover", 0.0)
        
        if "landsat" in platform.lower():
            path = properties.get("landsat:wrs_path", "")
            row = properties.get("landsat:wrs_row", "")
            tile_id = f"{path}{row}" if path and row else "Unknown"
            platform_short = "L8-9"
            target_resolution = 30 # Landsat resolution
        else:
            tile_id = properties.get("s2:mgrs_tile") or properties.get("mgrs:utm_zone", "Unknown")
            platform_short = "S2"
            target_resolution = self.resolution # Keep default 10m for S2 or whatever was passed
            
        print(f"[Pipeline] Found item: {item_id}")
        print(f"[Pipeline]   - Date: {datetime_str}")
        print(f"[Pipeline]   - Tile/PathRow: {tile_id}")
        print(f"[Pipeline]   - Cloud Cover (Metadata): {cloud_cover_metadata}%")
        print(f"[Pipeline]   - Target Resolution: {target_resolution}m")
        
        # Create scene
        scene = SentinelScene(
            item,
            aoi,
            resolution=target_resolution,
            dtype=self.dtype,
            fill_value=self.fill_value,
        )
        
        # Determine band selections based on platform
        if "landsat" in platform.lower():
            selections = L8_BAND_SELECTIONS
            qa_band = "qa_pixel"
        else:
            selections = S2_BAND_SELECTIONS
            qa_band = "SCL"
            
        if band_selection not in selections:
             raise ValueError(f"Unknown band_selection '{band_selection}' for platform '{platform}'")
             
        selected_bands = selections[band_selection]
        band_codes = [b[0] for b in selected_bands]
        band_names = [b[1] for b in selected_bands]
        
        # Load QA band for statistics
        print(f"[Pipeline] Loading QA band ({qa_band}) for statistics...")
        qa_dict = scene.load_bands([qa_band])
        qa_data = qa_dict[qa_band]
        
        # Calculate statistics
        valid_mask = None
        valid_pct = 0.0
        cloud_shadow_pct = 0.0
        
        if "landsat" in platform.lower():
            # Landsat QA Pixel Bitmask
            # Bit 0: Fill, Bit 1: Dilated Cloud, Bit 3: Cloud, Bit 4: Cloud Shadow
            qa_int = qa_data.astype(int)
            # Mask bits: 1 (Fill), 8 (Cloud), 16 (Cloud Shadow) -> 1 | 8 | 16 = 25
            # Simplified: strictly mask Cloud (3) and Cloud Shadow (4)
            # Bit 3 = 8, Bit 4 = 16.
            # (qa & 8) or (qa & 16)
            cloud_mask = (qa_int & (1 << 3)) > 0
            shadow_mask = (qa_int & (1 << 4)) > 0
            fill_mask = (qa_int & (1 << 0)) > 0
            
            # Additional masks if strict: Dilated Cloud (Bit 1), Cirrus (Bit 2)
            # let's be strict
            dilated_mask = (qa_int & (1 << 1)) > 0
            cirrus_mask = (qa_int & (1 << 2)) > 0
            
            invalid_mask = cloud_mask | shadow_mask | fill_mask | dilated_mask | cirrus_mask
            valid_mask = ~invalid_mask
            
            # Calculate cloud/shadow percentage roughly
            cloud_pixels = np.sum(cloud_mask | shadow_mask | dilated_mask | cirrus_mask)
            
        else:
            # Sentinel-2 SCL
            scl = qa_data.astype(int)
            # Exclude: 0 (No Data), 1 (Defective), 2 (Dark), 3 (Shadow), 8 (Med), 9 (High), 10 (Cirrus), 11 (Snow)
            # Valid: 4 (Veg), 5 (Bare), 6 (Water), 7 (Unclassified)
            excluded_numbers = [0, 1, 2, 3, 8, 9, 10, 11] # Default strict
            valid_mask = ~np.isin(scl, excluded_numbers)
            
            # Cloud/shadow specific (3, 8, 9, 10)
            cloud_pixels = np.sum(np.isin(scl, [3, 8, 9, 10]))
            
        total_pixels = valid_mask.size
        valid_pixels = np.sum(valid_mask)
        valid_pct = (valid_pixels / total_pixels) * 100
        cloud_shadow_pct = (cloud_pixels / total_pixels) * 100
        
        print(f"[Pipeline] Valid Pixels: {valid_pct:.2f}%")
        print(f"[Pipeline] Cloud/Shadow: {cloud_shadow_pct:.2f}%")
        
        # Generate Text Report
        output_base = f"{platform_short}_{datetime_str}_{tile_id}"
        report_filename = f"{output_base}_report.txt"
        report_path = os.path.join(output_directory, report_filename)
        
        os.makedirs(output_directory, exist_ok=True)
        with open(report_path, "w") as f:
            f.write(f"Tile ID: {tile_id}\n")
            f.write(f"Date: {datetime_str}\n")
            f.write(f"Platform: {platform}\n")
            f.write(f"Resolution: {target_resolution}m\n")
            f.write(f"Metadata Cloud Cover: {cloud_cover_metadata:.2f}%\n")
            f.write(f"Calculated Cloud/Shadow: {cloud_shadow_pct:.2f}%\n")
            f.write(f"Valid Pixels: {valid_pct:.2f}%\n")
            f.write(f"Tolerance Threshold: {max_cloud_tolerance}%\n")
            
            if cloud_shadow_pct > max_cloud_tolerance:
                 f.write("Result: REJECTED (Too Cloudy)\n")
                 status_msg = "REJECTED"
            else:
                 f.write("Result: ACCEPTED\n")
                 status_msg = "ACCEPTED"
                 
        print(f"[Pipeline] Report written to {report_path}")
        
        # Check tolerance
        # Use calculated cloud shadow pct as it is more accurate for the specific AOI
        # than tile-wide metadata
        if cloud_shadow_pct > max_cloud_tolerance:
            print(f"[Pipeline] [SKIP] Cloud coverage ({cloud_shadow_pct:.2f}%) exceeds tolerance ({max_cloud_tolerance}%).")
            print(f"[Pipeline] See report for details.")
            return {"status": "skipped", "report": report_path}
            
        # If accepted, proceed to download bands
        print(f"[Pipeline] [ACCEPT] Cloud coverage within tolerance. Downloading bands...")
        
        # Load ALL bands (we only loaded QA so far)
        bands_dict = scene.load_bands(band_codes)
        
        # Apply mask
        print(f"[Pipeline] Masking invalid pixels...")
        for code in band_codes:
             if code in bands_dict:
                 bands_dict[code][~valid_mask] = self.fill_value
                 
        # Stack and Save
        bands_list = [bands_dict[code] for code in band_codes]
        stacked_array = np.stack(bands_list, axis=-1)
        
        output_filename = f"{output_base}_{band_selection}.tif"
        output_path = os.path.join(output_directory, output_filename)
        
        print(f"[Pipeline] Saving TIFF to: {output_path}")
        scene.save_tiff(stacked_array, output_path, nodata_value=self.fill_value, band_names=band_names)
        
        return {"status": "downloaded", "output_path": output_path, "report": report_path}

