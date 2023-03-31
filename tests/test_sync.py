import os
import shutil
import tempfile
import unittest
from unittest.mock import patch, MagicMock
import logging
from io import StringIO
from datetime import datetime, timedelta
from typing import List

from sync import sync, read_dir, remove_files, remove_empty_folders


class TestSync(unittest.TestCase):
    def setUp(self):
        # Create mock logs
        self.mock_logger = MagicMock(spec=logging.Logger)
        self.patcher_log_debug = patch('logging.debug', self.mock_logger.debug)
        self.addCleanup(self.patcher_log_debug.stop)
        self.patcher_log_debug.start()
        # Create mock std output
        self.stdout = StringIO()
        self.patcher_stdout = patch('sys.stdout', self.stdout)
        self.addCleanup(self.patcher_stdout.stop)
        self.patcher_stdout.start()

        # Create a temporary directory for testing
        self.temp_dir = tempfile.mkdtemp()
        os.makedirs(os.path.join(self.temp_dir, 'subdir'))
        os.makedirs(os.path.join(self.temp_dir, 'subdir2'))

        # Create some files to use as test data
        self.files = [
            os.path.join(self.temp_dir, 'file1.txt'),
            os.path.join(self.temp_dir, 'file2.txt'),
            os.path.join(self.temp_dir, 'subdir', 'file3.txt'),
            os.path.join(self.temp_dir, 'subdir', 'file4.txt'),
            os.path.join(self.temp_dir, 'subdir2', 'file5.txt')
        ]

        for file in self.files:
            with open(file, 'w') as f:
                f.write('Test data')

        # Set up a destination directory
        self.dest_dir = tempfile.mkdtemp()

    def tearDown(self):
        # Remove the temporary directories and files
        shutil.rmtree(self.temp_dir)
        shutil.rmtree(self.dest_dir)

    def create_file(self, filename: str, content: str) -> str:
        file_path = os.path.join(self.temp_dir, filename)
        with open(file_path, 'w') as f:
            f.write(content)
        return file_path

    def test_sync_creates_dest_dir_if_not_exists(self):
        # Remove the destination directory to simulate it not existing
        shutil.rmtree(self.dest_dir)

        # Call the sync function and assert that the destination directory is created
        synced_files = sync(self.temp_dir, self.dest_dir)
        self.assertTrue(os.path.exists(self.dest_dir))

        # Assert that the files are synced
        for file in self.files:
            dest_file = os.path.join(
                self.dest_dir, os.path.relpath(file, self.temp_dir))
            self.assertTrue(os.path.exists(dest_file))
            self.assertTrue(dest_file in synced_files)

    def test_sync_copies_files_to_dest_dir(self):
        # Call the sync function and assert that the files are copied to the destination directory
        synced_files = sync(self.temp_dir, self.dest_dir)
        for file in self.files:
            dest_file = os.path.join(
                self.dest_dir, os.path.relpath(file, self.temp_dir))
            self.assertTrue(os.path.exists(dest_file))
            self.assertTrue(dest_file in synced_files)

    def test_sync_updates_existing_files(self):
        # Create a file in the destination directory with the same name as file1
        dest_file1 = os.path.join(
            self.dest_dir, os.path.basename(self.files[0]))
        with open(dest_file1, 'w') as f:
            f.write('Old data')

        # Set the modification time of file1 to be older than the destination file
        mod_time = datetime.now() - timedelta(days=1)
        os.utime(self.files[0], (mod_time.timestamp(), mod_time.timestamp()))

        # Call the sync function and assert that the file is updated in the destination directory
        synced_files = sync(self.temp_dir, self.dest_dir)
        with open(dest_file1, 'r') as f:
            data = f.read()
        self.assertEqual(data, 'Test data')
        self.assertTrue(dest_file1 in synced_files)


class TestReadDir(unittest.TestCase):
    def test_read_dir_returns_list_of_files(self):
        # Create a temporary directory and some files inside it
        with tempfile.TemporaryDirectory() as tempdir:
            file1 = os.path.join(tempdir, 'file1.txt')
            with open(file1, 'w') as f:
                f.write('hello')
            file2 = os.path.join(tempdir, 'file2.txt')
            with open(file2, 'w') as f:
                f.write('world')

            # Call the read_dir() function on the temporary directory
            files = read_dir(tempdir)

            # Check that the function returns a list of the two files
            self.assertIsInstance(files, List)
            self.assertEqual(len(files), 2)
            self.assertIn(file1, files)
            self.assertIn(file2, files)

    def test_read_dir_returns_empty_list_if_dir_does_not_exist(self):
        # Call the read_dir() function on a non-existent directory
        files = read_dir('nonexistent_dir')

        # Check that the function returns an empty list
        self.assertIsInstance(files, List)
        self.assertEqual(len(files), 0)

    def test_read_dir_returns_empty_list_if_dir_is_empty(self):
        # Create a temporary directory with no files
        with tempfile.TemporaryDirectory() as tempdir:
            # Call the read_dir() function on the temporary directory
            files = read_dir(tempdir)

            # Check that the function returns an empty list
            self.assertIsInstance(files, List)
            self.assertEqual(len(files), 0)


