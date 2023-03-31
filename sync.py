"""
Performs one-way syncing between source and destination directories,
Also removes empty folders and files that are not in the source directory 
from the destination directory

Usage:
    ./sync.py <source-directory> <destination-directory>
    Full deescription on parameters is accessibile by calling help:
    ./sync.py -h

"""

import logging
import os
from shutil import copy2, rmtree
from argparse import ArgumentParser
from time import sleep
from hashlib import sha256
from typing import Final, List

DEFAULT_INTERVAL: Final[int] = 15
DEFAULT_LOG_PATH: Final[str] = 'output.log'


def view_message(msg: str, log_level: str = 'debug') -> None:
    """
    Prints message to standard output and to the log
    Args:
        msg (str): Message to display.
        log_level (str): Type of log level ('debug' or 'error'). Default value is 'debug'
    Returns:
        Nothing
    """
    if log_level == 'error':
        logging.error(msg)
    else:
        logging.debug(msg)
    print(msg)


def sync(source_dir: str, dest_dir: str) -> List[str]:
    """
    Synchronize the files in a source directory with a destination directory.

    Args:
        source_dir (str): The path to the source directory.
        dest_dir (str): The path to the destination directory.

    Returns:
        List[str]: A list of paths to the files that were synchronized.
    """
    if not os.path.exists(dest_dir):
        view_message(f'Destination created {dest_dir}')
        os.mkdir(dest_dir)

    synced_files = []
    for root, _, files in os.walk(source_dir):
        # Get the relative path of the current directory
        rel_path = os.path.normpath(os.path.relpath(root, source_dir))
        # Create the corresponding directory in the destination directory
        dest_path = os.path.normpath(os.path.join(dest_dir, rel_path))

        if not os.path.exists(dest_path):
            view_message(f'Destination created {dest_path}')
            os.mkdir(dest_path)
        # Copy all the files in the current directory to the destination directory
        for file in files:
            src_file = os.path.join(root, file)
            dest_file = os.path.join(dest_path, file)
            if not os.path.exists(dest_file):
                view_message(f'{dest_file} created')
                copy2(src_file, dest_file)

            if is_updated(src_file, dest_file):
                view_message(f'{dest_file} updated')
                copy2(src_file, dest_file)

            synced_files.append(dest_file)

    return synced_files


def read_dir(directory: str) -> List[str]:
    """
    Recursively read all files in a directory and return a list of their paths.

    Args:
        directory (str): The path to the directory to read.

    Returns:
        List[str]: A list of paths to the files in the directory.
    """
    file_list = []
    for root, _, files in os.walk(directory):
        for file in files:
            file_list.append(os.path.normpath(os.path.join(root, file)))
    return file_list


def remove_files(files: List[str]) -> None:
    """
    Remove all files in a list of paths.

    Args:
        files (List[str]): A list of paths to the files to remove.

    Returns:
        Nothing
    """
    for file in files:
        try:
            os.remove(file)
            view_message(f'{file} removed')
        except OSError as error:
            view_message(f'Error: {error.filename} - {error.strerror}',
                         log_level='error')


def remove_empty_folders(root_dir: str) -> None:
    """
    Recursively remove all empty subdirectories of a directory.

    Args:
        root_dir (str): The path to the directory to remove empty subdirectories from.

    Returns:
        Nothing
    """
    # Get list of directories sorted by the length of subdirectories skipping the root folder
    listed_dirs = sorted(list(os.walk(root_dir))[1:],
                         key=lambda x: x[0].split(os.path.sep),
                         reverse=True)
    unique_dirs = list(dict.fromkeys(
        [os.path.normpath(listed_dir[0]) for listed_dir in listed_dirs]))
    for unique_dir in unique_dirs:
        if len(os.listdir(unique_dir)) == 0:
            view_message(f'Empty directory "{unique_dir}" was removed')
            rmtree(unique_dir)


def get_checksum(file: str) -> int:
    """
    Calculate the SHA-256 checksum of a file.

    Args:
        file (str): The path to the file to calculate the checksum of.

    Returns:
        int: The SHA-256 checksum of the file as an integer.
    """
    with open(file, 'rb') as file_data:
        return int(sha256(file_data.read()).hexdigest(), 16)


def is_updated(src_file: str, dest_file: str) -> bool:
    """
    Determine whether a source file is more recent than a destination file.

    Args:
        src_file (str): The path to the source file to compare.
        dest_file (str): The path to the destination file to compare.

    Returns:
        bool: True if the source file is more recent than the destination file, False otherwise.
    """
    return get_checksum(src_file) != get_checksum(dest_file)


if __name__ == '__main__':
    # Define command-line arguments
    parser = ArgumentParser(
        description='Periodically synchronize data between source and destination directories.')
    parser.add_argument('src_dir', metavar='<source>', type=str,
                        help='The path to the source directory')
    parser.add_argument('dst_dir', metavar='<destination>', type=str,
                        help='The path to the destination directory')
    parser.add_argument('-i', '--interval', metavar='<interval>', type=int, default=DEFAULT_INTERVAL,
                        help=f'The synchronization interval in seconds. Default value is {DEFAULT_INTERVAL}')
    parser.add_argument('-l', '--log_path', metavar='<log-path>', type=str, default=DEFAULT_LOG_PATH,
                        help=f'The log path for log. Default value is {DEFAULT_LOG_PATH}')
    # Parse command-line arguments
    args = parser.parse_args()

    # Logging setup with customized format, date and file
    logging.basicConfig(format='%(levelname)s,%(asctime)s,%(message)s',
                        datefmt='%d.%m.%Y-%H:%M:%S',
                        filename=args.log_path,
                        level=logging.DEBUG)

    view_message(f'Syncing between {args.src_dir} and {args.dst_dir}')
    view_message(f'Interval set to {args.interval} seconds')
    view_message(f'Logs being saved to {args.log_path}')

    while True:
        view_message('Syncing...')
        synced_dirs = sync(args.src_dir, args.dst_dir)
        if len(synced_dirs) > 0:
            destination_map = read_dir(args.dst_dir)
            files_to_remove = [
                f for f in destination_map if f not in synced_dirs]
            remove_files(files_to_remove)
            remove_empty_folders(args.dst_dir)
        else:
            view_message('No changes detected')
        view_message('Syncing completed')

        sleep(args.interval)
