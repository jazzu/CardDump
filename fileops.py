import os
import shutil

__author__ = 'jazzu'

DIR = 0
FILES = 1

files_total = 0
bytes_total = 0


def copy(src_file, dest_file, overwrite=False, block_size=32768):
    if not overwrite:
        if os.path.isfile(dest_file):
            raise IOError("File exists, not overwriting")

    # Open src and dest files, get src file size
    src = open(src_file, "rb")
    dest = open(dest_file, "wb")

    src_size = os.stat(src_file).st_size

    # Start copying file
    current_file_written = 0  # a running total of current position
    while True:
        cur_block = src.read(block_size)

        # If it's the end of file
        if not cur_block:
            break
        else:
            # ..if not, write the block and continue
            block_bytes_written = dest.write(cur_block)
            current_file_written = src.tell()
            print('file', src_size, current_file_written)
    # end while

    # Close files
    src.close()
    dest.close()

    shutil.copystat(src_file, dest_file)

    # Check output file is same size as input one!
    dest_size = os.stat(dest_file).st_size

    if dest_size != src_size:
        raise IOError(
            "New file-size does not match original (src: %s, dest: %s)" % (
            src_size, dest_size)
        )

    return src_size


def dump_card():
    # TODO: Bring source_dir and destination_dir in from the command line or environment
    source_dir = '/home/pi/test/source'
    destination_dir = '/home/pi/test/destination'
    copy_list = list()

    global files_total, bytes_total
    files_total = 0
    bytes_total = 0

    for root, dirs, files in os.walk(source_dir):
        copy_list.append((root, files))
        files_total += len(files)
        for f in files:
            bytes_total += os.stat(root + '/' + f).st_size

    for entry in copy_list:
        if entry[FILES]:
            for f in entry[FILES]:
                file_size = copy(entry[DIR] + '/' + f, destination_dir + '/' + f)
                print('total', bytes_total, file_size)
                # Just for reference:
                # OS level copy operation. Unusable if more fine grained progress is to be tracked
                # shutil.copy(entry[DIR] + '/' + file, destination_dir)
