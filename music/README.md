# Music Section

A minimalist showcase of my musical projects and bands. Built with vanilla JavaScript and modern CSS.

## Features

- Clean, minimal design focusing on band imagery
- Responsive grid layout that respects image aspect ratios
- Elegant hover effects showing band names
- Direct links to Spotify profiles
- Graceful fallback for missing images

## Structure

```
music/
├── images/          # Band photos
│   ├── atencion-tsunami.jpg
│   ├── incendios.jpg
│   ├── karen-koltrane.jpg
│   └── paracaidas.jpg
├── index.html       # Main page
└── README.md       # This file
```

## Implementation Details

- Uses CSS Grid for responsive layout
- Smooth transitions for hover effects
- No external dependencies
- Mobile-friendly design

## Adding/Updating Bands

To add or update a band:

1. Add the band's image to the `images/` directory
2. Update the `bands` array in `index.html`:

```javascript
{
    "name": "Band Name",
    "image": "images/band-name.jpg",
    "spotifyUrl": "https://open.spotify.com/artist/..."
}
```

## Publishing Changes

After making changes:
```bash
git add music/*
git commit -m "Update music projects"
git push origin main
