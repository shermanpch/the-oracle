#!/usr/bin/env python3
"""
Oracle I Ching Scraper

This script scrapes I Ching hexagram information from online sources and
saves it in a structured format that can be used by the Oracle I Ching application.
It imports the COORDINATE and HEXAGRAM constants from the core module.

Performance optimizations:
- Multithreading using ThreadPoolExecutor for parallel processing
- Caching system to avoid redundant downloads of web pages and images
- Error handling with timeouts to prevent hanging on slow connections
"""

import concurrent.futures
import hashlib
import os
import sys
import time
from urllib.parse import urlparse

import requests
from bs4 import BeautifulSoup
from tqdm import tqdm

# Add the project root to the Python path so we can import from src
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

# Import COORDINATE and HEXAGRAM from core modules
from src.app.core.coordinate import COORDINATE
from src.app.core.hexagram import HEXAGRAM

# Configuration for concurrent processing
MAX_WORKERS = 10  # Maximum number of worker threads
TIMEOUT = 30  # Request timeout in seconds
CACHE_DIR = os.path.join(
    project_root, ".scraper_cache"
)  # Cache directory for downloaded resources


def create_cache_dir():
    """Create cache directory if it doesn't exist."""
    if not os.path.exists(CACHE_DIR):
        os.makedirs(CACHE_DIR)
        print(f"Created cache directory: {CACHE_DIR}")


def get_cache_path(url):
    """Generate a unique cache file path for a URL."""
    url_hash = hashlib.md5(url.encode()).hexdigest()
    parsed_url = urlparse(url)
    filename = os.path.basename(parsed_url.path) or "index.html"
    return os.path.join(CACHE_DIR, f"{url_hash}_{filename}")


def fetch_and_parse(url):
    """Fetch a URL and return a BeautifulSoup object, with caching.

    The caching system works by:
    1. Creating a unique filename for each URL using an MD5 hash
    2. Checking if the HTML content exists in the cache
    3. Only downloading if the cached file doesn't exist
    4. Saving the content to cache for future use

    This significantly speeds up repeated runs and prevents unnecessary
    load on the source websites.
    """
    cache_path = get_cache_path(url)

    # Check cache first
    if os.path.exists(cache_path):
        with open(cache_path, "r", encoding="utf-8") as f:
            html = f.read()
            return BeautifulSoup(html, "html.parser")

    # Fetch and cache
    try:
        response = requests.get(url, timeout=TIMEOUT)
        response.encoding = "utf-8"
        html = response.text

        # Cache the response
        with open(cache_path, "w", encoding="utf-8") as f:
            f.write(html)

        return BeautifulSoup(html, "html.parser")
    except requests.exceptions.RequestException as e:
        print(f"Error fetching {url}: {e}")
        return None


def download_image(img_url, save_path):
    """Download and save an image from a given URL with caching.

    Implements a simple file-based caching system:
    - If the image already exists at the target path, skip downloading
    - Otherwise download and save the image

    This prevents redundant downloads, especially when the script is run
    multiple times during development and debugging.
    """
    # Skip if file already exists (image already downloaded)
    if os.path.exists(save_path):
        return f"Image already exists: {save_path}"

    try:
        response = requests.get(img_url, stream=True, timeout=TIMEOUT)
        response.raise_for_status()

        with open(save_path, "wb") as img_file:
            for chunk in response.iter_content(1024):
                img_file.write(chunk)
        return f"Saved image: {save_path}"

    except requests.exceptions.RequestException as e:
        return f"Failed to download image {img_url}: {e}"


def process_hexagram(coordinate_info):
    """Process a single hexagram and its lines."""
    coordinate, hex_name = coordinate_info
    results = []

    if hex_name not in HEXAGRAM:
        return [f"Hexagram '{hex_name}' not found in HEXAGRAM mapping, skipping..."]

    url = HEXAGRAM[hex_name]
    soup = fetch_and_parse(url)

    if not soup:
        return [f"Failed to fetch and parse {url} for hexagram {hex_name}"]

    title_divs = soup.find_all("div", class_="guatt cf f14 fb tleft")
    body_divs = soup.find_all("div", class_="gualist tleft f14 lh25")

    if not title_divs or not body_divs:
        return [f"No content found for hexagram {hex_name} at {url}"]

    parent_coord = f"{coordinate[0]}-{coordinate[1]}"

    for idx, (title_div, body_div) in enumerate(zip(title_divs, body_divs)):
        title_text = title_div.get_text(separator="\n", strip=True)
        body_text = body_div.get_text(separator="\n", strip=True)
        combined = f"{title_text}\n{body_text}"

        img_tag = body_div.find("img")
        img_url = img_tag["src"] if img_tag else None

        if idx == 0:
            # Parent text
            folder = os.path.join("data", parent_coord, "html")
        else:
            # Child text
            child_coord = idx % 6
            folder = os.path.join("data", parent_coord, str(child_coord), "html")

        os.makedirs(folder, exist_ok=True)

        file_path = os.path.join(folder, "body.txt")
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(combined)

        results.append(
            f"Saved {hex_name} {'parent' if idx == 0 else 'child ' + str(idx % 6)} text to {file_path}"
        )

        if img_url:
            if idx == 0:
                # No images for parent
                pass
            else:
                # Images for child
                child_coord = idx % 6
                img_folder = os.path.join(
                    "data", parent_coord, str(child_coord), "images"
                )
                os.makedirs(img_folder, exist_ok=True)
                img_path = os.path.join(img_folder, "hexagram.jpg")
                img_result = download_image(img_url, img_path)
                results.append(img_result)

    return results


def run_scraper():
    """Main function to run the scraper with parallel processing."""
    # Change to the project root directory
    os.chdir(project_root)
    print(f"Working directory set to: {os.getcwd()}")

    # Create data directory if it doesn't exist
    data_dir = os.path.join(project_root, "data")
    if not os.path.exists(data_dir):
        os.makedirs(data_dir)
        print(f"Created data directory: {data_dir}")

    # Create cache directory
    create_cache_dir()

    # Collect all coordinate info
    coordinate_info_list = [
        (coordinate, COORDINATE[coordinate]) for coordinate in COORDINATE
    ]
    total_coordinates = len(coordinate_info_list)
    print(f"Found {total_coordinates} hexagrams to scrape")

    start_time = time.time()

    # Process hexagrams in parallel
    with concurrent.futures.ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        # Submit all tasks and map them to their respective coordinates for display
        future_to_coord = {
            executor.submit(process_hexagram, coord_info): coord_info[1]
            for coord_info in coordinate_info_list
        }

        # Use tqdm to show progress
        with tqdm(total=total_coordinates, desc="Scraping Hexagrams") as progress:
            for future in concurrent.futures.as_completed(future_to_coord):
                hex_name = future_to_coord[future]
                try:
                    results = future.result()
                    # Log only the first result to avoid cluttering the console
                    if results:
                        print(f"Processed {hex_name}: {results[0]}")
                except Exception as exc:
                    print(f"{hex_name} generated an exception: {exc}")
                progress.update(1)

    end_time = time.time()
    elapsed_time = end_time - start_time

    print(f"Scraping completed in {elapsed_time:.2f} seconds")
    print(f"Data has been saved to {data_dir}")
    print(f"Cache is stored in {CACHE_DIR}")


if __name__ == "__main__":
    run_scraper()
