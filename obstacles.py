import pygame
import math
from settings import (
    TILE_SIZE, GROUND_BROWN, GROUND_TOP, GROUND_Y,
    SPIKE_WIDTH, SPIKE_HEIGHT, SPIKE_COLOR,
    GAP_WIDTH_TILES,
    MOVING_PLATFORM_WIDTH, MOVING_PLATFORM_HEIGHT, PLATFORM_COLOR,
    MOVING_PLATFORM_RANGE, MOVING_PLATFORM_SPEED,
    ENEMY_WIDTH, ENEMY_HEIGHT, ENEMY_COLOR,
    ENEMY_PATROL_RANGE, ENEMY_SPEED
)
import sprite_loader

class Ground(pygame.sprite.Sprite):
    """
    A single ground tile — Indian city sidewalk/road.
    """
    def __init__(self, x: int, y: int) -> None:
        super().__init__()
        self.rect = pygame.Rect(x, y, TILE_SIZE, TILE_SIZE)
        self.obstacle_type = 'ground'

    def update(self) -> None:
        pass

    def draw(self, surface: pygame.Surface, camera_offset: tuple) -> None:
        draw_rect = self.rect.copy()
        draw_rect.x -= camera_offset[0]
        draw_rect.y -= camera_offset[1]
        # Sidewalk concrete base
        pygame.draw.rect(surface, (115, 110, 105), draw_rect)
        # Curb stone highlight
        top_rect = pygame.Rect(draw_rect.x, draw_rect.y, TILE_SIZE, 3)
        pygame.draw.rect(surface, (170, 165, 155), top_rect)
        # Seam groove
        seam_rect = pygame.Rect(draw_rect.right - 1, draw_rect.y, 1, TILE_SIZE)
        pygame.draw.rect(surface, (90, 85, 80), seam_rect)


class Spike(pygame.sprite.Sprite):
    """
    Traffic cone hazard sitting on the sidewalk.
    """
    def __init__(self, x: int) -> None:
        super().__init__()
        self.rect = pygame.Rect(x, GROUND_Y - SPIKE_HEIGHT, SPIKE_WIDTH, SPIKE_HEIGHT)
        self.obstacle_type = 'spike'
        self.sprite = None

    def update(self) -> None:
        pass

    def draw(self, surface: pygame.Surface, camera_offset: tuple) -> None:
        draw_rect = self.rect.copy()
        draw_rect.x -= camera_offset[0]
        draw_rect.y -= camera_offset[1]

        if self.sprite is None:
            self.sprite = sprite_loader.load_traffic_cone()

        if self.sprite is not None:
            surface.blit(self.sprite, draw_rect)
        else:
            # Clean geometric cone fallback
            points = [
                (draw_rect.left + 4, draw_rect.bottom),
                (draw_rect.right - 4, draw_rect.bottom),
                (draw_rect.centerx, draw_rect.top)
            ]
            pygame.draw.polygon(surface, (245, 90, 30), points)
            pygame.draw.rect(surface, (230, 80, 20), (draw_rect.left, draw_rect.bottom - 6, draw_rect.width, 6))


class Gap:
    """
    The absence of ground tiles — a dangerous road pothole.
    """
    def __init__(self, x: int, width_tiles: int = GAP_WIDTH_TILES) -> None:
        self.x = x
        self.width_tiles = width_tiles
        self.obstacle_type = 'gap'


class MovingPlatform(pygame.sprite.Sprite):
    """
    Elevated Floating Metro / Construction Scaffolding Platform.
    Smooth, solid mechanical platform that glides horizontally.
    """
    def __init__(self, x: int, base_y: int) -> None:
        super().__init__()
        self.rect = pygame.Rect(x, base_y, MOVING_PLATFORM_WIDTH, MOVING_PLATFORM_HEIGHT)
        self.base_x = float(x)
        self.base_y = float(base_y)
        self.obstacle_type = 'moving_platform'
        
        # Horizontal gliding movement
        self.vel_x = MOVING_PLATFORM_SPEED
        self.vel_y = 0.0
        self.direction_x = 1
        self.direction = 1
        self.pulse = 0.0

    def update(self) -> None:
        self.rect.x += int(self.vel_x * self.direction_x)
        if self.rect.x >= self.base_x + MOVING_PLATFORM_RANGE:
            self.rect.x = int(self.base_x + MOVING_PLATFORM_RANGE)
            self.direction_x = -1
        elif self.rect.x <= self.base_x - MOVING_PLATFORM_RANGE:
            self.rect.x = int(self.base_x - MOVING_PLATFORM_RANGE)
            self.direction_x = 1

        self.pulse += 0.05

    def draw(self, surface: pygame.Surface, camera_offset: tuple) -> None:
        draw_rect = self.rect.copy()
        draw_rect.x -= camera_offset[0]
        draw_rect.y -= camera_offset[1]

        # Industrial high-tech metro platform styling
        # Base slab
        pygame.draw.rect(surface, (55, 65, 80), draw_rect, border_radius=4)
        # Yellow hazard top stripe
        top_stripe = pygame.Rect(draw_rect.x + 2, draw_rect.y + 1, draw_rect.width - 4, 3)
        pygame.draw.rect(surface, (250, 205, 45), top_stripe)
        # Metallic outline
        pygame.draw.rect(surface, (120, 140, 170), draw_rect, 1, border_radius=4)
        
        # Blue thruster indicator lights underneath
        light_glow = int(180 + math.sin(self.pulse) * 60)
        c = (50, light_glow, 255)
        pygame.draw.circle(surface, c, (draw_rect.left + 14, draw_rect.bottom + 1), 3)
        pygame.draw.circle(surface, c, (draw_rect.right - 14, draw_rect.bottom + 1), 3)


class Enemy(pygame.sprite.Sprite):
    """
    A stray dog patrolling horizontally with animated walk.
    """
    def __init__(self, x: int) -> None:
        super().__init__()
        self.rect = pygame.Rect(x, GROUND_Y - ENEMY_HEIGHT, ENEMY_WIDTH, ENEMY_HEIGHT)
        self.start_x = x
        self.obstacle_type = 'enemy'
        self.alive = True
        self.direction = 1
        self.frames_right = []
        self.frames_left = []
        self.anim_timer = 0.0

    def update(self) -> None:
        if not self.alive:
            return
            
        self.rect.x += int(ENEMY_SPEED * self.direction)
        if self.rect.x >= self.start_x + ENEMY_PATROL_RANGE:
            self.rect.x = self.start_x + ENEMY_PATROL_RANGE
            self.direction = -1
        elif self.rect.x <= self.start_x - ENEMY_PATROL_RANGE:
            self.rect.x = self.start_x - ENEMY_PATROL_RANGE
            self.direction = 1

        self.anim_timer += 0.12

    def draw(self, surface: pygame.Surface, camera_offset: tuple) -> None:
        if not self.alive:
            return
        draw_rect = self.rect.copy()
        draw_rect.x -= camera_offset[0]
        draw_rect.y -= camera_offset[1]

        if not self.frames_right:
            self.frames_right = sprite_loader.load_dog_frames()
            self.frames_left = sprite_loader.load_dog_frames_left()

        frames = self.frames_right if self.direction > 0 else self.frames_left

        if frames:
            idx = int(self.anim_timer) % len(frames)
            surface.blit(frames[idx], draw_rect)
        else:
            # Fallback stylized enemy dog
            pygame.draw.rect(surface, (180, 110, 50), draw_rect, border_radius=4)
