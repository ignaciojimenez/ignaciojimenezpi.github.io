#!/usr/bin/env python3
import os
import sys
import json
import shutil
from pathlib import Path
from PIL import Image
import argparse
import re

def extract_albums_from_js(content):
    # Find the albums array using regex
    match = re.search(r'const\s+albums\s*=\s*(\[[\s\S]*?\]);', content)
    if not match:
        print("No albums array found in index.html, will initialize it")
        return []
    
    # Extract the array text and convert JS to Python
    albums_text = match.group(1)
    # Convert JavaScript object syntax to Python dict syntax
    albums_text = re.sub(r'(\w+):', r'"\1":', albums_text)
    
    try:
        # Parse the JSON array
        return json.loads(albums_text)
    except json.JSONDecodeError:
        print("Error parsing albums array from index.html, will reinitialize it")
        return []

def create_album(album_name, title, description, image_dir, cover_image=None):
    # Setup paths
    base_dir = Path(__file__).parent
    albums_dir = base_dir / 'albums'
    images_dir = base_dir / 'images' / album_name
    template_path = albums_dir / 'template.html'
    
    # Verify template exists
    if not template_path.exists():
        print(f"Error: Template file not found at {template_path}")
        return False
    
    # Create directories if they don't exist
    images_dir.mkdir(parents=True, exist_ok=True)
    
    # Process images
    gallery_images = []
    image_files = []
    
    # Check if image_dir is a directory or a list of files
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
            
            # Calculate new size while maintaining aspect ratio
            max_size = 2000
            ratio = min(max_size/img.width, max_size/img.height)
            new_size = (int(img.width * ratio), int(img.height * ratio))
            
            # Resize and save
            img = img.resize(new_size, Image.Resampling.LANCZOS)
            
            # Save to images directory
            new_path = images_dir / img_path.name
            img.save(new_path, quality=85, optimize=True)
            
            # Add to gallery
            gallery_images.append({
                'url': f'/photography/images/{album_name}/{new_path.name}',
                'alt': f'{title} - {new_path.stem}'
            })
            
            # Set as cover if it's the first image and no cover specified
            if not cover_image and len(gallery_images) == 1:
                cover_image = gallery_images[0]['url']  # Use the full URL
            
            print(f"Processed: {img_path.name}")
        except Exception as e:
            print(f"Error processing {img_path.name}: {str(e)}")
            continue
    
    if not gallery_images:
        print("Error: No images were successfully processed")
        return False
    
    try:
        # Create album HTML
        with open(template_path, 'r') as f:
            template = f.read()
        
        album_html = template.replace('{{ALBUM_TITLE}}', title)
        album_html = album_html.replace('{{GALLERY_IMAGES}}', json.dumps(gallery_images, indent=4))
        
        # Save album HTML
        album_path = albums_dir / f'{album_name}.html'
        with open(album_path, 'w') as f:
            f.write(album_html)
        
        # Update index.html with new album
        index_path = base_dir / 'index.html'
        if not index_path.exists():
            print("Creating new index.html file")
            with open(index_path, 'w') as f:
                f.write('''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Photography Portfolio - Ignacio Jiménez Pi</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <link rel="stylesheet" href="styles.css">
</head>
<body class="bg-white">
    <div id="albums-grid" class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 p-4">
        <!-- Albums will be dynamically inserted here -->
    </div>
    <script>
        const albums = [];
        
        // Render albums
        const albumsGrid = document.getElementById('albums-grid');
        albums.forEach(album => {
            const albumElement = document.createElement('div');
            albumElement.className = 'relative group cursor-pointer';
            albumElement.innerHTML = `
                <a href="${album.url}" class="block">
                    <img src="${album.coverImage}" alt="${album.title}" class="w-full h-64 object-cover">
                    <div class="absolute inset-0 bg-black bg-opacity-0 group-hover:bg-opacity-75 transition-opacity duration-300 flex items-center justify-center">
                        <div class="text-white text-center opacity-0 group-hover:opacity-100 transition-opacity duration-300">
                            <h3 class="text-xl font-semibold">${album.title}</h3>
                            <p class="mt-2">${album.description}</p>
                        </div>
                    </div>
                </a>
            `;
            albumsGrid.appendChild(albumElement);
        });
    </script>
</body>
</html>''')
        
        with open(index_path, 'r') as f:
            index_content = f.read()
        
        # Extract existing albums
        albums = extract_albums_from_js(index_content)
        
        # Add new album
        new_album = {
            'id': album_name,
            'title': title,
            'coverImage': cover_image if cover_image.startswith('http') else f'/photography/images/{album_name}/{cover_image}',  # Handle both URLs and local files
            'description': description,
            'url': f'albums/{album_name}.html'
        }
        
        # Add to beginning of albums list
        albums.insert(0, new_album)
        
        # Update index.html
        new_albums_text = 'const albums = ' + json.dumps(albums, indent=12)
        new_index_content = re.sub(
            r'const\s+albums\s*=\s*\[[\s\S]*?\];',
            new_albums_text + ';',
            index_content
        )
        
        with open(index_path, 'w') as f:
            f.write(new_index_content)
        
        print(f"\nAlbum '{title}' created successfully!")
        print(f"- Album page: albums/{album_name}.html")
        print(f"- Images directory: images/{album_name}/")
        print(f"- Added to index.html")
        print("\nDon't forget to:")
        print(f"1. git add photography/albums/{album_name}.html")
        print(f"2. git add photography/images/{album_name}/*")
        print("3. git add photography/index.html")
        print(f'4. git commit -m "Add new album: {title}"')
        print("5. git push origin main")
        
        return True
    
    except Exception as e:
        print(f"Error creating album: {str(e)}")
        return False

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Create a new photo album')
    parser.add_argument('album_name', help='URL-friendly name for the album (e.g., "summer-2023")')
    parser.add_argument('title', help='Display title for the album (e.g., "Summer 2023")')
    parser.add_argument('description', help='Short description of the album')
    parser.add_argument('image_dir', help='Directory containing images or comma-separated list of image paths')
    parser.add_argument('--cover', help='Filename of cover image (will use first image if not specified)', default=None)
    
    args = parser.parse_args()
    
    success = create_album(args.album_name, args.title, args.description, args.image_dir, args.cover)
    if not success:
        sys.exit(1)
