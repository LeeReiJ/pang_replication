import os
from pyray import *
from settings import *
from entities import Player, Ball, Platform


class Game:
    def __init__(self):
        self.game_over = False
        self.pause = False
        self.survival_time = 0.0
        self.player = None
        self.balls = []
        self.platforms = []
        self._platform_timer = 0.0

        self.dev_mode = False
        self.invincible = False
        self.show_hitbox = False

        self._bg_texture = None
        self._player_texture = None
        self._ball_textures = []

        self._snd_jump = None
        self._snd_ball_hit = None
        self._snd_death = None
        self._snd_split = None
        self._snd_restart = None
        self._music = None

    def startup(self):
        init_audio_device()
        self._load_assets()
        self._init_game()
        self._music_play()

    def shutdown(self):
        if self._bg_texture: unload_texture(self._bg_texture)
        if self._player_texture: unload_texture(self._player_texture)
        for tx in self._ball_textures:
            unload_texture(tx)
        for snd in [self._snd_jump, self._snd_ball_hit, self._snd_death, self._snd_split, self._snd_restart]:
            if snd: unload_sound(snd)
        if self._music: unload_music_stream(self._music)
        close_audio_device()

    def _music_play(self):
        if not self._music:
            return
        seek_music_stream(self._music, 0.0)
        play_music_stream(self._music)

    def _music_stop(self):
        if self._music:
            stop_music_stream(self._music)

    def _load_sound_safe(self, path):
        if os.path.exists(path):
            return load_sound(path)
        print(f"[audio] missing {path} — run generate_assets.py")
        return None

    def _play(self, snd):
        if snd:
            play_sound(snd)

    def _load_assets(self):
        self._bg_texture = load_texture("assets/background.png")
        self._player_texture = load_texture("assets/player.png")
        self._ball_textures = [
            load_texture("assets/ball_big.png"),
            load_texture("assets/ball_medium.png"),
            load_texture("assets/ball_small.png"),
        ]
        Ball.TEXTURES = self._ball_textures

        self._snd_jump = self._load_sound_safe("assets/jump.wav")
        self._snd_ball_hit = self._load_sound_safe("assets/ball_hit.wav")
        self._snd_death = self._load_sound_safe("assets/death.wav")
        self._snd_split = self._load_sound_safe("assets/split.wav")
        self._snd_restart = self._load_sound_safe("assets/restart.wav")
        self._music = load_music_stream("assets/music.wav")
        set_music_volume(self._music, 0.4)

    def _init_game(self):
        self.game_over = False
        self.pause = False
        self.survival_time = 0.0
        self._platform_timer = 0.0
        self.platforms = []
        self.player = Player(self._player_texture)
        self.balls = [Ball(generation=0)]

    def update(self):
        if self._music:
            update_music_stream(self._music)

        if is_key_pressed(KeyboardKey.KEY_GRAVE):
            self.dev_mode = not self.dev_mode
            if not self.dev_mode:
                self.invincible = False
                self.show_hitbox = False

        if self.dev_mode:
            if is_key_pressed(KeyboardKey.KEY_I):
                self.invincible = not self.invincible
            if is_key_pressed(KeyboardKey.KEY_H):
                self.show_hitbox = not self.show_hitbox

        if self.game_over:
            if is_key_pressed(KeyboardKey.KEY_ENTER):
                self._play(self._snd_restart)
                self._music_play()
                self._init_game()
            return

        if is_key_pressed(KeyboardKey.KEY_P):
            self.pause = not self.pause
        if self.pause:
            return

        dt = get_frame_time()
        self.survival_time += dt

        self._update_platforms(dt)

        if self.player.update(self.platforms):
            self._play(self._snd_jump)

        self._update_balls()
        self._check_collisions()

    def _update_platforms(self, dt):
        self._platform_timer += dt
        if self._platform_timer >= PLATFORM_SPAWN_INTERVAL:
            self._platform_timer = 0.0
            self.platforms.append(Platform())
        for p in self.platforms:
            p.update()
        self.platforms = [p for p in self.platforms if p.active]

    def _update_balls(self):
        new_balls = []
        for ball in self.balls:
            should_split = ball.update()
            if should_split and ball.generation < Ball.MAX_GENERATION:
                self._play(self._snd_split)
                new_balls.extend(ball.split())
            elif not ball.active and ball.generation == Ball.MAX_GENERATION:
                new_balls.append(Ball())

        self.balls = [b for b in self.balls if b.active] + new_balls

        for ball in self.balls:
            if (ball.position.x - ball.radius <= 1 or
                    ball.position.x + ball.radius >= WINDOW_WIDTH - 1 or
                    ball.position.y + ball.radius >= WINDOW_HEIGHT - GROUND_HEIGHT - 1):
                if self._snd_ball_hit and not is_sound_playing(self._snd_ball_hit):
                    self._play(self._snd_ball_hit)
                break

    def _check_collisions(self):
        if self.invincible:
            return
        for ball in self.balls:
            if self.player.collides_with_ball(ball):
                self._play(self._snd_death)
                self._music_stop()
                self.game_over = True
                return

    def draw(self):
        src = Rectangle(0, 0, float(self._bg_texture.width), float(self._bg_texture.height))
        draw_texture_pro(self._bg_texture, src, Rectangle(0, 0, float(WINDOW_WIDTH), float(WINDOW_HEIGHT)), Vector2(0, 0), 0.0, WHITE)

        draw_rectangle(0, WINDOW_HEIGHT - GROUND_HEIGHT, WINDOW_WIDTH, GROUND_HEIGHT, DARKBROWN)
        draw_rectangle(0, WINDOW_HEIGHT - GROUND_HEIGHT, WINDOW_WIDTH, 3, BROWN)

        if not self.game_over:
            for p in self.platforms:
                p.draw()
            self.player.draw()
            for ball in self.balls:
                ball.draw()

            if self.show_hitbox:
                self._draw_hitboxes()

            draw_text(f"SURVIVED: {self.survival_time:.1f}s", 10, 10, 24, WHITE)
            draw_text(f"BALLS: {len(self.balls)}", 10, 38, 18, LIGHTGRAY)

            if self.dev_mode:
                self._draw_dev_hud()

            if self.pause:
                msg = "PAUSED"
                draw_text(msg, WINDOW_WIDTH // 2 - measure_text(msg, 40) // 2, WINDOW_HEIGHT // 2 - 20, 40, WHITE)
        else:
            draw_rectangle(0, 0, WINDOW_WIDTH, WINDOW_HEIGHT, Color(0, 0, 0, 160))
            msg = "YOU DIED"
            sub = f"Survived: {self.survival_time:.1f}s"
            sub2 = "PRESS [ENTER] TO PLAY AGAIN"
            draw_text(msg, WINDOW_WIDTH // 2 - measure_text(msg, 60) // 2, WINDOW_HEIGHT // 2 - 80, 60, RED)
            draw_text(sub, WINDOW_WIDTH // 2 - measure_text(sub, 30) // 2, WINDOW_HEIGHT // 2, 30, WHITE)
            draw_text(sub2, WINDOW_WIDTH // 2 - measure_text(sub2, 20) // 2, WINDOW_HEIGHT // 2 + 50, 20, LIGHTGRAY)

    def _draw_hitboxes(self):
        p = self.player
        col = GREEN if self.invincible else YELLOW
        draw_circle_lines(int(p.collider_center.x), int(p.collider_center.y), int(p.collider_radius), col)
        draw_rectangle_lines(int(p.position.x), int(p.position.y), int(p.size.x), int(p.size.y), fade(col, 0.5))
        for ball in self.balls:
            if ball.active:
                draw_circle_lines(int(ball.position.x), int(ball.position.y), int(ball.radius), ORANGE)
        for plat in self.platforms:
            draw_rectangle_lines(int(plat.rect.x), int(plat.rect.y), int(plat.rect.width), int(plat.rect.height), SKYBLUE)

    def _draw_dev_hud(self):
        p = self.player
        lines = [
            "[ DEV MODE — ` to off ]",
            f"I  invincible : {'ON' if self.invincible else 'off'}",
            f"H  hitboxes   : {'ON' if self.show_hitbox else 'off'}",
            "---------------------",
            f"pos  x:{p.position.x:.0f}  y:{p.position.y:.0f}",
            f"vel  x:{p.velocity.x:.2f}  y:{p.velocity.y:.2f}",
            f"on_ground: {p.on_ground}",
            f"balls: {len(self.balls)}",
        ]
        draw_rectangle(WINDOW_WIDTH - 216, 4, 210, len(lines) * 18 + 10, Color(0, 0, 0, 170))
        for i, line in enumerate(lines):
            color = GOLD if line.startswith("[ DEV") else (LIME if "ON" in line else LIGHTGRAY)
            draw_text(line, WINDOW_WIDTH - 210, 10 + i * 18, 14, color)