# -*- coding: utf-8 -*-
import os
import numpy as np
from datetime import datetime

from .aoi import AOI
from .search import SentinelSearch
from .scene import SentinelScene


def _unique_path(path: str) -> str:
    """Return path unchanged if it doesn't exist, otherwise append (1), (2)… until unique."""
    if not os.path.exists(path):
        return path
    base, ext = os.path.splitext(path)
    counter = 1
    while os.path.exists(f"{base}({counter}){ext}"):
        counter += 1
    return f"{base}({counter}){ext}"

SCL_FLAGS = {
    "No Data": 0, "Saturated or defective": 1, "Dark area pixels": 2,
    "Cloud shadows": 3, "Vegetation": 4, "Not vegetated": 5,
    "Water": 6, "Unclassified": 7, "Cloud medium probability": 8,
    "Cloud high probability": 9, "Thin cirrus": 10, "Snow or ice": 11,
}

S2_BAND_SELECTIONS = {
    "rgb_only":     [("B04","Red"), ("B03","Green"), ("B02","Blue")],
    "rgb_nir_swir": [("B04","Red"), ("B03","Green"), ("B02","Blue"),
                     ("B08","NIR"), ("B11","SWIR1"), ("B12","SWIR2")],
    "all_bands":    [
        ("B01","Coastal_Aerosol"), ("B02","Blue"), ("B03","Green"), ("B04","Red"),
        ("B05","Red_Edge_1"), ("B06","Red_Edge_2"), ("B07","Red_Edge_3"),
        ("B08","NIR"), ("B09","Narrow_NIR"), ("B11","SWIR1"), ("B12","SWIR2"),
    ],
}

L8_BAND_SELECTIONS = {
    "rgb_only":     [("red","Red"), ("green","Green"), ("blue","Blue")],
    "rgb_nir_swir": [("red","Red"), ("green","Green"), ("blue","Blue"),
                     ("nir08","NIR"), ("swir16","SWIR1"), ("swir22","SWIR2")],
    "all_bands":    [
        ("coastal","Coastal_Aerosol"), ("blue","Blue"), ("green","Green"),
        ("red","Red"), ("nir08","NIR"), ("swir16","SWIR1"), ("swir22","SWIR2"),
    ],
}


