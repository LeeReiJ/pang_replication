from pyray import *
from settings import *
from entities import Player, Shoot, Ball, Points
import random


class Game:
    def __init__(self):
        self.game_over = False
        self.victory   = False
        self.pause     = False
        self.score     = 0
        self.gravity   = 0.0

        self.player        = Player()
        self.shoots        = [Shoot() for _ in range(PLAYER_MAX_SHOOTS)]
        self.big_balls     = []
        self.medium_balls  = []
        self.small_balls   = []
        self.points_popups = [Points() for _ in range(5)]
        self.line_position = Vector2(0.0, 0.0)

        self._count_medium = 0
        self._count_small  = 0
        self._destroyed    = 0

    # ------------------------------------------------------------------ #
    #  Public lifecycle
    # ------------------------------------------------------------------ #
    def startup(self):
        self._init_game()

    def shutdown(self):
        pass

    def update(self):
        if not self.game_over and not self.victory:
            if is_key_pressed(KeyboardKey.KEY_P):
                self.pause = not self.pause

            if not self.pause:
                self._update_player()
                self._update_shoots()
                self._update_balls()
                self._check_player_ball_collisions()
                self._check_shoot_ball_collisions()

                total = MAX_BIG_BALLS + MAX_BIG_BALLS * 2 + MAX_BIG_BALLS * 4
                if self._destroyed == total:
                    self.victory = True
        else:
            if is_key_pressed(KeyboardKey.KEY_ENTER):
                self._init_game()

        for p in self.points_popups:
            p.update()

    def draw(self):
        if not self.game_over:
            self.player.draw()

            for ball in self.big_balls:
                ball.draw(DARKGRAY)
            for ball in self.medium_balls:
                ball.draw(GRAY)
            for ball in self.small_balls:
                ball.draw(GRAY)

            for sh in self.shoots:
                sh.draw(self.line_position)

            for p in self.points_popups:
                p.draw()

            draw_text(f"SCORE: {self.score}", 10, 10, 20, LIGHTGRAY)

            if self.victory:
                msg = "YOU WIN!"
                draw_text(msg, WINDOW_WIDTH // 2 - measure_text(msg, 60) // 2, 100, 60, LIGHTGRAY)
                sub = "PRESS [ENTER] TO PLAY AGAIN"
                draw_text(sub, WINDOW_WIDTH // 2 - measure_text(sub, 20) // 2, WINDOW_HEIGHT // 2 - 50, 20, LIGHTGRAY)

            if self.pause:
                msg = "GAME PAUSED"
                draw_text(msg, WINDOW_WIDTH // 2 - measure_text(msg, 40) // 2, WINDOW_HEIGHT // 2 - 40, 40, LIGHTGRAY)
        else:
            msg = "PRESS [ENTER] TO PLAY AGAIN"
            draw_text(msg, WINDOW_WIDTH // 2 - measure_text(msg, 20) // 2, WINDOW_HEIGHT // 2 - 50, 20, LIGHTGRAY)

    # ------------------------------------------------------------------ #
    #  Init
    # ------------------------------------------------------------------ #
    def _init_game(self):
        self.game_over     = False
        self.victory       = False
        self.pause         = False
        self.score         = 0
        self.gravity       = 0.25
        self.line_position = Vector2(0.0, 0.0)
        self._count_medium = 0
        self._count_small  = 0
        self._destroyed    = 0

        self.player        = Player()
        self.shoots        = [Shoot() for _ in range(PLAYER_MAX_SHOOTS)]
        self.points_popups = [Points() for _ in range(5)]

        # Big balls: random position in upper half, non-zero velocity
        self.big_balls = [Ball(BIG_BALL_RADIUS, BIG_BALL_POINTS) for _ in range(MAX_BIG_BALLS)]
        for ball in self.big_balls:
            ball.position = Vector2(
                random.randint(int(ball.radius), WINDOW_WIDTH  - int(ball.radius)),
                random.randint(int(ball.radius), WINDOW_HEIGHT // 2),
            )
            vx, vy = 0, 0
            while vx == 0 or vy == 0:
                vx = random.randint(-int(BALLS_SPEED), int(BALLS_SPEED))
                vy = random.randint(-int(BALLS_SPEED), int(BALLS_SPEED))
            ball.speed  = Vector2(float(vx), float(vy))
            ball.active = True

        # Medium / small pools start inactive
        self.medium_balls = [Ball(MEDIUM_BALL_RADIUS, MEDIUM_BALL_POINTS, extra_gravity=0.12)
                             for _ in range(MAX_BIG_BALLS * 2)]
        self.small_balls  = [Ball(SMALL_BALL_RADIUS,  SMALL_BALL_POINTS,  extra_gravity=0.25)
                             for _ in range(MAX_BIG_BALLS * 4)]

    # ------------------------------------------------------------------ #
    #  Per-frame update helpers  (thin — real logic lives in the classes)
    # ------------------------------------------------------------------ #
    def _update_player(self):
        self.player.update()

    def _update_shoots(self):
        # Fire
        if is_key_pressed(KeyboardKey.KEY_SPACE):
            for sh in self.shoots:
                if not sh.active:
                    sh.fire(self.player.position, self.player.ship_height)
                    self.line_position = Vector2(self.player.position.x,
                                                 self.player.position.y)
                    break

        for sh in self.shoots:
            sh.update()

    def _update_balls(self):
        for ball in self.big_balls:
            ball.update(self.gravity)
        for ball in self.medium_balls:
            ball.update(self.gravity)
        for ball in self.small_balls:
            ball.update(self.gravity)

    def _check_player_ball_collisions(self):
        all_balls = self.big_balls + self.medium_balls + self.small_balls
        for ball in all_balls:
            if self.player.collides_with_ball(ball):
                self.game_over = True
                return

    def _check_shoot_ball_collisions(self):
        lx = self.line_position.x

        for sh in self.shoots:
            if not sh.active:
                continue

            # Big balls → spawn 2 medium children
            for ball in self.big_balls:
                if sh.hits_ball(ball, lx):
                    self._destroy_ball(sh, ball)
                    self._count_medium = ball.spawn_children(
                        self.medium_balls, self._count_medium
                    )
                    break

            if not sh.active:
                continue

            # Medium balls → spawn 2 small children
            for ball in self.medium_balls:
                if sh.hits_ball(ball, lx):
                    self._destroy_ball(sh, ball)
                    self._count_small = ball.spawn_children(
                        self.small_balls, self._count_small
                    )
                    break

            if not sh.active:
                continue

            # Small balls → no children
            for ball in self.small_balls:
                if sh.hits_ball(ball, lx):
                    self._destroy_ball(sh, ball)
                    break

    def _destroy_ball(self, sh: Shoot, ball: Ball):
        """Common bookkeeping when a shoot kills a ball."""
        sh.reset()
        ball.active      = False
        self._destroyed += 1
        self.score      += ball.points
        self._spawn_popup(ball.position, ball.points)

    def _spawn_popup(self, position: Vector2, value: int):
        for p in self.points_popups:
            if p.alpha == 0.0:
                p.activate(position, value)
                break