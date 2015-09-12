import fileops

__author__ = 'jazzu'


def add_and_copy(device):
    print("Add and copy")
    fileops.dump_card()


def remove_and_notify(device):
    print("Remove and notify")


def udev_event_callback(action, device):
    """ Callback for later to handle mass storage attach and detach.
        device.action == add && device.action == remove """
    switch = {
        "add": add_and_copy,
        "remove": remove_and_notify,
    }
    f = switch.get(action)
    return f(device)
