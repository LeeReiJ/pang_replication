from pyray import *
from pang import Game
from settings import WINDOW_WIDTH, WINDOW_HEIGHT, WINDOW_TITLE, TARGET_FPS

if __name__ == '__main__':
    init_window(WINDOW_WIDTH, WINDOW_HEIGHT, WINDOW_TITLE)
    set_target_fps(TARGET_FPS)

    current_game = Game()
    current_game.startup()

    while not window_should_close():
        current_game.update()

        begin_drawing()
        clear_background(RAYWHITE)
        current_game.draw()
        end_drawing()

    current_game.shutdown()
    close_window()