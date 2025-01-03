#!/usr/bin/env python3

import os
import sys
import json
import shutil
import logging
import tempfile
import argparse
import re
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional
from config import ALBUMS_JSON, METADATA_SCHEMA, ALBUM_SCHEMA
from validation import validate_album_data, validate_image_file, validate_album_structure
from image_processor import ImageProcessor

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

def create_album_directory(album_name: str, temp_dir: Optional[Path] = None) -> Path:
    """Create album directory structure."""
    base_dir = temp_dir if temp_dir else ALBUMS_DIR
    album_dir = base_dir / album_name
    
    # Create main directories
    album_dir.mkdir(parents=True, exist_ok=True)
    images_dir = album_dir / 'images'
    images_dir.mkdir(exist_ok=True)
    
    # Create size-specific directories
    (images_dir / 'grid').mkdir(exist_ok=True)
    (images_dir / 'small').mkdir(exist_ok=True)
    (images_dir / 'medium').mkdir(exist_ok=True)
    (images_dir / 'large').mkdir(exist_ok=True)
    
    # Copy template.html if it exists
    template_path = ALBUMS_DIR / 'template.html'
    if template_path.exists():
        shutil.copy2(template_path, album_dir / 'index.html')
        logger.info(f"Created album directory and index.html: {album_dir}")
    
    return album_dir

def update_albums_json(
    album_name: str,
    title: str,
    description: str,
    date: str,
    cover_image: Optional[Dict] = None,
    images: Optional[List[Dict]] = None,
    temp_operation: bool = False
) -> bool:
    """Update the albums.json file with album information."""
    try:
        # Load current albums data
        with open(ALBUMS_JSON, 'r') as f:
            data = json.load(f)
        
        # Check if album already exists
        existing_album = next((a for a in data['albums'] if a['id'] == album_name), None)
        
        album_data = {
            'id': album_name,
            'title': title,
            'description': description,
            'date': date,
            'coverImage': cover_image or {},
            'images': images or []
        }
        
        if existing_album:
            # Update existing album
            existing_album.update(album_data)
        else:
            # Add new album
            data['albums'].append(album_data)
        
        # Sort albums by date (newest first)
        data['albums'].sort(key=lambda x: x['date'], reverse=True)
        
        # If this is a temporary operation, don't save to disk
        if not temp_operation:
            # Backup current file
            backup_path = Path(str(ALBUMS_JSON) + '.bak')
            shutil.copy2(ALBUMS_JSON, backup_path)
            
            # Save updated data
            with open(ALBUMS_JSON, 'w') as f:
                json.dump(data, f, indent=2)
        
        return True
        
    except Exception as e:
        logger.error(f"Failed to update albums.json: {e}")
        return False

def process_images(source_dir: str, album_dir: Path) -> List[Dict]:
    """Process and optimize images."""
    source_path = Path(source_dir)
    if not source_path.exists():
        raise FileNotFoundError(f"Source directory does not exist: {source_path}")
    
    # Get list of image files without copying them
    image_files = []
    if source_path.is_file():
        if source_path.suffix.lower() in {'.jpg', '.jpeg', '.png', '.webp'}:
            image_files.append(source_path)
    else:
        image_files.extend([
            p for p in source_path.glob('*')
            if p.suffix.lower() in {'.jpg', '.jpeg', '.png', '.webp'}
        ])
    
    if not image_files:
        raise ValueError("No valid images found in source directory")
    
    # Process images
    processor = ImageProcessor(album_dir)
    metadata = processor.process_album(image_files)
    
    # Convert metadata to list format and ensure no extensions in IDs
    images = [
        {
            'id': Path(img_id).stem.split('.')[0],  # Remove all extensions
            'sizes': img_data['sizes']
        }
        for img_id, img_data in metadata.items()
    ]
    
    return images

