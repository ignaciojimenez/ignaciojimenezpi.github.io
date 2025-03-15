"""Configuration settings for the photography portfolio."""

from typing import Dict, TypedDict, Optional
from pathlib import Path

# Base paths
BASE_DIR = Path(__file__).parent.parent
ALBUMS_DIR = BASE_DIR / 'albums'
ALBUMS_JSON = ALBUMS_DIR / 'albums.json'

# Image processing settings
class ImageSize(TypedDict):
    width: int
    height: Optional[int]
    quality: int

RESPONSIVE_SIZES: Dict[str, ImageSize] = {
    'grid': {'width': 400, 'height': None, 'quality': 85},
    'small': {'width': 800, 'height': None, 'quality': 85},
    'medium': {'width': 1200, 'height': None, 'quality': 85},
    'large': {'width': 1600, 'height': None, 'quality': 85}
}

# Image format settings
WEBP_QUALITY = 85
ALLOWED_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.webp'}  # Allow input images in various formats

# Directory structure
ALBUM_DIRS = {
    'images': 'images',
    'grid': 'images/grid',
    'small': 'images/small',
    'medium': 'images/medium',
    'large': 'images/large'
}

# Metadata schema
METADATA_SCHEMA = {
    "type": "object",
    "properties": {
        "sizes": {
            "type": "object",
            "required": ["grid", "small", "medium", "large"],
            "properties": {
                "grid": {
                    "type": "object",
                    "required": ["webp", "width", "height"],
                    "properties": {
                        "webp": {"type": "string"},
                        "width": {"type": "integer"},
                        "height": {"type": "integer"}
                    }
                },
                "small": {
                    "type": "object",
                    "required": ["webp", "width", "height"],
                    "properties": {
                        "webp": {"type": "string"},
                        "width": {"type": "integer"},
                        "height": {"type": "integer"}
                    }
                },
                "medium": {
                    "type": "object",
                    "required": ["webp", "width", "height"],
                    "properties": {
                        "webp": {"type": "string"},
                        "width": {"type": "integer"},
                        "height": {"type": "integer"}
                    }
                },
                "large": {
                    "type": "object",
                    "required": ["webp", "width", "height"],
                    "properties": {
                        "webp": {"type": "string"},
                        "width": {"type": "integer"},
                        "height": {"type": "integer"}
                    }
                }
            }
        }
    }
}

# Album schema
ALBUM_SCHEMA = {
    "type": "object",
    "required": ["id", "title", "date", "coverImage", "images"],
    "properties": {
        "id": {"type": "string"},
        "title": {"type": "string"},
        "description": {"type": "string", "default": ""},
        "date": {"type": "string", "pattern": "^\\d{4}-\\d{2}-\\d{2}$"},
        "favorite": {"type": "boolean", "default": False},
        "coverImage": {
            "type": "object",
            "required": ["width", "height", "webp"],
            "properties": {
                "width": {"type": "integer"},
                "height": {"type": "integer"},
                "webp": {"type": "string"}
            }
        },
        "images": {
            "type": "array",
            "items": {
                "type": "object",
                "required": ["id", "sizes"],
                "properties": {
                    "id": {"type": "string"},
                    "sizes": {
                        "type": "object",
                        "required": ["grid", "small", "medium", "large"],
                        "properties": {
                            "grid": {
                                "type": "object",
                                "required": ["webp", "width", "height"],
                                "properties": {
                                    "webp": {"type": "string"},
                                    "width": {"type": "integer"},
                                    "height": {"type": "integer"}
                                }
                            },
                            "small": {
                                "type": "object",
                                "required": ["webp", "width", "height"],
                                "properties": {
                                    "webp": {"type": "string"},
                                    "width": {"type": "integer"},
                                    "height": {"type": "integer"}
                                }
                            },
                            "medium": {
                                "type": "object",
                                "required": ["webp", "width", "height"],
                                "properties": {
                                    "webp": {"type": "string"},
                                    "width": {"type": "integer"},
                                    "height": {"type": "integer"}
                                }
                            },
                            "large": {
                                "type": "object",
                                "required": ["webp", "width", "height"],
                                "properties": {
                                    "webp": {"type": "string"},
                                    "width": {"type": "integer"},
                                    "height": {"type": "integer"}
                                }
                            }
                        }
                    }
                }
            }
        }
    }
}
