from unittest import TestCase
import os
import pathlib
from ..controller import create_folder, remove_folder, create_new_pool, Result
from ..ui import ViewportMode


class TestCore(TestCase):
    def test_create_folder_returns_result(self):
        path = os.path.join(pathlib.Path.home(), "Desktop", "Testing")
        self.assertIsInstance(create_folder(path), Result)

    def test_create_folder_on_invalid_path(self):
        path = "~//luhfklhflwkf"
        self.assertEqual(create_folder(path), Result.Fail)

        path = None
        self.assertEqual(create_folder(path), Result.Fail)

    def test_remove_folder_returns_result(self):
        path = os.path.join(pathlib.Path.home(), "Desktop", "Testing")
        self.assertIsInstance(remove_folder(path), Result)

    def test_remove_folder_on_invalid_path(self):
        path = "~//luhfklhflwkf"
        self.assertEqual(remove_folder(path), Result.Unchanged)

        path = None
        self.assertEqual(remove_folder(path), Result.Fail)

    def test_create_new_pool_materials(self):
        path = os.path.join(pathlib.Path.home(), "Desktop")

        create_new_pool(path, ViewportMode.Materials)
        self.assertTrue(os.path.exists(os.path.join(path, "MaterialPool")))
        self.assertTrue(os.path.exists(os.path.join(path, "MaterialPool", "Materials")))
        self.assertTrue(
            os.path.exists(os.path.join(path, "MaterialPool", "Thumbnails"))
        )
        self.assertTrue(os.path.exists(os.path.join(path, "MaterialPool", "Textures")))

        remove_folder(path)
