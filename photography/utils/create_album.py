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
import tempfile

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

def update_albums_json(
    album_name: str,
    title: str,
    description: str,
    date: str,
    cover_image: Optional[str] = None,
    images: Optional[List[str]] = None,
    metadata: Optional[Dict] = None
) -> bool:
    """Update the albums.json file with album information."""
    try:
        # Load current albums data
        with open(ALBUMS_JSON, 'r') as f:
            data = json.load(f)
        
        # Check if album already exists
        existing_album = next((a for a in data['albums'] if a['id'] == album_name), None)
        
        if existing_album:
            # Update existing album
            existing_album.update({
                'title': title,
                'description': description,
                'date': date,
                'coverImage': cover_image or existing_album.get('coverImage', ''),
                'images': images if images is not None else existing_album.get('images', []),
                'metadata': metadata if metadata is not None else existing_album.get('metadata', {})
            })
        else:
            # Add new album
            data['albums'].append({
                'id': album_name,
                'title': title,
                'description': description,
                'date': date,
                'coverImage': cover_image or '',
                'images': images or [],
                'metadata': metadata or {}
            })
        
        # Sort albums by date (newest first)
        data['albums'].sort(key=lambda x: x['date'], reverse=True)
        
        # Save updated data
        with open(ALBUMS_JSON, 'w') as f:
            json.dump(data, f, indent=2)
        
        return True
    except Exception as e:
        logger.error(f"Failed to update albums.json: {e}")
        return False

