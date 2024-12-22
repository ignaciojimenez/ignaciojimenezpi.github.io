"""Validation utilities for the photography portfolio."""

import json
from pathlib import Path
from typing import Dict, List, Optional, Union
from datetime import datetime
import jsonschema
from PIL import Image
import logging
from config import METADATA_SCHEMA, ALBUM_SCHEMA, ALLOWED_EXTENSIONS, ALBUMS_JSON

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

class ValidationError(Exception):
    """Custom exception for validation errors."""
    pass

def validate_image_file(path: Path) -> None:
    """Validate that a file is a valid image."""
    if not path.exists():
        raise ValidationError(f"Image file does not exist: {path}")
    
    if path.suffix.lower() not in ALLOWED_EXTENSIONS:
        raise ValidationError(f"Invalid image format: {path.suffix}")
    
    try:
        with Image.open(path) as img:
            img.verify()
    except Exception as e:
        raise ValidationError(f"Invalid image file {path}: {e}")

def validate_metadata(metadata: Dict) -> None:
    """Validate album metadata against schema."""
    try:
        jsonschema.validate(instance=metadata, schema=METADATA_SCHEMA)
    except jsonschema.exceptions.ValidationError as e:
        raise ValidationError(f"Invalid metadata format: {e}")

def validate_album_data(
    album_id: str,
    title: str,
    date: str,
    description: Optional[str] = "",
    cover_image: Optional[str] = None,
    images: Optional[List[str]] = None,
    metadata: Optional[Dict] = None
) -> Dict:
    """Validate and format album data."""
    try:
        # Validate date format
        datetime.strptime(date, '%Y-%m-%d')
        
        album_data = {
            "id": album_id,
            "title": title,
            "description": description or "",
            "date": date,
            "coverImage": cover_image or "",
            "images": images or [],
            "metadata": metadata or {}
        }
        
        jsonschema.validate(instance=album_data, schema=ALBUM_SCHEMA)
        return album_data
        
    except ValueError as e:
        raise ValidationError(f"Invalid date format. Use YYYY-MM-DD: {e}")
    except jsonschema.exceptions.ValidationError as e:
        raise ValidationError(f"Invalid album data format: {e}")

def validate_album_structure(album_dir: Path) -> None:
    """Validate album directory structure."""
    if not album_dir.exists():
        raise ValidationError(f"Album directory does not exist: {album_dir}")
    
    images_dir = album_dir / 'images'
    if not images_dir.exists():
        raise ValidationError(f"Images directory does not exist: {images_dir}")
    
    # Check root albums.json instead of per-album metadata
    metadata_file = ALBUMS_JSON
    if not metadata_file.exists():
        raise ValidationError(f"Root metadata file does not exist: {metadata_file}")
    
    try:
        with open(metadata_file) as f:
            data = json.load(f)
            # Find the album in the metadata
            album_id = album_dir.name
            album = next((a for a in data['albums'] if a['id'] == album_id), None)
            if not album:
                raise ValidationError(f"Album {album_id} not found in metadata")
    except json.JSONDecodeError as e:
        raise ValidationError(f"Invalid metadata JSON: {e}")

def validate_path_string(path: str) -> str:
    """Validate and normalize a path string."""
    try:
        # Convert to Path and back to string to normalize
        normalized = str(Path(path))
        # Remove leading 'albums/' if present
        if normalized.startswith('albums/'):
            normalized = normalized[7:]
        return normalized
    except Exception as e:
        raise ValidationError(f"Invalid path string: {e}")

def validate_image_paths(paths: List[str], base_dir: Path) -> List[str]:
    """Validate a list of image paths."""
    validated = []
    for path in paths:
        normalized = validate_path_string(path)
        full_path = base_dir / normalized
        validate_image_file(full_path)
        validated.append(normalized)
    return validated
