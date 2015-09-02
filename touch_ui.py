__author__ = 'jazzu'

import pygame
from pygame.locals import *

# set up the colors
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
RED = (255, 0, 0)
GREEN = (0, 255, 0)
BLUE = (0, 0, 255)
CYAN = (0, 255, 255)
MAGENTA = (255, 0, 255)
YELLOW = (255, 255, 0)

# Local reference to screen
screen = None
quit_box_rect = None
progress_bar_rect = None


def set_screen(scr=None):
    """
    Setup positions for different screen elements.

    :param scr:
    :return:
    """
    global screen, quit_box_rect, progress_bar_rect
    screen = scr
    quit_box_rect = pygame.Rect(290, 0, 30, 30)
    progress_bar_rect = pygame.Rect(10, (screen.get_height() / 2 - 20), (screen.get_width() - 20), 40)


def quit_button(inverse=False):
    global quit_box_rect
    quit_box = pygame.draw.rect(screen, BLACK, quit_box_rect)
    quit_box = pygame.draw.rect(screen, WHITE, quit_box_rect, inverse)
    font = pygame.font.Font(None, 36)

    if inverse:
        txt_fg = WHITE
    else:
        txt_fg = BLACK

    quit_x = font.render("X", 1, txt_fg)
    textpos = quit_x.get_rect(centerx=quit_box_rect.centerx, centery=quit_box_rect.centery)
    screen.blit(quit_x, textpos)


def progress_bar():
    global progress_bar_rect
    progress_bar_frame = pygame.draw.rect(screen, GREEN, progress_bar_rect, True)
    progress_bar_faux = pygame.draw.rect(screen, GREEN, (progress_bar_rect.x + 3,
                                                                  progress_bar_rect.y + 3,
                                                                  progress_bar_rect.width - 6,
                                                                  progress_bar_rect.height - 6))