def create_album(
    album_name: str,
    title: str,
    date: str,
    image_dir: str,
    description: Optional[str] = "",
    cover_image: Optional[str] = None
) -> bool:
    """Create a new album with optimized images."""
    temp_dir = None
    try:
        # Create temporary directory for processing
        temp_dir = Path(tempfile.mkdtemp())
        temp_album_dir = create_album_directory(album_name, temp_dir)
        
        # Process images in temporary directory
        images = process_images(image_dir, temp_album_dir)
        
        if not images:
            raise ValueError(f"No valid images found in directory: {image_dir}")
        
        # Handle cover image
        if cover_image:
            cover_path = Path(cover_image)
            if cover_path.is_file():
                cover_id = cover_path.stem.split('.')[0]  # Remove all extensions
                # Find the processed cover image in the metadata
                cover_img = next((img for img in images if img['id'] == cover_id), None)
                if cover_img:
                    cover_data = cover_img['sizes']['grid']
                else:
                    logger.warning(f"Specified cover image {cover_id} not found in processed images, using first image")
                    cover_data = images[0]['sizes']['grid']
            else:
                logger.warning("Cover image file not found, using first image")
                cover_data = images[0]['sizes']['grid']
        else:
            cover_data = images[0]['sizes']['grid']
        
        # Validate album data
        album_data = validate_album_data(
            album_id=album_name,
            title=title,
            date=date,
            description=description,
            cover_image=cover_data,
            images=images
        )
        
        # First update albums.json with initial data (temporary)
        if not update_albums_json(
            album_name=album_name,
            title=title,
            description=description,
            date=date,
            cover_image=cover_data,
            images=images,
            temp_operation=True
        ):
            raise ValueError("Failed to validate album data")
        
        # If everything is successful, move the temporary directory to final location
        final_album_dir = ALBUMS_DIR / album_name
        if final_album_dir.exists():
            shutil.rmtree(final_album_dir)
        shutil.copytree(temp_album_dir, final_album_dir)
        
        # Finally, update albums.json
        if not update_albums_json(
            album_name=album_name,
            title=title,
            description=description,
            date=date,
            cover_image=cover_data,
            images=images
        ):
            raise ValueError("Failed to update albums.json")
        
        logger.info(f"Successfully created album: {album_name}")
        return True
        
    except Exception as e:
        logger.error(f"Failed to create album: {e}")
        
        # Clean up the album entry from albums.json if it was created
        try:
            with open(ALBUMS_JSON, 'r') as f:
                data = json.load(f)
            data['albums'] = [a for a in data['albums'] if a['id'] != album_name]
            with open(ALBUMS_JSON, 'w') as f:
                json.dump(data, f, indent=2)
        except Exception as cleanup_error:
            logger.error(f"Error during cleanup: {cleanup_error}")
        
        # Clean up the album directory if it exists
        try:
            album_dir = ALBUMS_DIR / album_name
            if album_dir.exists():
                shutil.rmtree(album_dir)
        except Exception as cleanup_error:
            logger.error(f"Error cleaning up album directory: {cleanup_error}")
        
        return False
        
    finally:
        # Clean up temporary directory
        if temp_dir and temp_dir.exists():
            try:
                shutil.rmtree(temp_dir)
            except Exception as cleanup_error:
                logger.error(f"Error cleaning up temporary directory: {cleanup_error}")

def add_images_to_album(album_name: str, image_path: str) -> bool:
    """Add images to an existing album."""
    temp_dir = None
    try:
        album_dir = ALBUMS_DIR / album_name
        if not album_dir.exists():
            raise FileNotFoundError(f"Album not found: {album_name}")
        
        # Create temporary directory for processing
        temp_dir = Path(tempfile.mkdtemp())
        temp_album_dir = temp_dir / album_name
        
        # Copy existing album to temp directory
        shutil.copytree(album_dir, temp_album_dir)
        
        # Process new images
        new_images = process_images(image_path, temp_album_dir)
        
        # Load current album data
        with open(ALBUMS_JSON) as f:
            data = json.load(f)
        
        album = next((a for a in data['albums'] if a['id'] == album_name), None)
        if not album:
            raise ValueError(f"Album not found in metadata: {album_name}")
        
        # Add new images to existing ones
        existing_ids = {img['id'] for img in album['images']}
        album['images'].extend([img for img in new_images if img['id'] not in existing_ids])
        
        # Validate the updated album
        if not update_albums_json(
            album_name=album_name,
            title=album['title'],
            description=album.get('description', ''),
            date=album['date'],
            cover_image=album['coverImage'],
            images=album['images'],
            temp_operation=True
        ):
            raise ValueError("Failed to validate updated album data")
        
        # If everything is successful, replace the existing album
        shutil.rmtree(album_dir)
        shutil.copytree(temp_album_dir, album_dir)
        
        # Finally, update albums.json
        if not update_albums_json(
            album_name=album_name,
            title=album['title'],
            description=album.get('description', ''),
            date=album['date'],
            cover_image=album['coverImage'],
            images=album['images']
        ):
            raise ValueError("Failed to update albums.json")
        
        logger.info(f"Successfully added images to album: {album_name}")
        return True
        
    except Exception as e:
        logger.error(f"Failed to add images: {e}")
        return False
        
    finally:
        # Clean up temporary directory
        if temp_dir and temp_dir.exists():
            try:
                shutil.rmtree(temp_dir)
            except Exception as cleanup_error:
                logger.error(f"Error cleaning up temporary directory: {cleanup_error}")

