import threading
import os
import re
import shutil
from datetime import datetime

import pyudev
import sh


class DeviceManager(threading.Thread):
    DIR = 0
    FILES = 1

    _temp_dir = '/mnt/temp'
    _source_dir = '/mnt/source'
    _destination_dir = '/mnt/destination'
    _card_dump_dir = 'card-dump'

    # ensure that the mount dirs exist
    if not os.path.exists(_temp_dir):
        os.mkdir(_temp_dir)

    if not os.path.exists(_source_dir):
        os.mkdir(_source_dir)

    if not os.path.exists(_destination_dir):
        os.mkdir(_destination_dir)

    _source_indicator = 'DCIM'
    _destination_indicator = _card_dump_dir

    _device = None
    _action = None
    _return_q = None

    def _create_dump_destination_dir(self):
        try:
            os.mkdir(self._destination_dir)
        except OSError:
            print(self._destination_dir + ' exists.')

    def _create_next_copy_dir(self):
        # Create next folder, named by current date-time
        try:
            dt = datetime()
            os.mkdir(self._destination_dir + '/' + self._card_dump_dir + '/' + dt.strftime('%Y-%m-%d %H:%M:%S'))
        except OSError:
            print(
            self._destination_dir + '/' + self._card_dump_dir + '/' + dt.strftime('%Y-%m-%d %H:%M:%S') + ' exists.')

    def _copy_file(self, src_file, dest_file, overwrite=False, block_size=131072):
        """
        :param src_file: File to copy
        :param dest_file: Destination for copying to
        :param overwrite: Should possible existing file be overwritten?
        :param block_size: How big chunks should be used in copying (default 128 kB)
        :return: Size of the copied file
        """
        if not overwrite:
            if os.path.isfile(dest_file):
                raise IOError("File exists, not overwriting")

        # Open src and dest files, get src file size
        src = open(src_file, "rb")
        dest = open(dest_file, "wb")

        src_size = os.stat(src_file).st_size + 1

        # Start copying file
        while True:
            cur_block = src.read(block_size)

            # If it's the end of file or stop request has been set, abort
            if not cur_block or self._stop_request.is_set():
                break
            else:
                # ..if not, write the block and continue
                dest.write(cur_block)
                self._return_q.put_nowait({'stat': 'file',
                                          'total': src_size,
                                          'completed': src.tell() + 1})

        src.close()
        dest.close()
        shutil.copystat(src_file, dest_file)

        # TODO: Quick hash check also
        # Check output file is same size as input one!
        dest_size = os.stat(dest_file).st_size + 1

        if dest_size != src_size and not self._stop_request.is_set():
            raise IOError(
                "New file-size does not match original (src: %s, dest: %s)" % (
                    src_size, dest_size)
            )

        # In case of an abort, delete the incomplete copy the file
        if self._stop_request.is_set():
            os.remove(dest_file)

        return src_size

    def _add_and_copy(self):
        # TODO: Implement proper logging
        print('Add and copy')
        print(self._device.device_node)
        # TODO: Bring source_dir and destination_dir in from the command line or environment, if defined

        # Mount source (where's destination mounted?)
        DeviceManager.mount(self._device.device_node, self._source_dir)
        self._create_dump_destination_dir()
        self._create_next_copy_dir()

        # Discover & copy
        copy_list = []

        # Discover and count files and sum their sizes
        for root, dirs, files in os.walk(self._source_dir):
            copy_list.append((root, files))
            self.files_total += len(files)
            for f in files:
                self.bytes_total += os.stat(root + '/' + f).st_size

        # Guard against div/0
        self.bytes_total += 1

        # Copy files from non-empty directories, report total progress between each file
        for entry in copy_list:
            if entry[self.FILES]:
                for f in entry[self.FILES]:
                    # Check for stop request per file
                    if self._stop_request.is_set():
                        break
                    source = entry[self.DIR] + '/' + f
                    destination = self._destination_dir + '/' + self._card_dump_dir + '/' + f
                    self.bytes_completed += self._copy_file(source, destination)
                    self._return_q.put_nowait({'stat': 'total',
                                              'total': self.bytes_total,
                                              'completed': self.bytes_completed})

        DeviceManager.unmount(self._source_dir)
        self._return_q.put_nowait({'finished': True})

    def _remove_and_notify(self, device):
        print('Remove and notify')

    def __init__(self, group=None, target=None, name=None, args=(), kwargs=None, verbose=None):
        threading.Thread.__init__(self, group=group, target=target, name=name, verbose=verbose)
        self._return_q = kwargs['return_q']
        self._action = kwargs['action']
        self._device = kwargs['device']

        self.files_total = 0
        self.bytes_total = 0
        self.bytes_completed = 0

        self._stop_request = threading.Event()

    def run(self):
        switch = {
            'add': self._add_and_copy,
            'remove': self._remove_and_notify
        }

        if self._action in switch:
            switch[self._action]()

    def join(self, timeout=None):
        """ When this thread is asked to quit, set stop request flag so file operations
        can be wrapped up cleanly. """
        self._stop_request.set()
        super(DeviceManager, self).join(timeout)

    @staticmethod
    def mount(device, target):
        if not target:
            raise NameError('Mounting requires a target directory')

        try:
            sh.mount(device.device_node, target)
        except sh.ErrorReturnCode:
            print('Mounting ' + device.device_node + ' failed.')

    @staticmethod
    def unmount(target):
        if not target:
            raise NameError('Unmounting requires a target directory')

        try:
            sh.umount(target)
        except sh.ErrorReturnCode:
            print('Unmounting ' + target + ' failed.')

    @staticmethod
    def scan_usb_devices():
        discovered_devices = []
        # /dev/disk/by-path/  --> regex /usb/

        udev_context = pyudev.Context()
        device_list = udev_context.list_devices(subsystem='block', DEVTYPE='partition')
        for device in list(device_list):
            if re.search('usb', device.sys_path):
                # Pre-attached device found, make a note
                discovered_devices.append(device)

        return discovered_devices

    @staticmethod
    def list_media():
        candidate_devies = DeviceManager.scan_usb_devices()
        sources = []
        destinations = []
        empties = []

        for device in candidate_devies:
            DeviceManager.mount(device, DeviceManager._temp_dir)
            file_list = os.listdir(DeviceManager._temp_dir)

            # Priority for media binding: source > destination > empty
            # Never ever use a media as a dump destination, if it has source indications in it
            if DeviceManager._source_indicator in file_list:
                sources.append(device)
            elif DeviceManager._destination_indicator in file_list:
                destinations.append(device)
            else:
                empties.append(device)

            DeviceManager.unmount(DeviceManager._temp_dir)

        return sources, destinations, empties