class TestRemoveFiles(unittest.TestCase):
    def setUp(self):
        # Create a temporary directory and some files to test with
        self.temp_dir = tempfile.mkdtemp()
        self.file1 = os.path.join(self.temp_dir, "file1.txt")
        self.file2 = os.path.join(self.temp_dir, "file2.txt")
        with open(self.file1, "w") as f:
            f.write("test")
        with open(self.file2, "w") as f:
            f.write("test")
        # Create mock logs
        self.mock_logger = MagicMock(spec=logging.Logger)
        # Mock Debug log
        self.patcher_log_debug = patch('logging.debug', self.mock_logger.debug)
        self.addCleanup(self.patcher_log_debug.stop)
        self.patcher_log_debug.start()
        # Mock Error log
        self.patcher_log_error = patch('logging.error', self.mock_logger.error)
        self.addCleanup(self.patcher_log_error.stop)
        self.patcher_log_error.start()
        # Create mock std output
        self.stdout = StringIO()
        self.patcher_stdout = patch('sys.stdout', self.stdout)
        self.addCleanup(self.patcher_stdout.stop)
        self.patcher_stdout.start()

    def tearDown(self):
        # Remove the temporary directory and its contents
        for root, _, files in os.walk(self.temp_dir, topdown=False):
            for name in files:
                os.remove(os.path.join(root, name))
            os.rmdir(root)

    def test_remove_files(self):
        # Check that both files are present before removal
        self.assertTrue(os.path.exists(self.file1))
        self.assertTrue(os.path.exists(self.file2))

        # Remove the files
        remove_files([self.file1, self.file2])

        # Check that both files have been removed
        self.assertFalse(os.path.exists(self.file1))
        self.assertFalse(os.path.exists(self.file2))

    def test_remove_files_missing_files(self):
        # Check that a missing file does not cause an error
        missing_file = os.path.join(self.temp_dir, "missing.txt")
        remove_files([missing_file, self.file1])

        # Check that only the existing file has been removed
        self.assertFalse(os.path.exists(self.file1))
        self.assertTrue(os.path.exists(self.file2))

    def test_remove_files_empty_list(self):
        # Check that passing an empty list does not cause an error
        remove_files([])


class TestRemoveEmptyFolders(unittest.TestCase):
    def setUp(self):
        # Create mock logs
        self.mock_logger = MagicMock(spec=logging.Logger)
        self.patcher_log_debug = patch('logging.debug', self.mock_logger.debug)
        self.addCleanup(self.patcher_log_debug.stop)
        self.patcher_log_debug.start()
        # Create mock std output
        self.stdout = StringIO()
        self.patcher_stdout = patch('sys.stdout', self.stdout)
        self.addCleanup(self.patcher_stdout.stop)
        self.patcher_stdout.start()

    def test_remove_empty_folders(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create test directories
            os.makedirs(os.path.join(temp_dir, 'dir1', 'dir2', 'dir3'))
            os.makedirs(os.path.join(temp_dir, 'dir1', 'dir2', 'dir4'))
            os.makedirs(os.path.join(temp_dir, 'dir5'))

            # Create test files
            with open(os.path.join(temp_dir, 'dir1', 'file1.txt'), 'w') as f:
                f.write('test')
            with open(os.path.join(temp_dir, 'dir1', 'dir2', 'file2.txt'), 'w') as f:
                f.write('test')
            with open(os.path.join(temp_dir, 'dir1', 'dir2', 'dir3', 'file3.txt'), 'w') as f:
                f.write('test')

            # Remove empty directories
            remove_empty_folders(temp_dir)

            # Check if empty directories have been removed
            self.assertTrue(os.path.exists(
                os.path.join(temp_dir, 'dir1', 'dir2', 'dir3')))
            self.assertFalse(os.path.exists(
                os.path.join(temp_dir, 'dir1', 'dir2', 'dir4')))
            self.assertFalse(os.path.exists(os.path.join(temp_dir, 'dir5')))


if __name__ == '__main__':
    unittest.main()
