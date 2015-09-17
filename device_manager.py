import threading
import os
import shutil
import sh
from datetime import datetime


class DeviceManager(threading.Thread):
    DIR = 0
    FILES = 1

    _source_dir = '/mnt/card'
    _destination_dir = '/mnt/stick/card-dump'

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
                self.return_q.put_nowait({'stat': 'file',
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
        print(self.device.device_node)
        # TODO: Bring source_dir and destination_dir in from the command line or environment, if defined

        # '/devices/platform/bcm2708_usb/usb1/1-1/1-1.2' ATTRS['manufacturer'] and ATTRS['product']
        #   looking at parent device '/devices/platform/bcm2708_usb/usb1/1-1/1-1.4/1-1.4:1.0':
        # KERNELS=="1-1.4:1.0"
        # SUBSYSTEMS=="usb"
        # DRIVERS=="usb-storage"   <---- !!


        # /mnt/stick has to be mounted

        # Mount
        try:
            sh.mount(self.device.device_node, self._source_dir)
        except sh.ErrorReturnCode:
            print('Mounting ' + self.device.device_node + ' failed.')

        # Create target directory
        try:
            os.mkdir(self._destination_dir)
        except OSError:
            print(self._destination_dir + ' exists.')

        # Create next folder, named by current date-time
        try:
            dt = datetime()
            os.mkdir(self._destination_dir + '/' + dt.strftime('%Y-%m-%d %H:%M:%S'))
        except OSError:
            print(self._destination_dir + ' exists.')

        # Discover & copy
        copy_list = list()

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
                    destination = destination_dir + '/' + f
                    self.bytes_completed += self._copy_file(source, destination)
                    self.return_q.put_nowait({'stat': 'total',
                                              'total': self.bytes_total,
                                              'completed': self.bytes_completed})

        # Unmount
        try:
            sh.umount(self._source_dir)
        except sh.ErrorReturnCode:
            print('Unmounting ' + self._source_dir + ' failed.')

        self.return_q.put_nowait({'finished': True})

    def _remove_and_notify(self, device):
        print('Remove and notify')

    def __init__(self, group=None, target=None, name=None, args=(), kwargs=None, verbose=None):
        threading.Thread.__init__(self, group=group, target=target, name=name, verbose=verbose)
        self.return_q = kwargs['return_q']
        self.action = kwargs['action']
        self.device = kwargs['device']

        self.files_total = 0
        self.bytes_total = 0
        self.bytes_completed = 0

        self._stop_request = threading.Event()

    def run(self):
        """ Callback for later to handle mass storage attach and detach.
        device.action == add && device.action == remove """
        switch = {
            'add': self._add_and_copy,
            'remove': self._remove_and_notify,
        }
        action_function = switch.get(self.action)
        action_function()

    def join(self, timeout=None):
        """ When this thread is asked to quit, set stop request flag so file operations
        can be wrapped up cleanly. """
        self._stop_request.set()
        super(DeviceManager, self).join(timeout)
