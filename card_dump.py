import os
import Queue

import pyudev

import pygame
from pygame.locals import *

import touch_ui
from device_manager import DeviceManager


# Setup pipes for GUI update messages
message_q = Queue.Queue()
observer = None
copy_thread = None

os.environ['SDL_VIDEODRIVER'] = 'fbcon'
os.environ["SDL_FBDEV"] = "/dev/fb1"
os.environ["SDL_MOUSEDEV"] = "/dev/input/touchscreen"
os.environ["SDL_MOUSEDRV"] = "TSLIB"


def udev_event_callback(action, device):
    global copy_thread, message_q
    if not copy_thread:
        copy_thread = DeviceManager(kwargs={'return_q': message_q, 'action': action, 'device': device})
        copy_thread.start()


def clean_up():
    global observer, copy_thread

    # UI response
    touch_ui.quit_button(inverse=True)
    pygame.display.flip()

    # NB: udev async monitor observer thread must be explicitly stopped.
    observer.stop()

    if copy_thread:
        print("Stopping the copy thread")
        copy_thread.join()

    pygame.quit()


def main(args):
    # Set up GUI
    pygame.init()
    pygame.mouse.set_visible(False)
    screen = pygame.display.set_mode((320, 240), 0, 32)
    pygame.display.set_caption('Card Dump')

    touch_ui.set_screen(screen)

    # Set up udev event monitoring
    udev_context = pyudev.Context()
    udev_monitor = pyudev.Monitor.from_netlink(udev_context)

    # Monitor all storage device related signals
    udev_monitor.filter_by('block', 'partition')
    global observer
    observer = pyudev.MonitorObserver(udev_monitor, udev_event_callback)
    observer.start()

    # Mount and check USB attached partitions for either "DCIM" or "card-dump" indicator
    # (friendly names are in ID_FS_LABEL(_ENC) property of a device)
    # sub-routine returns a three item tuple of lists. First is source candidate list,
    # second is destination candidate list, and third is the empty media list.
    source_candidates, destination_candidates, empties = DeviceManager.list_media()

    # if only one DCIM folder: use it as source
    # if multiple DCIM folders: which one is copied on this run?
    # if only one card-dump folder: use it as destination
    # if multiple card-dump folders: which one is used as destination on this run?

    source_set, destination_set = False, False

    if len(source_candidates) == 1:
        DeviceManager.set_source = source_candidates[0]
        source_set = True
    elif len(source_candidates) > 1:
        # Too many source candidates - ask user which one to copy
        # TODO: Implement "Too many source candidates"
        list(source_candidates)
    else:
        # No source candidates, one might be attached later
        list(source_candidates)

    if len(destination_candidates) == 1:
        DeviceManager.set_destination = destination_candidates[0]
        destination_set = True
    elif len(destination_candidates) > 1:
        # Too many destination candidates - ask user which one to copy
        # TODO: Implement "Too many destination candidates"
        list(destination_candidates)
    else:
        # No destination candidates, one might be attached later
        list(destination_candidates)

    # If there is at least one available "empty" USB media, and no source is set, ask the user
    # Is this in any way a proper scenario? I mean, if there's no DCIM folder, do we still offer user the
    # possibility of dump that card?
    if len(empties) > 0 and not source_set:
        list(empties)

    # If there is still at least one available "empty" USB media, and no destination is set, ask the user
    if len(empties) > 0 and not destination_set:
        list(empties)

    touch_ui.quit_button()
    pygame.display.flip()
    running = True

    while running:
        for event in pygame.event.get():
            if event.type == QUIT:
                clean_up()
                sys.exit()
                running = False
            elif event.type == pygame.MOUSEBUTTONDOWN:
                # All interactions need to go here?
                # What's the pattern to check for GUI events?

                if touch_ui.quit_box_rect.collidepoint(pygame.mouse.get_pos()):
                    clean_up()
                    sys.exit()
                    running = False
                elif touch_ui.start_copy_rect.collidepoint(pygame.mouse.get_pos()):
                    touch_ui.mock_start_copy(inverse=True)
                    pygame.display.flip()
                    print("Start copying...")

                    # Manual call for testing purposes
                    udev_event_callback('add', 'foo')

            elif event.type == KEYDOWN and event.key == K_ESCAPE:
                clean_up(observer)
                running = False

        try:
            touch_ui.update_progress_bar(message_q.get_nowait())
            pygame.display.flip()
        except Queue.Empty:
            continue

        pygame.display.update()


if __name__ == '__main__':
    import sys

    main(sys.argv[1:])
