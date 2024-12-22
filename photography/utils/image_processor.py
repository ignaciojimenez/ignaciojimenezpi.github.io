"""Image processing utilities for the photography portfolio."""

from pathlib import Path
from typing import Dict, List, Optional, Tuple
from PIL import Image, ImageOps
import logging
from concurrent.futures import ThreadPoolExecutor
import json
from config import RESPONSIVE_SIZES, JPEG_QUALITY, WEBP_QUALITY
from validation import validate_image_file, validate_metadata

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

class ImageProcessor:
    """Handles all image processing operations."""
    
    def __init__(self, album_dir: Path, albums_json: Optional[Path] = None):
        self.album_dir = Path(album_dir)
        self.images_dir = self.album_dir / 'images'
        self.responsive_dir = self.album_dir / 'responsive'
        self.albums_json = albums_json or self.album_dir.parent / 'albums.json'
        self.metadata: Dict = {}
    
    def process_single_image(self, img_path: Path) -> Dict:
        """Process a single image and generate all required versions."""
        validate_image_file(img_path)
        
        try:
            with Image.open(img_path) as img:
                # Auto-orient image based on EXIF
                img = ImageOps.exif_transpose(img)
                orig_width, orig_height = img.size
                
                # Create responsive versions
                responsive_versions = self._create_responsive_versions(img, img_path)
                
                # Create WebP version of original
                webp_path = self._create_webp_version(img, img_path)
                
                return {
                    "original": {
                        "path": str(img_path.relative_to(self.album_dir)),
                        "width": orig_width,
                        "height": orig_height,
                        "webp": str(webp_path.relative_to(self.album_dir)) if webp_path else None
                    },
                    "responsive": responsive_versions
                }
        
        except Exception as e:
            logger.error(f"Failed to process image {img_path}: {e}")
            raise

    def process_album(self, save_metadata: bool = False) -> Dict:
        """Process all images in the album."""
        if not self.images_dir.exists():
            raise FileNotFoundError(f"Images directory not found: {self.images_dir}")
        
        # Create output directories
        self.responsive_dir.mkdir(exist_ok=True)
        for size_name in RESPONSIVE_SIZES:
            (self.responsive_dir / size_name).mkdir(exist_ok=True)
        
        # Get all images
        image_files = [p for p in self.images_dir.glob('*') 
                      if p.suffix.lower() in {'.jpg', '.jpeg', '.png'}]
        
        if not image_files:
            logger.warning(f"No images found in {self.images_dir}")
            return {}
        
        # Process images in parallel
        with ThreadPoolExecutor() as executor:
            future_to_path = {
                executor.submit(self.process_single_image, path): path
                for path in image_files
            }
            
            for future in future_to_path:
                path = future_to_path[future]
                try:
                    result = future.result()
                    if result:
                        self.metadata[path.name] = result
                except Exception as e:
                    logger.error(f"Failed to process {path}: {e}")
        
        # Save metadata only if requested
        if save_metadata:
            self._save_metadata()
            
        return self.metadata
    
    def _create_responsive_versions(self, img: Image.Image, source_path: Path) -> Dict:
        """Create all responsive versions of an image."""
        versions = {}
        
        for size_name, size_config in RESPONSIVE_SIZES.items():
            target_width = size_config['width']
            
            # If original is smaller, use original dimensions
            if img.width <= target_width:
                versions[size_name] = {
                    "path": str(source_path.relative_to(self.album_dir)),
                    "width": img.width,
                    "height": img.height,
                    "webp": str(source_path.with_suffix('.webp').relative_to(self.album_dir))
                }
                continue
            
            # Calculate height maintaining aspect ratio
            aspect_ratio = img.height / img.width
            target_height = int(target_width * aspect_ratio)
            
            size_dir = self.responsive_dir / size_name
            size_dir.mkdir(parents=True, exist_ok=True)
            
            # Create JPEG version
            jpeg_path = size_dir / source_path.name
            resized = img.resize((target_width, target_height), Image.Resampling.LANCZOS)
            resized.save(jpeg_path, 'JPEG', quality=size_config['quality'])
            
            # Create WebP version
            webp_path = jpeg_path.with_suffix('.webp')
            resized.save(webp_path, 'WEBP', quality=WEBP_QUALITY)
            
            versions[size_name] = {
                "path": str(jpeg_path.relative_to(self.album_dir)),
                "width": target_width,
                "height": target_height,
                "webp": str(webp_path.relative_to(self.album_dir))
            }
        
        return versions
    
    def _create_webp_version(self, img: Image.Image, source_path: Path) -> Optional[Path]:
        """Create WebP version of an image."""
        try:
            webp_path = source_path.with_suffix('.webp')
            img.save(webp_path, 'WEBP', quality=WEBP_QUALITY)
            return webp_path
        except Exception as e:
            logger.error(f"Error creating WebP version for {source_path}: {e}")
            return None
    
    def _save_metadata(self) -> None:
        """Save metadata to file."""
        try:
            # Load current albums data
            with open(self.albums_json) as f:
                albums_data = json.load(f)
            
            # Find the current album
            album_id = self.album_dir.name
            album = next((a for a in albums_data['albums'] if a['id'] == album_id), None)
            if not album:
                raise ValueError(f"Album not found: {album_id}")
            
            # Initialize metadata if needed
            if 'metadata' not in album:
                album['metadata'] = {}
            
            # Update metadata
            for img_name, metadata in self.metadata.items():
                album['metadata'][img_name] = metadata
                
                # Add to images list if not already present
                img_rel_path = f"{album_id}/images/{img_name}"
                if img_rel_path not in album['images']:
                    album['images'].append(img_rel_path)
                
                # Set as cover if none exists
                if not album.get('cover'):
                    album['cover'] = img_rel_path
            
            # Save updated albums data
            with open(self.albums_json, 'w') as f:
                json.dump(albums_data, f, indent=2)
            
            logger.info(f"Successfully saved metadata for {len(self.metadata)} images")
        
        except Exception as e:
            logger.error(f"Error saving metadata: {e}")
            raise
