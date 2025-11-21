"""Image processing utilities for the photography portfolio."""

from pathlib import Path
from typing import Dict, List, Optional, Tuple
from PIL import Image, ImageOps
import logging
from concurrent.futures import ThreadPoolExecutor
import json
from config import RESPONSIVE_SIZES, WEBP_QUALITY
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
        self.albums_json = albums_json or self.album_dir.parent / 'albums.json'
        self.metadata: Dict = {}
        
        # Create output directories
        for size_name in RESPONSIVE_SIZES:
            (self.images_dir / size_name).mkdir(parents=True, exist_ok=True)
    
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
                
                # Use filename without extension as ID
                return {
                    "id": img_path.stem,  # Just use stem (filename without extension)
                    "sizes": responsive_versions
                }
        
        except Exception as e:
            logger.error(f"Failed to process image {img_path.name}: {e}")
            raise
    
    def process_album(self, image_files: List[Path]) -> Dict:
        """Process all images in the album."""
        if not image_files:
            logger.warning("No images provided for processing")
            return {}
        
        total_images = len(image_files)
        logger.info(f"Starting to process {total_images} images...")
        processed_count = 0
        
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
                        processed_count += 1
                        if processed_count % max(1, total_images // 10) == 0:  # Show progress every 10%
                            logger.info(f"Processed {processed_count}/{total_images} images")
                except Exception as e:
                    logger.error(f"Failed to process {path.name}: {e}")
        
        if processed_count == total_images:
            logger.info("Image processing completed successfully")
        else:
            logger.warning(f"Completed with some failures: {processed_count}/{total_images} images processed")
        
        return self.metadata
    
    def process_directory(self, dir_path: Path) -> List[Dict]:
        """Process all images in a directory.
        
        Args:
            dir_path: Path to directory containing images
            
        Returns:
            List of image metadata dictionaries
        """
        # Get all image files in directory
        image_files = []
        for ext in ['.jpg', '.jpeg', '.png', '.webp', '.heic', '.heif']:
            image_files.extend(dir_path.glob(f'*{ext}'))
            image_files.extend(dir_path.glob(f'*{ext.upper()}'))
        
        if not image_files:
            logger.warning(f"No image files found in {dir_path}")
            return []
        
        # Sort files to ensure consistent order
        image_files = sorted(image_files)
        logger.info(f"Found {len(image_files)} images in {dir_path}")
        
        # Process images in parallel using process_album
        metadata = self.process_album(image_files)
        
        # Convert metadata dict to list in the same order as image_files
        return [metadata[f.name] for f in image_files if f.name in metadata]
    
    def _create_responsive_versions(self, img: Image.Image, source_path: Path) -> Dict:
        """Create responsive versions of an image."""
        versions = {}
        
        try:
            # Get base name without extension
            base_name = source_path.stem.split('.')[0]  # Remove all extensions
            
            # Create versions for each size
            for size_name, size_config in RESPONSIVE_SIZES.items():
                try:
                    # Calculate new dimensions
                    width = size_config['width']
                    orig_width, orig_height = img.size
                    
                    if width:
                        w_percent = width / float(orig_width)
                        height = int(float(orig_height) * float(w_percent))
                        if w_percent < 1:
                            resized = img.resize((width, height), Image.Resampling.LANCZOS)
                        else:
                            resized = img
                            width, height = orig_width, orig_height
                    else:
                        resized = img
                        width, height = orig_width, orig_height
                    
                    # Save WebP version
                    webp_path = self.images_dir / size_name / f"{base_name}.webp"
                    resized.save(str(webp_path), 'WEBP', quality=size_config['quality'])
                    
                    versions[size_name] = {
                        "webp": f"images/{size_name}/{base_name}.webp",
                        "width": width,
                        "height": height
                    }
                    
                except Exception as e:
                    logger.error(f"Failed to create {size_name} version of {source_path.name}: {e}")
                    raise
            
            return versions
            
        except Exception as e:
            logger.error(f"Failed to create responsive versions: {e}")
            raise
    
    def _save_metadata(self) -> None:
        """Save metadata to albums.json."""
        try:
            with open(self.albums_json, 'r') as f:
                data = json.load(f)
            
            # Find the current album
            album_id = self.album_dir.name
            album = next((a for a in data['albums'] if a['id'] == album_id), None)
            
            if album:
                # Update images list with new metadata
                album['images'] = [
                    {
                        "id": img_id,
                        "sizes": metadata["sizes"]
                    }
                    for img_id, metadata in self.metadata.items()
                ]
                
                # Save updated data
                with open(self.albums_json, 'w') as f:
                    json.dump(data, f, indent=2)
                    
            else:
                logger.error(f"Album {album_id} not found in albums.json")
                
        except Exception as e:
            logger.error(f"Failed to save metadata: {e}")
            raise
