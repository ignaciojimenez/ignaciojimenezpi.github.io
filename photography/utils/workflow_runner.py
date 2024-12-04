#!/usr/bin/env python3

import sys
import os

# Add the parent directory to Python path to make the utils package importable
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.create_album import create_album

if __name__ == '__main__':
    create_album(
        album_name=sys.argv[1],
        title=sys.argv[2],
        description=sys.argv[3],
        date=sys.argv[4],
        image_dir=sys.argv[5],
        cover_image=sys.argv[6] if len(sys.argv) > 6 else None
    )
