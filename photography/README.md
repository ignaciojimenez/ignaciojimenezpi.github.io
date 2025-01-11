# Photography Portfolio

A minimalist photography portfolio website with dynamic album loading and responsive images.

## Album Management

The album management system provides two modes of operation:

### Interactive Mode

Simply run:
```bash
cd photography/utils
python album.py
```

This will launch an interactive menu where you can:
- Create new albums
- Delete existing albums
- Update album metadata
- Add images to albums
- Remove images from albums

### CLI Mode

All operations support both interactive and non-interactive (CLI) usage. The CLI mode is designed for automation and scripting.

#### Create Album
```bash
python album.py create \
  --album-name my-album \
  --title "Album Title" \
  --date 2025-01-08 \
  --image-dir ~/photos \
  [--description "Optional description"] \
  [--cover-image cover.jpg] \
  [--yes]
```

#### Delete Album
```bash
python album.py delete \
  --album-name my-album \
  [--yes]  # Skip confirmation prompt
```

#### Update Album Metadata
```bash
python album.py update \
  --album-name my-album \
  [--title "New Title"] \
  [--date 2025-01-08] \
  [--description "New description"] \
  [--cover-image new-cover.jpg]
```

#### Add Images
```bash
python album.py add-images \
  --album-name my-album \
  --image-paths path1.jpg path2.jpg dir1/ \
  [--yes]
```

#### Remove Images
```bash
python album.py remove-images \
  --album-name my-album \
  --image-ids IMG_001 IMG_002 \
  [--yes]  # Skip confirmation prompt
```

### Common Options
All commands support these options:
- `--interactive/-i`: Run in interactive mode
- `--yes/-y`: Skip confirmation prompts (for automation)

## Project Structure
```
photography/
├── albums/                 # Album content and metadata
│   ├── */                 # Individual album directories
│   │   ├── images/        # Image directory
│   │   │   ├── grid/     # Grid thumbnails (400px)
│   │   │   ├── small/    # Small images (800px)
│   │   │   ├── medium/   # Medium images (1200px)
│   │   │   └── large/    # Large images (1600px)
│   │   └── index.html    # Album page
│   ├── template.html      # Album page template
│   └── albums.json        # Album index and metadata
├── css/                   # Stylesheet directory
│   ├── input.css         # Input styles for preprocessing
│   └── styles.css        # Main compiled stylesheet
├── js/                    # Frontend JavaScript
│   ├── album-viewer.js    # Album viewing functionality
│   ├── gallery.js         # Gallery layout and interactions
│   └── sw.js             # Service worker for offline support
├── utils/                 # Album management utilities
│   ├── album.py          # Main CLI/interactive tool
│   ├── album_manager.py   # Album operations
│   ├── image_processor.py # Image processing
│   ├── interactive.py     # Interactive prompts
│   ├── validation.py      # Input validation
│   ├── config.py         # Configuration
│   ├── create_album.py   # Legacy album creation script (deprecated)
│   └── delete_image.py   # Legacy image deletion script (deprecated)
└── index.html            # Portfolio home page
