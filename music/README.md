# Music Projects

A minimalist website showcasing my musical projects and bands.

## Features

- Responsive grid layout of band cards
- Links to Spotify profiles
- Hover effects and smooth transitions
- Mobile-friendly design

## Structure

- `index.html`: Main page with band grid
- `styles.css`: Custom styles for the music section

## Adding/Updating Bands

To add or update bands, modify the `bands` array in `index.html`. Each band object should have:

```javascript
{
    "name": "Band Name",
    "role": "Your Role",
    "genre": "Music Genre",
    "image": "URL to band image",
    "spotifyUrl": "Spotify profile URL",
    "description": "Short description"
}
```

## Development

1. Uses Tailwind CSS for styling (via CDN)
2. Custom CSS for specific effects
3. Vanilla JavaScript for rendering

## Publishing Changes

After making changes:
```bash
git add music/*
git commit -m "Update music projects"
git push origin main
```
