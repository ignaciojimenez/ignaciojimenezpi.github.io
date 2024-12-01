# Photography Portfolio

A minimalist photography portfolio website with dynamic image galleries and smooth interactions.

## Adding a New Album

### First Time Setup

1. Create Python virtual environment (only needed once):
```bash
# In the photography directory
python3 -m venv venv
./venv/bin/pip install Pillow
```

### Creating an Album

The script will create optimized copies of your images, create the album page, and update the landing page automatically.

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

1. Creates optimized copies of your images in `images/[album-name]/`
   - Resizes large images (max 2000px)
   - Optimizes for web (85% quality)
   - Original images remain untouched

2. Creates album page in `albums/[album-name].html`
   - Responsive masonry grid layout
   - Full-screen image viewer
   - Keyboard navigation

3. Updates landing page (`index.html`)
   - Adds album preview with cover image (first image by default, or specified cover)
   - Supports both local images and external URLs for covers
   - Updates navigation

### Publishing Changes

After creating an album, run:
```bash
git add photography/albums/[album-name].html
git add photography/images/[album-name]/*
git add photography/index.html
git commit -m "Add new album: [Album Title]"
git push origin main
```

## Features

- Responsive masonry grid layout
- Full-screen image viewer
- Keyboard navigation (←/→/Esc)
- Automatic image optimization
- Mobile-friendly design
