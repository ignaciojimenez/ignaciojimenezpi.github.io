"""Interactive utilities for the photography portfolio."""

import os
import json
from pathlib import Path
from typing import Dict, List, Optional, Union, Any
from datetime import datetime
import inquirer
import logging
from config import ALBUMS_DIR, ALBUMS_JSON
from album_manager import AlbumManager
from inquirer.themes import GreenPassion

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

def prompt_album_creation() -> Dict[str, Any]:
    """Interactive prompt for album creation."""
    # Use custom theme for better visibility
    theme = GreenPassion()
    
    questions = [
        inquirer.Text('title',
                     message="Enter album title"),
        inquirer.Text('id',
                     message="Enter album ID (lowercase, no spaces)",
                     validate=lambda _, x: x.replace('-', '').replace('_', '').isalnum(),
                     default=lambda answers: answers['title'].lower().replace(' ', '-')),
        inquirer.Text('description',
                     message="Enter album description (optional)",
                     default=""),
        inquirer.Text('date',
                     message="Enter album date (YYYY-MM-DD)",
                     validate=lambda _, x: validate_date(x),
                     default=datetime.now().strftime('%Y-%m-%d')),
        inquirer.Confirm('favorite',
                        message="Mark this album as a favorite? (will always appear first in gallery)",
                        default=False),
    ]
    
    # First get basic album info
    answers = inquirer.prompt(questions, theme=theme)
    if not answers:
        return {}
    
    # Then handle directory selection
    while True:
        try:
            path = input('Enter path to image directory: ')
            # Expand user directory
            path = os.path.expanduser(path)
            
            if not os.path.exists(path):
                print('Error: Directory does not exist')
                continue
            
            if not os.path.isdir(path):
                print('Error: Not a directory')
                continue
            
            # Path is valid
            answers['image_dir'] = path
            break
            
        except (KeyboardInterrupt, EOFError):
            print('\nOperation cancelled')
            return {}
    
    # Handle cover image selection after we know the image directory
    image_dir = Path(answers['image_dir'])
    image_files = list(filter(
        lambda x: x.suffix.lower() in {'.jpg', '.jpeg', '.png', '.webp'},
        image_dir.iterdir()
    ))
    
    if image_files:
        cover_questions = [
            inquirer.List('cover_image',
                         message="Select cover image",
                         choices=[
                             ('No cover image (use first image)', None),
                             *[(f.name, f.name) for f in sorted(image_files, key=lambda x: x.name)]
                         ])
        ]
        cover_answer = inquirer.prompt(cover_questions, theme=theme)
        if not cover_answer:
            return {}
        answers['cover_image'] = cover_answer['cover_image']
    
    return answers

def prompt_album_deletion() -> Optional[str]:
    """Interactive prompt for album deletion."""
    # Load existing albums
    albums = load_albums()
    if not albums:
        print("No albums found.")
        return None
        
    # Create choices with album details
    choices = []
    for album in sorted(albums, key=lambda x: x['date'], reverse=True):
        # Format: Album Title (ID) - YYYY-MM-DD
        choice_label = f"{album['title']} ({album['id']}) - {album['date']}"
        choices.append((choice_label, album['id']))
    
    questions = [
        inquirer.List('album_id',
                     message="Select album to delete",
                     choices=choices),
    ]
    
    # First selection
    answers = inquirer.prompt(questions, theme=GreenPassion())
    if not answers:
        return None
    
    # Confirmation
    album_id = answers['album_id']
    album = next(a for a in albums if a['id'] == album_id)
    confirm_questions = [
        inquirer.Confirm('confirm',
                        message=f"Are you sure you want to delete album '{album['title']}' ({album_id})?",
                        default=False)
    ]
    
    confirm = inquirer.prompt(confirm_questions, theme=GreenPassion())
    if not confirm or not confirm['confirm']:
        print("Album deletion cancelled.")
        return None
        
    return album_id

