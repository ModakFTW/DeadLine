# levels/level_oldwoman.py — Level 4: Help Grandmother cross the road with acrobatic Monkey AI
import pygame
import math
import random
from settings import (
    DISPLAY_WIDTH, DISPLAY_HEIGHT, MONKEY_SPEED, MONKEY_FLEE_TIME,
    WOMAN_SPEED, PLAYER_SPEED, FPS,
    WHITE, BLACK, BLUE, RED, GREEN, YELLOW, GOLD
)
from game_state import GameState
from levels.base_level import BaseLevel
from ai.monkey_ai import MonkeyAI
import sprite_loader


class LevelOldWoman(BaseLevel):
    """
    Level 4: Civic Empathy & Acrobatic Thief Monkey AI.
    Escort grandmother safely across the busy Indian city street to the waiting auto-rickshaw.
    Defend her from an intelligent, leaping Monkey AI that vaults over the player
    and tries to snatch her handbag!
    """

    def __init__(self, game_state: GameState):
        self.game_state = game_state

        # Road crossing surface baseline on bg_level4 (aligned with crosswalk pavement curb)
        self.ground_y = float(DISPLAY_HEIGHT - 65)

        # Player state
        self.player_x = 160.0
        self.player_y = float(self.ground_y)
        self.player_vel_y = 0.0
        self.player_on_ground = True
        self.facing_right = True
        self.player_anim_timer = 0.0

        # Grandmother state
        self.woman_x = 70.0
        self.woman_y = float(self.ground_y)
        self.woman_start_x = 70.0
        self.woman_anim_timer = 0.0
        self.woman_facing_right = True
        self.woman_panicking = False
        self.panic_timer = 0

        # Monkey state (with 2D acrobat physics)
        self.monkey_x = float(DISPLAY_WIDTH - 240)
        self.monkey_y = float(self.ground_y)
        self.monkey_vel_x = 0.0
        self.monkey_vel_y = 0.0
        self.monkey_on_ground = True
        self.monkey_facing_right = False
        self.monkey_anim_timer = 0.0
        self.monkey_has_bag = False
        self.bag_recovered = True
        self.monkey_flee_timer = 0
        self.monkey_state = "idle"
        self.monkey_ai = MonkeyAI()

        # Destination: Waiting Auto-Rickshaw
        self.rickshaw_x = float(DISPLAY_WIDTH - 190)
        self.rickshaw_y = float(self.ground_y)

        # Timers and feedback
        self.win_timer = 0
        self.scare_wave_timer = 0
        self.scare_wave_pos = (0, 0)
        self.alert_message = ""
        self.alert_timer = 0
        self.alert_color = GOLD

        # Fonts
        self.font_title = pygame.font.SysFont("segoeui, arial", 22, bold=True)
        self.font_large = pygame.font.SysFont("segoeui, arial", 44, bold=True)
        self.font_sub = pygame.font.SysFont("segoeui, arial", 16)
        self.font_badge = pygame.font.SysFont("segoeui, arial", 14, bold=True)

        # Assets & Sprites - scaled to match background perspective
        # Student: 48x72, Grandmother: 52x78, Monkey: 44x50 walk (tall/narrow:
        # same width as original art, +25% height, clearly smaller than humans)
        self.bg = sprite_loader.load_background("bg_level4.jpg", DISPLAY_WIDTH, DISPLAY_HEIGHT)
        self.student_frames_right = sprite_loader.load_student_frames()
        self.student_frames_left = sprite_loader.load_student_frames_left()
        self.grandma_frames_right = sprite_loader.load_grandma_frames(52, 78)
        self.grandma_frames_left = sprite_loader.load_grandma_frames_left(52, 78)
        self.monkey_sprites = sprite_loader.load_monkey_sprites(44, 50)
        raw_rickshaw = sprite_loader.load_rickshaw(160, 110)
        # Parked rickshaw on right faces towards incoming traffic (left)
        self.rickshaw_sprite = pygame.transform.flip(raw_rickshaw, True, False) if raw_rickshaw else None

        self.keys = {}

    def handle_events(self, events: list[pygame.event.Event]) -> str | None:
        for event in events:
            if event.type == pygame.KEYDOWN:
                self.keys[event.key] = True

                # Jump with Space, W, or Up
                if event.key in (pygame.K_SPACE, pygame.K_w, pygame.K_UP):
                    if self.player_on_ground:
                        self.player_vel_y = -13.5
                        self.player_on_ground = False

                    # Scare action pulse around player
                    dist = math.hypot(self.player_x - self.monkey_x, self.player_y - self.monkey_y)
                    self.scare_wave_timer = 18
                    self.scare_wave_pos = (int(self.player_x), int(self.player_y - 35))

                    if dist <= 130:
                        self.monkey_flee_timer = MONKEY_FLEE_TIME
                        self.monkey_vel_x = 4.5
                        self.monkey_facing_right = True
                        self._set_alert("SHOO! MONKEY SCARED AWAY!", (80, 220, 120))
                        if self.monkey_has_bag:
                            self.monkey_has_bag = False
                            self.bag_recovered = True
                            self._set_alert("RECOVERED GRANDMOTHER'S HANDBAG!", GOLD)

            elif event.type == pygame.KEYUP:
                self.keys[event.key] = False
        return None

    def _set_alert(self, msg: str, color: tuple = GOLD) -> None:
        self.alert_message = msg
        self.alert_timer = 70
        self.alert_color = color

    def update(self) -> str | None:
        if self.win_timer > 0:
            self.win_timer -= 1
            if self.win_timer <= 0:
                return 'exam_gate'
            return None

        if self.alert_timer > 0:
            self.alert_timer -= 1

        if self.scare_wave_timer > 0:
            self.scare_wave_timer -= 1

        # ── 1. Player Physics & Input ──
        player_speed = PLAYER_SPEED * 1.15
        is_moving = False
        if self.keys.get(pygame.K_LEFT) or self.keys.get(pygame.K_a):
            self.player_x -= player_speed
            self.facing_right = False
            is_moving = True
        if self.keys.get(pygame.K_RIGHT) or self.keys.get(pygame.K_d):
            self.player_x += player_speed
            self.facing_right = True
            is_moving = True

        self.player_x = max(35.0, min(float(DISPLAY_WIDTH - 50), self.player_x))

        # Gravity
        self.player_vel_y += 0.68
        self.player_y += self.player_vel_y
        if self.player_y >= self.ground_y:
            self.player_y = self.ground_y
            self.player_vel_y = 0.0
            self.player_on_ground = True

        if is_moving and self.player_on_ground:
            self.player_anim_timer += 0.20
        elif not self.player_on_ground:
            self.player_anim_timer = 1.0
        else:
            self.player_anim_timer = 0.0

        # ── 2. Grandmother Walking & Panic State ──
        if self.panic_timer > 0:
            self.panic_timer -= 1
            if self.panic_timer <= 0:
                self.woman_panicking = False

        dist_pw = self.player_x - self.woman_x
        if not self.woman_panicking and self.bag_recovered:
            # Grandmother follows player when student stays close
            if 20 < dist_pw <= 135:
                self.woman_x += WOMAN_SPEED
                self.woman_anim_timer += 0.14
                self.woman_facing_right = True
            elif dist_pw < -20:
                # Student went behind grandmother
                self.woman_anim_timer = 0.0
        elif self.woman_panicking or not self.bag_recovered:
            # Grandmother backs away or freezes in panic
            if self.woman_x > self.woman_start_x:
                self.woman_x -= WOMAN_SPEED * 1.2
                self.woman_anim_timer += 0.18
                self.woman_facing_right = False

        # ── 3. Monkey Acrobat AI & Physics ──
        self.monkey_anim_timer += 0.16

        # Decide AI Action
        if self.monkey_flee_timer > 0:
            self.monkey_flee_timer -= 1
            ai_action = 'flee_with_bag' if self.monkey_has_bag else 'flee'
        else:
            ai_action = self.monkey_ai.decide_action(
                self.monkey_x, self.monkey_y,
                self.player_x, self.player_y,
                self.woman_x, self.woman_y,
                has_bag=self.monkey_has_bag,
                on_ground=self.monkey_on_ground
            )

        self.monkey_state = ai_action

        # Handle Actions
        if ai_action == 'vault' and self.monkey_on_ground:
            # Acrobatic leap over player!
            self.monkey_vel_y = -13.5
            leap_dir = -1.0 if self.monkey_x > self.woman_x else 1.0
            self.monkey_vel_x = leap_dir * 5.0
            self.monkey_on_ground = False
            self.monkey_facing_right = (leap_dir > 0)
            self._set_alert("⚠ MONKEY IS VAULTING OVER YOU! JUMP TO INTERCEPT!", (245, 160, 40))

        elif ai_action == 'steal':
            # Snatched the handbag!
            if not self.monkey_has_bag:
                self.monkey_has_bag = True
                self.bag_recovered = False
                self.woman_panicking = True
                self.panic_timer = 140
                self.monkey_vel_y = -9.0
                self.monkey_vel_x = 4.5
                self.monkey_on_ground = False
                self.monkey_facing_right = True
                self._set_alert("🚨 THE THIEF MONKEY SNATCHED GRANDMOTHER'S BAG! CHASE IT!", (250, 70, 70))

        elif ai_action == 'flee_with_bag':
            # Sprinting right towards escape with stolen handbag
            self.monkey_vel_x = 4.0
            self.monkey_facing_right = True
            # Occasional hops
            if self.monkey_on_ground and random.random() < 0.03:
                self.monkey_vel_y = -8.0
                self.monkey_on_ground = False

        elif ai_action == 'flee':
            flee_dir = self.monkey_ai.get_flee_direction(self.monkey_x, self.player_x)
            self.monkey_vel_x = flee_dir * MONKEY_SPEED * 1.5
            self.monkey_facing_right = (flee_dir > 0)

        elif ai_action == 'approach' and self.monkey_on_ground:
            app_dir = self.monkey_ai.get_approach_direction(self.monkey_x, self.woman_x)
            self.monkey_vel_x = app_dir * MONKEY_SPEED * 1.2
            self.monkey_facing_right = (app_dir > 0)

        elif ai_action == 'idle' and self.monkey_on_ground:
            self.monkey_vel_x = math.sin(self.monkey_anim_timer * 2) * 0.6
            self.monkey_facing_right = (self.monkey_x < self.player_x)

        # Apply monkey gravity and movement
        if not self.monkey_on_ground:
            self.monkey_vel_y += 0.65
        self.monkey_x += self.monkey_vel_x
        self.monkey_y += self.monkey_vel_y

        if self.monkey_y >= self.ground_y:
            self.monkey_y = self.ground_y
            self.monkey_vel_y = 0.0
            self.monkey_on_ground = True
            if ai_action not in ('flee', 'flee_with_bag', 'approach'):
                self.monkey_vel_x = 0.0

        # Clamp monkey bounds
        self.monkey_x = max(40.0, min(float(DISPLAY_WIDTH - 60), self.monkey_x))

        # ── 4. Mid-Air Tackle / Interception Check ──
        # If player collides with monkey in air or on ground while chasing
        # (narrower tall sprite: radius tightened 60 -> 56 to match body)
        dist_pm = math.hypot(self.player_x - self.monkey_x, (self.player_y - 30) - (self.monkey_y - 30))
        if dist_pm < 56:
            # Intercepted!
            self.monkey_flee_timer = MONKEY_FLEE_TIME
            self.monkey_vel_x = 5.0
            self.monkey_facing_right = True
            if self.monkey_has_bag:
                self.monkey_has_bag = False
                self.bag_recovered = True
                self._set_alert("★ BAG RECOVERED! ESCORT GRANDMOTHER SAFELY! ★", (60, 220, 120))
            else:
                self._set_alert("INTERCEPTED MONKEY! IT RETREATS!", (80, 210, 255))

        # ── 5. Win Condition ──
        # Grandmother reaches auto-rickshaw while holding her bag
        if self.woman_x >= self.rickshaw_x - 30 and self.bag_recovered and self.win_timer == 0:
            self.win_timer = 90  # 1.5 second celebration animation

        return None

    def draw(self, surface: pygame.Surface) -> None:
        # 1. Full High-Res Pixel Art City Street Background
        if self.bg:
            surface.blit(self.bg, (0, 0))
        else:
            surface.fill((30, 35, 45))

        # 2. Waiting Auto-Rickshaw Destination
        if self.rickshaw_sprite:
            surface.blit(self.rickshaw_sprite, (int(self.rickshaw_x - 20), int(self.rickshaw_y - 110)))
        else:
            pygame.draw.rect(surface, (250, 200, 30), (int(self.rickshaw_x), int(self.rickshaw_y - 65), 100, 60), border_radius=8)

        # Destination pulse indicator
        pulse = int(math.sin(pygame.time.get_ticks() * 0.006) * 4)
        arrow_x = int(self.rickshaw_x + 50)
        arrow_y = int(self.rickshaw_y - 130 + pulse)
        pygame.draw.polygon(surface, GOLD, [
            (arrow_x - 10, arrow_y), (arrow_x + 10, arrow_y), (arrow_x, arrow_y + 12)
        ])

        # 3. Grandmother Character (Pixel Art)
        self._draw_grandmother(surface)

        # 4. Student Player Character (Pixel Art)
        self._draw_player(surface)

        # 5. Acrobat Thief Monkey (Pixel Art)
        self._draw_monkey(surface)

        # 6. Scare Shockwave Effect
        if self.scare_wave_timer > 0:
            wave_r = int((18 - self.scare_wave_timer) * 6)
            pygame.draw.circle(surface, (120, 220, 255), self.scare_wave_pos, wave_r, 2)

        # 7. UI HUD Banner
        self._draw_hud(surface)

    def _draw_player(self, surface: pygame.Surface) -> None:
        frames = self.student_frames_right if self.facing_right else self.student_frames_left
        idx = int(self.player_anim_timer) % len(frames) if frames else 0
        p_frame = frames[idx] if frames else None

        px = int(self.player_x - 24)
        py = int(self.player_y - 72)

        # Shadow
        pygame.draw.ellipse(surface, (20, 24, 30, 140), (self.player_x - 18, self.ground_y - 6, 36, 10))

        if p_frame:
            scaled = pygame.transform.smoothscale(p_frame, (48, 72))
            surface.blit(scaled, (px, py))
        else:
            pygame.draw.rect(surface, BLUE, (px, py, 40, 70), border_radius=6)

    def _draw_grandmother(self, surface: pygame.Surface) -> None:
        frames = self.grandma_frames_right if self.woman_facing_right else self.grandma_frames_left
        idx = int(self.woman_anim_timer * 2) % len(frames) if frames else 0
        g_frame = frames[idx] if frames else None

        gx = int(self.woman_x - 27)
        gy = int(self.woman_y - 82)

        # Shadow
        pygame.draw.ellipse(surface, (20, 24, 30, 140), (self.woman_x - 20, self.ground_y - 6, 40, 10))

        if g_frame:
            surface.blit(g_frame, (gx, gy))
        else:
            pygame.draw.rect(surface, (140, 30, 60), (gx, gy, 44, 76), border_radius=6)

        # Golden handbag if not stolen
        if self.bag_recovered:
            bag_x = self.woman_x + (14 if self.woman_facing_right else -18)
            bag_y = self.woman_y - 38
            pygame.draw.rect(surface, (245, 195, 45), (bag_x, bag_y, 14, 12), border_radius=3)
            pygame.draw.rect(surface, (160, 120, 20), (bag_x, bag_y, 14, 12), 1, border_radius=3)

    def _draw_monkey(self, surface: pygame.Surface) -> None:
        # Shadow (shrinks when jumping high; narrower than the tall sprite body)
        height_above_ground = max(0, int(self.ground_y - self.monkey_y))
        shadow_w = max(14, 36 - height_above_ground // 4)
        pygame.draw.ellipse(surface, (20, 24, 30, 140), (self.monkey_x - shadow_w // 2, self.ground_y - 5, shadow_w, 8))

        # Select sprite pose based on acrobatic state
        if not self.monkey_on_ground:
            pose_key = "jump_right" if self.monkey_facing_right else "jump_left"
        elif self.monkey_state == 'vault' or (abs(self.monkey_vel_x) < 0.2 and self.monkey_state == 'idle'):
            pose_key = "crouch_right" if self.monkey_facing_right else "crouch_left"
        else:
            pose_key = "walk_right" if self.monkey_facing_right else "walk_left"

        m_sprite = self.monkey_sprites.get(pose_key)
        if m_sprite:
            # Bottom-center anchor so the tall/narrow sprite sits on the ground correctly
            mx = int(self.monkey_x - m_sprite.get_width() // 2)
            my = int(self.monkey_y - m_sprite.get_height())
            surface.blit(m_sprite, (mx, my))
        else:
            pygame.draw.circle(surface, (150, 95, 45), (int(self.monkey_x), int(self.monkey_y - 24)), 16)

        # Stolen handbag attached to monkey
        if self.monkey_has_bag:
            bag_x = self.monkey_x + (12 if self.monkey_facing_right else -20)
            bag_y = self.monkey_y - 28
            pygame.draw.rect(surface, (255, 215, 0), (bag_x, bag_y, 16, 14), border_radius=3)
            pygame.draw.rect(surface, (160, 120, 20), (bag_x, bag_y, 16, 14), 1, border_radius=3)
            # Loot sparkles
            sparkle_x = bag_x + int(math.sin(pygame.time.get_ticks() * 0.01) * 8)
            pygame.draw.circle(surface, WHITE, (sparkle_x, int(bag_y - 4)), 2)

    def _draw_hud(self, surface: pygame.Surface) -> None:
        # Header banner
        banner = pygame.Rect(DISPLAY_WIDTH // 2 - 450, 16, 900, 68)
        pygame.draw.rect(surface, (14, 18, 28, 225), banner, border_radius=10)
        pygame.draw.rect(surface, (55, 80, 120), banner, 2, border_radius=10)

        t1 = self.font_title.render("LEVEL 4: ESCORT GRANDMOTHER TO THE AUTO-RICKSHAW", True, GOLD)
        surface.blit(t1, (DISPLAY_WIDTH // 2 - t1.get_width() // 2, 22))

        dist_to_goal = max(0, int((self.rickshaw_x - self.woman_x) / 10))
        h_text = f"Stay close to guide Grandmother ({dist_to_goal}m to Rickshaw)  |  SPACE / W: JUMP & SCARE THE MONKEY!"
        t2 = self.font_sub.render(h_text, True, (210, 225, 245))
        surface.blit(t2, (DISPLAY_WIDTH // 2 - t2.get_width() // 2, 52))

        # Dynamic Alert Popup
        if self.alert_timer > 0:
            abox = pygame.Rect(DISPLAY_WIDTH // 2 - 300, 92, 600, 36)
            pygame.draw.rect(surface, (20, 24, 36, 235), abox, border_radius=8)
            pygame.draw.rect(surface, self.alert_color, abox, 2, border_radius=8)
            asurf = self.font_badge.render(self.alert_message, True, self.alert_color)
            surface.blit(asurf, asurf.get_rect(center=abox.center))

        # Win Card
        if self.win_timer > 0:
            win_box = pygame.Rect(DISPLAY_WIDTH // 2 - 280, DISPLAY_HEIGHT // 2 - 60, 560, 100)
            pygame.draw.rect(surface, (15, 45, 25), win_box, border_radius=14)
            pygame.draw.rect(surface, (70, 220, 120), win_box, 3, border_radius=14)
            w_text = self.font_large.render("GRANDMOTHER IS SAFE!", True, (120, 255, 160))
            surface.blit(w_text, (win_box.centerx - w_text.get_width() // 2, win_box.y + 14))
            sub = self.font_sub.render("Auto-Rickshaw boarded! Proceeding to Final Exam Gate...", True, WHITE)
            surface.blit(sub, (win_box.centerx - sub.get_width() // 2, win_box.y + 64))
