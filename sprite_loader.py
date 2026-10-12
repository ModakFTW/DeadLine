# sprite_loader.py — Loads and caches transparent PNG sprite images and animations
import os
import pygame
from settings import (
    PLAYER_WIDTH, PLAYER_HEIGHT,
    SPIKE_WIDTH, SPIKE_HEIGHT,
    ENEMY_WIDTH, ENEMY_HEIGHT,
    TILE_SIZE
)

SPRITES_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                           'assets', 'sprites')

_cache: dict[str, pygame.Surface] = {}


def load_png(filename: str, width: int, height: int) -> pygame.Surface | None:
    """Load a transparent PNG image and scale smoothly."""
    cache_key = f"{filename}_{width}_{height}"
    if cache_key in _cache:
        return _cache[cache_key]

    path = os.path.join(SPRITES_DIR, filename)
    if not os.path.exists(path):
        _cache[cache_key] = None
        return None

    try:
        img = pygame.image.load(path).convert_alpha()
        img = pygame.transform.smoothscale(img, (width, height))
        _cache[cache_key] = img
        return img
    except Exception as e:
        print(f"Error loading {filename}: {e}")
        _cache[cache_key] = None
        return None


def load_student_frames() -> list[pygame.Surface]:
    """Load running animation for the student character."""
    cache_key = "student_frames_right"
    if cache_key in _cache:
        return _cache[cache_key]

    frames = []
    for i in range(4):
        f = load_png(f"student_run_{i}.png", PLAYER_WIDTH, PLAYER_HEIGHT)
        if f is not None:
            frames.append(f)
    if not frames:
        fallback = load_png("student.jpg", PLAYER_WIDTH, PLAYER_HEIGHT)
        if fallback:
            frames.append(fallback)
    _cache[cache_key] = frames
    return frames


def load_student_frames_left() -> list[pygame.Surface]:
    """Load running animation facing left."""
    cache_key = "student_frames_left"
    if cache_key in _cache:
        return _cache[cache_key]

    right_frames = load_student_frames()
    left_frames = [pygame.transform.flip(f, True, False) for f in right_frames]
    _cache[cache_key] = left_frames
    return left_frames


def load_student_idle(width: int = PLAYER_WIDTH, height: int = PLAYER_HEIGHT) -> pygame.Surface | None:
    """Load idle standing sprite for the student."""
    cache_key = f"student_idle_{width}_{height}"
    if cache_key in _cache:
        return _cache[cache_key]
    idle = load_png("student_combat_idle.png", width, height)
    if not idle:
        # Fallback to frame 0
        frames = load_student_frames()
        idle = frames[0] if frames else None
    _cache[cache_key] = idle
    return idle


def load_student_idle_left(width: int = PLAYER_WIDTH, height: int = PLAYER_HEIGHT) -> pygame.Surface | None:
    """Load idle standing sprite facing left."""
    cache_key = f"student_idle_left_{width}_{height}"
    if cache_key in _cache:
        return _cache[cache_key]
    right_idle = load_student_idle(width, height)
    left_idle = pygame.transform.flip(right_idle, True, False) if right_idle else None
    _cache[cache_key] = left_idle
    return left_idle


def load_traffic_cone() -> pygame.Surface | None:
    """Load clean transparent traffic cone."""
    return load_png("traffic_cone.png", SPIKE_WIDTH, SPIKE_HEIGHT)


def load_rickshaw(width: int = 140, height: int = 95) -> pygame.Surface | None:
    """Load the detailed auto rickshaw pixel art sprite."""
    return load_png("auto_rickshaw.png", width, height)


def load_dog_frames_left() -> list[pygame.Surface]:
    """Load stray dog walk animation frames facing left (native PNG orientation)."""
    cache_key = "dog_frames_left"
    if cache_key in _cache:
        return _cache[cache_key]

    frames = []
    f0 = load_png("stray_dog_0.png", ENEMY_WIDTH, ENEMY_HEIGHT)
    f1 = load_png("stray_dog_1.png", ENEMY_WIDTH, ENEMY_HEIGHT)
    if f0:
        frames.append(f0)
    if f1:
        frames.append(f1)
    if not frames:
        solo = load_png("stray_dog_solo.png", ENEMY_WIDTH, ENEMY_HEIGHT)
        if solo:
            frames.append(solo)
    _cache[cache_key] = frames
    return frames


def load_dog_frames() -> list[pygame.Surface]:
    """Load stray dog walk animation frames facing right (horizontally flipped)."""
    cache_key = "dog_frames_right"
    if cache_key in _cache:
        return _cache[cache_key]

    left_frames = load_dog_frames_left()
    right_frames = [pygame.transform.flip(f, True, False) for f in left_frames]
    _cache[cache_key] = right_frames
    return right_frames


def load_grandma_frames(width: int = 54, height: int = 84) -> list[pygame.Surface]:
    """Load Indian grandmother walking animation frames facing right."""
    cache_key = f"grandma_frames_{width}_{height}"
    if cache_key in _cache:
        return _cache[cache_key]

    frames = []
    for i in range(3):
        f = load_png(f"grandma_{i}.png", width, height)
        if f:
            frames.append(f)
    _cache[cache_key] = frames
    return frames


