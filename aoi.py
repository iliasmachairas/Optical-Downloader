# -*- coding: utf-8 -*-
from shapely.geometry import shape


class AOI:
    def __init__(self, geojson: dict):
        if "geometry" not in geojson:
            raise ValueError("GeoJSON must contain a 'geometry' field.")
        geom = geojson["geometry"]
        if geom["type"] == "Polygon":
            coords = geom["coordinates"][0]
            if coords[0] != coords[-1]:
                geom["coordinates"][0].append(coords[0])
        self.geojson  = geojson
        self.geometry = shape(geom)

    @property
    def bounds(self):
        return self.geometry.bounds  # (minx, miny, maxx, maxy)

    @property
    def centroid(self):
        c = self.geometry.centroid
        return (c.x, c.y)

    @property
    def to_geojson(self):
        return self.geojson

    @classmethod
    def from_four_points(cls, points, name="AOI"):
        if len(points) != 4:
            raise ValueError("Exactly four corner points required.")
        geojson = {
            "type": "Feature",
            "properties": {"name": name},
            "geometry": {"type": "Polygon", "coordinates": [points + [points[0]]]},
        }
        return cls(geojson)
