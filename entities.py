from pyray import *
from settings import *
import math
import random


class Platform:
    def __init__(self):
        self.rect = Rectangle(WINDOW_WIDTH, random.uniform(WINDOW_HEIGHT * PLATFORM_Y_MIN, WINDOW_HEIGHT * PLATFORM_Y_MAX), PLATFORM_WIDTH, PLATFORM_HEIGHT)
        self.speed = random.uniform(PLATFORM_SPEED_MIN, PLATFORM_SPEED_MAX)
        self.active = True

    def update(self):
        self.rect.x -= self.speed
        if self.rect.x + self.rect.width < 0:
            self.active = False

    @property
    def top(self): return self.rect.y
    @property
    def left(self): return self.rect.x
    @property
    def right(self): return self.rect.x + self.rect.width

    def draw(self):
        draw_rectangle_rec(self.rect, DARKBROWN)
        draw_rectangle(int(self.rect.x), int(self.rect.y), int(self.rect.width), 3, BROWN)


class Player:
    def __init__(self, texture):
        self.texture = texture
        self.size = Vector2(PLAYER_BASE_SIZE * 2, PLAYER_BASE_SIZE * 2.4)
        self.position = Vector2(WINDOW_WIDTH / 2, WINDOW_HEIGHT - GROUND_HEIGHT - self.size.y)
        self.velocity = Vector2(0.0, 0.0)
        self.on_ground = False
        self.facing_right = True
        self.collider_radius = PLAYER_BASE_SIZE * 0.55

    @property
    def collider_center(self):
        return Vector2(self.position.x + self.size.x / 2, self.position.y + self.size.y / 2)

    @property
    def feet(self):
        return self.position.y + self.size.y

    def update(self, platforms):
        jumped = False
        self.velocity.x = 0.0

        if is_key_down(KeyboardKey.KEY_LEFT):
            self.velocity.x = -PLAYER_SPEED
            self.facing_right = False
        if is_key_down(KeyboardKey.KEY_RIGHT):
            self.velocity.x = PLAYER_SPEED
            self.facing_right = True

        if is_key_pressed(KeyboardKey.KEY_SPACE) and self.on_ground:
            self.velocity.y = PLAYER_JUMP_FORCE
            jumped = True

        prev_feet_y = self.position.y + self.size.y

        self.velocity.y += PLAYER_GRAVITY
        self.position.x += self.velocity.x
        self.position.y += self.velocity.y

        if self.position.x < 0:
            self.position.x = 0.0
        if self.position.x + self.size.x > WINDOW_WIDTH:
            self.position.x = WINDOW_WIDTH - self.size.x

        self.on_ground = False

        ground_y = WINDOW_HEIGHT - GROUND_HEIGHT - self.size.y
        if self.position.y >= ground_y:
            self.position.y = ground_y
            self.velocity.y = 0.0
            self.on_ground = True

        for plat in platforms:
            if not plat.active:
                continue
            if not (self.position.x + self.size.x > plat.left and self.position.x < plat.right):
                continue
            crossed_top = prev_feet_y <= plat.top and self.feet >= plat.top
            on_top = abs(self.feet - plat.top) <= 2 and self.velocity.y >= 0
            if crossed_top or on_top:
                self.position.y = plat.top - self.size.y
                self.velocity.y = 0.0
                self.on_ground = True
                break

        return jumped

    def collides_with_ball(self, ball):
        if not ball.active:
            return False
        return check_collision_circles(self.collider_center, self.collider_radius, ball.position, ball.radius)

    def draw(self):
        src = Rectangle(0, 0, float(self.texture.width), float(self.texture.height))
        if not self.facing_right:
            src.width = -src.width
        dst = Rectangle(self.position.x, self.position.y, self.size.x, self.size.y)
        draw_texture_pro(self.texture, src, dst, Vector2(0, 0), 0.0, WHITE)


