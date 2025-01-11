"""Album management utilities for the photography portfolio."""

import os
import json
import shutil
import logging
from pathlib import Path
from typing import Dict, List, Optional, Union
from datetime import datetime

from config import ALBUMS_JSON, METADATA_SCHEMA, ALBUM_SCHEMA, ALBUMS_DIR, BASE_DIR
from validation import validate_album_data, validate_image_file, validate_album_structure
from image_processor import ImageProcessor

logger = logging.getLogger(__name__)

class AlbumManager:
    """Manages album operations including creation, deletion, and updates."""
    
    def __init__(self):
        """Initialize album manager."""
        self.albums_json = ALBUMS_JSON
    
    def create_album(
        self,
        album_name: str,
        title: str,
        date: str,
        image_dir: str,
        description: str = "",
        cover_image: Optional[str] = None
    ) -> bool:
        """Create a new album with the given parameters."""
        try:
            # Create album directory
            album_dir = Path(ALBUMS_JSON).parent / album_name
            if album_dir.exists():
                raise ValueError(f"Album directory already exists: {album_dir}")
            
            # Process images
            image_dir_path = Path(os.path.expanduser(image_dir))
            if not image_dir_path.is_dir():
                raise ValueError(f"Image directory does not exist: {image_dir}")
                
            # Create base album directory
            album_dir.mkdir(parents=True)
            
            logger.info(f"Creating album '{title}' from {image_dir}")
            
            # Copy and rename template.html
            template_path = ALBUMS_DIR / 'template.html'
            if not template_path.exists():
                raise ValueError(f"Template file not found: {template_path}")
            shutil.copy2(template_path, album_dir / 'index.html')
            logger.info(f"Copied template.html to {album_dir / 'index.html'}")
            
            # Process images (this will create all necessary subdirectories)
            processor = ImageProcessor(album_dir)
            images_metadata = processor.process_directory(image_dir_path)
            
            if not images_metadata:
                shutil.rmtree(album_dir)
                raise ValueError(f"No valid images found in {image_dir}")
            
            # Handle cover image
            cover_metadata = None
            if cover_image:
                # Get filename without extension for matching
                cover_id = Path(cover_image).stem
                cover_metadata = next(
                    (img for img in images_metadata if img['id'] == cover_id),
                    None
                )
                if not cover_metadata:
                    raise ValueError(f"Cover image not found in processed images: {cover_image}")
            else:
                # Use first image as cover
                cover_metadata = images_metadata[0]
            
            # Create album metadata
            album_data = validate_album_data(
                album_id=album_name,
                title=title,
                date=date,
                description=description,
                cover_image=cover_metadata['sizes']['grid'],
                images=images_metadata
            )
            
            # Update albums.json
            self._update_albums_json(album_data)
            
            logger.info(f"Successfully created album: {album_name}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to create album: {e}")
            # Clean up if album directory was created
            if 'album_dir' in locals() and album_dir.exists():
                shutil.rmtree(album_dir)
            return False
    
    def delete_album(self, album_id: str) -> bool:
        """Delete an album by its ID."""
        try:
            # Load current albums
            albums_data = self._load_albums_json()
            
            # Find and remove album
            albums = albums_data['albums']
            album = next((a for a in albums if a['id'] == album_id), None)
            if not album:
                raise ValueError(f"Album not found: {album_id}")
            
            # Remove album directory
            album_dir = self.albums_json.parent / album_id
            if album_dir.exists():
                shutil.rmtree(album_dir)
            
            # Update albums.json
            albums_data['albums'] = [a for a in albums if a['id'] != album_id]
            self._save_albums_json(albums_data)
            
            logger.info(f"Successfully deleted album: {album_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to delete album: {e}")
            return False
    
    def add_images(self, album_id: str, image_paths: Union[str, List[str]]) -> bool:
        """Add one or more images to an existing album."""
        try:
            # Convert single path to list
            if isinstance(image_paths, str):
                image_paths = [image_paths]
            
            # Load album data
            albums_data = self._load_albums_json()
            album = next((a for a in albums_data['albums'] if a['id'] == album_id), None)
            if not album:
                raise ValueError(f"Album not found: {album_id}")
            
            album_dir = ALBUMS_DIR / album_id
            if not album_dir.exists():
                raise ValueError(f"Album directory not found: {album_id}")
            
            # Process new images
            processor = ImageProcessor(album_dir)
            new_images = []
            for path in image_paths:
                path = Path(path)
                if path.is_file():
                    metadata = processor.process_single_image(path)
                    if metadata:
                        new_images.append(metadata)
                elif path.is_dir():
                    metadata_list = processor.process_directory(path)
                    new_images.extend(metadata_list)
            
            if not new_images:
                raise ValueError("No valid images found to add")
            
            # Update album data
            album['images'].extend(new_images)
            self._save_albums_json(albums_data)
            
            logger.info(f"Successfully added {len(new_images)} images to album {album_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to add images: {e}")
            return False
    
    def delete_images(self, album_id: str, image_ids: Union[str, List[str]]) -> bool:
        """Delete one or more images from an album."""
        try:
            # Convert single ID to list
            if isinstance(image_ids, str):
                image_ids = [image_ids]
            
            # Load album data
            albums_data = self._load_albums_json()
            album = next((a for a in albums_data['albums'] if a['id'] == album_id), None)
            if not album:
                raise ValueError(f"Album not found: {album_id}")
            
            album_dir = ALBUMS_DIR / album_id
            if not album_dir.exists():
                raise ValueError(f"Album directory not found: {album_id}")
            
            # Track success for each image
            success = True
            for image_id in image_ids:
                try:
                    # Find image in album
                    target_image = next((img for img in album['images'] if img['id'] == image_id), None)
                    if not target_image:
                        logger.error(f"Image not found in album: {image_id}")
                        success = False
                        continue
                    
                    # Delete image files for all sizes
                    for size_name, size_info in target_image['sizes'].items():
                        webp_path = album_dir / size_info['webp']
                        if webp_path.exists():
                            webp_path.unlink()
                    
                    # Update cover image if needed
                    if album['coverImage']['webp'] == target_image['sizes']['grid']['webp']:
                        remaining_images = [img for img in album['images'] if img['id'] != image_id]
                        if remaining_images:
                            album['coverImage'] = remaining_images[0]['sizes']['grid']
                        else:
                            album['coverImage'] = {}
                    
                    # Remove image from album data
                    album['images'] = [img for img in album['images'] if img['id'] != image_id]
                    logger.info(f"Deleted image {image_id}")
                    
                except Exception as e:
                    logger.error(f"Failed to delete image {image_id}: {e}")
                    success = False
            
            # Save updated album data
            self._save_albums_json(albums_data)
            return success
            
        except Exception as e:
            logger.error(f"Failed to delete images: {e}")
            return False
    
    def list_albums(self) -> List[Dict]:
        """List all albums."""
        try:
            albums_data = self._load_albums_json()
            return sorted(albums_data['albums'], key=lambda x: x['date'], reverse=True)
        except Exception as e:
            logger.error(f"Failed to list albums: {e}")
            return []
    
    def get_album(self, album_id: str) -> Optional[Dict]:
        """Get album by ID."""
        try:
            albums_data = self._load_albums_json()
            return next((a for a in albums_data['albums'] if a['id'] == album_id), None)
        except Exception as e:
            logger.error(f"Failed to get album {album_id}: {e}")
            return None
    
    def update_album(self, album_id: str, **updates) -> bool:
        """Update album metadata.
        
        Args:
            album_id: Album ID to update
            **updates: Keyword arguments for updates:
                - title: New album title
                - date: New album date (YYYY-MM-DD)
                - description: New album description
                - cover_image: New cover image ID (must be an existing image in the album)
        """
        try:
            # Load album data
            albums_data = self._load_albums_json()
            album = next((a for a in albums_data['albums'] if a['id'] == album_id), None)
            if not album:
                raise ValueError(f"Album not found: {album_id}")
            
            # Update title
            if 'title' in updates:
                album['title'] = updates['title']
            
            # Update date
            if 'date' in updates:
                date = updates['date']
                # Validate date format
                try:
                    datetime.strptime(date, '%Y-%m-%d')
                    album['date'] = date
                except ValueError:
                    raise ValueError("Date must be in YYYY-MM-DD format")
            
            # Update description
            if 'description' in updates:
                album['description'] = updates['description']
            
            # Update cover image
            if 'cover_image' in updates:
                cover_id = updates['cover_image']
                # Find image in album
                cover_image = next((img for img in album['images'] if img['id'] == cover_id), None)
                if not cover_image:
                    raise ValueError(f"Cover image not found in album: {cover_id}")
                album['coverImage'] = cover_image['sizes']['grid']
            
            # Save changes
            self._save_albums_json(albums_data)
            logger.info(f"Successfully updated album: {album_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to update album: {e}")
            return False
    
    def _load_albums_json(self) -> Dict:
        """Load albums.json data."""
        if not self.albums_json.exists():
            return {'albums': []}
        with open(self.albums_json, 'r') as f:
            return json.load(f)
    
    def _save_albums_json(self, data: Dict) -> None:
        """Save albums.json data."""
        with open(self.albums_json, 'w') as f:
            json.dump(data, f, indent=2)
    
    def _update_albums_json(self, new_album: Dict) -> None:
        """Update albums.json with a new album."""
        albums_data = self._load_albums_json()
        
        # Check for duplicate
        if any(a['id'] == new_album['id'] for a in albums_data['albums']):
            raise ValueError(f"Album ID already exists: {new_album['id']}")
        
        albums_data['albums'].append(new_album)
        self._save_albums_json(albums_data)
