#!/usr/bin/env python3
"""Command-line interface for album management."""

import sys
import logging
import argparse
from pathlib import Path
from datetime import datetime

from album_manager import AlbumManager
from interactive import (
    prompt_album_creation, prompt_album_deletion,
    prompt_image_deletion, prompt_image_addition,
    prompt_album_update, prompt_operation,
    prompt_album_selection
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

def validate_date(date_str: str) -> bool:
    """Validate date string format."""
    try:
        datetime.strptime(date_str, '%Y-%m-%d')
        return True
    except ValueError:
        return False

def validate_image_path(path_str: str) -> bool:
    """Validate image path exists."""
    path = Path(path_str).expanduser()
    return path.exists()

def main() -> bool:
    """Main function."""
    parser = argparse.ArgumentParser(
        description='Album management for photography portfolio'
    )
    
    # Create subparsers for different commands
    subparsers = parser.add_subparsers(dest='command', help='Commands')
    
    # Common arguments
    common_parser = argparse.ArgumentParser(add_help=False)
    common_parser.add_argument('--interactive', '-i', action='store_true',
                           help='Run in interactive mode')
    common_parser.add_argument('--yes', '-y', action='store_true',
                           help='Skip confirmation prompts')
    
    # Create command
    create_parser = subparsers.add_parser('create', help='Create a new album',
                                      parents=[common_parser])
    create_parser.add_argument('--album-name', '-n', 
                           help='Album name (ID)')
    create_parser.add_argument('--title', '-t',
                           help='Album title')
    create_parser.add_argument('--date', '-d',
                           help='Album date (YYYY-MM-DD)')
    create_parser.add_argument('--description',
                           help='Album description')
    create_parser.add_argument('--image-dir',
                           help='Directory containing images')
    create_parser.add_argument('--cover-image',
                           help='Cover image file')
    create_parser.add_argument('--favorite', action='store_true',
                           help='Mark album as favorite (will always appear first in gallery)')
    
    # Delete album command
    delete_parser = subparsers.add_parser('delete', help='Delete an album',
                                      parents=[common_parser])
    delete_parser.add_argument('--album-name', '-n', 
                           help='Album name (ID) to delete')
    
    # Update album command
    update_parser = subparsers.add_parser('update', help='Update album metadata',
                                      parents=[common_parser])
    update_parser.add_argument('--album-name', '-n', 
                           help='Album name (ID)')
    update_parser.add_argument('--title', '-t',
                           help='New album title')
    update_parser.add_argument('--date', '-d',
                           help='New album date (YYYY-MM-DD)')
    update_parser.add_argument('--description',
                           help='New album description')
    update_parser.add_argument('--cover-image',
                           help='New cover image ID')
    
    # Add images command
    add_parser = subparsers.add_parser('add-images', help='Add images to an album',
                                   parents=[common_parser])
    add_parser.add_argument('--album-name', '-n', 
                         help='Album name (ID)')
    add_parser.add_argument('--image-paths', nargs='+',
                         help='One or more paths to image files or directories')
    
    # Delete images command
    remove_parser = subparsers.add_parser('remove-images', help='Remove images from an album',
                                      parents=[common_parser])
    remove_parser.add_argument('--album-name', '-n', 
                           help='Album name (ID)')
    remove_parser.add_argument('--image-ids', nargs='+',
                           help='One or more image IDs to remove')
    
    args = parser.parse_args()
    
    try:
        if not args.command:
            # Show operation selection menu
            operation = prompt_operation()
            if not operation:
                return True
                
            if operation in ['update', 'add-images', 'remove-images']:
                # For operations that need an album, prompt for selection first
                album_id = prompt_album_selection(f"Select album to {operation.replace('-', ' ')}")
                if not album_id:
                    return False
                sys.argv = [sys.argv[0], operation, '-i', '--album-name', album_id]
            else:
                # For other operations, just add interactive flag
                sys.argv = [sys.argv[0], operation, '-i']
            return main()
            
        album_manager = AlbumManager()
        
        if args.command == 'create':
            if args.interactive:
                params = prompt_album_creation()
                if not params:
                    return False
                return album_manager.create_album(
                    album_name=params['id'],
                    title=params['title'],
                    date=params['date'],
                    description=params['description'],
                    image_dir=params['image_dir'],
                    cover_image=params['cover_image'],
                    favorite=params['favorite']
                )
            else:
                # Validate arguments
                if not args.album_name:
                    logger.error("Album name is required")
                    return False
                if not args.title:
                    logger.error("Album title is required")
                    return False
                if not args.date:
                    logger.error("Album date is required")
                    return False
                if not validate_date(args.date):
                    logger.error(f"Invalid date format: {args.date}. Use YYYY-MM-DD")
                    return False
                
                image_dir = Path(args.image_dir).expanduser() if args.image_dir else None
                if image_dir and not image_dir.is_dir():
                    logger.error(f"Image directory does not exist: {args.image_dir}")
                    return False
                
                return album_manager.create_album(
                    album_name=args.album_name,
                    title=args.title,
                    date=args.date,
                    description=args.description or "",
                    image_dir=str(image_dir) if image_dir else None,
                    cover_image=args.cover_image,
                    favorite=args.favorite
                )
                
        elif args.command == 'delete':
            if args.interactive:
                album_id = prompt_album_deletion()
                if album_id:
                    return album_manager.delete_album(album_id)
                return False
            else:
                # Check if album exists
                if not args.album_name:
                    logger.error("Album name is required")
                    return False
                
                if not album_manager.get_album(args.album_name):
                    logger.error(f"Album not found: {args.album_name}")
                    return False
                
                # Confirm deletion unless --yes flag is used
                if not args.yes:
                    confirm = input(f"Are you sure you want to delete album '{args.album_name}'? [y/N] ")
                    if confirm.lower() != 'y':
                        return False
                
                return album_manager.delete_album(args.album_name)
            
        elif args.command == 'update':
            if args.interactive:
                updates = prompt_album_update(args.album_name)
                if updates:
                    return album_manager.update_album(args.album_name, **updates)
                return False
            else:
                # Check if album exists
                if not args.album_name:
                    logger.error("Album name is required")
                    return False
                
                if not album_manager.get_album(args.album_name):
                    logger.error(f"Album not found: {args.album_name}")
                    return False
                
                # Validate date if provided
                if args.date and not validate_date(args.date):
                    logger.error(f"Invalid date format: {args.date}. Use YYYY-MM-DD")
                    return False
                
                # Collect non-None updates
                updates = {}
                if args.title is not None:
                    updates['title'] = args.title
                if args.date is not None:
                    updates['date'] = args.date
                if args.description is not None:
                    updates['description'] = args.description
                if args.cover_image is not None:
                    updates['cover_image'] = args.cover_image
                
                if not updates:
                    logger.error("At least one update parameter is required")
                    return False
                
                return album_manager.update_album(args.album_name, **updates)
            
        elif args.command == 'add-images':
            if args.interactive:
                image_path = prompt_image_addition(args.album_name)
                if image_path:
                    return album_manager.add_images(args.album_name, image_path)
                return False
            else:
                # Check if album exists
                if not args.album_name:
                    logger.error("Album name is required")
                    return False
                
                if not album_manager.get_album(args.album_name):
                    logger.error(f"Album not found: {args.album_name}")
                    return False
                
                # Validate image paths
                valid_paths = []
                for path_str in args.image_paths:
                    path = Path(path_str).expanduser()
                    if not path.exists():
                        logger.error(f"Path does not exist: {path_str}")
                        return False
                    valid_paths.append(str(path))
                
                return album_manager.add_images(args.album_name, valid_paths)
            
        elif args.command == 'remove-images':
            if args.interactive:
                image_ids = prompt_image_deletion(args.album_name)
                if image_ids:
                    # Ensure image_ids is a list even if only one ID is returned
                    if isinstance(image_ids, str):
                        image_ids = [image_ids]
                    return album_manager.delete_images(args.album_name, image_ids)
                return False
            else:
                # Check if album exists
                album = album_manager.get_album(args.album_name)
                if not album:
                    logger.error(f"Album not found: {args.album_name}")
                    return False
                
                # Validate image IDs
                album_image_ids = {img['id'] for img in album['images']}
                invalid_ids = set(args.image_ids) - album_image_ids
                if invalid_ids:
                    logger.error(f"Invalid image IDs for album {args.album_name}: {', '.join(invalid_ids)}")
                    return False
                
                # Confirm deletion unless --yes flag is used
                if not args.yes:
                    confirm = input(f"Are you sure you want to remove {len(args.image_ids)} images from album '{args.album_name}'? [y/N] ")
                    if confirm.lower() != 'y':
                        return False
                
                return album_manager.delete_images(args.album_name, args.image_ids)
    
    except Exception as e:
        logger.error(f"Failed to {args.command}: {e}")
        return False

if __name__ == '__main__':
    sys.exit(0 if main() else 1)
