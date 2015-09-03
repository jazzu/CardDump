__author__ = 'jazzu'

import os

source_dir = '/home/pi/test/source'
destination_dir = '/home/pi/test/destination'
copy_list = list()

for root, dirs, files in os.walk(source_dir):
    copy_list.append((root, files))

