# scripts/run_lake_chla.py
import json
import numpy as np
from datetime import datetime, timedelta
from Optical_Downloader import Optical_Downloader
from config import xmin, xmax, ymin, ymax, selected_date, max_cloud_tile, extra_days
from aoi import AOI 


def main():
    pipeline = Optical_Downloader(
        stac_url="https://planetarycomputer.microsoft.com/api/stac/v1",
        collection="sentinel-2-l2a",
    )
    
    try:
        # Calculate date range
        # Parse selected_date (assuming YYYY-MM-DD format)
        dt_selected = datetime.strptime(selected_date, "%Y-%m-%d")
        
        # Calculate start and end dates
        start_date = dt_selected - timedelta(days=extra_days)
        end_date = dt_selected + timedelta(days=extra_days)
        
        # Format as STAC datetime string (ISO 8601 range)
        date_str = f"{start_date.strftime('%Y-%m-%d')}/{end_date.strftime('%Y-%m-%d')}"
        
        print(f"[Main] Selected Date: {selected_date}")
        print(f"[Main] Search Window: +/- {extra_days} days")
        print(f"[Main] Date Range String: {date_str}")
        print(f"[Main] Max Cloud Tile Coverage: {max_cloud_tile}%")

        # Convert bounding box to 4 corner points (matching original order)
        selected_coords = [
            [xmin, ymax],  # top-left
            [xmax, ymax],  # top-right
            [xmax, ymin],  # bottom-right
            [xmin, ymin]   # bottom-left
        ]
        
        result = pipeline.run(
            points_list=selected_coords,
            date_str=date_str,
            max_cloud_tile=max_cloud_tile,
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
