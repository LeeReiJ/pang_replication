from pyray import *
from settings import *
import random

class Player():
    def __init__(self):
        self.position = Vector2(WINDOW_WIDTH / 2, WINDOW_HEIGHT)
        self.size = Vector2(WINDOW_WIDTH / 10, 20)
        self.life = PLAYER_MAX_LIFE

    def update(self):
        dt = get_frame_time()
        if is_key_down(KeyboardKey.KEY_LEFT):
            self.position.x -= 5 * 60 * dt
        if (self.position.x - self.size.x / 2) <= 0:
            self.position.x = self.size.x / 2
        if is_key_down(KeyboardKey.KEY_RIGHT):
            self.position.x += 5 * 60 * dt
        if (self.position.x + self.size.x / 2) >= WINDOW_WIDTH:
            self.position.x = WINDOW_WIDTH - self.size.x / 2

    def draw(self):
        draw_rectangle(int(self.position.x - self.size.x / 2), int(self.position.y - self.size.y / 2), int(self.size.x), int(self.size.y), BLACK)

class Shoot():
    pass

class Ball():
    def __init__(self):
        self.radius = 7
        self.position = Vector2(0, 0)
        self.speed = Vector2(0, 0)
        self.active = False
        self._was_active = False

    def update(self, player, bricks, brick_size, powerups):
        dt = get_frame_time()
        if not self.active:
            if not self._was_active:
                self.position.x = player.position.x
                self.position.y = player.position.y - player.size.y / 2 - self.radius
            return
        self.position.x += self.speed.x * 60 * dt
        self.position.y += self.speed.y * 60 * dt

        if (self.position.x + self.radius) >= WINDOW_WIDTH or (self.position.x - self.radius) <= 0:
            self.speed.x *= -1
        if (self.position.y - self.radius) <= 0:
            self.speed.y *= -1
        if (self.position.y + self.radius) >= WINDOW_HEIGHT:
            self.speed = Vector2(0, 0)
            self.active = False

        player_rect = Rectangle(player.position.x - player.size.x / 2, player.position.y - player.size.y / 2, player.size.x, player.size.y)
        if check_collision_circle_rec(self.position, self.radius, player_rect):
            if self.speed.y > 0:
                self.speed.y *= -1
                self.speed.x = (self.position.x - player.position.x) / (player.size.x / 2) * 5 * GAME_SPEED

        for i in range(LINES_OF_BRICKS):
            for j in range(BRICKS_PER_LINE):
                b = bricks[i][j]
                if not b.active:
                    continue
                sdx = self.speed.x * 60 * dt
                sdy = self.speed.y * 60 * dt
                hit = False

                if (self.position.y - self.radius) <= (b.position.y + brick_size.y / 2) and (self.position.y - self.radius) > (b.position.y + brick_size.y / 2 + sdy) and abs(self.position.x - b.position.x) < (brick_size.x / 2 + self.radius * 2 / 3) and self.speed.y < 0:
                    hit = True; self.speed.y *= -1
                elif (self.position.y + self.radius) >= (b.position.y - brick_size.y / 2) and (self.position.y + self.radius) < (b.position.y - brick_size.y / 2 + sdy) and abs(self.position.x - b.position.x) < (brick_size.x / 2 + self.radius * 2 / 3) and self.speed.y > 0:
                    hit = True; self.speed.y *= -1
                elif (self.position.x + self.radius) >= (b.position.x - brick_size.x / 2) and (self.position.x + self.radius) < (b.position.x - brick_size.x / 2 + sdx) and abs(self.position.y - b.position.y) < (brick_size.y / 2 + self.radius * 2 / 3) and self.speed.x > 0:
                    hit = True; self.speed.x *= -1
                elif (self.position.x - self.radius) <= (b.position.x + brick_size.x / 2) and (self.position.x - self.radius) > (b.position.x + brick_size.x / 2 + sdx) and abs(self.position.y - b.position.y) < (brick_size.y / 2 + self.radius * 2 / 3) and self.speed.x < 0:
                    hit = True; self.speed.x *= -1

                if hit:
                    b.active = False
                    if b.is_powerup:
                        powerups.append(Powerup(Vector2(b.position.x, b.position.y)))

    def draw(self):
        if self.active or not self._was_active:
            draw_circle_v(self.position, self.radius, MAROON)


class Brick():
    def __init__(self, position, active, is_powerup=False):
        self.position = position
        self.active = active
        self.is_powerup = is_powerup

    def draw(self, brick_size, color):
        draw_rectangle(int(self.position.x - brick_size.x / 2), int(self.position.y - brick_size.y / 2), int(brick_size.x), int(brick_size.y), color)
        if self.is_powerup:
            draw_text("x2", int(self.position.x) - 8, int(self.position.y) - 7, 14, YELLOW)


