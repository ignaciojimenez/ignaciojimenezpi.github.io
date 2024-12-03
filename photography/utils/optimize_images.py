#!/usr/bin/env python3

import os
import sys
from PIL import Image
from pathlib import Path
import logging
from concurrent.futures import ThreadPoolExecutor
from typing import List, Tuple
import json

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('image_optimization.log')
    ]
)
logger = logging.getLogger(__name__)

# Image sizes for responsive images
SIZES = {
    'thumbnail': 400,
    'small': 800,
    'medium': 1200,
    'large': 1600,
    'xlarge': 2000
}

def create_webp_version(img_path: Path, output_dir: Path, size_name: str = None) -> Path:
    """Create WebP version of an image"""
    if size_name:
        webp_path = output_dir / size_name / img_path.name.replace('.jpg', '.webp').replace('.jpeg', '.webp')
    else:
        webp_path = output_dir / img_path.name.replace('.jpg', '.webp').replace('.jpeg', '.webp')
    
    webp_path.parent.mkdir(parents=True, exist_ok=True)
    
    try:
        img = Image.open(img_path)
        img.save(str(webp_path), 'WEBP', quality=85)
        logger.info(f"Created WebP version: {webp_path}")
        return webp_path
    except Exception as e:
        logger.error(f"Error creating WebP version for {img_path}: {e}")
        return None

def create_responsive_images(img_path: Path, output_dir: Path) -> List[Tuple[str, Path, Path]]:
    """Create responsive image versions and their WebP counterparts"""
    results = []
    try:
        img = Image.open(img_path)
        orig_width, orig_height = img.size
        aspect_ratio = orig_height / orig_width

        for size_name, target_width in SIZES.items():
            size_dir = output_dir / size_name
            size_dir.mkdir(parents=True, exist_ok=True)
            
            # Skip if image is smaller than target size
            if orig_width <= target_width:
                continue

            target_height = int(target_width * aspect_ratio)
            resized_img = img.resize((target_width, target_height), Image.Resampling.LANCZOS)
            
            # Save JPEG version
            jpeg_path = size_dir / img_path.name
            resized_img.save(str(jpeg_path), 'JPEG', quality=85)
            logger.info(f"Created {size_name} version: {jpeg_path}")
            
            # Save WebP version
            webp_path = create_webp_version(img_path, output_dir, size_name)
            
            results.append((size_name, jpeg_path, webp_path))
            
    except Exception as e:
        logger.error(f"Error creating responsive images for {img_path}: {e}")
    
    return results

def get_relative_path(path: Path, base_dir: Path) -> str:
    """Convert absolute path to relative path from base_dir"""
    try:
        # Get the path relative to the album directory, not the photography directory
        rel_path = path.relative_to(base_dir)
        # Don't include 'albums' in the path since it's already in the base URL
        parts = rel_path.parts
        if parts[0] == 'albums':
            return str(Path(*parts[1:]))
        return str(rel_path)
    except ValueError:
        return str(path)

def process_image(img_path: Path, output_dir: Path, base_dir: Path) -> dict:
    """Process a single image and return its metadata"""
    try:
        img = Image.open(img_path)
        orig_width, orig_height = img.size
        
        # Create responsive versions
        responsive_versions = create_responsive_images(img_path, output_dir)
        
        # Create original WebP version
        webp_path = create_webp_version(img_path, output_dir.parent / 'images')
        
        metadata = {
            "original": {
                "path": get_relative_path(img_path, base_dir),
                "width": orig_width,
                "height": orig_height,
                "webp": get_relative_path(webp_path, base_dir) if webp_path else None
            },
            "responsive": {}
        }
        
        for size_name, jpeg_path, webp_path in responsive_versions:
            resized_img = Image.open(jpeg_path)
            metadata["responsive"][size_name] = {
                "path": get_relative_path(jpeg_path, base_dir),
                "width": resized_img.size[0],
                "height": resized_img.size[1],
                "webp": get_relative_path(webp_path, base_dir) if webp_path else None
            }
        
        return metadata
    except Exception as e:
        logger.error(f"Error processing {img_path}: {e}")
        return None

def optimize_album_images(album_dir: Path) -> dict:
    """Optimize all images in an album directory"""
    # If the path ends with 'images', use it directly
    if album_dir.name == 'images':
        images_dir = album_dir
        album_dir = album_dir.parent
    else:
        images_dir = album_dir / 'images'
        
    if not images_dir.exists():
        logger.error(f"Images directory not found: {images_dir}")
        return {}
    
    # Create output directory for responsive images
    responsive_dir = album_dir / 'responsive'
    responsive_dir.mkdir(exist_ok=True)
    
    # Get all images
    image_files = list(images_dir.glob('*.jp*g'))
    if not image_files:
        logger.error(f"No JPEG images found in {images_dir}")
        return {}
    
    # Get base directory for relative paths (photography directory)
    base_dir = album_dir
    while base_dir.name != 'photography':
        base_dir = base_dir.parent
        if base_dir == base_dir.parent:  # reached root
            base_dir = album_dir
            break
    
    # Process images in parallel
    metadata = {}
    with ThreadPoolExecutor() as executor:
        future_to_path = {
            executor.submit(process_image, img_path, responsive_dir, base_dir): img_path
            for img_path in image_files
        }
        
        for future in future_to_path:
            img_path = future_to_path[future]
            try:
                result = future.result()
                if result:
                    metadata[img_path.name] = result
            except Exception as e:
                logger.error(f"Error processing {img_path}: {e}")
    
    # Save metadata
    metadata_path = album_dir / 'metadata.json'
    try:
        with open(metadata_path, 'w') as f:
            json.dump(metadata, f, indent=2)
        logger.info(f"Saved metadata to {metadata_path}")
    except Exception as e:
        logger.error(f"Error saving metadata: {e}")
    
    return metadata

if __name__ == '__main__':
    if len(sys.argv) != 2:
        print("Usage: optimize_images.py <album_directory>")
        sys.exit(1)
    
    album_dir = Path(sys.argv[1])
    if not album_dir.exists():
        print(f"Album directory not found: {album_dir}")
        sys.exit(1)
    
    optimize_album_images(album_dir)
