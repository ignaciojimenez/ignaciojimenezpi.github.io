# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Personal portfolio website for Ignacio Jiménez Pi, hosted on Cloudflare Pages. Sections: home, photography (film album gallery), music (band showcase). Deployed to ignacio.jimenezpi.com and ignacio.systems.

Stack: Vanilla JS, Tailwind CSS v3, Python utilities for album management, GitHub Actions for automation. No JS frameworks.

## Commands

### CSS (required before committing)

```bash
npm install                  # Install dependencies
npm run build:css:all        # Build all CSS files (run before committing)
npm run watch:css:all        # Watch all CSS during development
```

Individual section builds: `npm run build:css`, `npm run build:css:photography`, `npm run build:css:music`

### Album Management (Python)

```bash
cd photography/utils

# Interactive mode
python album.py

# CLI mode
python album.py create --album-name my-album --title "My Album" --date 2025-01-08 --image-dir ~/photos
python album.py delete --album-name my-album --yes
python album.py update --album-name my-album --title "New Title"
python album.py add-images --album-name my-album --image-paths path1.jpg
python album.py remove-images --album-name my-album --image-ids IMG_001
```

Python deps: `pip install -r photography/utils/requirements.txt` (Pillow, pillow-heif, jsonschema, inquirer)

### Tests

```bash
python tests/test_staging_workflow.py
```

## Architecture

### CSS Pipeline

Three separate Tailwind CSS pipelines (main, photography, music), each with their own `input.css` → `styles.css`. Compiled files are committed to the repo (required for static hosting). PostCSS + Autoprefixer are applied during build.

### Photography Section

- **`photography/albums/albums.json`** — Index of all albums (metadata: id, title, date, cover image)
- **`photography/albums/[album-name]/album.json`** — Per-album metadata (images list, captions)
- **`photography/albums/[album-name]/index.html`** — Per-album page (generated from template)
- Images stored in 4 sizes: `grid/` (400px), `small/` (800px), `medium/` (1200px), `large/` (1600px), all WebP

JS files: `gallery.js` + `gallery-init.js` for the album index; `album-viewer.js` + `album-init.js` for individual albums. Service worker (`sw.js`) handles offline caching.

### Album Management Pipeline

Python utilities in `photography/utils/`:
- `album.py` — CLI entry point (argparse + interactive mode via `inquirer`)
- `album_manager.py` — Core operations class (create/delete/update albums, update `albums.json`)
- `image_processor.py` — Resizes images into 4 size variants using Pillow, converts HEIF/HEIC
- `process_staging.py` — Processes albums uploaded to a staging directory (used by GitHub Actions)

### GitHub Actions Workflows

- **`process_album.yml`** — Triggered by push to staging directory; runs `process_staging.py`, auto-commits processed albums
- **`remove_album.yml`** — Manual dispatch or `repository_dispatch`; deletes an album by ID and auto-commits

### Music Section

`music/bands.json` is the data source. `music/js/bands.js` reads it and dynamically renders the band cards.

### Security

`_headers` file enforces strict CSP, HSTS, X-Frame-Options via Cloudflare Pages. No inline scripts allowed — all JS must be in external files.

## Key Conventions

- **Commit compiled CSS**: `css/styles.css`, `photography/css/styles.css`, `music/css/styles.css` are committed artifacts
- **Image format**: WebP throughout (Pillow converts on ingest)
- **Data files**: JSON only — no database, no server-side rendering
- **No JS build step**: JS files are used directly, no bundler