class Powerup():
    WIDTH = 24
    HEIGHT = 12

    def __init__(self, position):
        self.position = Vector2(position.x, position.y)
        self.active = True
        self.rect = Rectangle(self.position.x - self.WIDTH / 2, self.position.y - self.HEIGHT / 2, self.WIDTH, self.HEIGHT)

    def update(self):
        self.position.y += POWERUP_SPEED * get_frame_time()
        self.rect = Rectangle(self.position.x - self.WIDTH / 2, self.position.y - self.HEIGHT / 2, self.WIDTH, self.HEIGHT)
        if self.position.y > WINDOW_HEIGHT:
            self.active = False

    def draw(self):
        draw_rectangle_rec(self.rect, ORANGE)
        draw_text("x2", int(self.position.x) - 8, int(self.position.y) - 7, 14, WHITE)


class Game():
    def __init__(self):
        self.game_over = False
        self.pause = False
        self.player = Player()
        self.balls = [Ball()]
        self.powerups = []
        self.brick_size = Vector2(WINDOW_WIDTH / BRICKS_PER_LINE, 40)
        self.bricks = []

    def startup(self):
        b = self.balls[0]
        b.position = Vector2(self.player.position.x, self.player.position.y - self.player.size.y / 2 - b.radius)
        self.bricks = []
        for i in range(LINES_OF_BRICKS):
            row = []
            for j in range(BRICKS_PER_LINE):
                pos = Vector2(j * self.brick_size.x + self.brick_size.x / 2, i * self.brick_size.y + INITIAL_DOWN_POSITION)
                row.append(Brick(pos, True, random.random() < POWERUP_CHANCE))
            self.bricks.append(row)

    def _split_balls(self):
        new_balls = []
        for ball in self.balls:
            if not ball.active:
                continue
            clone = Ball()
            clone.active = True
            clone._was_active = True
            clone.position = Vector2(ball.position.x, ball.position.y)
            clone.speed = Vector2(-ball.speed.x, ball.speed.y)
            new_balls.append(clone)
        self.balls.extend(new_balls)

    def update(self):
        if not self.game_over:
            if is_key_pressed(KeyboardKey.KEY_P):
                self.pause = not self.pause

            if not self.pause:
                if all(not b.active for b in self.balls) and is_key_pressed(KeyboardKey.KEY_SPACE):
                    self.balls[0].active = True
                    self.balls[0]._was_active = True
                    self.balls[0].speed = Vector2(0, -5 * GAME_SPEED)

                self.player.update()
                for ball in self.balls:
                    ball.update(self.player, self.bricks, self.brick_size, self.powerups)

                if any(b._was_active for b in self.balls) and all(not b.active for b in self.balls):
                    self.player.life -= 1
                    self.balls = [Ball()]

                player_rect = Rectangle(self.player.position.x - self.player.size.x / 2, self.player.position.y - self.player.size.y / 2, self.player.size.x, self.player.size.y)
                for p in self.powerups:
                    if not p.active:
                        continue
                    p.update()
                    if check_collision_recs(p.rect, player_rect):
                        p.active = False
                        self._split_balls()
                self.powerups = [p for p in self.powerups if p.active]

            if self.player.life <= 0:
                self.game_over = True
            else:
                self.game_over = True
                for row in self.bricks:
                    for b in row:
                        if b.active:
                            self.game_over = False
                            break

        else:
            if is_key_pressed(KeyboardKey.KEY_ENTER):
                self.game_over = False
                self.pause = False
                self.player = Player()
                self.balls = [Ball()]
                self.powerups = []
                self.startup()

    def draw(self):
        if not self.game_over:
            self.player.draw()
            for i in range(self.player.life):
                draw_rectangle(20 + 40 * i, WINDOW_HEIGHT - 30, 35, 10, LIGHTGRAY)
            active_count = sum(1 for b in self.balls if b.active)
            if active_count > 1:
                draw_text(f"Balls: {active_count}", WINDOW_WIDTH - 100, WINDOW_HEIGHT - 30, 20, DARKBLUE)
            for ball in self.balls:
                ball.draw()
            for p in self.powerups:
                p.draw()
            for i in range(LINES_OF_BRICKS):
                for j in range(BRICKS_PER_LINE):
                    b = self.bricks[i][j]
                    if b.active:
                        color = (PURPLE if (i + j) % 2 == 0 else VIOLET) if b.is_powerup else (GRAY if (i + j) % 2 == 0 else DARKGRAY)
                        b.draw(self.brick_size, color)
            if self.pause:
                msg = "GAME PAUSED"
                draw_text(msg, WINDOW_WIDTH // 2 - measure_text(msg, 40) // 2, WINDOW_HEIGHT // 2 - 40, 40, GRAY)
        else:
            msg = "PRESS [ENTER] TO PLAY AGAIN"
            draw_text(msg, WINDOW_WIDTH // 2 - measure_text(msg, 20) // 2, WINDOW_HEIGHT // 2 - 50, 20, GRAY)

    def shutdown(self):
        pass