# -*- coding: utf-8 -*-
import time
import requests
import json


class SentinelSearch:
    def __init__(self, stac_url, collection):
        self.stac_url   = stac_url.rstrip('/')
        self.collection = collection
        self.sign_url   = "https://planetarycomputer.microsoft.com/api/sas/v1/sign"
        self.max_retries = 3
        self.retry_delay = 5  # seconds between retries

    def _sign_asset_url(self, href):
        try:
            r = requests.get(self.sign_url, params={"href": href})
            r.raise_for_status()
            return r.json().get("href", href)
        except Exception:
            return href

    def _sign_item_assets(self, item):
        for asset_data in item.get("assets", {}).values():
            if "href" in asset_data:
                asset_data["href"] = self._sign_asset_url(asset_data["href"])
        return item

    def find_best_item(self, aoi_json: dict, datetime_str: str, max_cloud_tile: int = 20):
        endpoint = f"{self.stac_url}/search"
        geom     = aoi_json.get("geometry", aoi_json)
        body     = {
            "collections": [self.collection],
            "intersects":  geom,
            "datetime":    datetime_str,
            "query":       {"eo:cloud_cover": {"lt": max_cloud_tile}},
            "limit":       1,
            "sortby":      [{"field": "eo:cloud_cover", "direction": "asc"}],
        }

        last_error = None
        for attempt in range(1, self.max_retries + 1):
            try:
                print(f"[Search] STAC query attempt {attempt}/{self.max_retries}…")
                r = requests.post(endpoint, json=body, timeout=60)
                r.raise_for_status()
                items = r.json().get("features", [])
                if not items:
                    raise RuntimeError(
                        "No scenes found for the given AOI, date range, and cloud threshold.")
                return self._sign_item_assets(items[0])

            except requests.exceptions.HTTPError as e:
                # 504 / 503 are transient — retry; anything else fail immediately
                if r.status_code in (503, 504) and attempt < self.max_retries:
                    print(f"[Search] Server timeout ({r.status_code}), "
                          f"retrying in {self.retry_delay}s…")
                    time.sleep(self.retry_delay)
                    last_error = e
                else:
                    raise RuntimeError(
                        f"STAC API error {r.status_code}: {r.text}") from e

            except requests.exceptions.Timeout:
                if attempt < self.max_retries:
                    print(f"[Search] Request timed out, retrying in {self.retry_delay}s…")
                    time.sleep(self.retry_delay)
                else:
                    raise RuntimeError("STAC API timed out after all retries.")

        raise RuntimeError("STAC API failed after all retries.") from last_error
