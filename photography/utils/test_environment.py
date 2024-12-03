#!/usr/bin/env python3
"""Test script to verify the album creation environment."""

import os
import sys
from pathlib import Path

def test_imports():
    """Test that all required packages are available."""
    try:
        from PIL import Image
        import jsonschema
        print("✓ All required packages are installed")
    except ImportError as e:
        print(f"✗ Import error: {e}")
        sys.exit(1)

def test_paths():
    """Test that all required paths exist."""
    required_paths = [
        'utils/config.py',
        'utils/validation.py',
        'utils/image_processor.py',
        'albums'
    ]
    
    base_path = Path(__file__).parent.parent
    
    for path in required_paths:
        full_path = base_path / path
        if full_path.exists():
            print(f"✓ Found {path}")
        else:
            print(f"✗ Missing {path}")
            sys.exit(1)

def test_permissions():
    """Test write permissions in albums directory."""
    try:
        base_path = Path(__file__).parent.parent
        test_path = base_path / 'albums' / '.test_write'
        test_path.touch()
        test_path.unlink()
        print("✓ Album directory is writable")
    except Exception as e:
        print(f"✗ Permission error: {e}")
        sys.exit(1)

def main():
    """Run all environment tests."""
    print("\nTesting Album Creation Environment\n" + "="*30)
    
    print("\n1. Testing imports:")
    test_imports()
    
    print("\n2. Testing paths:")
    test_paths()
    
    print("\n3. Testing permissions:")
    test_permissions()
    
    print("\n✓ All tests passed successfully!")

if __name__ == "__main__":
    main()
