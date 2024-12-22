"""Configuration settings for the photography portfolio."""

from typing import Dict, TypedDict
from pathlib import Path

# Base paths
BASE_DIR = Path(__file__).parent.parent
ALBUMS_DIR = BASE_DIR / 'albums'
ALBUMS_JSON = ALBUMS_DIR / 'albums.json'

# Image processing settings
class ImageSize(TypedDict):
    width: int
    height: int
    quality: int

RESPONSIVE_SIZES: Dict[str, ImageSize] = {
    'thumbnail': {'width': 400, 'height': None, 'quality': 85},
    'small': {'width': 800, 'height': None, 'quality': 85},
    'medium': {'width': 1200, 'height': None, 'quality': 85},
    'large': {'width': 1600, 'height': None, 'quality': 85}
}

# Image format settings
JPEG_QUALITY = 85
WEBP_QUALITY = 85
ALLOWED_EXTENSIONS = {'.jpg', '.jpeg', '.png'}

# Directory structure
ALBUM_DIRS = {
    'images': 'images',           # Original images
    'responsive': 'responsive'    # Responsive versions
}

# Metadata schema
METADATA_SCHEMA = {
    "type": "object",
    "properties": {
        "original": {
            "type": "object",
            "required": ["path", "width", "height", "webp"],
            "properties": {
                "path": {"type": "string"},
                "width": {"type": "integer"},
                "height": {"type": "integer"},
                "webp": {"type": ["string", "null"]}
            }
        },
        "responsive": {
            "type": "object",
            "patternProperties": {
                "^(thumbnail|small|medium|large)$": {
                    "type": "object",
                    "required": ["path", "width", "height", "webp"],
                    "properties": {
                        "path": {"type": "string"},
                        "width": {"type": "integer"},
                        "height": {"type": "integer"},
                        "webp": {"type": ["string", "null"]}
                    }
                }
            }
        }
    }
}

# Album schema
ALBUM_SCHEMA = {
    "type": "object",
    "required": ["id", "title", "date", "coverImage", "images", "metadata"],
    "properties": {
        "id": {"type": "string"},
        "title": {"type": "string"},
        "description": {"type": "string", "default": ""},
        "date": {"type": "string", "pattern": "^\\d{4}-\\d{2}-\\d{2}$"},
        "coverImage": {"type": "string"},
        "images": {
            "type": "array",
            "items": {"type": "string"}
        },
        "metadata": {
            "type": "object",
            "patternProperties": {
                ".*": METADATA_SCHEMA
            }
        }
    }
}
