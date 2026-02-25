from pyray import *
from pang import Game
from settings import WINDOW_WIDTH, WINDOW_HEIGHT

if __name__ == '__main__':
    init_window(WINDOW_WIDTH, WINDOW_HEIGHT, "arkanoid")
    set_target_fps(60)

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