# boss.py — The Chief Proctor / Examiner AI Boss Entity
import math
import random
import pygame

from settings import (
    SCREEN_WIDTH, SCREEN_HEIGHT, GROUND_Y,
    BOSS_MAX_HP, BOSS_WIDTH, BOSS_HEIGHT,
    RED, YELLOW, CYAN, GOLD, WHITE
)
from ai.boss_ai import BossAI


class BossProjectile(pygame.sprite.Sprite):
    """Flying question papers launched by the Boss."""
    def __init__(self, x: float, y: float, vel_x: float, vel_y: float) -> None:
        super().__init__()
        self.rect = pygame.Rect(int(x), int(y), 16, 12)
        self.pos_x = float(x)
        self.pos_y = float(y)
        self.vel_x = vel_x
        self.vel_y = vel_y
        self.rot = 0.0

    def update(self) -> None:
        self.pos_x += self.vel_x
        self.pos_y += self.vel_y
        self.rect.x = int(self.pos_x)
        self.rect.y = int(self.pos_y)
        self.rot += 12.0

    def draw(self, surface: pygame.Surface) -> None:
        # White paper with red exam header lines
        p_surf = pygame.Surface((16, 12), pygame.SRCALPHA)
        p_surf.fill((250, 250, 255))
        pygame.draw.rect(p_surf, (220, 50, 50), (2, 2, 12, 2))
        pygame.draw.rect(p_surf, (160, 160, 180), (2, 6, 12, 1))
        pygame.draw.rect(p_surf, (160, 160, 180), (2, 9, 8, 1))
        rotated = pygame.transform.rotate(p_surf, self.rot)
        rot_rect = rotated.get_rect(center=self.rect.center)
        surface.blit(rotated, rot_rect)


class Shockwave(pygame.sprite.Sprite):
    """Ground shockwave from Exam Bell Slam."""
    def __init__(self, start_x: float, direction: int) -> None:
        super().__init__()
        self.rect = pygame.Rect(int(start_x), GROUND_Y - 18, 24, 18)
        self.pos_x = float(start_x)
        self.direction = direction
        self.speed = 4.5
        self.lifetime = 75

    def update(self) -> None:
        self.pos_x += self.speed * self.direction
        self.rect.x = int(self.pos_x)
        self.lifetime -= 1

    def draw(self, surface: pygame.Surface) -> None:
        pts = [
            (self.rect.left, self.rect.bottom),
            (self.rect.centerx, self.rect.top),
            (self.rect.right, self.rect.bottom)
        ]
        pygame.draw.polygon(surface, (255, 180, 40), pts)
        pygame.draw.polygon(surface, (255, 240, 120), [
            (self.rect.left + 4, self.rect.bottom),
            (self.rect.centerx, self.rect.top + 4),
            (self.rect.right - 4, self.rect.bottom)
        ])


