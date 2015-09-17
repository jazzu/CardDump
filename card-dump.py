import os
import sys
import pyudev
import pygame
from pygame.locals import *
import Queue
import touch_ui
from device_manager import DeviceManager

# Setup pipes for GUI update messages
message_q = Queue.Queue()
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


def main(args):
    # Setup udev event monitoring
    udev_context = pyudev.Context()
    udev_monitor = pyudev.Monitor.from_netlink(udev_context)

    # Monitor all storage device related signals
    udev_monitor.filter_by('block', 'partition')
    observer = pyudev.MonitorObserver(udev_monitor, udev_event_callback)
    observer.start()

    pygame.init()
    pygame.mouse.set_visible(False)
    screen = pygame.display.set_mode((320, 240), 0, 32)
    pygame.display.set_caption('Card Dump')

    touch_ui.set_screen(screen)

    touch_ui.quit_button()
    touch_ui.progress_bar()
    touch_ui.mock_start_copy()

    pygame.display.flip()

    running = True

    while running:
        for event in pygame.event.get():
            if event.type == QUIT:
                # UI response
                touch_ui.quit_button(inverse=True)
                pygame.display.flip()

                # NB: udev async monitor observer thread must be explicitly stopped.
                observer.stop()

                if copy_thread:
                    print("Stopping thread 1")
                    copy_thread.join()

                pygame.quit()
                sys.exit()
                running = False
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if touch_ui.quit_box_rect.collidepoint(pygame.mouse.get_pos()):
                    # UI response
                    touch_ui.quit_button(inverse=True)
                    pygame.display.flip()
                    print("Quitting...")

                    # NB: udev async monitor observer thread must be explicitly stopped.
                    observer.stop()

                    if copy_thread:
                        print("Stopping thread 2")
                        copy_thread.join()

                    pygame.quit()
                    sys.exit()
                    running = False
                elif touch_ui.start_copy_rect.collidepoint(pygame.mouse.get_pos()):
                    touch_ui.mock_start_copy(inverse=True)
                    pygame.display.flip()
                    print("Start copying...")

                    # Manual call for testing purposes
                    udev_event_callback('add', 'foo')

            elif event.type == KEYDOWN and event.key == K_ESCAPE:
                running = False

        try:
            touch_ui.update(message_q.get_nowait())
            pygame.display.flip()
        except Queue.Empty:
            continue

        pygame.display.update()

if __name__ == '__main__':
    import sys
    main(sys.argv[1:])
