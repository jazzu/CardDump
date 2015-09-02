__author__ = 'jazzu'

import os
import sys
import pyudev
import pygame
from pygame.locals import *

import touch_ui


def some_callback_function(action, device):
    """ Callback for later to handle mass storage attach and detach.
        device.action == add && device.action == remove """
    print("Action!")


# Setup udev event monitoring
udev_context = pyudev.Context()
udev_monitor = pyudev.Monitor.from_netlink(udev_context)

# Monitor all storage device related signals
udev_monitor.filter_by('block', 'partition')
observer = pyudev.MonitorObserver(udev_monitor, some_callback_function)
observer.start()


os.environ['SDL_VIDEODRIVER'] = 'fbcon'
os.environ["SDL_FBDEV"] = "/dev/fb1"
os.environ["SDL_MOUSEDEV"] = "/dev/input/touchscreen"
os.environ["SDL_MOUSEDRV"] = "TSLIB"

pygame.init()
pygame.mouse.set_visible(False)

screen = pygame.display.set_mode((320, 240), 0, 32)
touch_ui.set_screen(screen)
pygame.display.set_caption('Card Dump')

touch_ui.quit_button(inverse=False)
touch_ui.progress_bar()

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
                pygame.quit()
                sys.exit()
                running = False
        elif event.type == KEYDOWN and event.key == K_ESCAPE:
            running = False
    pygame.display.update()

