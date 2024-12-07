#!/usr/bin/env python3

"""Script to delete a specific image from an album."""

import os
import sys
import json
import shutil
import argparse
import logging
from pathlib import Path
from typing import Dict, List, Optional

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

# Base paths
BASE_DIR = Path(__file__).parent.parent
ALBUMS_DIR = BASE_DIR / 'albums'
ALBUMS_JSON = ALBUMS_DIR / 'albums.json'

def load_albums() -> Dict:
    """Load the albums.json file."""
    try:
        with open(ALBUMS_JSON) as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Failed to load albums.json: {e}")
        sys.exit(1)

def save_albums(albums_data: Dict) -> None:
    """Save the albums data back to albums.json."""
    try:
        with open(ALBUMS_JSON, 'w') as f:
            json.dump(albums_data, f, indent=2)
    except Exception as e:
        logger.error(f"Failed to save albums.json: {e}")
        sys.exit(1)

def delete_image_files(album_path: str, image_name: str) -> None:
    """Delete the image file and its responsive versions."""
    # Delete original image
    original_path = ALBUMS_DIR / album_path / 'images' / image_name
    if original_path.exists():
        original_path.unlink()
        logger.info(f"Deleted original image: {original_path}")

    # Delete responsive versions
    responsive_dir = ALBUMS_DIR / album_path / 'responsive'
    if responsive_dir.exists():
        # Get image name without extension
        name_without_ext = Path(image_name).stem
        # Delete all responsive versions of the image
        for size_dir in ['thumbnail', 'small', 'medium', 'large']:
            size_path = responsive_dir / size_dir
            if size_path.exists():
                # Delete both jpg and webp versions if they exist
                for ext in ['.jpg', '.webp']:
                    responsive_file = size_path / f"{name_without_ext}{ext}"
                    if responsive_file.exists():
                        responsive_file.unlink()
                        logger.info(f"Deleted responsive image: {responsive_file}")

def update_metadata(album_id: str, image_name: str) -> None:
    """Update the album's metadata.json file to remove the image entry."""
    metadata_path = ALBUMS_DIR / album_id / 'metadata.json'
    try:
        # Load metadata
        with open(metadata_path) as f:
            metadata = json.load(f)
        
        # Remove the image entry if it exists
        if image_name in metadata:
            del metadata[image_name]
            logger.info(f"Removed metadata entry for: {image_name}")
            
            # Save updated metadata
            with open(metadata_path, 'w') as f:
                json.dump(metadata, f, indent=2)
    except Exception as e:
        logger.error(f"Failed to update metadata.json: {e}")
        raise

def delete_image(album_id: str, image_path: str) -> bool:
    """Delete a specific image from an album."""
    try:
        # Load albums data
        albums_data = load_albums()
        
        # Find the album
        album = next((a for a in albums_data['albums'] if a['id'] == album_id), None)
        if not album:
            raise ValueError(f"Album not found: {album_id}")
        
        # Check if image exists in album
        if image_path not in album['images']:
            raise ValueError(f"Image not found in album: {image_path}")
        
        # Get just the image name from the path
        image_name = Path(image_path).name
        
        # Update metadata.json
        update_metadata(album_id, image_name)
        
        # Remove image from the list
        album['images'].remove(image_path)
        
        # If this was the cover image, set a new one
        if album['coverImage'] == image_path and album['images']:
            album['coverImage'] = album['images'][0]
            logger.info(f"Updated cover image to: {album['coverImage']}")
        
        # Delete the actual image files
        delete_image_files(album_id, image_name)
        
        # Save updated albums data
        save_albums(albums_data)
        
        logger.info(f"Successfully deleted image: {image_path}")
        return True
        
    except Exception as e:
        logger.error(f"Failed to delete image: {e}")
        return False

def main():
    parser = argparse.ArgumentParser(description='Delete an image from an album')
    parser.add_argument('album_id', help='ID of the album')
    parser.add_argument('image_name', help='Name of the image file to delete')
    
    args = parser.parse_args()
    
    # Construct the full image path as it appears in albums.json
    image_path = f"{args.album_id}/images/{args.image_name}"
    
    if not delete_image(args.album_id, image_path):
        sys.exit(1)

if __name__ == '__main__':
    main()
