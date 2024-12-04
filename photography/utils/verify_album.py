#!/usr/bin/env python3

import sys
import json
import logging
from pathlib import Path
from typing import Dict, List, Set
import re
from datetime import datetime
from .config import RESPONSIVE_SIZES

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

class AlbumVerificationError(Exception):
    """Custom exception for album verification errors."""
    pass

def verify_directory_structure(album_dir: Path) -> None:
    """Verify that all required directories exist."""
    required_dirs = ['images', 'responsive']
    for dir_name in required_dirs:
        dir_path = album_dir / dir_name
        if not dir_path.is_dir():
            raise AlbumVerificationError(f"Required directory missing: {dir_path}")
    logger.info("✓ Directory structure verified")

def verify_required_files(album_dir: Path) -> None:
    """Verify that all required files exist."""
    required_files = ['index.html', 'metadata.json']
    for file_name in required_files:
        file_path = album_dir / file_name
        if not file_path.is_file():
            raise AlbumVerificationError(f"Required file missing: {file_path}")
    logger.info("✓ Required files verified")

def verify_metadata_json(album_dir: Path) -> Dict:
    """Verify metadata.json structure and content."""
    metadata_path = album_dir / 'metadata.json'
    try:
        with open(metadata_path) as f:
            metadata = json.load(f)
            
        required_fields = {'original', 'responsive'}
        if not all(field in metadata for field in required_fields):
            raise AlbumVerificationError("Metadata missing required fields")
            
        # Verify each image entry
        for img_data in metadata.values():
            if 'original' not in img_data:
                raise AlbumVerificationError("Image missing original data")
            if 'responsive' not in img_data:
                raise AlbumVerificationError("Image missing responsive data")
                
        logger.info("✓ metadata.json verified")
        return metadata
    except json.JSONDecodeError:
        raise AlbumVerificationError("Invalid metadata.json format")

def verify_responsive_images(album_dir: Path, metadata: Dict) -> None:
    """Verify that all responsive images exist and match metadata."""
    for img_name, img_data in metadata.items():
        # Check original image
        orig_path = album_dir / img_data['original']['path']
        if not orig_path.is_file():
            raise AlbumVerificationError(f"Original image missing: {orig_path}")
            
        # Check WebP version of original
        if img_data['original'].get('webp'):
            webp_path = album_dir / img_data['original']['webp']
            if not webp_path.is_file():
                raise AlbumVerificationError(f"WebP version missing: {webp_path}")
                
        # Check responsive versions
        for size_name, size_data in img_data['responsive'].items():
            if size_name not in RESPONSIVE_SIZES:
                raise AlbumVerificationError(f"Unknown responsive size: {size_name}")
                
            jpeg_path = album_dir / size_data['path']
            if not jpeg_path.is_file():
                raise AlbumVerificationError(f"Responsive image missing: {jpeg_path}")
                
            webp_path = album_dir / size_data['webp']
            if not webp_path.is_file():
                raise AlbumVerificationError(f"Responsive WebP missing: {webp_path}")
                
    logger.info("✓ Responsive images verified")

def verify_albums_json(albums_json_path: Path, album_name: str) -> None:
    """Verify that the album is properly registered in albums.json."""
    try:
        with open(albums_json_path) as f:
            albums_data = json.load(f)
            
        if 'albums' not in albums_data:
            raise AlbumVerificationError("Invalid albums.json structure")
            
        album_entry = None
        for album in albums_data['albums']:
            if album.get('id') == album_name:
                album_entry = album
                break
                
        if not album_entry:
            raise AlbumVerificationError(f"Album {album_name} not found in albums.json")
            
        # Verify required fields
        required_fields = {'id', 'title', 'date', 'coverImage'}
        if not all(field in album_entry for field in required_fields):
            raise AlbumVerificationError("Album entry missing required fields")
            
        # Verify date format
        try:
            datetime.strptime(album_entry['date'], '%Y-%m-%d')
        except ValueError:
            raise AlbumVerificationError("Invalid date format in albums.json")
            
        logger.info("✓ albums.json verified")
    except json.JSONDecodeError:
        raise AlbumVerificationError("Invalid albums.json format")

def verify_album(album_name: str) -> bool:
    """
    Verify the complete album structure and contents.
    Returns True if verification passes, raises AlbumVerificationError otherwise.
    """
    try:
        logger.info(f"Verifying album: {album_name}")
        base_dir = Path("photography/albums")
        album_dir = base_dir / album_name
        
        if not album_dir.exists():
            raise AlbumVerificationError(f"Album directory not found: {album_dir}")
        
        # Run all verifications
        verify_directory_structure(album_dir)
        verify_required_files(album_dir)
        metadata = verify_metadata_json(album_dir)
        verify_responsive_images(album_dir, metadata)
        verify_albums_json(base_dir / "albums.json", album_name)
        
        logger.info(f"✓ Album {album_name} verification completed successfully")
        return True
        
    except AlbumVerificationError as e:
        logger.error(f"Album verification failed: {str(e)}")
        return False
    except Exception as e:
        logger.error(f"Unexpected error during verification: {str(e)}")
        return False

if __name__ == '__main__':
    if len(sys.argv) != 2:
        print("Usage: verify_album.py <album_name>")
        sys.exit(1)
        
    album_name = sys.argv[1]
    if not verify_album(album_name):
        sys.exit(1)
