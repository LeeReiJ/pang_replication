from pyray import *
from settings import *
import math
import random


# --------------------------------------------------
# Player
# --------------------------------------------------
class Player:
    def __init__(self):
        self.ship_height = (PLAYER_BASE_SIZE / 2) / math.tan(math.radians(20))
        self.position    = Vector2(WINDOW_WIDTH / 2, WINDOW_HEIGHT)
        self.speed       = Vector2(PLAYER_SPEED, PLAYER_SPEED)
        self.rotation    = 0.0
        self.collider    = Vector3(
            self.position.x,
            self.position.y - self.ship_height / 2.0,
            12.0
        )

    def update(self):
        if is_key_down(KeyboardKey.KEY_LEFT):
            self.position.x -= self.speed.x
        if is_key_down(KeyboardKey.KEY_RIGHT):
            self.position.x += self.speed.x

        # Wall clamp
        if self.position.x + PLAYER_BASE_SIZE / 2 > WINDOW_WIDTH:
            self.position.x = WINDOW_WIDTH - PLAYER_BASE_SIZE / 2
        elif self.position.x - PLAYER_BASE_SIZE / 2 < 0:
            self.position.x = PLAYER_BASE_SIZE / 2

        # Keep collider in sync
        self.collider = Vector3(
            self.position.x,
            self.position.y - self.ship_height / 2.0,
            12.0
        )

    def collides_with_ball(self, ball: "Ball") -> bool:
        if not ball.active:
            return False
        cp = Vector2(self.collider.x, self.collider.y)
        return check_collision_circles(cp, self.collider.z, ball.position, ball.radius)

    def draw(self):
        rot = self.rotation
        sh  = self.ship_height
        v1 = Vector2(
            self.position.x + math.sin(math.radians(rot)) * sh,
            self.position.y - math.cos(math.radians(rot)) * sh,
        )
        v2 = Vector2(
            self.position.x - math.cos(math.radians(rot)) * (PLAYER_BASE_SIZE / 2),
            self.position.y - math.sin(math.radians(rot)) * (PLAYER_BASE_SIZE / 2),
        )
        v3 = Vector2(
            self.position.x + math.cos(math.radians(rot)) * (PLAYER_BASE_SIZE / 2),
            self.position.y + math.sin(math.radians(rot)) * (PLAYER_BASE_SIZE / 2),
        )
        draw_triangle(v1, v2, v3, MAROON)


# --------------------------------------------------
# Shoot
# --------------------------------------------------
class Shoot:
    def __init__(self):
        self.position   = Vector2(0.0, 0.0)
        self.speed      = Vector2(0.0, 0.0)
        self.radius     = 2.0
        self.rotation   = 0.0
        self.life_spawn = 0
        self.active     = False

    def fire(self, origin: Vector2, ship_height: float):
        """Activate this shoot from the player's tip."""
        self.position   = Vector2(origin.x, origin.y - ship_height)
        self.speed      = Vector2(0.0, PLAYER_SPEED)
        self.life_spawn = 0
        self.active     = True

    def reset(self):
        self.position   = Vector2(0.0, 0.0)
        self.speed      = Vector2(0.0, 0.0)
        self.life_spawn = 0
        self.active     = False

    def update(self):
        if not self.active:
            return

        self.life_spawn  += 1
        self.position.y  -= self.speed.y

        off = self.radius
        oob = (self.position.x >  WINDOW_WIDTH  + off or
               self.position.x < -off or
               self.position.y >  WINDOW_HEIGHT + off or
               self.position.y < -off)
        if oob or self.life_spawn >= 120:
            self.reset()

    def hits_ball(self, ball: "Ball", line_x: float) -> bool:
        """
        Vertical-line collision: the shot travels along line_x.
        A ball is hit when line_x is inside its horizontal span
        AND its bottom edge has descended to or past the bullet tip.
        """
        if not self.active or not ball.active:
            return False
        return (ball.position.x - ball.radius <= line_x <= ball.position.x + ball.radius and
                ball.position.y + ball.radius >= self.position.y)

    def draw(self, line_origin: Vector2):
        if self.active:
            draw_line(
                int(line_origin.x), int(line_origin.y),
                int(self.position.x), int(self.position.y),
                RED,
            )


# --------------------------------------------------
# Ball
# --------------------------------------------------
class Ball:
    def __init__(self, radius: float, points: int, extra_gravity: float = 0.0):
        self.radius        = radius
        self.points        = points
        self.extra_gravity = extra_gravity   # 0, +0.12, or +0.25 per tier
        self.position      = Vector2(-100.0, -100.0)
        self.speed         = Vector2(0.0, 0.0)
        self.active        = False

    @property
    def ceiling_bounce(self) -> float:
        """Big balls bounce harder off the ceiling (-1.5); others use -1."""
        return -1.5 if self.radius == BIG_BALL_RADIUS else -1.0

    def update(self, gravity: float):
        if not self.active:
            return

        self.position.x += self.speed.x
        self.position.y += self.speed.y

        # Horizontal walls
        if (self.position.x + self.radius) >= WINDOW_WIDTH or (self.position.x - self.radius) <= 0:
            self.speed.x *= -1

        # Ceiling
        if (self.position.y - self.radius) <= 0:
            self.speed.y *= self.ceiling_bounce

        # Floor
        if (self.position.y + self.radius) >= WINDOW_HEIGHT:
            self.speed.y   *= -1
            self.position.y = WINDOW_HEIGHT - self.radius

        self.speed.y += gravity + self.extra_gravity

    def spawn_children(self, pool: "list[Ball]", next_index: int) -> int:
        """
        Activate two children from pool starting at next_index.
        Even pool index → moves left, odd → moves right.
        Small balls (detected by radius) launch upward; medium launch downward.
        Returns updated next_index.
        """
        for j in range(2):
            idx = next_index + j
            if idx >= len(pool):
                break
            child          = pool[idx]
            child.position = Vector2(self.position.x, self.position.y)
            direction      = -BALLS_SPEED if (idx % 2 == 0) else BALLS_SPEED
            vy             = -BALLS_SPEED if child.radius == SMALL_BALL_RADIUS else BALLS_SPEED
            child.speed    = Vector2(direction, vy)
            child.active   = True
        return next_index + 2

    def draw(self, color_active=DARKGRAY):
        if self.active:
            draw_circle_v(self.position, self.radius, color_active)
        else:
            draw_circle_v(self.position, self.radius, fade(LIGHTGRAY, 0.3))


# --------------------------------------------------
# Points  (floating score popup)
# --------------------------------------------------
class Points:
    def __init__(self):
        self.position = Vector2(0.0, 0.0)
        self.value    = 0
        self.alpha    = 0.0

    def activate(self, position: Vector2, value: int):
        self.position = Vector2(position.x, position.y)
        self.value    = value
        self.alpha    = 1.0

    def update(self):
        if self.alpha > 0.0:
            self.position.y -= 2
            self.alpha      -= 0.02
        if self.alpha < 0.0:
            self.alpha = 0.0

    def draw(self):
        if self.alpha > 0.0:
            draw_text(
                f"+{self.value:02d}",
                int(self.position.x),
                int(self.position.y),
                20,
                fade(BLUE, self.alpha),
            )
            
            
