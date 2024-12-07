#!/usr/bin/env python3

import os
import sys
import json
import shutil
import logging
import argparse
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime

from config import BASE_DIR, ALBUMS_DIR, ALBUMS_JSON
from validation import (
    validate_album_data,
    validate_album_structure,
    validate_image_paths,
    ValidationError
)
from image_processor import ImageProcessor

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

def create_album_directory(album_id: str) -> Path:
    """Create album directory and copy template."""
    album_dir = ALBUMS_DIR / album_id
    try:
        # Create album directory
        album_dir.mkdir(parents=True, exist_ok=True)
        
        # Create images directory
        (album_dir / 'images').mkdir(exist_ok=True)
        
        # Copy and customize template.html
        template_path = ALBUMS_DIR / "template.html"
        index_path = album_dir / "index.html"
        
        if not template_path.exists():
            raise FileNotFoundError(f"Template file not found: {template_path}")
            
        shutil.copy2(template_path, index_path)
        logger.info(f"Created album directory and index.html: {album_dir}")
        
        return album_dir
    except Exception as e:
        logger.error(f"Failed to create album directory: {e}")
        raise

def update_albums_json(album_data: Dict) -> None:
    """Update albums.json with new album data."""
    try:
        if ALBUMS_JSON.exists():
            with open(ALBUMS_JSON, 'r') as f:
                data = json.load(f)
        else:
            data = {"albums": []}
            
        # Check for duplicate album ID
        if any(album['id'] == album_data['id'] for album in data['albums']):
            raise ValidationError(f"Album with ID {album_data['id']} already exists")
            
        data['albums'].append(album_data)
        
        # Create backup
        if ALBUMS_JSON.exists():
            backup_path = ALBUMS_JSON.with_suffix('.json.bak')
            shutil.copy2(ALBUMS_JSON, backup_path)
            logger.info(f"Created backup of albums.json: {backup_path}")
        
        # Write new data
        with open(ALBUMS_JSON, 'w') as f:
            json.dump(data, f, indent=2)
            
        logger.info("Successfully updated albums.json")
    except Exception as e:
        logger.error(f"Error updating albums.json: {e}")
        raise

def process_images(source_dir: str, album_dir: Path) -> List[str]:
    """Process and optimize images."""
    source_path = Path(source_dir)
    if not source_path.exists():
        raise FileNotFoundError(f"Source directory does not exist: {source_path}")
    
    # Copy original images
    images_dir = album_dir / 'images'
    image_files = []
    
    for img_path in source_path.glob('*'):
        if img_path.suffix.lower() in {'.jpg', '.jpeg', '.png'}:
            dest_path = images_dir / img_path.name
            shutil.copy2(img_path, dest_path)
            image_files.append(img_path.name)
            logger.info(f"Copied original image: {img_path.name}")
    
    if not image_files:
        raise ValidationError("No valid images found in source directory")
    
    # Process images and create responsive versions
    processor = ImageProcessor(album_dir)
    try:
        metadata = processor.process_album()
        logger.info("Successfully processed images and created responsive versions")
    except Exception as e:
        logger.error(f"Error processing images: {e}")
        raise
    
    return image_files

def create_album(
    album_name: str,
    title: str,
    date: str,
    image_dir: str,
    description: Optional[str] = "",
    cover_image: Optional[str] = None
) -> bool:
    """Create a new album with optimized images."""
    try:
        # Validate input directory exists
        if not os.path.isdir(image_dir):
            raise ValidationError(f"Image directory does not exist: {image_dir}")
            
        # Validate and create album data
        album_data = validate_album_data(
            album_id=album_name,
            title=title,
            date=date,
            description=description
        )
        
        logger.info(f"Creating album: {title} ({album_name})")
        
        # Create album directory
        album_dir = create_album_directory(album_name)
        
        # Process images
        image_files = process_images(image_dir, album_dir)
        
        if not image_files:
            raise ValidationError(f"No valid images found in directory: {image_dir}")
        
        # Format image paths relative to album
        album_data['images'] = [f"{album_name}/images/{img}" for img in image_files]
        
        # Set cover image
        if cover_image:
            if cover_image not in image_files:
                raise ValidationError(f"Cover image not found in album: {cover_image}")
            album_data['coverImage'] = f"{album_name}/images/{cover_image}"
        else:
            album_data['coverImage'] = f"{album_name}/images/{image_files[0]}"
        
        # Update albums.json
        update_albums_json(album_data)
        
        logger.info(f"Successfully created album: {album_name}")
        return True
        
    except ValidationError as e:
        logger.error(f"Validation error: {e}")
        return False
    except Exception as e:
        logger.error(f"Unexpected error while creating album: {e}")
        return False

