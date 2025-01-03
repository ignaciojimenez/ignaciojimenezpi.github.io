"""Delete images from an album."""

import os
import json
import logging
import argparse
from pathlib import Path
from typing import List, Dict

from config import ALBUMS_DIR, ALBUMS_JSON

logger = logging.getLogger(__name__)

def load_albums_json() -> Dict:
    """Load albums.json data."""
    try:
        with open(ALBUMS_JSON, 'r') as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Failed to load albums.json: {e}")
        return {'albums': []}

def save_albums_json(data: Dict) -> bool:
    """Save albums.json data."""
    try:
        with open(ALBUMS_JSON, 'w') as f:
            json.dump(data, f, indent=2)
        return True
    except Exception as e:
        logger.error(f"Failed to save albums.json: {e}")
        return False

def delete_image(album_name: str, image_id: str) -> bool:
    """Delete an image from an album."""
    try:
        # Load album data
        albums_data = load_albums_json()
        album = next((a for a in albums_data['albums'] if a['id'] == album_name), None)
        if not album:
            logger.error(f"Album not found: {album_name}")
            return False

        # Find image in album
        target_image = next((img for img in album['images'] if img['id'] == image_id), None)
        if not target_image:
            logger.error(f"Image not found in album: {image_id}")
            return False

        album_dir = ALBUMS_DIR / album_name

        # Delete image files for all sizes
        for size_name in target_image['sizes']:
            size_info = target_image['sizes'][size_name]
            webp_path = album_dir / size_info['webp']
            if webp_path.exists():
                webp_path.unlink()
                logger.info(f"Deleted {webp_path}")

        # Update cover image if needed
        if album['coverImage']['webp'] == target_image['sizes']['grid']['webp']:
            remaining_images = [img for img in album['images'] if img['id'] != image_id]
            if remaining_images:
                album['coverImage'] = remaining_images[0]['sizes']['grid']
            else:
                album['coverImage'] = {}

        # Remove image from album data
        album['images'] = [img for img in album['images'] if img['id'] != image_id]
        
        # Save updated album data
        if save_albums_json(albums_data):
            logger.info(f"Successfully deleted image {image_id} from album {album_name}")
            return True
        return False

    except Exception as e:
        logger.error(f"Failed to delete image: {e}")
        return False

def delete_images(album_name: str, image_ids: List[str]) -> bool:
    """Delete multiple images from an album."""
    success = True
    for image_id in image_ids:
        if not delete_image(album_name, image_id):
            success = False
    return success

def interactive_delete(album_name: str) -> bool:
    """Interactive mode for deleting images."""
    try:
        # Load album data
        albums_data = load_albums_json()
        album = next((a for a in albums_data['albums'] if a['id'] == album_name), None)
        if not album:
            logger.error(f"Album not found: {album_name}")
            return False

        # Display available images
        print("\nAvailable images:")
        for i, img in enumerate(album['images']):
            print(f"{i+1}. {img['id']}")

        # Get user selection
        try:
            selections = input("\nEnter image numbers to delete (comma-separated): ").split(',')
            indices = [int(s.strip()) - 1 for s in selections]
            
            # Validate selections
            if any(i < 0 or i >= len(album['images']) for i in indices):
                logger.error("Invalid selection")
                return False
            
            # Get image IDs and delete
            image_ids = [album['images'][i]['id'] for i in indices]
            return delete_images(album_name, image_ids)
            
        except ValueError:
            logger.error("Invalid input")
            return False

    except Exception as e:
        logger.error(f"Interactive deletion failed: {e}")
        return False

def main():
    parser = argparse.ArgumentParser(description='Delete images from an album')
    parser.add_argument('--album', help='Album name')
    parser.add_argument('--image', help='Image ID to delete')
    parser.add_argument('--interactive', action='store_true', help='Interactive mode')
    
    args = parser.parse_args()
    
    if args.interactive:
        if not args.album:
            parser.error("--album is required with --interactive")
        return interactive_delete(args.album)
    
    if not args.album or not args.image:
        parser.error("Both --album and --image are required")
    
    return delete_image(args.album, args.image)

if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO, format='%(levelname)s - %(message)s')
    import sys
    sys.exit(0 if main() else 1)
