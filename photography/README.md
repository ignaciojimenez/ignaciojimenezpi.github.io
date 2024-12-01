# Photography Portfolio

A minimalist photography portfolio website with dynamic album loading and smooth interactions.

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
1. Create optimized copies of your images
2. Create the album page
3. Update the albums.json file automatically

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

3. Updates `albums/albums.json`
   - Adds new album to the beginning of the list
   - Includes title, description, cover image, and URL
   - Used by main.js to dynamically load albums

### Project Structure

```
photography/
├── albums/
│   ├── albums.json     # Album metadata
│   ├── template.html   # Album page template
│   └── [album].html   # Individual album pages
├── images/
│   └── [album]/       # Optimized images for each album
├── create_album.py    # Album creation script
├── index.html         # Main gallery page
├── main.js           # Gallery initialization
└── styles.css        # Custom styles
```

### Development

The website uses:
- Vanilla JavaScript for dynamic rendering
- CSS Grid for responsive layout
- Masonry layout for image grids
- Intersection Observer for lazy loading
- Tailwind CSS for styling

### Contributing

1. Create a new branch for your changes
2. Make your modifications
3. Test locally using a web server (e.g., `python3 -m http.server`)
4. Submit a pull request

### License

MIT License - feel free to use this code for your own portfolio!
