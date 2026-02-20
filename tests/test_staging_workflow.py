import unittest
import unittest.mock
import shutil
import json
import os
from pathlib import Path
import sys

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Mock pillow_heif if not installed (only needed for HEIC support in CI/local dev)
if 'pillow_heif' not in sys.modules:
    sys.modules['pillow_heif'] = unittest.mock.MagicMock()

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

class TestCoverIndexResolution(unittest.TestCase):
    """Test cover_index resolution logic in process_staging_album."""

    def setUp(self):
        self.test_id = "test-cover-index"
        self.staging_dir = BASE_DIR / 'staging' / self.test_id
        self.albums_dir = BASE_DIR / 'albums' / self.test_id

        for d in [self.staging_dir, self.albums_dir]:
            if d.exists():
                shutil.rmtree(d)

        self.staging_dir.mkdir(parents=True)

        # Create dummy images with known names (alphabetical order: aaa, bbb, ccc)
        from PIL import Image
        for name in ['bbb.jpg', 'aaa.jpg', 'ccc.jpg']:
            img = Image.new('RGB', (100, 100), color='red')
            img.save(self.staging_dir / name)

    def tearDown(self):
        for d in [self.staging_dir, self.albums_dir]:
            if d.exists():
                shutil.rmtree(d)
        if ALBUMS_JSON.exists():
            with open(ALBUMS_JSON, 'r') as f:
                data = json.load(f)
            data['albums'] = [a for a in data['albums'] if a['id'] != self.test_id]
            with open(ALBUMS_JSON, 'w') as f:
                json.dump(data, f, indent=2)

    def test_cover_index_resolves_to_sorted_filename(self):
        """cover_index=2 should resolve to the 2nd image alphabetically."""
        metadata = {
            "title": "Cover Index Test",
            "date": "2025-01-01",
            "cover_index": 2
        }
        with open(self.staging_dir / 'metadata.json', 'w') as f:
            json.dump(metadata, f)

        result = process_staging_album(self.staging_dir)
        self.assertTrue(result)

        # The album should have been created with cover = 'bbb' (2nd alphabetically: aaa, bbb, ccc)
        album_json = self.albums_dir / 'album.json'
        self.assertTrue(album_json.exists())
        with open(album_json) as f:
            album = json.load(f)
        self.assertEqual(album['coverImage']['webp'], 'images/grid/bbb.webp')

    def test_cover_image_takes_precedence_over_cover_index(self):
        """Explicit cover_image should be used even if cover_index is also set."""
        metadata = {
            "title": "Cover Precedence Test",
            "date": "2025-01-01",
            "cover_image": "ccc",
            "cover_index": 1
        }
        with open(self.staging_dir / 'metadata.json', 'w') as f:
            json.dump(metadata, f)

        result = process_staging_album(self.staging_dir)
        self.assertTrue(result)

        album_json = self.albums_dir / 'album.json'
        with open(album_json) as f:
            album = json.load(f)
        self.assertEqual(album['coverImage']['webp'], 'images/grid/ccc.webp')

    def test_cover_index_out_of_range_falls_back(self):
        """Out-of-range cover_index should not crash, falls back to default."""
        metadata = {
            "title": "Out of Range Test",
            "date": "2025-01-01",
            "cover_index": 99
        }
        with open(self.staging_dir / 'metadata.json', 'w') as f:
            json.dump(metadata, f)

        result = process_staging_album(self.staging_dir)
        self.assertTrue(result)
        # Should still create album (with default first-image cover)
        self.assertTrue(self.albums_dir.exists())


if __name__ == '__main__':
    unittest.main()
