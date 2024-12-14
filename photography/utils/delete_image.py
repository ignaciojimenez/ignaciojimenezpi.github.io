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
        for size_dir in responsive_dir.iterdir():
            if size_dir.is_dir():
                img_path = size_dir / image_name
                if img_path.exists():
                    img_path.unlink()
                webp_path = img_path.with_suffix('.webp')
                if webp_path.exists():
                    webp_path.unlink()
        logger.info(f"Deleted responsive versions for: {image_name}")

def update_albums_json(album_id: str, image_name: str) -> None:
    """Update albums.json to remove the image entry."""
    try:
        # Load current data
        albums_data = load_albums()
        
        # Find target album
        album = next((a for a in albums_data['albums'] if a['id'] == album_id), None)
        if not album:
            raise ValueError(f"Album not found: {album_id}")
        
        # Remove image from images list
        image_path = f"{album_id}/images/{image_name}"
        if image_path in album['images']:
            album['images'].remove(image_path)
        
        # Remove metadata for this image
        if 'metadata' in album and image_name in album['metadata']:
            del album['metadata'][image_name]
        
        # Update cover image if needed
        if album.get('cover') == image_path:
            album['cover'] = album['images'][0] if album['images'] else ''
        
        # Save changes
        save_albums(albums_data)
        logger.info(f"Updated albums.json: removed {image_name}")
        
    except Exception as e:
        logger.error(f"Failed to update albums.json: {e}")
        raise

def delete_image(album_id: str, image_path: str) -> None:
    """Delete a specific image from an album."""
    try:
        # Extract image name from path
        image_name = Path(image_path).name
        
        # Delete image files
        delete_image_files(album_id, image_name)
        
        # Update albums.json
        update_albums_json(album_id, image_name)
        
        logger.info(f"Successfully deleted image: {image_name}")
        
    except Exception as e:
        logger.error(f"Failed to delete image: {e}")
        raise

def select_album() -> Optional[str]:
    """Interactively select an album."""
    try:
        # Load albums data
        albums_data = load_albums()
        
        print("\nAvailable albums:")
        albums = [(a['id'], a['title']) for a in albums_data['albums']]
        for i, (id, title) in enumerate(albums, 1):
            print(f"{i}. {title} ({id})")
        
        while True:
            choice = input("\nEnter the number of the album (or 'q' to quit): ")
            if choice.lower() == 'q':
                return None
            
            try:
                idx = int(choice) - 1
                if 0 <= idx < len(albums):
                    return albums[idx][0]
                else:
                    print("Invalid selection. Please try again.")
            except ValueError:
                print("Please enter a valid number.")
    
    except Exception as e:
        logger.error(f"Failed to select album: {e}")
        return None

def select_images(album_id: str) -> Optional[List[str]]:
    """Interactively select images to delete from an album."""
    try:
        # Load albums data
        albums_data = load_albums()
        
        # Find the album
        album = next((a for a in albums_data['albums'] if a['id'] == album_id), None)
        if not album:
            raise ValueError(f"Album not found: {album_id}")
        
        if not album['images']:
            print("No images found in this album.")
            return None
        
        print("\nImages in album:")
        for i, img_path in enumerate(album['images'], 1):
            img_name = Path(img_path).name
            cover_marker = " (cover)" if img_path == album['cover'] else ""
            print(f"{i}. {img_name}{cover_marker}")
        
        selected_indices = set()
        while True:
            choice = input("\nEnter image number to delete (or 'done'/'q' when finished): ")
            if choice.lower() in ['q', 'quit']:
                return None
            if choice.lower() == 'done' and selected_indices:
                break
            
            try:
                idx = int(choice) - 1
                if 0 <= idx < len(album['images']):
                    if idx in selected_indices:
                        print("Image already selected.")
                    else:
                        selected_indices.add(idx)
                        print(f"Selected: {Path(album['images'][idx]).name}")
                else:
                    print("Invalid selection. Please try again.")
            except ValueError:
                if choice.lower() not in ['done', 'q', 'quit']:
                    print("Please enter a valid number.")
        
        return [album['images'][i] for i in sorted(selected_indices)]
    
    except Exception as e:
        logger.error(f"Failed to select images: {e}")
        return None

def delete_images(album_id: str, image_paths: List[str]) -> bool:
    """Delete multiple images from an album."""
    success = True
    for image_path in image_paths:
        try:
            delete_image(album_id, image_path)
        except Exception as e:
            logger.error(f"Failed to delete image: {e}")
            success = False
    return success

def main():
    parser = argparse.ArgumentParser(description='Delete images from an album')
    parser.add_argument('--album', help='ID of the album')
    parser.add_argument('--image', help='Name of the image file to delete')
    parser.add_argument('--interactive', action='store_true', help='Use interactive mode to select images')
    
    args = parser.parse_args()
    
    if args.interactive:
        # Interactive mode
        album_id = args.album or select_album()
        if not album_id:
            print("No album selected. Exiting.")
            sys.exit(0)
        
        image_paths = select_images(album_id)
        if not image_paths:
            print("No images selected. Exiting.")
            sys.exit(0)
        
        if delete_images(album_id, image_paths):
            print(f"Successfully deleted {len(image_paths)} image(s)")
        else:
            print("Some images failed to delete")
            sys.exit(1)
    
    else:
        # Direct mode (original functionality)
        if not args.album or not args.image:
            parser.error("Both --album and --image are required in non-interactive mode")
        
        image_path = f"{args.album}/images/{args.image}"
        try:
            delete_image(args.album, image_path)
        except Exception as e:
            logger.error(f"Failed to delete image: {e}")
            sys.exit(1)
        print(f"Successfully deleted image: {args.image}")

if __name__ == '__main__':
    main()
