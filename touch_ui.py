import pygame
import math

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
start_copy_rect = None


def set_screen(scr=None):
    """
    Setup positions for different screen elements.

    :param scr:
    :return:
    """
    global screen, quit_box_rect, progress_bar_rect, start_copy_rect
    screen = scr
    quit_box_rect = pygame.Rect(290, 0, 30, 30)
    progress_bar_rect = pygame.Rect(10, (screen.get_height() / 2 - 20), (screen.get_width() - 20), 40)
    start_copy_rect = pygame.Rect(130, 155, 60, 30)


def quit_button(inverse=False):
    global quit_box_rect
    quit_box = pygame.draw.rect(screen, BLACK, quit_box_rect)
    quit_box = pygame.draw.rect(screen, WHITE, quit_box_rect, inverse)
    font = pygame.font.Font(None, 36)

    if inverse:
        text_fg = WHITE
    else:
        text_fg = BLACK

    text = font.render("X", 1, text_fg)
    textpos = text.get_rect(centerx=quit_box_rect.centerx, centery=quit_box_rect.centery)
    screen.blit(text, textpos)


def progress_bar():
    global progress_bar_rect
    # progress_bar_frame = pygame.draw.rect(screen, GREEN, progress_bar_rect, True)


def mock_start_copy(inverse=False):
    global start_copy_rect
    start_copy = pygame.draw.rect(screen, GREEN, start_copy_rect)
    start_copy = pygame.draw.rect(screen, YELLOW, start_copy_rect, inverse)
    font = pygame.font.Font(None, 20)
    text_fg = BLACK
    text = font.render("Start", 1, text_fg)
    textpos = text.get_rect(centerx=start_copy_rect.centerx, centery=start_copy_rect.centery)
    screen.blit(text, textpos)


def update(data):
    global progress_bar_rect
    if data['stat'] == 'total':
        pb_total = pygame.draw.rect(screen, GREEN, (progress_bar_rect.x,
                                                    progress_bar_rect.y,
                                                    int(math.ceil(float(data['completed']) / data['total'] * progress_bar_rect.width)),
                                                    progress_bar_rect.height / 2))
        # "Reset" file progress bar
        pb_file = pygame.draw.rect(screen, BLACK, (progress_bar_rect.x,
                                                  progress_bar_rect.y + (progress_bar_rect.height / 2),
                                                  progress_bar_rect.width,
                                                  progress_bar_rect.height / 2))
    elif data['stat'] == 'file':
        pb_file = pygame.draw.rect(screen, BLUE, (progress_bar_rect.x,
                                                  progress_bar_rect.y + (progress_bar_rect.height / 2),
                                                  int(math.ceil(float(data['completed']) / data['total'] * progress_bar_rect.width)),
                                                  progress_bar_rect.height / 2))