def update_album_metadata(album_name: str, image_path: str) -> bool:
    """Update album metadata when adding new images."""
    try:
        # Load current albums data
        with open(ALBUMS_JSON, 'r') as f:
            data = json.load(f)
        
        # Find target album
        album = next((a for a in data['albums'] if a['id'] == album_name), None)
        if not album:
            raise ValidationError(f"Album not found: {album_name}")
        
        # Initialize metadata if it doesn't exist
        if 'metadata' not in album:
            album['metadata'] = {'images': []}
        
        # Add new image metadata
        image_name = os.path.basename(image_path)
        if image_name not in [img['name'] for img in album['metadata']['images']]:
            album['metadata']['images'].append({
                'name': image_name,
                'date': datetime.now().strftime('%Y-%m-%d')
            })
        
        # Save updated data
        with open(ALBUMS_JSON, 'w') as f:
            json.dump(data, f, indent=2)
        
        return True
    except Exception as e:
        logger.error(f"Failed to update metadata: {e}")
        return False

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
    temp_dir = None
    try:
        # Validate input directory exists
        if not os.path.isdir(image_dir):
            raise ValidationError(f"Image directory does not exist: {image_dir}")
            
        # Create temporary directory for processing
        temp_dir = Path(tempfile.mkdtemp())
        temp_album_dir = temp_dir / album_name
        temp_album_dir.mkdir(parents=True)
        (temp_album_dir / 'images').mkdir()  # Create images directory
        (temp_album_dir / 'responsive').mkdir()  # Create responsive directory
        
        # Copy images from source directory to temp directory
        source_dir = Path(image_dir)
        temp_images_dir = temp_album_dir / 'images'
        for img_path in source_dir.glob('*'):
            if img_path.suffix.lower() in {'.jpg', '.jpeg', '.png'}:
                shutil.copy2(img_path, temp_images_dir / img_path.name)
                logger.info(f"Copied original image: {img_path.name}")
        
        # Validate and create album data
        album_data = validate_album_data(
            album_id=album_name,
            title=title,
            date=date,
            description=description,
            metadata={}  # Initialize empty metadata
        )
        
        logger.info(f"Creating album: {title} ({album_name})")
        
        # First update albums.json with initial data
        success = update_albums_json(
            album_name=album_name,
            title=title,
            description=description,
            date=date,
            cover_image=""  # Will update this after processing images
        )
        
        if not success:
            raise ValidationError("Failed to update albums.json")
        
        # Process images in temporary directory
        processor = ImageProcessor(temp_album_dir, albums_json=ALBUMS_JSON)
        metadata = processor.process_album(save_metadata=False)  # Don't save metadata directly
        
        if not metadata:
            raise ValidationError(f"No valid images found in directory: {image_dir}")
        
        # Get list of processed images
        image_files = list(metadata.keys())
        
        if not image_files:
            raise ValidationError(f"No valid images found in directory: {image_dir}")
        
        # Update albums.json with cover image and metadata
        relative_image_paths = [f"{album_name}/images/{img}" for img in image_files]
        if cover_image:
            cover_basename = os.path.basename(cover_image)
            if cover_basename in image_files:
                cover_path = f"{album_name}/images/{cover_basename}"
            else:
                cover_path = relative_image_paths[0]
        else:
            cover_path = relative_image_paths[0]
        
        success = update_albums_json(
            album_name=album_name,
            title=title,
            description=description,
            date=date,
            cover_image=cover_path,
            images=relative_image_paths,
            metadata=metadata
        )
        
        if not success:
            raise ValidationError("Failed to update albums.json with cover image")
        
        # If everything is successful, move the temporary directory to final location
        final_album_dir = ALBUMS_DIR / album_name
        if final_album_dir.exists():
            shutil.rmtree(final_album_dir)
        shutil.copytree(temp_album_dir, final_album_dir)
        
        # Create index.html from template
        template_path = ALBUMS_DIR / "template.html"
        index_path = final_album_dir / "index.html"
        if template_path.exists():
            shutil.copy2(template_path, index_path)
        
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
    """Add images to an existing album.
    
    Args:
        album_name: Name of the album to add images to
        image_path: Path to an image file or directory containing images
    """
    temp_dir = None
    try:
        album_dir = ALBUMS_DIR / album_name
        if not album_dir.exists():
            raise ValidationError(f"Album not found: {album_name}")
        
        # Validate album structure
        validate_album_structure(album_dir)
        
        # Create temporary directory for processing
        temp_dir = Path(tempfile.mkdtemp())
        temp_album_dir = temp_dir / album_name
        temp_album_dir.mkdir(parents=True)
        (temp_album_dir / 'images').mkdir()
        (temp_album_dir / 'responsive').mkdir()
        
        # Copy existing images to temp directory
        for img_path in (album_dir / 'images').glob('*'):
            if img_path.suffix.lower() in {'.jpg', '.jpeg', '.png'}:
                shutil.copy2(img_path, temp_album_dir / 'images' / img_path.name)
        
        # Add new images to temp directory
        source_path = Path(image_path)
        if source_path.is_file():
            if source_path.suffix.lower() in {'.jpg', '.jpeg', '.png'}:
                shutil.copy2(source_path, temp_album_dir / 'images' / source_path.name)
                logger.info(f"Copied new image: {source_path.name}")
        else:
            for img_path in source_path.glob('*'):
                if img_path.suffix.lower() in {'.jpg', '.jpeg', '.png'}:
                    shutil.copy2(img_path, temp_album_dir / 'images' / img_path.name)
                    logger.info(f"Copied new image: {img_path.name}")
        
        # Process all images
        processor = ImageProcessor(temp_album_dir, albums_json=ALBUMS_JSON)
        metadata = processor.process_album(save_metadata=False)
        
        if not metadata:
            raise ValidationError("No valid images found")
        
        # Get current album data
        with open(ALBUMS_JSON, 'r') as f:
            data = json.load(f)
        album_data = next((a for a in data['albums'] if a['id'] == album_name), None)
        if not album_data:
            raise ValidationError(f"Album not found in albums.json: {album_name}")
        
        # Update album data with new images and metadata
        relative_image_paths = [f"{album_name}/images/{img}" for img in metadata.keys()]
        success = update_albums_json(
            album_name=album_name,
            title=album_data['title'],
            description=album_data.get('description', ''),
            date=album_data['date'],
            cover_image=album_data.get('coverImage', relative_image_paths[0]),
            images=relative_image_paths,
            metadata=metadata
        )
        
        if not success:
            raise ValidationError("Failed to update albums.json")
        
        # If everything is successful, replace the album directory
        if album_dir.exists():
            shutil.rmtree(album_dir)
        shutil.copytree(temp_album_dir, album_dir)
        
        logger.info(f"Successfully added images to album {album_name}")
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