def prompt_image_deletion(album_id: str) -> Optional[List[str]]:
    """Interactive prompt for image deletion."""
    # Load album data
    album = get_album(album_id)
    if not album:
        print(f"Album not found: {album_id}")
        return None
    
    if not album['images']:
        print("No images found in album.")
        return None
    
    # Create choices with image details
    choices = [(img['id'], img['id']) for img in album['images']]
    
    questions = [
        inquirer.Checkbox('image_ids',
                         message="Select images to delete (use space to select, enter to confirm)",
                         choices=choices)
    ]
    
    # Selection
    answers = inquirer.prompt(questions, theme=GreenPassion())
    if not answers or not answers['image_ids']:
        return None
    
    # Confirmation
    image_ids = answers['image_ids']
    confirm_questions = [
        inquirer.Confirm('confirm',
                        message=f"Are you sure you want to delete {len(image_ids)} image(s)?",
                        default=False)
    ]
    
    confirm = inquirer.prompt(confirm_questions, theme=GreenPassion())
    if not confirm or not confirm['confirm']:
        print("Image deletion cancelled.")
        return None
    
    # Always ensure we return a list, even if only one item is selected
    if isinstance(image_ids, str):
        return [image_ids]
    return image_ids

def prompt_image_addition(album_id: str) -> Optional[Union[str, List[str]]]:
    """Interactive prompt for adding images to an album."""
    # First verify album exists
    album = get_album(album_id)
    if not album:
        print(f"Album not found: {album_id}")
        return None
    
    questions = [
        inquirer.List('source_type',
                     message="Select source type",
                     choices=[
                         ('Single image file', 'file'),
                         ('Directory of images', 'directory')
                     ])
    ]
    
    answers = inquirer.prompt(questions, theme=GreenPassion())
    if not answers:
        return None
    
    is_file = answers['source_type'] == 'file'
    
    try:
        while True:
            try:
                path = input(f'Enter path to image{"" if is_file else " directory"}: ')
                # Expand user directory
                path = os.path.expanduser(path)
                
                # Validate path
                if not os.path.exists(path):
                    print('Error: Path does not exist')
                    continue
                
                if is_file:
                    if not os.path.isfile(path):
                        print('Error: Not a file')
                        continue
                    if not path.lower().endswith(('.jpg', '.jpeg', '.png')):
                        print('Error: Not an image file (must be jpg/jpeg/png)')
                        continue
                else:
                    if not os.path.isdir(path):
                        print('Error: Not a directory')
                        continue
                
                # Path is valid
                break
                
            except (KeyboardInterrupt, EOFError):
                print('\nOperation cancelled')
                return None
        
        # Convert to absolute path
        return str(Path(path).resolve())
        
    except (KeyboardInterrupt, EOFError):
        print('\nOperation cancelled')
        return None

