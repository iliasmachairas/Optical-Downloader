# scripts/run_lake_chla.py
import json
import numpy as np
from Optical_Downloader import Optical_Downloader
from config import xmin, xmax, ymin, ymax, selected_date
from aoi import AOI 


def main():
    pipeline = Optical_Downloader(
        stac_url="https://planetarycomputer.microsoft.com/api/stac/v1",
        collection="sentinel-2-l2a",
    )
    
    try:
        # Convert bounding box to 4 corner points (matching original order)
        selected_coords = [
            [xmin, ymax],  # top-left
            [xmax, ymax],  # top-right
            [xmax, ymin],  # bottom-right
            [xmin, ymin]   # bottom-left
        ]
        
        result = pipeline.run(
            points_list=selected_coords,
            date_str="2024-07-01/2024-07-31",
            max_cloud=20,
        )
        
        print(f"\n[Main] Pipeline completed successfully")
        print(f"[Main] [OK] Data extraction completed")
        
    except Exception as e:
        print(f"[Main] ERROR: {type(e).__name__}: {str(e)}")
        import traceback
        traceback.print_exc()
        raise

if __name__ == "__main__":
    main()