def add_images_to_album(album_name: str, image_dir: str) -> bool:
    """Add images to an existing album."""
    try:
        album_dir = ALBUMS_DIR / album_name
        if not album_dir.exists():
            raise ValidationError(f"Album not found: {album_name}")
        
        # Validate album structure
        validate_album_structure(album_dir)
        
        # Process new images
        new_images = process_images(image_dir, album_dir)
        
        # Update albums.json
        with open(ALBUMS_JSON, 'r') as f:
            data = json.load(f)
        
        for album in data['albums']:
            if album['id'] == album_name:
                album['images'].extend([f"{album_name}/images/{img}" for img in new_images])
                break
        
        with open(ALBUMS_JSON, 'w') as f:
            json.dump(data, f, indent=2)
        
        logger.info(f"Successfully added {len(new_images)} images to album {album_name}")
        return True
        
    except Exception as e:
        logger.error(f"Failed to add images: {e}")
        return False

def delete_album(album_name: str) -> bool:
    """Delete an album and all its associated files and metadata."""
    success = False
    try:
        # Remove from albums.json first
        if ALBUMS_JSON.exists():
            try:
                with open(ALBUMS_JSON, 'r') as f:
                    data = json.load(f)
                
                # Find and remove the album from the albums array
                if 'albums' in data:
                    original_length = len(data['albums'])
                    data['albums'] = [album for album in data['albums'] if album.get('id') != album_name]
                    
                    if len(data['albums']) < original_length:
                        with open(ALBUMS_JSON, 'w') as f:
                            json.dump(data, f, indent=2)
                        logger.info(f"Removed '{album_name}' from albums.json")
                        success = True
            except Exception as e:
                logger.error(f"Failed to update albums.json: {e}")
                return False

        # Try to delete album directory if it exists
        album_dir = ALBUMS_DIR / album_name
        if album_dir.exists():
            shutil.rmtree(album_dir)
            logger.info(f"Deleted album directory: {album_dir}")
            success = True

        # Try to delete album HTML file if it exists
        album_html = ALBUMS_DIR / f"{album_name}.html"
        if album_html.exists():
            album_html.unlink()
            logger.info(f"Deleted album HTML file: {album_html}")
            success = True

        if not success:
            logger.warning(f"Album '{album_name}' not found in filesystem or metadata")
            
        return success

    except Exception as e:
        logger.error(f"Failed to delete album: {e}")
        return False

if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description='Create, modify, or delete photo albums',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    # Create a new album
    %(prog)s new-album --title "My New Album" --description "Photos from my trip" --date 2023-12-25 --images ./photos

    # Add images to existing album
    %(prog)s existing-album --add --images ./more-photos

    # Delete an album
    %(prog)s existing-album --delete
    """
    )
    
    parser.add_argument('album_name', help='URL-friendly name for the album (e.g., "summer-2023")')
    parser.add_argument('--title', help='Display title for the album')
    parser.add_argument('--description', help='Album description')
    parser.add_argument('--date', help='Album date (YYYY-MM-DD)')
    parser.add_argument('--images', help='Directory containing images to process')
    parser.add_argument('--cover', help='Cover image filename (must be in images directory)')
    parser.add_argument('--add', action='store_true', help='Add images to existing album')
    parser.add_argument('--delete', action='store_true', help='Delete the specified album')
    
    args = parser.parse_args()
    
    if args.delete:
        if delete_album(args.album_name):
            print(f"Successfully deleted album: {args.album_name}")
        else:
            print("Failed to delete album")
            sys.exit(1)
    elif args.add:
        if not args.images:
            parser.error("--images is required when adding to an album")
        
        if add_images_to_album(args.album_name, args.images):
            print(f"Successfully added images to album: {args.album_name}")
        else:
            print("Failed to add images to album")
            sys.exit(1)
    else:
        if not all([args.title, args.date, args.images]):
            parser.error("--title, --date, and --images are required when creating a new album")
        
        if create_album(
            album_name=args.album_name,
            title=args.title,
            date=args.date,
            image_dir=args.images,
            description=args.description,
            cover_image=args.cover
        ):
            print(f"Successfully created album: {args.album_name}")
            print(f"View it at: /photography/albums/{args.album_name}")
        else:
            print("Failed to create album")
            sys.exit(1)
