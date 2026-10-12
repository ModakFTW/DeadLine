import pygame
from settings import (
    SCREEN_WIDTH, SCREEN_HEIGHT, TILE_SIZE, SPIKE_WIDTH, SPIKE_HEIGHT,
    ENEMY_WIDTH, ENEMY_HEIGHT, COLOR_SKY, COLOR_ROAD, COLOR_GROUND,
    COLOR_RED, COLOR_YELLOW, COLOR_GREEN, COLOR_WHITE, COLOR_DARK_GRAY
)
import sprite_loader

class Platform(pygame.sprite.Sprite):
    def __init__(self, x: int, y: int, width: int, height: int, is_ground: bool = True):
        super().__init__()
        self.rect = pygame.Rect(x, y, width, height)
        self.is_ground = is_ground

    def draw(self, surface: pygame.Surface, camera):
        draw_rect = camera.apply_rect(self.rect)
        color = COLOR_ROAD if self.is_ground else COLOR_GROUND
        pygame.draw.rect(surface, color, draw_rect)
        # Top curb edge
        pygame.draw.rect(surface, COLOR_YELLOW if self.is_ground else COLOR_WHITE,
                         (draw_rect.x, draw_rect.y, draw_rect.width, 4))

class TrafficCone(pygame.sprite.Sprite):
    """Spike hazard."""
    def __init__(self, x: int, y: int):
        super().__init__()
        self.rect = pygame.Rect(x, y - SPIKE_HEIGHT, SPIKE_WIDTH, SPIKE_HEIGHT)
        self.image = sprite_loader.load_traffic_cone()

    def draw(self, surface: pygame.Surface, camera):
        pos = camera.apply(self.rect)
        if self.image:
            surface.blit(self.image, pos)
        else:
            r = camera.apply_rect(self.rect)
            points = [(r.left, r.bottom), (r.right, r.bottom), (r.centerx, r.top)]
            pygame.draw.polygon(surface, COLOR_RED, points)

class StrayDog(pygame.sprite.Sprite):
    """Patrolling dog hazard."""
    def __init__(self, x: int, y: int, patrol_distance: int = 140, speed: float = 2.0):
        super().__init__()
        self.start_x = x
        self.patrol_distance = patrol_distance
        self.speed = speed
        self.direction = 1
        self.rect = pygame.Rect(x, y - ENEMY_HEIGHT, ENEMY_WIDTH, ENEMY_HEIGHT)
        self.frames_right = sprite_loader.load_dog_frames()
        self.frames_left = sprite_loader.load_dog_frames_left()
        self.anim_idx = 0.0

    def update(self):
        self.rect.x += int(self.speed * self.direction)
        if abs(self.rect.x - self.start_x) >= self.patrol_distance:
            self.direction *= -1

        self.anim_idx += 0.15

    def draw(self, surface: pygame.Surface, camera):
        frames = self.frames_right if self.direction > 0 else self.frames_left
        pos = camera.apply(self.rect)
        if frames:
            img = frames[int(self.anim_idx) % len(frames)]
            surface.blit(img, pos)
        else:
            r = camera.apply_rect(self.rect)
            pygame.draw.rect(surface, (170, 100, 40), r, border_radius=5)

class AutoRickshaw(pygame.sprite.Sprite):
    """Large moving or stationary street hazard."""
    def __init__(self, x: int, y: int, width: int = 140, height: int = 95):
        super().__init__()
        self.rect = pygame.Rect(x, y - height, width, height)
        self.image = sprite_loader.load_rickshaw(width, height)

    def draw(self, surface: pygame.Surface, camera):
        pos = camera.apply(self.rect)
        if self.image:
            surface.blit(self.image, pos)
        else:
            r = camera.apply_rect(self.rect)
            pygame.draw.rect(surface, COLOR_YELLOW, r, border_radius=6)
            pygame.draw.rect(surface, COLOR_GREEN, (r.x, r.bottom - 20, r.width, 20))

class GoalFlag(pygame.sprite.Sprite):
    """College gate / goal flag to finish the level."""
    def __init__(self, x: int, y: int):
        super().__init__()
        self.rect = pygame.Rect(x, y - 120, 50, 120)

    def draw(self, surface: pygame.Surface, camera):
        r = camera.apply_rect(self.rect)
        # Flag pole
        pygame.draw.rect(surface, COLOR_WHITE, (r.x, r.y, 8, r.height))
        # Banner
        banner_poly = [(r.x + 8, r.y), (r.x + 48, r.y + 20), (r.x + 8, r.y + 40)]
        pygame.draw.polygon(surface, COLOR_GREEN, banner_poly)


class Grandma(pygame.sprite.Sprite):
    """Slow moving obstacle on footpaths."""
    def __init__(self, x: int, y: int, width: int = 54, height: int = 84):
        super().__init__()
        self.rect = pygame.Rect(x, y - height, width, height)
        self.start_x = x
        self.speed = 1.0
        self.direction = 1
        self.frames_right = sprite_loader.load_grandma_frames(width, height)
        self.frames_left = sprite_loader.load_grandma_frames_left(width, height)
        self.anim_idx = 0.0

    def update(self):
        self.rect.x += int(self.speed * self.direction)
        if abs(self.rect.x - self.start_x) >= 90:
            self.direction *= -1
        self.anim_idx += 0.1

    def draw(self, surface: pygame.Surface, camera):
        frames = self.frames_right if self.direction > 0 else self.frames_left
        pos = camera.apply(self.rect)
        if frames:
            img = frames[int(self.anim_idx) % len(frames)]
            surface.blit(img, pos)
        else:
            r = camera.apply_rect(self.rect)
            pygame.draw.rect(surface, (180, 80, 160), r, border_radius=6)
            pygame.draw.circle(surface, (230, 200, 170), (r.centerx, r.top + 16), 14)

class Monkey(pygame.sprite.Sprite):
    """Jumping rooftop / platform monkey hazard (tall/narrow, +25% height)."""
    def __init__(self, x: int, y: int, width: int = 52, height: int = 60):
        super().__init__()
        self.rect = pygame.Rect(x, y - height, width, height)
        self.base_y = y - height
        self.vel_y = 0.0
        self.speed = 2.4
        self.direction = 1
        self.start_x = x
        self.sprites = sprite_loader.load_monkey_sprites(width, height)

    def update(self):
        self.rect.x += int(self.speed * self.direction)
        if abs(self.rect.x - self.start_x) >= 140:
            self.direction *= -1

        # Periodic hop
        if self.rect.y >= self.base_y:
            self.vel_y = -8.0
        self.vel_y += 0.4
        self.rect.y += int(self.vel_y)
        if self.rect.y > self.base_y:
            self.rect.y = self.base_y
            self.vel_y = 0.0

    def draw(self, surface: pygame.Surface, camera):
        pos = camera.apply(self.rect)
        sp_key = "walk_right" if self.direction > 0 else "walk_left"
        img = self.sprites.get(sp_key) if self.sprites else None
        if img:
            surface.blit(img, pos)
        else:
            r = camera.apply_rect(self.rect)
            pygame.draw.rect(surface, (120, 65, 20), r, border_radius=6)
            pygame.draw.circle(surface, (200, 140, 80), (r.centerx, r.top + 12), 10)
