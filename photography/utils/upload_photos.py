#!/usr/bin/env python3

import sys
import os
import json
import argparse
from datetime import datetime
from pathlib import Path
import requests
import logging
from typing import List, Optional
import subprocess
import shutil

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

def get_github_token() -> str:
    """Get GitHub token using the GitHub CLI."""
    try:
        result = subprocess.run(['gh', 'auth', 'token'], 
                              capture_output=True, 
                              text=True, 
                              check=True)
        token = result.stdout.strip()
        if not token:
            raise ValueError("No token returned from GitHub CLI")
        return token
    except subprocess.CalledProcessError as e:
        logger.error("Failed to get GitHub token. Make sure you're logged in with 'gh auth login'")
        raise
    except Exception as e:
        logger.error(f"Error getting GitHub token: {e}")
        raise

def run_command(cmd: List[str], cwd: Optional[str] = None) -> bool:
    """Run a shell command and return True if successful."""
    try:
        subprocess.run(cmd, cwd=cwd, check=True, capture_output=True, text=True)
        return True
    except subprocess.CalledProcessError as e:
        logger.error(f"Command failed: {' '.join(cmd)}")
        logger.error(f"Error: {e.stderr}")
        return False

def setup_git_branch(branch_name: str) -> bool:
    """Create and checkout a new branch for the upload."""
    return (
        run_command(['git', 'fetch', 'origin']) and
        run_command(['git', 'checkout', '-b', branch_name, 'origin/photography-automation'])
    )

def copy_images_to_album(image_paths: List[str], album_name: str) -> List[str]:
    """Copy images to the album directory and return relative paths."""
    album_dir = Path('photography/albums') / album_name / 'images'
    album_dir.mkdir(parents=True, exist_ok=True)
    
    relative_paths = []
    for img_path in image_paths:
        src = Path(img_path)
        dest = album_dir / src.name
        shutil.copy2(src, dest)
        relative_paths.append(f"albums/{album_name}/images/{src.name}")
    
    return relative_paths

def commit_and_push_images(branch_name: str, album_name: str) -> bool:
    """Commit and push the images to GitHub."""
    return (
        run_command(['git', 'add', f'photography/albums/{album_name}/images/']) and
        run_command(['git', 'commit', '-m', f'Upload images for album: {album_name}']) and
        run_command(['git', 'push', 'origin', branch_name])
    )

def trigger_workflow(
    repo_owner: str,
    repo_name: str,
    github_token: str,
    branch_name: str,
    album_name: str,
    album_title: str,
    description: str,
    date: str,
    image_paths: List[str],
    cover_image: Optional[str] = None
) -> bool:
    """Trigger GitHub Actions workflow with album metadata."""
    try:
        # Prepare the repository dispatch event payload
        payload = {
            "event_type": "photo-upload",
            "client_payload": {
                "branch_name": branch_name,
                "album_name": album_name,
                "album_title": album_title,
                "description": description,
                "date": date,
                "image_paths": image_paths,
                "cover_image": cover_image if cover_image else ""
            }
        }

        logger.info(f"Sending request to GitHub API...")
        
        # Trigger the workflow
        response = requests.post(
            f"https://api.github.com/repos/{repo_owner}/{repo_name}/dispatches",
            headers={
                "Accept": "application/vnd.github.v3+json",
                "Authorization": f"token {github_token}",
                "Content-Type": "application/json"
            },
            json=payload
        )
        
        if response.status_code != 204:
            error_msg = f"GitHub API Error: {response.status_code} - {response.text}"
            logger.error(error_msg)
            return False
            
        logger.info("Successfully triggered photo processing workflow")
        return True
        
    except Exception as e:
        logger.error(f"Failed to trigger workflow: {str(e)}")
        return False

def main():
    parser = argparse.ArgumentParser(description='Upload photos to create a new album')
    parser.add_argument('album_name', help='Unique identifier for the album')
    parser.add_argument('album_title', help='Display title for the album')
    parser.add_argument('--description', default='', help='Album description')
    parser.add_argument('--date', default=datetime.now().strftime('%Y-%m-%d'),
                      help='Album date (YYYY-MM-DD)')
    parser.add_argument('--cover-image', help='Filename to use as cover image')
    parser.add_argument('images', nargs='+', help='Paths to image files')
    
    args = parser.parse_args()
    
    # Get GitHub token using GitHub CLI
    try:
        github_token = get_github_token()
    except Exception as e:
        sys.exit(1)
    
    # Validate image paths
    image_paths = []
    for path in args.images:
        img_path = Path(path)
        if not img_path.exists():
            logger.error(f"Image not found: {path}")
            sys.exit(1)
        if img_path.suffix.lower() not in {'.jpg', '.jpeg', '.png'}:
            logger.error(f"Unsupported image format: {path}")
            sys.exit(1)
        image_paths.append(str(img_path.absolute()))
    
    # Validate cover image
    if args.cover_image and not any(args.cover_image in p for p in image_paths):
        logger.error(f"Cover image not found in provided images: {args.cover_image}")
        sys.exit(1)

    # Create a new branch for this upload
    branch_name = f"upload-{args.album_name}-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
    if not setup_git_branch(branch_name):
        logger.error("Failed to create git branch")
        sys.exit(1)

    # Copy images to album directory
    relative_paths = copy_images_to_album(image_paths, args.album_name)

    # Commit and push images
    if not commit_and_push_images(branch_name, args.album_name):
        logger.error("Failed to commit and push images")
        sys.exit(1)

    # Trigger the workflow
    if trigger_workflow(
        "ignaciojimenez",
        "ignaciojimenezpi.github.io",
        github_token,
        branch_name,
        args.album_name,
        args.album_title,
        args.description,
        args.date,
        relative_paths,
        args.cover_image
    ):
        logger.info("Photos uploaded successfully!")
    else:
        sys.exit(1)

if __name__ == '__main__':
    main()
