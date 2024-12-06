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
    
    def __init__(self, album_dir: Path):
        self.album_dir = Path(album_dir)
        self.images_dir = self.album_dir / 'images'
        self.responsive_dir = self.album_dir / 'responsive'
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
            logger.error(f"Error processing image {img_path}: {e}")
            return None
    
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
    
    def process_album(self) -> Dict:
        """Process all images in the album."""
        if not self.images_dir.exists():
            raise FileNotFoundError(f"Images directory not found: {self.images_dir}")
        
        # Create output directories
        self.responsive_dir.mkdir(exist_ok=True)
        
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
        
        # Save metadata
        self._save_metadata()
        return self.metadata
    
    def _save_metadata(self) -> None:
        """Save metadata to file."""
        metadata_path = self.album_dir / 'metadata.json'
        validate_metadata(self.metadata)
        
        try:
            with open(metadata_path, 'w') as f:
                json.dump(self.metadata, f, indent=2)
            logger.info(f"Saved metadata to {metadata_path}")
        except Exception as e:
            logger.error(f"Error saving metadata: {e}")
            raise
