# import math
# from loguru import logger
#
# # Approximate conversion factors
# KM_PER_DEGREE_LAT = 111.32  # 1 degree latitude ≈ 111.32 km
# LAT_PER_KM = 1 / KM_PER_DEGREE_LAT  # Degrees latitude per kilometer
#
#
# # The conversion for longitude varies by latitude
# def km_per_degree_lon_at_lat(latitude):
#     return 111.32 * math.cos(math.radians(latitude))  # Approximation
#
#
# def split_rectangle_into_squares(rectangle, grid_size_km):
#     low_lat = rectangle["low"]["latitude"]
#     low_lon = rectangle["low"]["longitude"]
#     high_lat = rectangle["high"]["latitude"]
#     high_lon = rectangle["high"]["longitude"]
#
#     # Calculate the degree size of 5km in latitude and longitude
#     lat_step = grid_size_km * LAT_PER_KM
#     lon_step = grid_size_km / km_per_degree_lon_at_lat((low_lat + high_lat) / 2)  # Using average latitude
#
#     grids = []
#
#     # Start from the low lat/lon and go to high lat/lon in grid steps
#     lat = low_lat
#     while lat + lat_step < high_lat:
#         lon = low_lon
#         while lon + lon_step < high_lon:
#             grid = {
#                 "low": {
#                     "latitude": lat,
#                     "longitude": lon
#                 },
#                 "high": {
#                     "latitude": lat + lat_step,
#                     "longitude": lon + lon_step
#                 }
#             }
#             grids.append(grid)
#             lon += lon_step
#         lat += lat_step
#
#     return grids
#
#
# if __name__ == "__main__":
# # Rectangle bounds for New York City
#     location = {
#         "rectangle": {
#             "low": {
#                 "latitude": 40.477398,
#                 "longitude": -74.259087
#             },
#             "high": {
#                 "latitude": 40.91618,
#                 "longitude": -73.70018
#             }
#         }
#     }
#
#     # Grid size in kilometers (5x5 km)
#     grid_size_km = 5
#
#     # Split the rectangle into smaller squares
#     grids = split_rectangle_into_squares(location["rectangle"], grid_size_km)
#
#     # Print the smaller grid squares
#     for idx, grid in enumerate(grids):
#         logger.info(f"Grid {idx + 1}: {grid}")

import math
from loguru import logger

EARTH_RADIUS_KM = 6371  # Earth's mean radius in kilometers


def haversine_distance(lat1, lon1, lat2, lon2):
    """Calculate the great-circle distance between two points on Earth."""
    lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = math.sin(dlat / 2) ** 2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2) ** 2
    c = 2 * math.asin(math.sqrt(a))
    return EARTH_RADIUS_KM * c


def calculate_lat_lon_steps(lat, lon, distance_km):
    """Calculate latitude and longitude steps for a given distance at a given point."""
    lat_step = distance_km / EARTH_RADIUS_KM * (180 / math.pi)
    lon_step = abs(distance_km / (EARTH_RADIUS_KM * math.cos(math.radians(lat))) * (180 / math.pi))
    return lat_step, lon_step


def split_rectangle_into_squares(rectangle, grid_size_km):
    low_lat = min(rectangle["low"]["latitude"], rectangle["high"]["latitude"])
    low_lon = min(rectangle["low"]["longitude"], rectangle["high"]["longitude"])
    high_lat = max(rectangle["low"]["latitude"], rectangle["high"]["latitude"])
    high_lon = max(rectangle["low"]["longitude"], rectangle["high"]["longitude"])

    grids = []
    lat = low_lat
    while lat < high_lat:
        lon = low_lon
        while lon < high_lon:
            lat_step, lon_step = calculate_lat_lon_steps(lat, lon, grid_size_km)

            grid_high_lat = min(lat + lat_step, high_lat)
            grid_high_lon = min(lon + lon_step, high_lon)

            grid = {
                "low": {"latitude": lat, "longitude": lon},
                "high": {"latitude": grid_high_lat, "longitude": grid_high_lon}
            }
            grids.append(grid)

            actual_distance = haversine_distance(lat, lon, grid_high_lat, grid_high_lon)
            logger.debug(f"Grid size: {actual_distance:.2f} km")

            lon = grid_high_lon
        lat = min(lat + lat_step, high_lat)

    return grids


def validate_rectangle(rectangle):
    if (rectangle["low"]["latitude"] > rectangle["high"]["latitude"] or
            rectangle["low"]["longitude"] > rectangle["high"]["longitude"]):
        raise ValueError("Invalid rectangle: 'low' coordinates must be less than or equal to 'high' coordinates")


if __name__ == "__main__":
    # Rectangle bounds for New York City
    location = {
        "rectangle": {
            "low": {"latitude": 40.477398, "longitude": -74.259087},
            "high": {"latitude": 40.91618, "longitude": -73.70018}
        }
    }

    grid_size_km = 5

    try:
        validate_rectangle(location["rectangle"])
        grids = split_rectangle_into_squares(location["rectangle"], grid_size_km)

        for idx, grid in enumerate(grids):
            logger.info(f"Grid {idx + 1}: {grid}")

        logger.info(f"Total number of grids: {len(grids)}")
    except ValueError as e:
        logger.error(f"Error: {e}")
