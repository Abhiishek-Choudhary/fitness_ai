"""
Geo service — Single Responsibility: all distance/proximity logic.
No Django model knowledge beyond what's passed in.
"""
import math
from typing import Optional

EARTH_RADIUS_KM = 6371.0
DEFAULT_RADIUS_KM = 50


def haversine(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Return great-circle distance in kilometres between two lat/lon points."""
    lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = math.sin(dlat / 2) ** 2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2) ** 2
    return 2 * EARTH_RADIUS_KM * math.asin(math.sqrt(a))


def bounding_box(lat: float, lon: float, radius_km: float) -> tuple:
    """
    Return (min_lat, max_lat, min_lon, max_lon) for a square bounding box.
    Used as a fast DB pre-filter before exact Haversine computation.
    """
    lat_delta = radius_km / 111.0
    lon_delta = radius_km / (111.0 * math.cos(math.radians(lat)))
    return (lat - lat_delta, lat + lat_delta, lon - lon_delta, lon + lon_delta)


def filter_qs_by_radius(qs, lat: float, lon: float, radius_km: float,
                         lat_field: str = 'latitude', lon_field: str = 'longitude'):
    """Apply bounding-box pre-filter on a queryset with lat/lon fields."""
    min_lat, max_lat, min_lon, max_lon = bounding_box(lat, lon, radius_km)
    return qs.filter(**{
        f'{lat_field}__range': (min_lat, max_lat),
        f'{lon_field}__range': (min_lon, max_lon),
        f'{lat_field}__isnull': False,
        f'{lon_field}__isnull': False,
    })


def attach_distance(objects: list, origin_lat: float, origin_lon: float,
                    lat_attr: str = 'latitude', lon_attr: str = 'longitude',
                    radius_km: Optional[float] = None) -> list:
    """
    Attach a `.distance_km` float attribute to each object.
    Optionally exclude objects beyond radius_km.
    Returns list sorted by distance ascending.
    """
    result = []
    for obj in objects:
        obj_lat = getattr(obj, lat_attr, None)
        obj_lon = getattr(obj, lon_attr, None)
        if obj_lat is None or obj_lon is None:
            continue
        dist = haversine(origin_lat, origin_lon, float(obj_lat), float(obj_lon))
        if radius_km is not None and dist > radius_km:
            continue
        obj.distance_km = round(dist, 2)
        result.append(obj)
    return sorted(result, key=lambda o: o.distance_km)


def format_distance(km: float) -> str:
    if km < 1:
        return f"{int(km * 1000)} m"
    return f"{round(km, 1)} km"
