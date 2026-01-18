# pipeline.py
import numpy as np
from aoi import AOI
from search import SentinelSearch
from scene import SentinelScene
import os
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
BAND_SELECTIONS = {
    "rgb_only": [("B04", "Red"), ("B03", "Green"), ("B02", "Blue")],
    "rgb_nir_swir": [("B04", "Red"), ("B03", "Green"), ("B02", "Blue"), ("B08", "NIR"), ("B11", "SWIR1"), ("B12", "SWIR2")],
    "all_bands": [
        ("B01", "Coastal_Aerosol"),
        ("B02", "Blue"),
        ("B03", "Green"),
        ("B04", "Red"),
        ("B05", "Red_Edge_1"),
        ("B06", "Red_Edge_2"),
        ("B07", "Red_Edge_3"),
        ("B08", "NIR"),
        ("B09", "Narrow_NIR"),
        ("B09", "Water_Vapor"),
        ("B11", "SWIR1"),
        ("B12", "SWIR2"),
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
        self.resolution = resolution
        self.dtype = dtype
        self.fill_value = fill_value

    def run(self, points_list: list, date_str: str, max_cloud: int = 20):
        # 1) AOI + search
        aoi = AOI.from_four_points(points_list)
        print(f"[Pipeline] AOI bounds: {aoi.bounds}")
        item = self.search.find_best_item(aoi.to_geojson, date_str, max_cloud=max_cloud)
        
        # Print tile information
        if isinstance(item, dict):
            item_id = item.get("id", "Unknown")
            properties = item.get("properties", {})
            tile_id = properties.get("s2:mgrs_tile") or properties.get("mgrs:utm_zone") or properties.get("s2:product_uri", "Unknown")
            datetime_str = properties.get("datetime", "Unknown")
            cloud_cover = properties.get("eo:cloud_cover", "Unknown")
        else:
            item_id = getattr(item, "id", "Unknown")
            properties = getattr(item, "properties", {})
            tile_id = properties.get("s2:mgrs_tile") if isinstance(properties, dict) else getattr(properties, "s2:mgrs_tile", "Unknown")
            datetime_str = properties.get("datetime", "Unknown") if isinstance(properties, dict) else getattr(properties, "datetime", "Unknown")
            cloud_cover = properties.get("eo:cloud_cover", "Unknown") if isinstance(properties, dict) else getattr(properties, "eo:cloud_cover", "Unknown")
        
        print(f"[Pipeline] Found Sentinel-2 tile:")
        print(f"[Pipeline]   - Item ID: {item_id}")
        print(f"[Pipeline]   - MGRS Tile: {tile_id}")
        print(f"[Pipeline]   - Date/Time: {datetime_str}")
        print(f"[Pipeline]   - Cloud Cover: {cloud_cover}%")
        
        # Create scene
        scene = SentinelScene(
            item,
            aoi,
            resolution=self.resolution,
            dtype=self.dtype,
            fill_value=self.fill_value,
        )
        
        return self._run_download_data(scene)
    
    def _run_download_data(self, scene):
        """Handle data download: load and save selected bands as TIFF files"""
        print(f"\n[Pipeline] Mode: download_data")
        print(f"[Pipeline] Band selection: {band_selection}")
        
        if band_selection not in BAND_SELECTIONS:
            raise ValueError(f"Unknown band_selection: {band_selection}. Must be one of: {list(BAND_SELECTIONS.keys())}")
        
        selected_bands = BAND_SELECTIONS[band_selection]
        band_codes = [band_code for band_code, band_name in selected_bands]
        band_names = [band_name for band_code, band_name in selected_bands]
        
        # Ensure SCL is loaded for filtering
        bands_to_load = list(band_codes)
        if "SCL" not in bands_to_load:
            bands_to_load.append("SCL")
            
        print(f"[Pipeline] Loading bands: {bands_to_load}")
        print(f"[Pipeline] Band names: {band_names} + [SCL]")
        
        # Load bands
        bands_dict = scene.load_bands(bands_to_load)
        
        # Process SCL and calculate valid pixels
        if "SCL" in bands_dict:
            scl = bands_dict["SCL"]
            print(f"\n[Pipeline] Processing Scene Classification Layer (SCL)...")
            print(f"[Pipeline] Excluded flags (names): {excluded_flags}")
            
            # Convert flag names to numbers
            excluded_flag_numbers = []
            for flag_name in excluded_flags:
                if flag_name in SCL_FLAGS:
                    excluded_flag_numbers.append(SCL_FLAGS[flag_name])
                else:
                    print(f"[Pipeline] WARNING: Unknown SCL flag name '{flag_name}'. Available flags: {list(SCL_FLAGS.keys())}")
            
            print(f"[Pipeline] Excluded flag numbers: {excluded_flag_numbers}")
            
            # Create valid mask (True = Valid, False = Invalid/Excluded)
            # scl is likely float due to scene loading, need to cast to int for comparison safely
            scl_int = scl.astype(int)
            valid_mask = ~np.isin(scl_int, excluded_flag_numbers)
            
            # Calculate percentage
            total_pixels = valid_mask.size
            valid_pixels = np.sum(valid_mask)
            valid_percentage = (valid_pixels / total_pixels) * 100
            cloud_shadow_percentage = 100 - valid_percentage
            
            print(f"[Pipeline] Valid pixels: {valid_pixels} / {total_pixels}")
            print(f"[Pipeline] Valid pixel percentage: {valid_percentage:.2f}%")
            print(f"[Pipeline] Cloud/Shadow percentage: {cloud_shadow_percentage:.2f}%")
            
            # Apply mask to all other bands
            print(f"[Pipeline] Masking invalid pixels in output bands...")
            for code in band_codes:
                if code in bands_dict:
                    # Set invalid pixels to fill_value or NaN
                    # If fill_value is 0, we can just multiply by mask (boolean 0/1)
                    # But safer to explicitly set
                    bands_dict[code][~valid_mask] = self.fill_value
        else:
            print(f"[Pipeline] WARNING: SCL band not found. Skipping filtering and valid pixel estimation.")
        
        # Stack bands into multi-band array (height, width, n_bands)
        # Only stack the requested bands, not SCL (unless requested)
        bands_list = [bands_dict[code] for code in band_codes]
        stacked_array = np.stack(bands_list, axis=-1)
        
        # Build output file path
        os.makedirs(output_directory, exist_ok=True)
        output_filename = f"{base_name}_{band_selection}.tif"
        output_path = os.path.join(output_directory, output_filename)
        
        print(f"\n[Pipeline] Saving bands to: {output_path}")
        scene.save_tiff(stacked_array, output_path, nodata_value=self.fill_value, band_names=band_names)
        
        # Print band information
        print(f"[Pipeline] [OK] Saved {len(band_codes)} bands:")
        for code, name in zip(band_codes, band_names):
            print(f"[Pipeline]   - {code} ({name})")
        
        return {"bands": bands_dict, "output_path": output_path}

