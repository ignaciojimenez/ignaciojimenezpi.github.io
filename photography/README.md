# Photography Portfolio

A minimalist photography portfolio website with dynamic album loading and responsive images.

## Album Management

### Create Album
```bash
cd photography/utils
python3 create_album.py album-name \
  --title "Album Title" \
  --description "Description" \
  --date "YYYY-MM-DD" \
  --images path/to/images \
  --cover cover-image.jpg
```

### Add Images to Album
```bash
# Add directory of images
python3 create_album.py album-name --add --images path/to/more-images

# Add single image
python3 create_album.py album-name --add --images path/to/single-image.jpg
```

### Change Metadata
```bash
# Interactive selection from album images
python3 create_album.py album-name --change-cover

# Directly specify cover image
python3 create_album.py album-name --change-cover --cover path/to/image.jpg

# Change title
python3 create_album.py existing-album --new-title "Updated Title"

# Change date
python3 create_album.py existing-album --new-date 2023-12-31
```

### Delete Images from Album
```bash
# Interactive mode - select multiple images
python3 delete_image.py --interactive

# Interactive mode with pre-selected album
python3 delete_image.py --interactive --album album-name

# Direct mode - delete single image
python3 delete_image.py --album album-name --image image-name.jpg
```

### Delete Album
```bash
python3 create_album.py album-name --delete
```

## Features
- Responsive images with WebP support
- Dynamic image loading
- Mobile-friendly design
- Automated image optimization
- Comprehensive album management utilities:
  - Create and delete albums
  - Add single images or directories
  - Interactive image deletion
  - Change album cover images
  - Automatic responsive image generation

## Project Structure
```
photography/
├── albums/              # Album content and metadata
│   ├── */              # Individual album directories
│   │   ├── images/     # Original images
│   │   ├── responsive/ # Responsive image versions
│   │   └── metadata.json
│   └── albums.json     # Album index and configuration
├── css/                # Stylesheet directory
│   └── styles.css      # Main stylesheet
├── js/                 # Frontend JavaScript
│   ├── album-viewer.js # Album viewing functionality
│   ├── gallery.js      # Gallery layout and interactions
│   └── sw.js          # Service worker for offline support
├── utils/              # Album management scripts
│   ├── create_album.py # Album creation and modification
│   ├── delete_image.py # Image deletion utility
│   └── config.py       # Utility configuration
├── index.html          # Portfolio home page
└── manifest.json       # Progressive Web App manifest
