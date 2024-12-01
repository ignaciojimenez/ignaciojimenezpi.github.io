# Photography Portfolio

A minimalist photography portfolio website with dynamic album loading and smooth interactions.

## Features
- Dynamic image loading with lazy loading
- Responsive Masonry grid layout
- Image optimization (max 2000px, 85% quality)
- Modal image viewer with keyboard navigation
- Mobile-friendly design
- Automatic image list generation

## Project Structure
```
photography/
├── albums/
│   ├── albums.json         # Album metadata
│   ├── template.html       # Generic album template
│   └── [album-name]/      # Individual album directories
│       ├── index.html     # Album page (from template)
│       ├── images.json    # List of images in album
│       └── images/        # Optimized images
├── create_album.py        # Album creation utility
├── styles.css            # Global styles
└── index.html           # Portfolio home page
```

## Adding a New Album

### First Time Setup

1. Create Python virtual environment (only needed once):
```bash
# In the photography directory
python3 -m venv venv
./venv/bin/pip install Pillow
```

### Creating an Album

The script will:
1. Create a new album directory with optimized images
2. Generate images.json with the list of images
3. Create the album's index.html from template
4. Update the albums.json file automatically

```bash
./venv/bin/python create_album.py [album-name] "Album Title" "Album Description" [path-to-images]
```

#### Examples

```bash
# Create album from a directory of images
./venv/bin/python create_album.py italy-2023 "Italy Trip" "Summer adventures in Italy" ~/Pictures/Italy/

# Create album from specific images
./venv/bin/python create_album.py portraits "Portrait Work" "Recent portrait photography" "photo1.jpg,photo2.jpg,photo3.jpg"

# Use a specific local image as cover
./venv/bin/python create_album.py wedding "Smith Wedding" "Smith wedding in Barcelona" ~/Pictures/Smith-Wedding/ --cover ceremony.jpg

# Use an external URL as cover image (e.g., from Unsplash)
./venv/bin/python create_album.py nature "Nature Gallery" "Beautiful landscapes" ~/Pictures/Nature/ --cover https://images.unsplash.com/photo-1472214103451-9374bd1c798e
```

### What Happens

1. Creates album directory in `albums/[album-name]/`
   - `index.html`: Album page with image grid (from template)
   - `images.json`: List of images in the album
   - `images/`: Directory containing optimized images
     - Resizes large images (max 2000px)
     - Optimizes for web (85% quality)
     - Original images remain untouched

2. Updates `albums.json` with new album metadata:
   - Album ID (URL-friendly name)
   - Title
   - Description
   - Cover image URL

## Technical Details

### Dependencies
- Python 3 with Pillow for image processing
- Tailwind CSS for styling
- Masonry Layout for responsive grid
- ImagesLoaded for smooth loading
- Intersection Observer for lazy loading

### Browser Support
- Modern browsers with JavaScript enabled
- Graceful degradation for older browsers
- Mobile-friendly responsive design

### Performance
- Lazy loading of images
- Optimized image sizes
- Minimal JavaScript dependencies
- No build step required