def prompt_album_update(album_id: str) -> Optional[Dict[str, Any]]:
    """Interactive prompt for updating album metadata."""
    # Load album data
    album = get_album(album_id)
    if not album:
        print(f"Album not found: {album_id}")
        return None
    
    # Show current values and prompt for updates
    print("\nCurrent album details:")
    print(f"Title: {album['title']}")
    print(f"Date: {album['date']}")
    print(f"Description: {album['description']}")
    print(f"Cover Image: {album['coverImage']['webp']}")
    print(f"Favorite: {album.get('favorite', False)}")
    print("\nLeave fields empty to keep current values")
    
    questions = [
        inquirer.Text('title',
                     message="New title",
                     default=''),
        inquirer.Text('date',
                     message="New date (YYYY-MM-DD)",
                     validate=lambda _, x: not x or validate_date(x),
                     default=''),
        inquirer.Text('description',
                     message="New description",
                     default=''),
        inquirer.List('favorite',
                     message="Favorite status",
                     choices=[
                         ('No change', None),
                         ('Mark as favorite', True),
                         ('Remove favorite status', False)
                     ]),
    ]
    
    # First get basic updates
    answers = inquirer.prompt(questions, theme=GreenPassion())
    if not answers:
        return None
    
    # Remove empty values and handle favorite status
    updates = {k: v for k, v in answers.items() if v is not None and v != ''}
    
    # Handle favorite status separately since it can be a boolean False
    if answers['favorite'] is not None:
        updates['favorite'] = answers['favorite']
    
    # Handle cover image selection if there are images
    if album['images']:
        cover_questions = [
            inquirer.List('change_cover',
                         message="Change cover image?",
                         choices=[
                             ('Keep current cover', False),
                             ('Select new cover', True)
                         ])
        ]
        
        cover_choice = inquirer.prompt(cover_questions, theme=GreenPassion())
        if not cover_choice:
            return None
            
        if cover_choice['change_cover']:
            choices = [(img['id'], img['id']) for img in album['images']]
            image_questions = [
                inquirer.List('cover_image',
                            message="Select new cover image",
                            choices=choices)
            ]
            
            cover_answer = inquirer.prompt(image_questions, theme=GreenPassion())
            if cover_answer:
                updates['cover_image'] = cover_answer['cover_image']
    
    # Confirm changes
    if not updates:
        print("No changes requested.")
        return None
    
    print("\nRequested changes:")
    for key, value in updates.items():
        print(f"{key}: {value}")
    
    confirm = confirm_action("Apply these changes?")
    if not confirm:
        print("Update cancelled.")
        return None
    
    return updates

def prompt_album_selection(message: str = "Select an album") -> Optional[str]:
    """Prompt user to select an album.
    
    Args:
        message: Custom message for the prompt
        
    Returns:
        Selected album ID or None if cancelled
    """
    # Load albums data
    albums = load_albums()
    if not albums:
        print("No albums found.")
        return None
    
    # Create choices list
    choices = []
    for album in albums:
        album_id = album['id']
        title = album['title']
        date = album['date']
        choices.append((f"{title} ({album_id}) - {date}", album_id))
    
    # Sort choices by date (newest first)
    choices.sort(key=lambda x: x[0].split(" - ")[1], reverse=True)
    
    questions = [
        inquirer.List('album_id',
                     message=message,
                     choices=choices)
    ]
    
    answers = inquirer.prompt(questions, theme=GreenPassion())
    if not answers:
        return None
    
    return answers['album_id']

def prompt_operation() -> Optional[str]:
    """Prompt user to select an operation."""
    questions = [
        inquirer.List('operation',
                     message="What would you like to do?",
                     choices=[
                         ('Create new album', 'create'),
                         ('Update existing album', 'update'),
                         ('Delete album', 'delete'),
                         ('Add images to album', 'add-images'),
                         ('Remove images from album', 'remove-images'),
                         ('Exit', 'exit')
                     ])
    ]
    
    answers = inquirer.prompt(questions, theme=GreenPassion())
    if not answers or answers['operation'] == 'exit':
        return None
    
    return answers['operation']

def validate_date(date_str: str) -> bool:
    """Validate date string format."""
    try:
        datetime.strptime(date_str, '%Y-%m-%d')
        return True
    except ValueError:
        return False

def confirm_action(message: str) -> bool:
    """Prompt for confirmation."""
    questions = [
        inquirer.Confirm('confirm',
                        message=message,
                        default=False)
    ]
    answers = inquirer.prompt(questions, theme=GreenPassion())
    return answers.get('confirm', False)

def load_albums() -> List[Dict]:
    """Load albums from albums.json."""
    if not ALBUMS_JSON.exists():
        return []
    with open(ALBUMS_JSON, 'r') as f:
        return json.load(f)['albums']

def get_album(album_id: str) -> Optional[Dict]:
    """Get album by ID."""
    albums = load_albums()
    return next((a for a in albums if a['id'] == album_id), None)
