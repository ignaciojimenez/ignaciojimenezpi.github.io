# Music Section

A minimalist showcase of my musical projects and bands. Built with vanilla JavaScript and modern CSS.

## Features

- Clean, minimal design focusing on band imagery
- Responsive grid layout that respects image aspect ratios
- Elegant hover effects showing band names
- Direct links to Spotify profiles
- Graceful fallback for missing images
- Easy band management through JSON file

## Structure

```
music/
├── bands.json      # Band data configuration
├── images/         # Band photos
│   ├── atencion-tsunami.jpg
│   ├── incendios.jpg
│   ├── karen-koltrane.jpg
│   └── paracaidas.jpg
├── index.html      # Main page
└── README.md      # This file
```

## Implementation Details

- Uses CSS Grid for responsive layout
- Smooth transitions for hover effects
- No external dependencies
- Mobile-friendly design
- Asynchronous JSON data loading

## Managing Bands

Bands are configured in `bands.json`. To add or update bands:

1. Add the band's image to the `images/` directory
2. Edit `bands.json`:

```json
{
    "bands": [
        {
            "name": "Band Name",
            "image": "images/band-name.jpg",
            "spotifyUrl": "https://open.spotify.com/artist/..."
        }
    ]
}
```

No code changes are needed when updating band information - just modify the JSON file!

## Publishing Changes

After making changes:
```bash
git add music/*
git commit -m "Update music projects"
git push origin main
