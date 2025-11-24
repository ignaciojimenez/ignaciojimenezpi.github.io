import unittest
import shutil
import json
import os
from pathlib import Path
import sys

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from photography.utils.process_staging import process_staging_album
from photography.utils.config import BASE_DIR, ALBUMS_JSON

class TestStagingWorkflow(unittest.TestCase):
    def setUp(self):
        self.test_id = "test-staging-album"
        self.staging_dir = BASE_DIR / 'staging' / self.test_id
        self.albums_dir = BASE_DIR / 'albums' / self.test_id
        
        # Clean up any previous test runs
        if self.staging_dir.exists():
            shutil.rmtree(self.staging_dir)
        if self.albums_dir.exists():
            shutil.rmtree(self.albums_dir)
            
        # Create staging directory
        self.staging_dir.mkdir(parents=True)
        
        # Create metadata.json
        self.metadata = {
            "title": "Test Staging Album",
            "date": "2025-01-01",
            "description": "Created via test script",
            "favorite": False
        }
        with open(self.staging_dir / 'metadata.json', 'w') as f:
            json.dump(self.metadata, f)
            
        # Create a dummy image
        # We need a real image for PIL to process it, or mock PIL.
        # Let's try to find a real image in the repo to copy
        source_images = list((BASE_DIR / 'photography' / 'albums').glob('**/*.jpg'))
        if source_images:
            shutil.copy(source_images[0], self.staging_dir / 'test_image.jpg')
        else:
            # Create a simple RGB image if no images found
            from PIL import Image
            img = Image.new('RGB', (100, 100), color = 'red')
            img.save(self.staging_dir / 'test_image.jpg')

    def tearDown(self):
        # Clean up
        if self.staging_dir.exists():
            shutil.rmtree(self.staging_dir)
        if self.albums_dir.exists():
            shutil.rmtree(self.albums_dir)
            
        # Remove from albums.json
        if ALBUMS_JSON.exists():
            with open(ALBUMS_JSON, 'r') as f:
                data = json.load(f)
            data['albums'] = [a for a in data['albums'] if a['id'] != self.test_id]
            with open(ALBUMS_JSON, 'w') as f:
                json.dump(data, f, indent=2)

    def test_process_staging(self):
        # Run the processing
        result = process_staging_album(self.staging_dir)
        
        self.assertTrue(result, "Processing should return True")
        self.assertFalse(self.staging_dir.exists(), "Staging directory should be removed")
        self.assertTrue(self.albums_dir.exists(), "Album directory should be created")
        self.assertTrue((self.albums_dir / 'index.html').exists(), "index.html should be created")
        
        # Verify albums.json
        with open(ALBUMS_JSON, 'r') as f:
            data = json.load(f)
        album = next((a for a in data['albums'] if a['id'] == self.test_id), None)
        self.assertIsNotNone(album, "Album should be in albums.json")
        self.assertEqual(album['title'], self.metadata['title'])

if __name__ == '__main__':
    unittest.main()
