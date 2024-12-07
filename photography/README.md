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
python3 create_album.py album-name --add --images path/to/more-images
```

### Delete Image from Album
```bash
python3 delete_image.py album-name image-name.jpg
```
This will:
- Remove the image from albums.json
- Delete the image and its responsive versions
- Update metadata.json
- Update album cover if needed

### Delete Album
```bash
python3 create_album.py album-name --delete
```

## Features
- Responsive images with WebP support
- Dynamic image loading
- Mobile-friendly design
- Automated image optimization
- Album management utilities

## Project Structure
```
photography/
├── albums/              # Album content and metadata
├── utils/              # Album management scripts
├── js/                 # Frontend JavaScript
└── index.html         # Portfolio home page
