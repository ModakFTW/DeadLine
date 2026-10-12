import pygame
import math
from settings import (
    PLAYER_WIDTH, PLAYER_HEIGHT, PLAYER_COLOR,
    PLAYER_MAX_HP, PLAYER_SPEED,
    GRAVITY, MAX_FALL_SPEED,
    JUMP_FORCE, SCREEN_HEIGHT, INVINCIBILITY_FRAMES,
    COYOTE_TIME, JUMP_BUFFER_TIME, FPS
)
import sprite_loader

RICKSHAW_BOOST_DURATION = 6 * FPS  # 6 seconds of invincibility + speed
RICKSHAW_BOOST_SPEED_MULT = 1.6    # extra multiplier while boost is active

class Player(pygame.sprite.Sprite):
    """
    The main player character sprite with run animation,
    platform riding, and standard physics.
    """
    def __init__(self, x: int, y: int) -> None:
        super().__init__()
        self.image = pygame.Surface((PLAYER_WIDTH, PLAYER_HEIGHT))
        self.image.fill(PLAYER_COLOR)
        self.rect = self.image.get_rect(topleft=(x, y))
        self.vel_x = 0.0
        self.vel_y = 0.0
        self.hp = PLAYER_MAX_HP
        self.alive = True
        self.invincible_timer = 0
        self.coyote_timer = 0
        self.jump_buffer = 0
        self.on_ground = False
        self.current_platform = None
        self.checkpoint_pos = (x, y)
        self.facing_right = True

        # Animation state
        self.frames_right = []
        self.frames_left = []
        self.anim_timer = 0.0
        self.anim_speed = 0.20

        # Rickshaw Powerup Mode (unlocked with 4/5 in Level 1)
        self.has_rickshaw = False
        self.rickshaw_sprite_right = None
        self.rickshaw_sprite_left = None
        # V-activated boost: 6s invincibility + speed (requires rickshaw unlock)
        self.has_rickshaw_powerup = False
        self.powerup_timer = 0

    @property
    def boost_active(self) -> bool:
        return self.powerup_timer > 0

    def try_activate_rickshaw_boost(self) -> bool:
        """Activate 6s invincibility + speed with the 'V' key. Returns True if triggered."""
        if not (self.has_rickshaw or self.has_rickshaw_powerup):
            return False
        if self.powerup_timer > 0:
            return False  # already running
        self.powerup_timer = RICKSHAW_BOOST_DURATION
        return True

    def enable_rickshaw_mode(self) -> None:
        """Equip the student with an auto-rickshaw mount."""
        self.has_rickshaw = True
        self.has_rickshaw_powerup = True
        self.rickshaw_sprite_right = sprite_loader.load_rickshaw(60, 42)
        if self.rickshaw_sprite_right:
            self.rickshaw_sprite_left = pygame.transform.flip(self.rickshaw_sprite_right, True, False)

    def handle_input(self, keys: pygame.key.ScancodeWrapper) -> None:
        """
        Reads WASD/arrow keys for horizontal movement and Space for jumping.
        """
        move_speed = PLAYER_SPEED * 1.55 if self.has_rickshaw else PLAYER_SPEED
        if self.powerup_timer > 0:
            move_speed *= RICKSHAW_BOOST_SPEED_MULT
        self.vel_x = 0
        if keys[pygame.K_LEFT] or keys[pygame.K_a]:
            self.vel_x = -move_speed
            self.facing_right = False
        if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
            self.vel_x = move_speed
            self.facing_right = True
            
        if keys[pygame.K_SPACE]:
            self.jump_buffer = JUMP_BUFFER_TIME

    def update(self, platforms: pygame.sprite.Group) -> None:
        """
        Update the player's position, physics, and handle collisions.
        Carries player along with moving platforms.
        """
        # If standing on a moving platform, carry the player with its velocity
        if self.on_ground and self.current_platform is not None:
            plat_vx = getattr(self.current_platform, 'vel_x', 0.0)
            plat_vy = getattr(self.current_platform, 'vel_y', 0.0)
            plat_dir_x = getattr(self.current_platform, 'direction_x', 1)
            plat_dir_y = getattr(self.current_platform, 'direction', 1)
            self.rect.x += int(plat_vx * plat_dir_x)
            self.rect.y += int(plat_vy * plat_dir_y)

        # Apply gravity
        self.vel_y += GRAVITY
        if self.vel_y > MAX_FALL_SPEED:
            self.vel_y = MAX_FALL_SPEED

        # Move horizontally
        self.rect.x += int(self.vel_x)
        for platform in platforms:
            if self.rect.colliderect(platform.rect):
                if self.vel_x > 0:
                    self.rect.right = platform.rect.left
                elif self.vel_x < 0:
                    self.rect.left = platform.rect.right

        # Move vertically
        self.rect.y += int(self.vel_y)
        was_on_ground = self.on_ground
        self.on_ground = False
        self.current_platform = None
        
        for platform in platforms:
            if self.rect.colliderect(platform.rect):
                if self.vel_y > 0:
                    self.rect.bottom = platform.rect.top
                    self.vel_y = 0
                    self.on_ground = True
                    self.current_platform = platform
                elif self.vel_y < 0:
                    self.rect.top = platform.rect.bottom
                    self.vel_y = 0

        # Coyote time
        if was_on_ground and not self.on_ground:
            self.coyote_timer = COYOTE_TIME
        elif self.on_ground:
            self.coyote_timer = 0
        else:
            if self.coyote_timer > 0:
                self.coyote_timer -= 1

        # Jump buffer logic
        if self.jump_buffer > 0:
            if self.on_ground or self.coyote_timer > 0:
                self.vel_y = JUMP_FORCE
                self.jump_buffer = 0
                self.coyote_timer = 0
                self.on_ground = False
                self.current_platform = None
            else:
                self.jump_buffer -= 1

        # Invincibility timer
        if self.invincible_timer > 0:
            self.invincible_timer -= 1

        # Rickshaw boost timer (invincibility + speed for 6s)
        if self.powerup_timer > 0:
            self.powerup_timer -= 1

        # Fell off screen check
        if self.rect.top > SCREEN_HEIGHT + 60:
            self.die()

        # Update animation timer when moving
        if self.vel_x != 0 and self.on_ground:
            self.anim_timer += self.anim_speed
        elif not self.on_ground:
            self.anim_timer = 1.0  # jump frame
        else:
            self.anim_timer = 0.0  # idle frame

    def take_damage(self) -> None:
        """
        Takes a hit. Reduces HP and kills player if HP reaches 0.
        No damage while i-frames or rickshaw boost is active.
        """
        if self.invincible_timer > 0 or self.powerup_timer > 0:
            return

        self.hp -= 1
        self.invincible_timer = INVINCIBILITY_FRAMES
        if self.hp <= 0:
            self.die()

    def die(self) -> None:
        """Kill the player."""
        self.alive = False

    def respawn(self) -> None:
        """Respawn player at checkpoint."""
        self.rect.topleft = self.checkpoint_pos
        self.vel_x = 0
        self.vel_y = 0
        self.hp = PLAYER_MAX_HP
        self.alive = True
        self.invincible_timer = INVINCIBILITY_FRAMES
        self.powerup_timer = 0

    def set_checkpoint(self, x: int, y: int) -> None:
        """Update the checkpoint position."""
        self.checkpoint_pos = (x, y)

    def draw(self, surface: pygame.Surface, camera_offset: tuple) -> None:
        """
        Draw the player on the given surface offset by the camera.
        """
        # Flashing during invincibility
        if self.invincible_timer > 0 and (self.invincible_timer // 4) % 2 == 0:
            return

        draw_rect = self.rect.copy()
        draw_rect.x -= camera_offset[0]
        draw_rect.y -= camera_offset[1]

        # Rickshaw boost shield (6s invincibility bubble, only while boost active)
        boosting = self.powerup_timer > 0
        if boosting:
            shield = draw_rect.inflate(16, 16)
            pygame.draw.ellipse(surface, (80, 220, 255), shield, 3)
            pygame.draw.ellipse(surface, (255, 215, 0), draw_rect.inflate(8, 8), 2)

        # Lazy-load animation frames
        if not self.frames_right:
            self.frames_right = sprite_loader.load_student_frames()
            self.frames_left = sprite_loader.load_student_frames_left()

        frames = self.frames_right if self.facing_right else self.frames_left

        if boosting:
            # During boost: swap student sprite for the auto-rickshaw mount
            r_sprite = self.rickshaw_sprite_right if self.facing_right else self.rickshaw_sprite_left
            if r_sprite:
                rx = draw_rect.centerx - r_sprite.get_width() // 2 + (4 if self.facing_right else -4)
                ry = draw_rect.bottom - r_sprite.get_height() + 2
                surface.blit(r_sprite, (rx, ry))
            else:
                r_box = pygame.Rect(draw_rect.x - 10, draw_rect.bottom - 28, 52, 28)
                pygame.draw.rect(surface, (250, 205, 30), r_box, border_radius=4)
                pygame.draw.rect(surface, (30, 160, 60), (r_box.x, r_box.bottom - 12, r_box.w, 12), border_radius=2)
        elif frames:
            frame_idx = int(self.anim_timer) % len(frames)
            surface.blit(frames[frame_idx], draw_rect)
        else:
            pygame.draw.rect(surface, PLAYER_COLOR, draw_rect)
            eye_rect = pygame.Rect(0, 0, 8, 8)
            eye_rect.centery = draw_rect.top + 12
            if self.facing_right:
                eye_rect.right = draw_rect.right - 4
            else:
                eye_rect.left = draw_rect.left + 4
            pygame.draw.rect(surface, (255, 255, 255), eye_rect)