def delete_album(album_name: str) -> bool:
    """Delete an album and all its contents."""
    try:
        # Load albums data
        albums_data = load_albums_json()
        
        # Check if album exists
        if not any(a['id'] == album_name for a in albums_data['albums']):
            logger.error(f"Album not found: {album_name}")
            return False
        
        # Remove album directory
        album_dir = ALBUMS_DIR / album_name
        if album_dir.exists():
            shutil.rmtree(album_dir)
            logger.info(f"Deleted album directory: {album_dir}")
        
        # Update albums.json
        albums_data['albums'] = [a for a in albums_data['albums'] if a['id'] != album_name]
        if save_albums_json(albums_data):
            logger.info(f"Successfully deleted album: {album_name}")
            return True
        return False
        
    except Exception as e:
        logger.error(f"Failed to delete album: {e}")
        return False

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

def main():
    parser = argparse.ArgumentParser(description='Create or modify a photo album')
    parser.add_argument('album', help='Album name')
    parser.add_argument('--title', help='Album title')
    parser.add_argument('--date', help='Album date (YYYY-MM-DD)')
    parser.add_argument('--description', help='Album description')
    parser.add_argument('--images', help='Path to images directory or file')
    parser.add_argument('--cover', help='Path to cover image')
    parser.add_argument('--add', action='store_true', help='Add images to existing album')
    parser.add_argument('--change-cover', action='store_true', help='Change album cover image')
    parser.add_argument('--new-title', help='Update album title')
    parser.add_argument('--new-date', help='Update album date')
    parser.add_argument('--delete', action='store_true', help='Delete the album')
    
    args = parser.parse_args()
    
    # Handle album deletion
    if args.delete:
        return delete_album(args.album)
    
    # Load existing album data if needed
    albums_data = load_albums_json()
    existing_album = next((a for a in albums_data['albums'] if a['id'] == args.album), None)
    
    # Handle metadata changes
    if args.new_title or args.new_date or args.change_cover:
        if not existing_album:
            logger.error(f"Album {args.album} not found")
            return False
            
        if args.new_title:
            existing_album['title'] = args.new_title
            
        if args.new_date:
            if not re.match(r'^\d{4}-\d{2}-\d{2}$', args.new_date):
                logger.error("Date must be in YYYY-MM-DD format")
                return False
            existing_album['date'] = args.new_date
            
        if args.change_cover:
            album_dir = ALBUMS_DIR / args.album
            if args.cover:
                cover_path = Path(args.cover)
                if not cover_path.is_file():
                    logger.error(f"Cover image not found: {cover_path}")
                    return False
                    
                # Process cover image if it's not already in the album
                if not any(img['id'] == cover_path.name for img in existing_album['images']):
                    processor = ImageProcessor(album_dir)
                    cover_metadata = processor.process_single_image(cover_path)
                    existing_album['images'].append(cover_metadata)
                    
                # Update cover image
                cover_id = cover_path.name
                cover_img = next((img for img in existing_album['images'] if img['id'] == cover_id), None)
                if cover_img:
                    existing_album['coverImage'] = cover_img['sizes']['grid']
            else:
                # Interactive selection
                print("\nAvailable images:")
                for i, img in enumerate(existing_album['images']):
                    print(f"{i+1}. {img['id']}")
                try:
                    choice = int(input("\nSelect cover image number: ")) - 1
                    if 0 <= choice < len(existing_album['images']):
                        existing_album['coverImage'] = existing_album['images'][choice]['sizes']['grid']
                    else:
                        logger.error("Invalid selection")
                        return False
                except ValueError:
                    logger.error("Invalid input")
                    return False
        
        # Save changes
        save_albums_json(albums_data)
        logger.info(f"Successfully updated album {args.album}")
        return True
    
    # Handle album creation or image addition
    if not args.title and not args.date and not args.images and not args.add:
        parser.print_help()
        return False
    
    if args.add:
        if not existing_album:
            logger.error(f"Album {args.album} not found")
            return False
        if not args.images:
            logger.error("--images is required when adding to existing album")
            return False
            
        # Add images to existing album
        album_dir = ALBUMS_DIR / args.album
        new_images = process_images(args.images, album_dir)
        existing_album['images'].extend(new_images)
        save_albums_json(albums_data)
        logger.info(f"Successfully added images to album {args.album}")
        return True
    
    # Create new album
    if not all([args.title, args.date, args.images]):
        logger.error("--title, --date, and --images are required for new albums")
        return False
        
    return create_album(
        album_name=args.album,
        title=args.title,
        date=args.date,
        image_dir=args.images,
        description=args.description or "",
        cover_image=args.cover
    )

if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO, format='%(levelname)s - %(message)s')
    sys.exit(0 if main() else 1)