class Ball:
    MAX_GENERATION = 2
    TEXTURES = []

    def __init__(self, generation=None):
        if generation is None:
            generation = random.randint(0, self.MAX_GENERATION)
        self.generation = max(0, min(generation, self.MAX_GENERATION))
        self.radius = BALL_SIZES[self.generation]
        self.position = Vector2(
            random.uniform(self.radius, WINDOW_WIDTH - self.radius),
            random.uniform(self.radius, WINDOW_HEIGHT * 0.4)
        )
        angle = random.uniform(0, math.pi * 2)
        spd = random.uniform(BALL_BASE_SPEED * 0.8, BALL_BASE_SPEED * 1.4)
        self.speed = Vector2(math.cos(angle) * spd, math.sin(angle) * spd)
        self.active = True

        if self.generation < self.MAX_GENERATION:
            self.split_timer = random.uniform(BALL_SPLIT_TIME_MIN, BALL_SPLIT_TIME_MAX)
            self.disappear_timer = None
        else:
            self.split_timer = None
            self.disappear_timer = random.uniform(BALL_DISAPPEAR_TIME_MIN, BALL_DISAPPEAR_TIME_MAX)

    def _rand_bounce(self):
        return -random.uniform(BOUNCE_RANDOM_MIN, BOUNCE_RANDOM_MAX)

    def update(self):
        if not self.active:
            return False

        dt = get_frame_time()
        self.position.x += self.speed.x
        self.position.y += self.speed.y

        if (self.position.x + self.radius) >= WINDOW_WIDTH:
            self.position.x = WINDOW_WIDTH - self.radius
            self.speed.x = self._rand_bounce() * abs(self.speed.x)
        elif (self.position.x - self.radius) <= 0:
            self.position.x = self.radius
            self.speed.x = abs(self.speed.x) * random.uniform(BOUNCE_RANDOM_MIN, BOUNCE_RANDOM_MAX)

        if (self.position.y - self.radius) <= 0:
            self.position.y = self.radius
            self.speed.y = abs(self.speed.y) * random.uniform(BOUNCE_RANDOM_MIN, BOUNCE_RANDOM_MAX)

        if (self.position.y + self.radius) >= WINDOW_HEIGHT - GROUND_HEIGHT:
            self.position.y = WINDOW_HEIGHT - GROUND_HEIGHT - self.radius
            self.speed.y = self._rand_bounce() * abs(self.speed.y)

        max_spd = BALL_BASE_SPEED * 2.5
        if abs(self.speed.x) > max_spd:
            self.speed.x = math.copysign(max_spd, self.speed.x)
        if abs(self.speed.y) > max_spd:
            self.speed.y = math.copysign(max_spd, self.speed.y)

        if self.split_timer is not None:
            self.split_timer -= dt
            if self.split_timer <= 0:
                self.active = False
                return True

        if self.disappear_timer is not None:
            self.disappear_timer -= dt
            if self.disappear_timer <= 0:
                self.active = False

        return False

    def split(self):
        children = []
        for i in range(2):
            child = Ball(self.generation + 1)
            child.position = Vector2(self.position.x, self.position.y)
            spd = random.uniform(BALL_BASE_SPEED, BALL_BASE_SPEED * 1.5)
            child.speed = Vector2(spd if i == 0 else -spd, -random.uniform(BALL_BASE_SPEED * 0.5, BALL_BASE_SPEED * 1.2))
            children.append(child)
        return children

    def draw(self):
        if not self.active:
            return

        if self.TEXTURES:
            tex = self.TEXTURES[self.generation]
            d = self.radius * 2
            src = Rectangle(0, 0, float(tex.width), float(tex.height))
            dst = Rectangle(self.position.x - self.radius, self.position.y - self.radius, d, d)
            draw_texture_pro(tex, src, dst, Vector2(0, 0), 0.0, WHITE)
        else:
            draw_circle_v(self.position, self.radius, [RED, BLUE, GREEN][self.generation])

        bar_x = self.position.x - self.radius
        bar_y = self.position.y - self.radius - 8
        bar_w = self.radius * 2

        if self.split_timer is not None:
            ratio = max(0.0, self.split_timer / BALL_SPLIT_TIME_MAX)
            draw_rectangle(int(bar_x), int(bar_y), int(bar_w), 4, DARKGRAY)
            draw_rectangle(int(bar_x), int(bar_y), int(bar_w * ratio), 4, ORANGE)

        if self.disappear_timer is not None:
            ratio = max(0.0, self.disappear_timer / BALL_DISAPPEAR_TIME_MAX)
            draw_rectangle(int(bar_x), int(bar_y), int(bar_w), 4, DARKGRAY)
            draw_rectangle(int(bar_x), int(bar_y), int(bar_w * ratio), 4, RED)