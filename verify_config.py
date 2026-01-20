from config import max_cloud_tile, extra_days, selected_date
from datetime import datetime, timedelta

print(f"max_cloud_tile: {max_cloud_tile}")
print(f"extra_days: {extra_days}")
print(f"selected_date: {selected_date}")

dt_selected = datetime.strptime(selected_date, "%Y-%m-%d")
start_date = dt_selected - timedelta(days=extra_days)
end_date = dt_selected + timedelta(days=extra_days)
date_str = f"{start_date.strftime('%Y-%m-%d')}/{end_date.strftime('%Y-%m-%d')}"
print(f"Calculated date_str: {date_str}")