class Boss(pygame.sprite.Sprite):
    """
    The Chief Invigilator / Examiner AI.
    Features state machine attack choreography driven by BossAI.
    """
    def __init__(self, arena_left_x: float) -> None:
        super().__init__()
        self.arena_left = arena_left_x
        self.arena_right = arena_left_x + SCREEN_WIDTH

        self.width = BOSS_WIDTH
        self.height = BOSS_HEIGHT
        self.base_y = GROUND_Y - self.height - 40
        self.rect = pygame.Rect(int(self.arena_right - 120), int(self.base_y), self.width, self.height)

        self.hp = BOSS_MAX_HP
        self.max_hp = BOSS_MAX_HP
        self.alive = True

        # AI Agent
        self.ai = BossAI()

        # Attack state machine
        self.state = "hover"   # 'hover', 'telegraph', 'attacking', 'breather'
        self.current_attack = "none"
        self.state_timer = 60
        self.vulnerable = False
        self.hover_angle = 0.0

        # Projectiles and shockwaves
        self.projectiles = pygame.sprite.Group()
        self.shockwaves = pygame.sprite.Group()

        # Hit flashing
        self.hit_flash = 0
        self.dash_dir = -1

    def take_hit(self) -> bool:
        """Called when player stomps the boss or hits during breather."""
        if self.hit_flash > 0:
            return False
        self.hp -= 1
        self.hit_flash = 25
        if self.hp <= 0:
            self.hp = 0
            self.alive = False
        return True

    def update(self, player) -> None:
        """Updates boss logic, AI decisions, attacks, and projectiles."""
        if not self.alive:
            return

        if self.hit_flash > 0:
            self.hit_flash -= 1

        self.hover_angle += 0.06
        self.state_timer -= 1

        # Track player movement relative to boss
        if player.vel_x < -0.5:
            self.ai.record_player_action("left")
        elif player.vel_x > 0.5:
            self.ai.record_player_action("right")
        if not player.on_ground and player.vel_y < 0:
            self.ai.record_player_action("jump")

        # ── State Machine ──
        if self.state == "hover":
            self.vulnerable = False
            # Smooth hover bob
            self.rect.y = int(self.base_y + math.sin(self.hover_angle) * 14)

            # Move slightly toward player's relative horizontal side
            target_x = self.arena_right - 130
            self.rect.x += int((target_x - self.rect.x) * 0.05)

            if self.state_timer <= 0:
                # Decide next move using BossAI
                self.current_attack = self.ai.decide_next_attack(
                    player.hp, self.hp, player.rect.x, self.rect.x
                )
                if self.current_attack == "breather":
                    self.state = "breather"
                    self.vulnerable = True
                    self.state_timer = 110  # 1.8 seconds of vulnerability
                else:
                    self.state = "telegraph"
                    self.state_timer = 40   # telegraph warning before strike

        elif self.state == "telegraph":
            # Warning shake before striking
            shake = int(math.sin(self.hover_angle * 6) * 4)
            self.rect.x += shake
            if self.state_timer <= 0:
                self.state = "attacking"
                self._execute_attack(player)

        elif self.state == "attacking":
            if self.current_attack == "deadline_dash":
                self.rect.x += int(8.0 * self.dash_dir)
                if self.rect.left <= self.arena_left + 20:
                    self.dash_dir = 1
                elif self.rect.right >= self.arena_right - 20 and self.dash_dir == 1:
                    # Dash completed
                    self.state = "hover"
                    self.state_timer = 50

            elif self.current_attack == "exam_bell_slam":
                # Slam down to ground
                if self.rect.bottom < GROUND_Y:
                    self.rect.y += 10
                else:
                    self.rect.bottom = GROUND_Y
                    # Spawn left & right ground shockwaves
                    self.shockwaves.add(Shockwave(self.rect.left, -1))
                    self.shockwaves.add(Shockwave(self.rect.right, 1))
                    self.state = "breather"
                    self.vulnerable = True
                    self.state_timer = 70

            elif self.state_timer <= 0:
                self.state = "hover"
                self.state_timer = 45

        elif self.state == "breather":
            # Boss drops low and is stunned / overheated
            self.vulnerable = True
            self.rect.y = GROUND_Y - self.height + 6
            if self.state_timer <= 0:
                self.state = "hover"
                self.vulnerable = False
                self.state_timer = 50

        # Update active projectiles
        for p in list(self.projectiles):
            p.update()
            if (p.rect.right < self.arena_left or p.rect.left > self.arena_right or
                    p.rect.bottom > SCREEN_HEIGHT + 50):
                self.projectiles.remove(p)

        # Update active shockwaves
        for sw in list(self.shockwaves):
            sw.update()
            if sw.lifetime <= 0 or sw.rect.right < self.arena_left or sw.rect.left > self.arena_right:
                self.shockwaves.remove(sw)

    def _execute_attack(self, player) -> None:
        """Triggers the chosen attack action."""
        if self.current_attack == "question_paper_barrage":
            # Launch 3 spread question papers aimed at player
            dx = player.rect.centerx - self.rect.centerx
            dy = player.rect.centery - self.rect.centery
            dist = max(1.0, math.hypot(dx, dy))
            base_vx = (dx / dist) * 4.5
            base_vy = (dy / dist) * 4.5

            for angle_offset in [-0.25, 0.0, 0.25]:
                vx = base_vx * math.cos(angle_offset) - base_vy * math.sin(angle_offset)
                vy = base_vx * math.sin(angle_offset) + base_vy * math.cos(angle_offset)
                self.projectiles.add(BossProjectile(self.rect.centerx, self.rect.centery, vx, vy))
            self.state_timer = 45

        elif self.current_attack == "deadline_dash":
            self.dash_dir = -1
            self.rect.y = GROUND_Y - self.height - 8
            self.state_timer = 120

        elif self.current_attack == "exam_bell_slam":
            # Rise high then slam down
            self.rect.y = self.base_y - 60
            self.state_timer = 60

    def draw(self, surface: pygame.Surface, camera_offset: tuple) -> None:
        """Draw boss, telegraph markers, projectiles, and shockwaves."""
        screen_x = self.rect.x - camera_offset[0]
        screen_y = self.rect.y - camera_offset[1]
        draw_rect = pygame.Rect(screen_x, screen_y, self.width, self.height)

        # Draw shockwaves & projectiles (offset by camera)
        for sw in self.shockwaves:
            sw_draw = sw.rect.copy()
            sw_draw.x -= camera_offset[0]
            sw_draw.y -= camera_offset[1]
            sw.draw(surface)

        for p in self.projectiles:
            p_draw = p.rect.copy()
            p_draw.x -= camera_offset[0]
            p_draw.y -= camera_offset[1]
            p.draw(surface)

        if not self.alive:
            return

        # Telegraph Warning Reticle
        if self.state == "telegraph":
            t_surf = pygame.Surface((self.width + 24, self.height + 24), pygame.SRCALPHA)
            pygame.draw.rect(t_surf, (255, 50, 50, 110), (0, 0, self.width + 24, self.height + 24), 2, border_radius=8)
            surface.blit(t_surf, (draw_rect.x - 12, draw_rect.y - 12))

        # Boss Base Body: High-tech Invigilator Monitor Drone
        body_color = (255, 255, 255) if self.hit_flash > 0 else (45, 50, 68)
        if self.vulnerable:
            body_color = (130, 80, 50)  # Overheated copper color

        pygame.draw.rect(surface, body_color, draw_rect, border_radius=12)
        pygame.draw.rect(surface, (140, 160, 200), draw_rect, 2, border_radius=12)

        # Screen Monitor Face
        face_rect = pygame.Rect(draw_rect.x + 8, draw_rect.y + 12, draw_rect.width - 16, 40)
        face_bg = (15, 20, 30) if not self.vulnerable else (60, 20, 20)
        pygame.draw.rect(surface, face_bg, face_rect, border_radius=6)

        # Digital Eyes / AI Camera Iris
        eye_color = (255, 50, 50) if self.hp <= 3 else (60, 220, 255)
        if self.vulnerable:
            eye_color = (255, 220, 40)
            # Vulnerable "X X" eyes
            pygame.draw.line(surface, eye_color, (face_rect.centerx - 14, face_rect.centery - 6), (face_rect.centerx - 4, face_rect.centery + 6), 2)
            pygame.draw.line(surface, eye_color, (face_rect.centerx - 4, face_rect.centery - 6), (face_rect.centerx - 14, face_rect.centery + 6), 2)
            pygame.draw.line(surface, eye_color, (face_rect.centerx + 4, face_rect.centery - 6), (face_rect.centerx + 14, face_rect.centery + 6), 2)
            pygame.draw.line(surface, eye_color, (face_rect.centerx + 14, face_rect.centery - 6), (face_rect.centerx + 4, face_rect.centery + 6), 2)
        else:
            # Glowing Scanning Eye
            pygame.draw.circle(surface, eye_color, face_rect.center, 10)
            pygame.draw.circle(surface, WHITE, face_rect.center, 4)

        # "CHIEF EXAMINER" Badge Label
        font = pygame.font.SysFont("segoeui, arial", 10, bold=True)
        tag = font.render("PROCTOR AI", True, (240, 200, 60))
        surface.blit(tag, (draw_rect.centerx - tag.get_width() // 2, draw_rect.bottom - 22))

        # Floating Energy Orbs around boss
        orb_orbit = math.sin(self.hover_angle * 2) * 20
        pygame.draw.circle(surface, (255, 100, 100), (draw_rect.left - 6, int(draw_rect.centery + orb_orbit)), 4)
        pygame.draw.circle(surface, (255, 100, 100), (draw_rect.right + 6, int(draw_rect.centery - orb_orbit)), 4)
