import threading
import os
import shutil

class DeviceManager(threading.Thread):
    DIR = 0
    FILES = 1

    def _copy_file(self, src_file, dest_file, overwrite=False, block_size=131072):
        if not overwrite:
            if os.path.isfile(dest_file):
                raise IOError("File exists, not overwriting")

        # Open src and dest files, get src file size
        src = open(src_file, "rb")
        dest = open(dest_file, "wb")

        src_size = os.stat(src_file).st_size

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
                                          'completed': src.tell()})

        src.close()
        dest.close()
        shutil.copystat(src_file, dest_file)

        # TODO: Quick hash check also
        # Check output file is same size as input one!
        dest_size = os.stat(dest_file).st_size

        if dest_size != src_size and not self._stop_request.is_set():
            raise IOError(
                "New file-size does not match original (src: %s, dest: %s)" % (
                src_size, dest_size)
            )

        # In case of an abort, delete the incomplete copy the file
        if self._stop_request.is_set():
            os.remove(dest_file)

        return src_size

    def _add_and_copy(self, device):
        print('Add and copy')
        # TODO: Bring source_dir and destination_dir in from the command line or environment
        source_dir = '/home/pi/test/source'
        destination_dir = '/home/pi/test/destination'
        copy_list = list()

        # Discover and count files and sum their sizes
        for root, dirs, files in os.walk(source_dir):
            copy_list.append((root, files))
            self.files_total += len(files)
            for f in files:
                self.bytes_total += os.stat(root + '/' + f).st_size

        # Copy files from non-empty directories, report total progress between each file
        for entry in copy_list:
            if entry[DeviceManager.FILES]:
                for f in entry[DeviceManager.FILES]:
                    # Check for stop request per file
                    if self._stop_request.is_set():
                        break
                    source = entry[DeviceManager.DIR] + '/' + f
                    destination = destination_dir + '/' + f
                    self.bytes_completed += self._copy_file(source, destination)
                    self.return_q.put_nowait({'stat': 'total',
                                              'total': self.bytes_total,
                                              'completed': self.bytes_completed})


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
        action_function(self.device)

    def join(self, timeout=None):
        """ When this thread is asked to quit, set stop request flag so file operations
        can be wrapped up cleanly. """
        self._stop_request.set()
        super(DeviceManager, self).join(timeout)