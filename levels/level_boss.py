"""levels/level_boss.py - Professor Terminus 3-phase boss fight for DeadLine."""
import pygame
import math
import random
from settings import (
    SCREEN_WIDTH, SCREEN_HEIGHT, COLOR_DARK_GRAY, COLOR_RED, COLOR_YELLOW,
    COLOR_BLUE, COLOR_GREEN, COLOR_WHITE, COLOR_PURPLE, COLOR_ORANGE,
    BULLET_SPEED, RULER_REACH, RULER_DAMAGE, SLINGSHOT_DAMAGE,
    BOSS_WIDTH, BOSS_HEIGHT, BOSS_HP
)
from player import Player
from levels.hazards import Platform
import sprite_loader

# ── Mini quiz for HP restore between phases ────────────────────────────────
PHASE_QUESTIONS = [
    {
        "question": "The Markov chain selects the next obstacle based on:",
        "options": ["Random seed", "Previous obstacle type", "Player HP", "Timer"],
        "correct": 1
    },
    {
        "question": "The Elo-style difficulty tracker adjusts score using:",
        "options": ["Fixed table", "Player name", "Expected vs actual outcome", "Random roll"],
        "correct": 2
    },
]


class Projectile:
    def __init__(self, x, y, dx, dy, is_boss=False, is_fireball=False):
        self.rect = pygame.Rect(x - 7, y - 7, 14, 14)
        self.dx = dx
        self.dy = dy
        self.is_boss = is_boss
        self.is_fireball = is_fireball

    def update(self):
        self.rect.x += int(self.dx)
        self.rect.y += int(self.dy)
        if self.is_fireball:
            self.dy = min(self.dy + 0.18, 6.0)   # slight gravity arc

    def draw(self, surface):
        if self.is_fireball:
            pygame.draw.circle(surface, COLOR_ORANGE, self.rect.center, 10)
            pygame.draw.circle(surface, COLOR_YELLOW, self.rect.center, 6)
        else:
            pygame.draw.circle(surface, COLOR_YELLOW, self.rect.center, 6)


