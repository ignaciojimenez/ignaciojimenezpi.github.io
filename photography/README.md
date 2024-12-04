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

### Using GitHub Actions (Recommended)

You can create new albums using the GitHub Actions workflow either through the web interface or using the GitHub CLI.

#### Using GitHub CLI
```bash
gh workflow run album_processor.yml --ref photography-automation \
  -f album_name="your-album-name" \
  -f album_title="Your Album Title" \
  -f album_date="YYYY-MM-DD" \
  -f album_description="Your album description" \
  -f cover_image=""
```

Required parameters:
- `album_name`: URL-friendly name for the album (e.g., "winter-2023")
- `album_title`: Display title for the album (e.g., "Winter Adventures 2023")
- `album_date`: Date in YYYY-MM-DD format

Optional parameters:
- `album_description`: Description of the album
- `cover_image`: Name of the cover image file (if empty, first image will be used)

#### Using GitHub Web Interface
1. Go to the "Actions" tab in the repository
2. Click on the "Process New Album" workflow
3. Click "Run workflow"
4. Fill in the required parameters
5. Click "Run workflow"

Note: The workflow will create the album structure but will fail if no images are present in the source directory. This is expected behavior - you'll need to add images to the album directory after it's created.

### Manual Setup (Alternative)

1. Create Python virtual environment (only needed once):
```bash
cd utils
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

2. Run the create_album script:
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
