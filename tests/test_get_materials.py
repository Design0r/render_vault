import unittest
from pathlib import Path
import shutil
import tempfile
from ..controller import get_materials_and_thumbnails


class TestGetMaterialsAndThumbnails(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.pool_path = Path(self.test_dir) / "MaterialPool"
        self.material_path = self.pool_path / "Materials"
        self.thumbnail_path = self.pool_path / "Thumbnails"

        self.material_path.mkdir(parents=True)
        self.thumbnail_path.mkdir(parents=True)

        self.material_names = ["material1", "material2"]
        self.thumbnail_names = ["material1.png", "material2.jpg"]

        for material in self.material_names:
            (self.material_path / f"{material}.mb").touch()
        for thumbnail in self.thumbnail_names:
            (self.thumbnail_path / thumbnail).touch()

    def tearDown(self):
        print(self.test_dir)
        # shutil.rmtree(self.test_dir)

    def test_get_materials_and_thumbnails(self):
        expected_results = [
            ("material1", str(self.thumbnail_path / "material1.png")),
            ("material2", str(self.thumbnail_path / "material2.jpg")),
        ]
        results = list(get_materials_and_thumbnails(self.test_dir))
        self.assertEqual(results, expected_results)
