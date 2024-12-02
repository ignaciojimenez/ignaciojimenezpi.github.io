#!/usr/bin/env python3
import os
import sys
import json
from pathlib import Path
from PIL import Image
import argparse
from datetime import datetime

def load_albums():
    """Load existing albums from albums.json"""
    base_dir = Path(__file__).parent
    albums_file = base_dir / 'albums' / 'albums.json'
    
    if not albums_file.exists():
        print("No albums.json found, will initialize it")
        return {'albums': []}
    
    try:
        with open(albums_file, 'r') as f:
            return json.load(f)
    except json.JSONDecodeError:
        print("Error parsing albums.json, will reinitialize it")
        return {'albums': []}

def generate_images_json(images_dir):
    """Generate images.json file for an album directory"""
    images = []
    for img_path in sorted(Path(images_dir).glob('*')):
        if img_path.suffix.lower() in ['.jpg', '.jpeg', '.png', '.gif', '.webp']:
            images.append(img_path.name)
    
    images_json = {'images': images}
    json_path = Path(images_dir).parent / 'images.json'
    
    with open(json_path, 'w') as f:
        json.dump(images_json, f, indent=4)
    
    return images

def create_album(album_name, title, description, date, image_dir, cover_image=None):
    """Create a new album with optimized images and update albums.json"""
    # Setup paths
    base_dir = Path(__file__).parent
    album_dir = base_dir / 'albums' / album_name
    images_dir = album_dir / 'images'
    template_path = base_dir / 'albums' / 'template.html'
    
    # Verify template exists
    if not template_path.exists():
        print(f"Error: Template file not found at {template_path}")
        return False
    
    # Create directories
    album_dir.mkdir(parents=True, exist_ok=True)
    images_dir.mkdir(parents=True, exist_ok=True)
    
    # Process images
    gallery_images = []
    
    # Get image files
    if os.path.isdir(image_dir):
        image_files = [f for f in Path(image_dir).glob('*') if f.suffix.lower() in ['.jpg', '.jpeg', '.png']]
    else:
        image_files = [Path(f) for f in image_dir.split(',') if Path(f).suffix.lower() in ['.jpg', '.jpeg', '.png']]
    
    if not image_files:
        print(f"Error: No valid images found in {image_dir}")
        return False
    
    # Process each image
    for img_path in image_files:
        try:
            # Create optimized version
            img = Image.open(img_path)
            
            # Calculate new size maintaining aspect ratio
            max_size = 2000
            ratio = min(max_size/img.width, max_size/img.height)
            new_size = (int(img.width * ratio), int(img.height * ratio))
            
            # Resize and save
            img = img.resize(new_size, Image.Resampling.LANCZOS)
            
            # Save to album's images directory
            new_path = images_dir / img_path.name
            img.save(new_path, quality=85, optimize=True)
            
            # Add to gallery
            gallery_images.append({
                'url': f'/photography/albums/{album_name}/images/{new_path.name}',
                'alt': f'{title} - {new_path.stem}'
            })
            
            # Set as cover if it's the first image and no cover specified
            if not cover_image and len(gallery_images) == 1:
                cover_image = gallery_images[0]['url']
            
            print(f"Processed: {img_path.name}")
        except Exception as e:
            print(f"Error processing {img_path.name}: {str(e)}")
            continue
    
    if not gallery_images:
        print("Error: No images were successfully processed")
        return False
    
    try:
        # Generate images.json
        generate_images_json(images_dir)
        
        # Create album HTML
        with open(template_path, 'r') as f:
            template = f.read()
        
        # Save as index.html in album directory
        index_path = album_dir / 'index.html'
        with open(index_path, 'w') as f:
            f.write(template)
        
        # Load existing albums
        albums_data = load_albums()
        
        # Add new album
        new_album = {
            'id': album_name,
            'title': title,
            'description': description,
            'date': date,
            'coverImage': cover_image if cover_image else f'albums/{album_name}/images/{os.path.basename(image_files[0].name)}',
            'images': [img.name for img in image_files]
        }
        
        # Add to beginning of albums list
        albums_data['albums'].insert(0, new_album)
        
        # Save updated albums.json
        albums_file = base_dir / 'albums' / 'albums.json'
        with open(albums_file, 'w') as f:
            json.dump(albums_data, f, indent=2)
        
        print(f"\nAlbum '{title}' created successfully!")
        print(f"- Album directory: albums/{album_name}/")
        print(f"- Album page: albums/{album_name}/index.html")
        print(f"- Images directory: albums/{album_name}/images/")
        print(f"- Images list: albums/{album_name}/images.json")
        print(f"- Added to albums.json")
        print("\nDon't forget to:")
        print(f"1. git add photography/albums/{album_name}")
        print("2. git add photography/albums/albums.json")
        print(f'3. git commit -m "Add new album: {title}"')
        print("4. git push origin main")
        
        return True
    
    except Exception as e:
        print(f"Error creating album: {str(e)}")
        return False

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Create a new photo album')
    parser.add_argument('album_name', help='URL-friendly name for the album (e.g., "summer-2023")')
    parser.add_argument('title', help='Display title for the album (e.g., "Summer 2023")')
    parser.add_argument('description', help='Short description of the album')
    parser.add_argument('date', help='Album date in YYYY-MM-DD format (used for sorting)')
    parser.add_argument('image_dir', help='Directory containing images or comma-separated list of image paths')
    parser.add_argument('--cover', help='Cover image filename (from image_dir)', default=None)
    
    args = parser.parse_args()
    
    # Validate date format
    try:
        datetime.strptime(args.date, '%Y-%m-%d')
    except ValueError:
        print("Error: Date must be in YYYY-MM-DD format")
        sys.exit(1)
    
    create_album(args.album_name, args.title, args.description, args.date, args.image_dir, args.cover)
