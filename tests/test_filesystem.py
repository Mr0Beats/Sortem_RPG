import unittest
import os
from unittest.mock import MagicMock
from cli.filesystem import FileManager, DirectoryState, FileViewState
from infra.io import IDisplay

class TestFileSystem(unittest.TestCase):
    def setUp(self):
        self.mock_display = MagicMock(spec=IDisplay)
        self.manager = FileManager(self.mock_display)

    def test_initial_state(self):
        self.assertIsInstance(self.manager.current_state, DirectoryState)

    def test_cd_command(self):
        initial_path = self.manager.current_state.current_path
        
        self.manager.current_state.router.handle("cd", [".."])
        
        new_path = self.manager.current_state.current_path
        self.assertNotEqual(initial_path, new_path)

    def test_open_file_transition(self):
        test_file = "test_temp.txt"
        with open(test_file, "w") as f:
            f.write("test content")

        try:
            self.manager.current_state.router.handle("open", [test_file])
            self.assertIsInstance(self.manager.current_state, FileViewState)
            self.assertEqual(self.manager.current_state.filepath, os.path.join(os.getcwd(), test_file))
        finally:
            if os.path.exists(test_file):
                os.remove(test_file)

if __name__ == '__main__':
    unittest.main()