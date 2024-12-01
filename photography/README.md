# Photography Portfolio

A minimalist photography portfolio website with dynamic album loading and smooth interactions.

## Features
- Dynamic image loading with lazy loading
- Responsive grid layout with hover effects
- Chronological album sorting (newest first)
- Image optimization (max 2000px, 85% quality)
- Modal image viewer with keyboard navigation
- Mobile-friendly design
- Automatic image list generation

## Project Structure
```
photography/
├── albums/
│   ├── albums.json         # Album metadata and configuration
│   ├── template.html       # Generic album template
│   └── [album-name]/      # Individual album directories
│       ├── index.html     # Album page (from template)
│       ├── images.json    # List of images in album
│       └── images/        # Optimized images
├── create_album.py        # Album creation utility
├── styles.css            # Global styles
└── index.html           # Portfolio home page
```

## Album Configuration
Each album in `albums.json` has the following structure:
```json
{
  "id": "album-name",
  "title": "Album Title",
  "description": "Album description",
  "date": "YYYY-MM-DD",
  "coverImage": "path/to/cover/image",
  "images": ["image1.jpg", "image2.jpg"]
}
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
./venv/bin/python create_album.py [album-name] "Album Title" "Album Description" "YYYY-MM-DD" [path-to-images] --cover [cover-image]
```

#### Required Parameters
- `album-name`: URL-friendly name (e.g., "summer-2023")
- `Album Title`: Display title (e.g., "Summer 2023")
- `Album Description`: Short description of the album
- `YYYY-MM-DD`: Date of the album (used for sorting)
- `path-to-images`: Directory containing the images

#### Optional Parameters
- `--cover`: Specify a cover image (must be in the images directory)

#### Example
```bash
./venv/bin/python create_album.py urban "Urban Photography" "City landscapes" "2023-12-01" path/to/images --cover modern-architecture.jpg
```

## Features
### Landing Page
- Albums sorted chronologically (newest first)
- Hover effects showing album title, date, and description
- Responsive grid layout
- Lazy loading for better performance

### Album Pages
- Responsive image grid
- Modal viewer with keyboard navigation
- Image lazy loading
- Smooth loading transitions