class Optical_Downloader:
    def __init__(self, stac_url: str, collection: str,
                 resolution: int = 10, dtype: str = "float32", fill_value: float = 0.0):
        self.search     = SentinelSearch(stac_url, collection)
        self.collection = collection
        self.resolution = resolution
        self.dtype      = dtype
        self.fill_value = fill_value

    def run(
        self,
        points_list: list,
        date_str: str,
        max_cloud_tile: int = 100,
        max_cloud_tolerance: int = 20,
        platform: str = "sentinel-2-l2a",
        band_selection: str = "all_bands",
        output_directory: str = "./output",
        excluded_flags: list = None,
        create_report: bool = True,
        progress_callback=None,
    ):
        def _p(pct, msg=""):
            if progress_callback:
                progress_callback(pct, msg)

        excluded_flags = excluded_flags or []

        # 1. AOI + STAC search
        aoi  = AOI.from_four_points(points_list)
        _p(20, "Querying STAC API…")
        item = self.search.find_best_item(aoi.to_geojson, date_str,
                                          max_cloud_tile=max_cloud_tile)

        props = item.get("properties", {}) if isinstance(item, dict) \
            else getattr(item, "properties", {})

        datetime_val         = props.get("datetime", "Unknown")
        datetime_str         = datetime_val[:10] if datetime_val != "Unknown" else "Unknown"
        cloud_cover_metadata = props.get("eo:cloud_cover", 0.0)

        if "landsat" in platform.lower():
            path           = props.get("landsat:wrs_path", "")
            row            = props.get("landsat:wrs_row", "")
            tile_id        = f"{path}{row}" if path and row else "Unknown"
            platform_short = "L8-9"
            target_res     = 30
        else:
            tile_id        = props.get("s2:mgrs_tile") or props.get("mgrs:utm_zone", "Unknown")
            platform_short = "S2"
            target_res     = self.resolution

        _p(35, f"Scene: {tile_id}  ({datetime_str})  cloud={cloud_cover_metadata:.1f}%")
        print(f"[Pipeline] {tile_id} | {datetime_str} | cloud={cloud_cover_metadata}%")

        # 2. Create scene object
        scene = SentinelScene(item, aoi, resolution=target_res,
                              dtype=self.dtype, fill_value=self.fill_value)

        # 3. Band lists
        if "landsat" in platform.lower():
            selections, qa_band = L8_BAND_SELECTIONS, "qa_pixel"
        else:
            selections, qa_band = S2_BAND_SELECTIONS, "SCL"

        if band_selection not in selections:
            raise ValueError(f"Unknown band_selection '{band_selection}'")

        selected_bands = selections[band_selection]
        band_codes     = [b[0] for b in selected_bands]
        band_names_out = [b[1] for b in selected_bands]

        # 4. Load QA band → cloud statistics
        _p(40, "Analysing cloud cover…")
        qa_data = scene.load_bands([qa_band])[qa_band]

        if "landsat" in platform.lower():
            qi           = qa_data.astype(int)
            invalid_mask = ((qi & (1<<0)) | (qi & (1<<1)) |
                            (qi & (1<<2)) | (qi & (1<<3)) | (qi & (1<<4))) > 0
            valid_mask   = ~invalid_mask
            cloud_pixels = int(np.sum((qi & ((1<<1)|(1<<2)|(1<<3))) > 0))
        else:
            scl             = qa_data.astype(int)
            base_excl       = {SCL_FLAGS[f] for f in excluded_flags if f in SCL_FLAGS}
            base_excl      |= {0, 1}  # always exclude No Data / Saturated
            valid_mask      = ~np.isin(scl, sorted(base_excl))
            cloud_pixels    = int(np.sum(np.isin(scl, [3, 8, 9, 10])))

        total_pixels     = valid_mask.size
        valid_pct        = (int(np.sum(valid_mask)) / total_pixels) * 100
        cloud_shadow_pct = (cloud_pixels / total_pixels) * 100

        _p(55, f"Cloud/shadow: {cloud_shadow_pct:.1f}%  Valid: {valid_pct:.1f}%")

        # 5. Write report
        output_base = f"{platform_short}_{datetime_str}_{tile_id}"
        report_path = None
        if create_report:
            os.makedirs(output_directory, exist_ok=True)
            report_path = os.path.join(output_directory, f"{output_base}_report.txt")
            result_str  = "REJECTED (Too Cloudy)" if cloud_shadow_pct > max_cloud_tolerance \
                          else "ACCEPTED"
            with open(report_path, "w") as f:
                f.write(f"Tile ID: {tile_id}\nDate: {datetime_str}\n"
                        f"Platform: {platform}\nResolution: {target_res}m\n"
                        f"Metadata Cloud Cover: {cloud_cover_metadata:.2f}%\n"
                        f"Calculated Cloud/Shadow: {cloud_shadow_pct:.2f}%\n"
                        f"Valid Pixels: {valid_pct:.2f}%\n"
                        f"Tolerance Threshold: {max_cloud_tolerance}%\n"
                        f"Result: {result_str}\n")

        # 6. Check tolerance
        if cloud_shadow_pct > max_cloud_tolerance:
            _p(100, f"Skipped — too cloudy ({cloud_shadow_pct:.1f}%)")
            return {"status": "skipped", "report": report_path}

        # 7. Download bands, mask, stack, save
        _p(60, "Downloading spectral bands…")
        bands_dict = scene.load_bands(band_codes)

        _p(80, "Applying cloud mask…")
        for code in band_codes:
            if code in bands_dict:
                bands_dict[code][~valid_mask] = self.fill_value

        stacked     = np.stack([bands_dict[c] for c in band_codes], axis=-1)
        output_path = _unique_path(
            os.path.join(output_directory, f"{output_base}_{band_selection}.tif"))

        os.makedirs(output_directory, exist_ok=True)
        _p(90, "Saving GeoTIFF…")
        scene.save_tiff(stacked, output_path, nodata_value=self.fill_value,
                        band_names=band_names_out)

        return {"status": "downloaded", "output_path": output_path, "report": report_path}