class BossTerminus:
    def __init__(self, x, y):
        self.start_x = x
        self.rect = pygame.Rect(x, y - BOSS_HEIGHT, BOSS_WIDTH, BOSS_HEIGHT)
        self.hp = BOSS_HP
        self.max_hp = BOSS_HP
        self.facing_left = True
        self.attack_timer = 0
        self.phase = 1          # 1, 2, 3
        self.move_speed = 1.2
        self.direction = -1
        self.sprites = sprite_loader.load_boss_sprites(BOSS_WIDTH, BOSS_HEIGHT)
        self.state = "idle"

    @property
    def phase(self):
        return self._phase

    @phase.setter
    def phase(self, v):
        self._phase = v
        # Get faster and more aggressive each phase
        self.move_speed = 1.2 + (v - 1) * 0.9
        self.cast_interval = max(40, 90 - (v - 1) * 25)

    def update(self, player_x):
        self.facing_left = self.rect.centerx > player_x
        self.attack_timer += 1

        # Phase 2/3: boss walks toward player
        if self._phase >= 2:
            dx = -self.move_speed if self.facing_left else self.move_speed
            self.rect.x += int(dx)
            self.rect.x = max(SCREEN_WIDTH // 2, min(SCREEN_WIDTH - BOSS_WIDTH - 10, self.rect.x))

    def draw(self, surface):
        key = f"{self.state}_{'left' if self.facing_left else 'right'}"
        img = self.sprites.get(key) if self.sprites else None
        if img:
            surface.blit(img, self.rect.topleft)
        else:
            color = [COLOR_PURPLE, (120, 20, 140), (180, 10, 60)][self._phase - 1]
            pygame.draw.rect(surface, color, self.rect, border_radius=8)
            # Cape
            cape_pts = [
                (self.rect.left, self.rect.top + 30),
                (self.rect.left - 20, self.rect.bottom),
                (self.rect.right + 20, self.rect.bottom),
                (self.rect.right, self.rect.top + 30),
            ]
            pygame.draw.polygon(surface, (50, 0, 70), cape_pts)
            # Glasses (facing dir)
            gx = self.rect.left + 22 if self.facing_left else self.rect.right - 42
            pygame.draw.circle(surface, COLOR_WHITE, (gx, self.rect.top + 28), 8, 2)
            pygame.draw.circle(surface, COLOR_WHITE, (gx + 20, self.rect.top + 28), 8, 2)
            # Phase glow ring
            glow_color = [(0, 200, 255), (255, 140, 0), (255, 30, 30)][self._phase - 1]
            pygame.draw.rect(surface, glow_color, self.rect, 3, border_radius=8)


class MiniQuiz:
    """Brief in-fight quiz; correct answers restore player HP."""
    def __init__(self, questions):
        self.questions = questions
        self.idx = 0
        self.done = False
        self.score = 0
        self.selected = -1
        self.feedback_timer = 0
        self.font_q = pygame.font.SysFont("segoeui,arial", 26, bold=True)
        self.font_o = pygame.font.SysFont("segoeui,arial", 22)

    def handle_event(self, event):
        if self.done or self.feedback_timer > 0:
            return
        if event.type == pygame.KEYDOWN and pygame.K_1 <= event.key <= pygame.K_4:
            self._submit(event.key - pygame.K_1)

    def _submit(self, idx):
        q = self.questions[self.idx]
        self.selected = idx
        if idx == q["correct"]:
            self.score += 1
        self.feedback_timer = 40

    def update(self):
        if self.feedback_timer > 0:
            self.feedback_timer -= 1
            if self.feedback_timer == 0:
                self.idx += 1
                self.selected = -1
                if self.idx >= len(self.questions):
                    self.done = True

    def draw(self, surface):
        if self.done:
            return
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 170))
        surface.blit(overlay, (0, 0))

        q = self.questions[self.idx]
        q_surf = self.font_q.render(q["question"], True, COLOR_WHITE)
        surface.blit(q_surf, ((SCREEN_WIDTH - q_surf.get_width()) // 2, 200))

        for i, opt in enumerate(q["options"]):
            rect = pygame.Rect((SCREEN_WIDTH - 700) // 2, 280 + i * 70, 700, 52)
            bg = COLOR_DARK_GRAY
            if self.feedback_timer > 0:
                if i == q["correct"]:
                    bg = COLOR_GREEN
                elif i == self.selected:
                    bg = COLOR_RED
            pygame.draw.rect(surface, bg, rect, border_radius=6)
            pygame.draw.rect(surface, COLOR_WHITE, rect, 2, border_radius=6)
            t = self.font_o.render(f"{i+1}. {opt}", True, COLOR_WHITE)
            surface.blit(t, (rect.x + 20, rect.y + 12))


class LevelBossFight:
    """Level 5 – Professor Terminus 3-phase arena."""

    def __init__(self, difficulty_tracker=None, game_state=None):
        self.difficulty_tracker = difficulty_tracker
        self.game_state = game_state or {}
        self.ground_y = SCREEN_HEIGHT - 100
        self.player = Player(150, self.ground_y - 100)

        has_powerup = self.game_state.get("has_rickshaw_powerup", False)
        self.player.has_rickshaw_powerup = has_powerup
        if has_powerup and not self.player.has_rickshaw:
            self.player.enable_rickshaw_mode()

        self._v_held = False

        self.boss = BossTerminus(SCREEN_WIDTH - 250, self.ground_y)

        self.platforms = pygame.sprite.Group(
            Platform(0, self.ground_y, SCREEN_WIDTH, 100, is_ground=True),
            Platform(230, self.ground_y - 150, 160, 22, is_ground=False),
            Platform(SCREEN_WIDTH - 390, self.ground_y - 150, 160, 22, is_ground=False),
        )

        self.player_projectiles = []
        self.boss_projectiles = []

        self.ruler_cd = 0
        self.sling_cd = 0
        self.slash_timer = 0
        self.is_slashing = False

        self.phase_quiz = None
        self.in_phase_transition = False
        self.phase_transitioned_to = 0

        self.completed = False
        self.failed = False

        self.font_hud = pygame.font.SysFont("segoeui,arial", 20, bold=True)

    # ─── Input ────────────────────────────────────────────────────────────
    def handle_input(self):
        if self.in_phase_transition:
            return
        self.player.handle_input()
        keys = pygame.key.get_pressed()

        # Rickshaw boost on 'V' (edge-triggered, 6s invincibility + speed)
        v_down = keys[pygame.K_v]
        if v_down and not self._v_held:
            self.player.try_activate_rickshaw_boost()
        self._v_held = v_down

        phase = self.boss.phase

        # Slingshot (Z/J) – Phase 1 and 3
        if phase != 2 and (keys[pygame.K_z] or keys[pygame.K_j]) and self.sling_cd <= 0:
            dx = BULLET_SPEED if self.player.facing_right else -BULLET_SPEED
            sx = self.player.rect.right if self.player.facing_right else self.player.rect.left
            self.player_projectiles.append(
                Projectile(sx, self.player.rect.centery - 10, dx, 0, is_boss=False)
            )
            self.sling_cd = 22

        # Ruler slash (X/K) – Phase 2 and 3
        if phase != 1 and (keys[pygame.K_x] or keys[pygame.K_k]) and self.ruler_cd <= 0:
            self.is_slashing = True
            self.slash_timer = 14
            self.ruler_cd = 28
            slash_rect = pygame.Rect(
                self.player.rect.right if self.player.facing_right else self.player.rect.left - RULER_REACH,
                self.player.rect.top, RULER_REACH, self.player.rect.height
            )
            if slash_rect.colliderect(self.boss.rect):
                self.boss.hp = max(0, self.boss.hp - RULER_DAMAGE)
                self.boss.state = "hurt"

    # ─── Update ───────────────────────────────────────────────────────────
    def update(self):
        if self.completed or self.failed:
            return

        # Phase-transition quiz
        if self.in_phase_transition:
            if self.phase_quiz:
                self.phase_quiz.update()
                if self.phase_quiz.done:
                    self._finish_phase_quiz()
            return

        self.player.update(self.platforms)
        self.boss.update(self.player.rect.centerx)

        # Cooldowns
        for attr in ("sling_cd", "ruler_cd"):
            v = getattr(self, attr)
            if v > 0:
                setattr(self, attr, v - 1)
        if self.slash_timer > 0:
            self.slash_timer -= 1
            if self.slash_timer == 0:
                self.is_slashing = False

        # Boss attack pattern
        if self.boss.attack_timer % self.boss.cast_interval == 0:
            self._boss_attack()

        # Move player projectiles
        for p in list(self.player_projectiles):
            p.update()
            if p.rect.colliderect(self.boss.rect):
                self.boss.hp = max(0, self.boss.hp - SLINGSHOT_DAMAGE)
                self.boss.state = "hurt"
                self.player_projectiles.remove(p)
            elif not (0 <= p.rect.x <= SCREEN_WIDTH):
                self.player_projectiles.remove(p)

        # Move boss projectiles
        for bp in list(self.boss_projectiles):
            bp.update()
            if bp.rect.colliderect(self.player.rect):
                self.player.take_damage(1)
                self.boss_projectiles.remove(bp)
            elif bp.rect.y > SCREEN_HEIGHT + 50 or not (0 <= bp.rect.x <= SCREEN_WIDTH):
                self.boss_projectiles.remove(bp)

        # Contact with boss
        if self.player.rect.colliderect(self.boss.rect) and self.boss.phase >= 2:
            self.player.take_damage(1)

        # Phase transitions at 200 and 100 HP
        hp = self.boss.hp
        phase = self.boss.phase
        if phase == 1 and hp <= 200:
            self._start_phase_transition(2)
            return
        if phase == 2 and hp <= 100:
            self._start_phase_transition(3)
            return

        if self.boss.hp <= 0:
            self.completed = True
        if self.player.hp <= 0:
            self.failed = True

    def _boss_attack(self):
        phase = self.boss.phase
        cx, cy = self.boss.rect.centerx, self.boss.rect.centery

        # Phase 1: Triple spread slingshot
        if phase == 1:
            for spread in (-0.2, 0.0, 0.2):
                dx = -7.0 if self.boss.facing_left else 7.0
                self.boss_projectiles.append(
                    Projectile(cx, cy, dx, math.sin(spread) * 4.0, is_boss=True)
                )

        # Phase 2: Fireballs with arc
        elif phase == 2:
            for i in range(3):
                dx = -6.0 if self.boss.facing_left else 6.0
                self.boss_projectiles.append(
                    Projectile(cx, cy - 20 + i * 20, dx, -2.0 + i * 1.0,
                               is_boss=True, is_fireball=True)
                )

        # Phase 3: Both spreads AND fireballs
        elif phase == 3:
            for spread in (-0.3, 0.0, 0.3):
                dx = -9.0 if self.boss.facing_left else 9.0
                self.boss_projectiles.append(
                    Projectile(cx, cy, dx, math.sin(spread) * 5.0, is_boss=True)
                )
            self.boss_projectiles.append(
                Projectile(cx, cy - 30, -5.5 if self.boss.facing_left else 5.5,
                           -3.0, is_boss=True, is_fireball=True)
            )

    def _start_phase_transition(self, new_phase):
        self.in_phase_transition = True
        self.phase_transitioned_to = new_phase
        self.boss_projectiles.clear()
        self.player_projectiles.clear()
        self.phase_quiz = MiniQuiz(PHASE_QUESTIONS[:1] if new_phase == 2 else PHASE_QUESTIONS[1:])

    def _finish_phase_quiz(self):
        q = self.phase_quiz
        # Restore HP: 1/2 correct → 50% lost HP, 2/2 → full restore
        lost = self.player.max_hp - self.player.hp
        if q.score == len(q.questions):
            self.player.hp = self.player.max_hp
        elif q.score >= 1:
            self.player.hp = min(self.player.max_hp, self.player.hp + lost // 2)

        self.boss.phase = self.phase_transitioned_to
        self.in_phase_transition = False
        self.phase_quiz = None

    # ─── Draw ────────────────────────────────────────────────────────────
    def draw(self, surface):
        surface.fill(COLOR_DARK_GRAY)

        # Arena background
        board = pygame.Rect(60, 30, SCREEN_WIDTH - 120, 210)
        pygame.draw.rect(surface, (22, 42, 28), board, border_radius=6)
        pygame.draw.rect(surface, (110, 80, 50), board, 6, border_radius=6)

        class DummyCam:
            def apply_rect(self, r): return r
            def apply(self, r): return r.topleft

        dc = DummyCam()
        for plat in self.platforms:
            plat.draw(surface, dc)

        self.boss.draw(surface)
        self.player.draw(surface, dc)

        if self.is_slashing:
            sx = self.player.rect.right if self.player.facing_right else self.player.rect.left - RULER_REACH
            pygame.draw.rect(surface, (210, 225, 240),
                             (sx, self.player.rect.centery - 8, RULER_REACH, 16),
                             border_radius=4)

        for p in self.player_projectiles:
            p.draw(surface)
        for bp in self.boss_projectiles:
            bp.draw(surface)

        self._draw_hud(surface)

        if self.in_phase_transition and self.phase_quiz:
            self.phase_quiz.draw(surface)

        # Powerup indicator
        if self.player.has_rickshaw_powerup:
            label = "⚡ V: Rickshaw Boost" + (" ACTIVE!" if self.player.powerup_timer > 0 else "")
            t = self.font_hud.render(label, True, COLOR_YELLOW)
            surface.blit(t, (20, SCREEN_HEIGHT - 35))

    def _draw_hud(self, surface):
        bw, bh = 600, 22
        bx = (SCREEN_WIDTH - bw) // 2
        by = 20
        pygame.draw.rect(surface, (30, 30, 30), (bx, by, bw, bh), border_radius=4)
        ratio = max(0.0, self.boss.hp / self.boss.max_hp)
        bar_color = [COLOR_GREEN, COLOR_ORANGE, COLOR_RED][self.boss.phase - 1]
        pygame.draw.rect(surface, bar_color, (bx, by, int(bw * ratio), bh), border_radius=4)
        pygame.draw.rect(surface, COLOR_WHITE, (bx, by, bw, bh), 2, border_radius=4)
        label = f"PROFESSOR TERMINUS   Phase {self.boss.phase}/3   {self.boss.hp}/{self.boss.max_hp}"
        t = self.font_hud.render(label, True, COLOR_WHITE)
        surface.blit(t, (bx + 10, by - 22))

        # Player hp
        for i in range(self.player.max_hp):
            c = COLOR_RED if i < self.player.hp else (50, 50, 50)
            pygame.draw.rect(surface, c, (20 + i * 26, 20, 20, 20), border_radius=4)