def load_grandma_frames_left(width: int = 54, height: int = 84) -> list[pygame.Surface]:
    """Load Indian grandmother walking animation frames facing left."""
    cache_key = f"grandma_frames_left_{width}_{height}"
    if cache_key in _cache:
        return _cache[cache_key]

    right_frames = load_grandma_frames(width, height)
    left_frames = [pygame.transform.flip(f, True, False) for f in right_frames]
    _cache[cache_key] = left_frames
    return left_frames


def load_monkey_sprites(width: int = 52, height: int = 60) -> dict[str, pygame.Surface]:
    """Load monkey walk, jump, and crouch sprites (facing right and left).

    Tall/narrow proportions (+25% height at original width) match the native
    monkey art aspect and keep the monkey visibly smaller than the student.
    Jump/crouch poses are widened to preserve their native square/wide aspects.
    """
    cache_key = f"monkey_sprites_{width}_{height}"
    if cache_key in _cache:
        return _cache[cache_key]

    walk = load_png("monkey_walk.png", width, height)
    jump = load_png("monkey_jump.png", int(width * 1.3), int(height * 1.15))
    crouch = load_png("monkey_crouch.png", int(width * 1.3), int(height * 0.85))

    sprites = {
        "walk_right": walk,
        "jump_right": jump,
        "crouch_right": crouch,
        "walk_left": pygame.transform.flip(walk, True, False) if walk else None,
        "jump_left": pygame.transform.flip(jump, True, False) if jump else None,
        "crouch_left": pygame.transform.flip(crouch, True, False) if crouch else None,
    }
    _cache[cache_key] = sprites
    return sprites


def load_boss_sprites(width: int = 120, height: int = 120) -> dict[str, pygame.Surface]:
    """Load Professor Terminus boss combat sprites (PNGs natively face right)."""
    cache_key = f"boss_sprites_{width}_{height}"
    if cache_key in _cache:
        return _cache[cache_key]

    idle = load_png("boss_idle.png", width, height)
    atk = load_png("boss_attack.png", int(width * 1.2), int(height * 1.1))
    cast = load_png("boss_cast.png", int(width * 1.25), int(height * 1.05))
    hurt = load_png("boss_hurt.png", width, height)

    # Native boss PNGs face RIGHT towards incoming characters.
    # Flip for left-facing orientation when facing player on left.
    sprites = {
        "idle_right": idle,
        "idle_left": pygame.transform.flip(idle, True, False) if idle else None,
        "attack_right": atk,
        "attack_left": pygame.transform.flip(atk, True, False) if atk else None,
        "cast_right": cast,
        "cast_left": pygame.transform.flip(cast, True, False) if cast else None,
        "hurt_right": hurt,
        "hurt_left": pygame.transform.flip(hurt, True, False) if hurt else None,
    }
    _cache[cache_key] = sprites
    return sprites


def load_player_combat_sprites(width: int = 70, height: int = 85) -> dict[str, any]:
    """Load player combat sprites: running frames, slingshot, steel ruler sword, and ready idle."""
    cache_key = f"player_combat_sprites_{width}_{height}"
    if cache_key in _cache:
        return _cache[cache_key]

    idle = load_png("student_combat_idle.png", width, height)
    sling = load_png("student_slingshot.png", int(width * 1.1), height)
    sword = load_png("student_ruler_slash.png", int(width * 1.3), int(height * 1.05))

    run_right = []
    for i in range(4):
        rf = load_png(f"student_combat_run_{i}.png", width, height)
        if rf:
            run_right.append(rf)
    run_left = [pygame.transform.flip(rf, True, False) for rf in run_right]

    sprites = {
        "idle_right": idle,
        "idle_left": pygame.transform.flip(idle, True, False) if idle else None,
        "slingshot_right": sling,
        "slingshot_left": pygame.transform.flip(sling, True, False) if sling else None,
        "ruler_right": sword,
        "ruler_left": pygame.transform.flip(sword, True, False) if sword else None,
        "run_right": run_right,
        "run_left": run_left,
    }
    _cache[cache_key] = sprites
    return sprites


BACKGROUNDS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                               'assets', 'backgrounds')


def load_background(
    bg_filename: str,
    width: int = 1280,
    height: int = 720,
    blur: bool = False,
    dim_alpha: int = 0
) -> pygame.Surface | None:
    """Load, scale, optionally blur and dim a background image with caching."""
    cache_key = f"bg_{bg_filename}_{width}_{height}_{blur}_{dim_alpha}"
    if cache_key in _cache:
        return _cache[cache_key]

    path = os.path.join(BACKGROUNDS_DIR, bg_filename)
    if not os.path.exists(path):
        _cache[cache_key] = None
        return None

    try:
        img = pygame.image.load(path).convert()
        img = pygame.transform.smoothscale(img, (width, height))

        if blur:
            # Create out-of-focus blur effect via downsample & smoothscale upsample
            blur_w = max(1, int(width * 0.12))
            blur_h = max(1, int(height * 0.12))
            small = pygame.transform.smoothscale(img, (blur_w, blur_h))
            img = pygame.transform.smoothscale(small, (width, height))

        if dim_alpha > 0:
            # Apply semi-transparent dark overlay to make foreground platforms and player pop
            overlay = pygame.Surface((width, height), pygame.SRCALPHA)
            overlay.fill((10, 14, 24, min(255, dim_alpha)))
            img.blit(overlay, (0, 0))

        _cache[cache_key] = img
        return img
    except Exception as e:
        print(f"Error loading background {bg_filename}: {e}")
        _cache[cache_key] = None
        return None
