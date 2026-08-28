def rectangle_from_points(points, name="Rectangle AOI"):
    if len(points) != 5:
        raise ValueError("Rectangle needs exactly 5 points (closed ring).")
    return {
        "type": "Feature",
        "properties": {"name": name},
        "geometry": {"type": "Polygon", "coordinates": [points]},
    }
