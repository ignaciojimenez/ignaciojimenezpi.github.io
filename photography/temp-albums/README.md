# Temporary Albums Directory

This directory is used by the GitHub Actions workflow to process new albums uploaded via iOS shortcuts.

## Album Configuration Format

Create an `album-config.json` file with the following structure:

```json
{
  "album_name": "my-new-album",
  "title": "My New Album",
  "description": "Description of the album",
  "date": "2024-12-21",
  "icloud_share_url": "https://share.icloud.com/photos/xyz"
}
```

The workflow will:
1. Validate this configuration
2. Download images from the iCloud shared album
3. Process the images using the existing utilities
4. Create the album in the main repository