def change_album_cover(album_name: str, cover_image: Optional[str] = None) -> bool:
    """Change the cover image of an existing album.
    
    Args:
        album_name: Name of the album to modify
        cover_image: Optional path to new cover image. If not provided, will show selection menu
    """
    try:
        album_dir = ALBUMS_DIR / album_name
        if not album_dir.exists():
            raise ValidationError(f"Album not found: {album_name}")
        
        # Load current album data
        with open(ALBUMS_JSON, 'r') as f:
            data = json.load(f)
        
        target_album = None
        for album in data['albums']:
            if album['id'] == album_name:
                target_album = album
                break
        
        if not target_album:
            raise ValidationError(f"Album {album_name} not found in albums.json")
        
        # If cover image provided, validate and use it
        if cover_image:
            if Path(cover_image).is_file():
                # Add image to album if it's not already there
                temp_result = add_images_to_album(album_name, cover_image)
                if not temp_result:
                    return False
                cover_path = f"{album_name}/images/{Path(cover_image).name}"
            else:
                # Assume it's a path relative to the album
                cover_path = cover_image
                if not (album_dir / 'images' / Path(cover_image).name).exists():
                    raise ValidationError(f"Cover image not found: {cover_image}")
        else:
            # Show selection menu
            print("\nCurrent album images:")
            images = target_album['images']
            for i, img in enumerate(images, 1):
                print(f"{i}. {Path(img).name}")
            
            while True:
                try:
                    choice = input("\nEnter the number of the image to use as cover (or 'q' to quit): ")
                    if choice.lower() == 'q':
                        return False
                    
                    idx = int(choice) - 1
                    if 0 <= idx < len(images):
                        cover_path = images[idx]
                        break
                    else:
                        print("Invalid selection. Please try again.")
                except ValueError:
                    print("Please enter a valid number.")
        
        # Update album cover
        target_album['coverImage'] = cover_path
        
        # Save changes
        with open(ALBUMS_JSON, 'w') as f:
            json.dump(data, f, indent=2)
        
        logger.info(f"Successfully updated cover image for album {album_name}")
        return True
        
    except Exception as e:
        logger.error(f"Failed to change cover image: {e}")
        return False

def change_album_metadata(album_name: str, new_title: Optional[str] = None, new_date: Optional[str] = None) -> bool:
    """Change the title and/or date of an existing album.
    
    Args:
        album_name: Name of the album to modify
        new_title: Optional new title for the album
        new_date: Optional new date for the album (YYYY-MM-DD)
    """
    try:
        # Load current albums data
        with open(ALBUMS_JSON, 'r') as f:
            data = json.load(f)
        
        # Find target album
        target_album = next((a for a in data['albums'] if a['id'] == album_name), None)
        if not target_album:
            raise ValidationError(f"Album not found: {album_name}")
        
        # Update metadata
        if new_title:
            target_album['title'] = new_title
            logger.info(f"Updated title to: {new_title}")
            
        if new_date:
            # Validate date format
            try:
                datetime.strptime(new_date, '%Y-%m-%d')
                target_album['date'] = new_date
                logger.info(f"Updated date to: {new_date}")
            except ValueError:
                raise ValidationError("Date must be in YYYY-MM-DD format")
        
        # Save changes
        with open(ALBUMS_JSON, 'w') as f:
            json.dump(data, f, indent=2)
        
        logger.info(f"Successfully updated metadata for album {album_name}")
        return True
        
    except Exception as e:
        logger.error(f"Failed to update album metadata: {e}")
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

    # Change album cover image (interactive)
    %(prog)s existing-album --change-cover

    # Change album cover image (direct)
    %(prog)s existing-album --change-cover --cover path/to/image.jpg

    # Change album title
    %(prog)s existing-album --new-title "Updated Title"

    # Change album date
    %(prog)s existing-album --new-date 2023-12-31

    # Change both title and date
    %(prog)s existing-album --new-title "Updated Title" --new-date 2023-12-31

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
    parser.add_argument('--change-cover', action='store_true', help='Change album cover image')
    parser.add_argument('--new-title', help='New title for the album')
    parser.add_argument('--new-date', help='New date for the album in YYYY-MM-DD format')
    
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
    elif args.new_title or args.new_date:
        if change_album_metadata(args.album_name, args.new_title, args.new_date):
            print(f"Successfully updated metadata for album: {args.album_name}")
        else:
            print("Failed to update album metadata")
            sys.exit(1)
    elif args.change_cover:
        if change_album_cover(args.album_name, args.cover):
            print(f"Successfully changed cover image for album: {args.album_name}")
        else:
            print("Failed to change cover image")
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
