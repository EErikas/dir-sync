# File Sync Script
The script has been implemented using Python programming language and has been tested on machines running `Windows 11` and `Ubuntu 20.04` with `Python 3.10.10`.
## Usage
The script can be invoked by navigating to the project root:
```bash
python script.py /path/to/source /path/to/destination
```
Usage instructions can be accessed via the help menu with the following command:
```bash
python script.py -h
```
### Arguments
The script can be executed from the command line and accepts the following arguments:

* `src_dir` - the path to the source directory.
* `dst_dir` - the path to the destination directory.
* `-i` or `--interval` (optional) - the synchronization interval, in seconds. The default value is 15 seconds.
* `-l` or `--log-path` (optional) - log path. By default, the file is saved as `output.log` in the directory from which the script is called

## Testing 
To launch tests, navigate to the project root and enter the following command:
```
python -m unittest discover
```