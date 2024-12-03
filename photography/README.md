# Photography Portfolio

A minimalist photography portfolio website with dynamic album loading, responsive images, and modern web optimizations.

## Features
- Dynamic image loading with lazy loading
- Responsive grid layout with hover effects
- WebP image support with fallbacks
- Chronological album sorting (newest first)
- Progressive Web App capabilities
- Mobile-friendly design
- Automated image optimization

## Project Structure
```
photography/
├── albums/
│   ├── albums.json         # Album metadata and configuration
│   └── [album-name]/      # Individual album directories
│       ├── images/        # Original images
│       ├── responsive/    # Responsive image versions
│       └── metadata.json  # Album metadata and EXIF data
├── utils/                 # Album management utilities
│   ├── config.py         # Configuration settings
│   ├── validation.py     # Data validation
│   ├── image_processor.py # Image optimization
│   └── create_album.py   # Album creation utility
├── js/                   # Frontend JavaScript
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
  "coverImage": "album-name/images/cover.jpg",
  "images": ["album-name/images/image1.jpg"]
}
```

## Adding a New Album

### First Time Setup

1. Create Python virtual environment (only needed once):
```bash
cd utils
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### Creating an Album

The script will:
1. Create album directory structure
2. Generate responsive images and WebP versions
3. Extract and store image metadata
4. Update albums.json automatically

```bash
python -m utils.create_album "album-name" \
  --title "Album Title" \
  --description "Album Description" \
  --date "YYYY-MM-DD" \
  --images path/to/images \
  --cover cover-image.jpg
```

#### Example
```bash
python -m utils.create_album urban \
  --title "Urban Photography" \
  --description "City landscapes" \
  --date "2023-12-01" \
  --images path/to/images \
  --cover modern-architecture.jpg
```

## Development
Start a local server:
```bash
python -m http.server 8000
```
Visit `http://localhost:8000/photography/`
