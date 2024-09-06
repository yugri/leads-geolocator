import os
import requests
import time
import pandas as pd
from loguru import logger

from utils import split_rectangle_into_squares, validate_rectangle

API_KEY = os.getenv("GOOGLE_MAPS_API_KEY")


def search_places_with_pagination(query: str, location: dict):
    # URL for the Places API search
    url = 'https://places.googleapis.com/v1/places:searchText'

    headers = {
        'Content-Type': 'application/json',
        'X-Goog-Api-Key': API_KEY,
        'X-Goog-FieldMask': 'places.displayName,places.formattedAddress,places.location,places.name,places.websiteUri,nextPageToken'
    }

    # Split the location rectangle into smaller squares
    validate_rectangle(location["rectangle"])
    grids = split_rectangle_into_squares(location["rectangle"], 5)

    results = []
    seen_place_ids = set()

    for idx, grid in enumerate(grids):
        logger.info(f"Searching in grid {idx + 1}: {grid}")
        grid_results = []

        payload = {
            "textQuery": query,
            "locationBias": {
                "rectangle": {
                    "low": grid["low"],
                    "high": grid["high"]
                }
            }
        }

        while True:
            try:
                # Make the request
                response = requests.post(url, headers=headers, json=payload)
                response.raise_for_status()  # Raise exception for HTTP errors
            except requests.exceptions.RequestException as e:
                logger.error(f"Error: {e}")
                break

            data = response.json()

            # Add the results to the grid results list
            places = data.get('places', [])
            for place in places:
                place_id = place.get('name')
                if place_id and place_id not in seen_place_ids:
                    grid_results.append(place)
                    seen_place_ids.add(place_id)  # Track the place to avoid duplicates

            # Check if there's a next_page_token for more results
            next_page_token = data.get("nextPageToken")
            if next_page_token:
                # Google API asks you to wait a few seconds before using next_page_token
                time.sleep(2)  # Wait 2 seconds
                # Update the payload with the next_page_token for the next request
                payload['pageToken'] = next_page_token
            else:
                logger.info(f"Found {len(grid_results)} places in grid {idx + 1}")
                results.extend(grid_results)
                # No more pages, break the loop
                break

    return results


# Example usage
if __name__ == "__main__":
    query = "gift shop"
    location = {
        "rectangle": {
            "low": {
                "latitude": 40.477398,
                "longitude": -74.259087
            },
            "high": {
                "latitude": 40.91618,
                "longitude": -73.70018
            }
        }
    }  # Approx New York City coordinates rectangle area

    all_results = search_places_with_pagination(query, location)

    # Convert to pandas dataframe
    df = pd.DataFrame(all_results)

    # Save to CSV
    file_name = f"{"_".join(query.split()).lower()}_results.csv"
    df.to_csv(file_name, index=False)
    logger.info(f"Data saved to {file_name}")