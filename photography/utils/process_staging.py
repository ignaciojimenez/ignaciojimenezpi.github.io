#!/usr/bin/env python3
"""
Script to process albums staged in the photography/staging directory.
This is designed to be run by GitHub Actions when new content is pushed to staging.
"""

import os
import json
import shutil
import logging
from pathlib import Path
from typing import Dict, Optional

# Add current directory to path to allow imports
import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from album_manager import AlbumManager
from config import BASE_DIR

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

STAGING_DIR = BASE_DIR / 'staging'

from datetime import datetime

def load_metadata(metadata_path: Path) -> Optional[Dict]:
    """Load and validate metadata.json."""
    try:
        with open(metadata_path, 'r') as f:
            data = json.load(f)
            
        # Basic validation
        required_fields = ['title', 'date']
        for field in required_fields:
            if field not in data:
                logger.error(f"Missing required field '{field}' in {metadata_path}")
                return None

        # Normalize date if needed
        # iOS Shortcuts might send "19 Nov 2025 at 00:09"
        if 'date' in data:
            try:
                # Try parsing common formats
                date_str = data['date']
                # If it's already YYYY-MM-DD, this might fail or just work if we use strptime correctly
                # But let's handle the specific format mentioned first
                if ' at ' in date_str:
                    # Format: "19 Nov 2025 at 00:09"
                    dt = datetime.strptime(date_str, "%d %b %Y at %H:%M")
                    data['date'] = dt.strftime("%Y-%m-%d")
                    logger.info(f"Normalized date from '{date_str}' to '{data['date']}'")
            except ValueError:
                # If parsing fails, leave it as is and let downstream validation handle it
                # or try other formats if needed
                pass
                
        return data
    except Exception as e:
        logger.error(f"Failed to load metadata from {metadata_path}: {e}")
        return None

def process_staging_album(album_dir: Path) -> bool:
    """Process a single album directory in staging."""
    logger.info(f"Processing staged album: {album_dir.name}")
    
    # Check for metadata.json
    metadata_path = album_dir / 'metadata.json'
    if not metadata_path.exists():
        logger.info(f"No metadata.json found in {album_dir}. Skipping (waiting for upload completion).")
        return True  # Return True to avoid failing the action
        
    metadata = load_metadata(metadata_path)
    if not metadata:
        return False
        
    # Initialize manager
    manager = AlbumManager()
    
    # Check if album already exists (update vs create)
    # For now, we assume new albums or appending images to existing ones if ID matches
    album_id = album_dir.name
    
    # Validate album_id for security (prevent path traversal)
    import re
    if not re.match(r'^[a-zA-Z0-9-_]+$', album_id):
        logger.error(f"Invalid album ID '{album_id}'. Must contain only alphanumeric characters, dashes, and underscores.")
        return False

    existing_album = manager.get_album(album_id)
    
    success = False
    
    # Pre-process files: Rename extensionless files
    # iOS Shortcuts often upload files without extensions. We use Pillow to detect the format.
    from PIL import Image
    import pillow_heif
    pillow_heif.register_heif_opener()
    
    for file_path in album_dir.iterdir():
        if file_path.is_file() and file_path.name != 'metadata.json' and not file_path.name.startswith('.'):
            # Debug: Check file header
            try:
                with open(file_path, 'rb') as f:
                    header = f.read(20)
                    logger.info(f"File {file_path.name} header: {header!r}")
            except Exception as e:
                logger.warning(f"Could not read header for {file_path.name}: {e}")

            # Check if file has no extension
            if not file_path.suffix:
                try:
                    with Image.open(file_path) as img:
                        fmt = img.format.lower() if img.format else 'jpg'
                        # Normalize jpeg to jpg and heif to heic
                        if fmt == 'jpeg':
                            fmt = 'jpg'
                        elif fmt == 'heif':
                            fmt = 'heic'
                        
                        new_path = file_path.with_suffix(f'.{fmt}')
                        file_path.rename(new_path)
                        logger.info(f"Renamed extensionless file {file_path.name} to {new_path.name}")
                except Exception as e:
                    logger.warning(f"Could not determine format for {file_path.name}: {e}")

    # Get all image files
    # iOS Shortcuts might upload files without extensions or with various extensions
    # We'll treat any file that isn't metadata.json or hidden as an image
    image_files = [
        f for f in album_dir.iterdir()
        if f.is_file()
        and f.name != 'metadata.json'
        and not f.name.startswith('.')
    ]

    if not image_files:
        logger.info(f"No images found in {album_dir}. Skipping (waiting for upload completion).")
        return True  # Return True to avoid failing the action

    # Resolve cover image from filename or numeric index
    cover_image = metadata.get('cover_image')
    if not cover_image and metadata.get('cover_index') is not None:
        try:
            idx = int(metadata['cover_index']) - 1  # 1-based to 0-based
            sorted_images = sorted(image_files)
            if 0 <= idx < len(sorted_images):
                cover_image = sorted_images[idx].stem
                logger.info(f"Resolved cover_index {metadata['cover_index']} to {cover_image}")
            else:
                logger.warning(f"cover_index {metadata['cover_index']} out of range (1-{len(sorted_images)})")
        except (ValueError, IndexError) as e:
            logger.warning(f"Invalid cover_index: {e}")

    if existing_album:
        logger.info(f"Album {album_id} exists, adding images...")
        # Add images to existing album
        # We pass the list of paths as strings
        image_paths = [str(p) for p in image_files]
        success = manager.add_images(album_id, image_paths)
    else:
        logger.info(f"Creating new album {album_id}...")
        # Create new album
        success = manager.create_album(
            album_name=album_id,
            title=metadata['title'],
            date=metadata['date'],
            description=metadata.get('description', ''),
            image_dir=str(album_dir),
            cover_image=cover_image,
            favorite=metadata.get('favorite', False)
        )
        
    if success:
        logger.info(f"Successfully processed {album_dir.name}")
        # Clean up staging directory
        try:
            shutil.rmtree(album_dir)
            logger.info(f"Removed staged directory {album_dir}")
        except Exception as e:
            logger.error(f"Failed to remove staged directory {album_dir}: {e}")
            # Don't fail the whole process if cleanup fails, but it's annoying
            
    return success

def main():
    """Main entry point."""
    if not STAGING_DIR.exists():
        logger.info(f"Staging directory {STAGING_DIR} does not exist. Nothing to do.")
        return
        
    # Look for directories in staging
    # Ignore hidden files/dirs
    staged_items = [
        item for item in STAGING_DIR.iterdir() 
        if item.is_dir() and not item.name.startswith('.')
    ]
    
    if not staged_items:
        logger.info("No staged albums found.")
        return
        
    success_count = 0
    for album_dir in staged_items:
        if process_staging_album(album_dir):
            success_count += 1
            
    logger.info(f"Processed {success_count}/{len(staged_items)} staged albums.")
    
    if success_count < len(staged_items):
        sys.exit(1)

if __name__ == '__main__':
    main()
