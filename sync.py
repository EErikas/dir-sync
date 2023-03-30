import argparse
import shutil
import os
from time import time, sleep
from hashlib import sha256
from typing import Final

DEFAULT_INTERVAL: Final[int] = 15
# Define command-line arguments
parser = argparse.ArgumentParser(
    description='Periodically synchronize data between source and destination directories.')
parser.add_argument('src_dir', metavar='<source>', type=str,
                    help='the path to the source directory')
parser.add_argument('dst_dir', metavar='<destination>', type=str,
                    help='the path to the destination directory')
parser.add_argument('--interval', metavar='<interval>', type=int, default=DEFAULT_INTERVAL,
                    help=f'The synchronization interval in seconds. Default value is {DEFAULT_INTERVAL}')
# Parse command-line arguments
args = parser.parse_args()

# Define the source and destination directories and synchronization interval
src_dir = args.src_dir
dst_dir = args.dst_dir
interval = args.interval

# Keep track of the last synchronization time and the checksums of the source files
last_sync_time = time()
src_checksums = {}

while True:
    # Check if the synchronization interval has elapsed
    current_time = time()
    elapsed_time = current_time - last_sync_time
    if elapsed_time >= interval:
        # Synchronize the files from the source to the destination
        for file_name in os.listdir(src_dir):
            src_path = os.path.join(src_dir, file_name)
            dst_path = os.path.join(dst_dir, file_name)
            # Calculate the checksum of the source file
            with open(src_path, 'rb') as f:
                src_checksum = sha256(f.read()).hexdigest()
            # Check if the source file has changed since the last synchronization
            if file_name not in src_checksums or src_checksum != src_checksums[file_name]:
                shutil.copy(src_path, dst_path)
                # Update the checksum of the source file
                src_checksums[file_name] = src_checksum

        # Update the last synchronization time
        last_sync_time = current_time

    # Wait for the synchronization interval
    sleep(10)
