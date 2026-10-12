# settings.py — Single source of truth for all game constants

import pygame

# ─── Display ─────────────────────────────────────────────
DISPLAY_WIDTH = 1280
DISPLAY_HEIGHT = 720
# Internal resolution — game renders here, then scales up for a zoomed-in feel
SCREEN_WIDTH = 640
SCREEN_HEIGHT = 360
SCALE_FACTOR = DISPLAY_WIDTH // SCREEN_WIDTH   # 2x zoom
FPS = 60
TITLE = "DeadLine: Adaptive AI Platformer"

# ─── Colors ──────────────────────────────────────────────
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
DARK_GRAY = (35, 38, 48)
LIGHT_GRAY = (180, 185, 200)
RED = (235, 60, 60)
GREEN = (50, 210, 95)
BLUE = (60, 130, 240)
YELLOW = (250, 210, 45)
ORANGE = (255, 140, 40)
CYAN = (60, 220, 240)
PURPLE = (175, 75, 240)
GOLD = (255, 215, 0)
DARK_GREEN = (30, 100, 50)
SKY_BLUE = (135, 195, 240)
GROUND_BROWN = (120, 80, 50)
GROUND_TOP = (80, 160, 60)
SPIKE_COLOR = (240, 70, 70)
ENEMY_COLOR = (190, 60, 190)
PLATFORM_COLOR = (70, 130, 180)
CHALK_WHITE = (230, 225, 215)
CHALKBOARD_GREEN = (30, 70, 45)
CAGE_IRON = (90, 95, 105)
DUNGEON_BG = (18, 16, 22)
ROAD_GRAY = (80, 82, 88)

# ─── Physics ─────────────────────────────────────────────
GRAVITY = 0.8
MAX_FALL_SPEED = 15
PLAYER_SPEED = 5
PLAYER_ACCELERATION = 0.6
PLAYER_FRICTION = 0.85
JUMP_FORCE = -14
COYOTE_TIME = 6                  # frames of grace after leaving a platform
JUMP_BUFFER_TIME = 6             # frames of input buffering for jump
INVINCIBILITY_FRAMES = 60        # frames of invincibility after respawn

# ─── World / Tiles ───────────────────────────────────────
TILE_SIZE = 40
GROUND_Y = SCREEN_HEIGHT - TILE_SIZE * 3   # y-position of top of ground
CHUNK_WIDTH = SCREEN_WIDTH * 2             # generate this far ahead of camera
CLEANUP_DISTANCE = SCREEN_WIDTH * 3        # remove obstacles this far behind camera

# ─── Player ──────────────────────────────────────────────
PLAYER_WIDTH = 32
PLAYER_HEIGHT = 48
PLAYER_COLOR = BLUE
PLAYER_START_X = 100
PLAYER_START_Y = GROUND_Y - PLAYER_HEIGHT  # start standing on ground
PLAYER_MAX_HP = 3

# ─── Obstacle & Entity dimensions ────────────────────────
SPIKE_WIDTH = 36
SPIKE_HEIGHT = 36
GAP_WIDTH_TILES = 3              # gap is this many tiles wide

# Floating Metro / Scaffolding Platform
MOVING_PLATFORM_WIDTH = 96
MOVING_PLATFORM_HEIGHT = 16
MOVING_PLATFORM_RANGE = 120      # horizontal float distance
MOVING_PLATFORM_SPEED = 1.5

# Stray Dog Enemy
ENEMY_WIDTH = 40
ENEMY_HEIGHT = 32
ENEMY_PATROL_RANGE = 110         # pixels the enemy walks back and forth
ENEMY_SPEED = 1.6

# ─── Obstacle spacing ────────────────────────────────────
MIN_OBSTACLE_SPACING = 200       # minimum pixels between obstacle centers
MAX_OBSTACLE_SPACING = 380       # maximum pixels between obstacle centers
TUTORIAL_LENGTH = 6              # curated starting obstacles

# ─── Difficulty thresholds ────────────────────────────────
SKILL_START = 5.0
SKILL_K = 0.5                    # Elo K-factor — how fast skill moves
EASY_THRESHOLD = 4.0             # skill < 4 = easy
HARD_THRESHOLD = 7.0             # skill > 7 = hard

# Obstacle difficulty ratings (for the Elo formula)
OBSTACLE_DIFFICULTY = {
    "spike": 4.0,
    "gap": 3.0,
    "moving_platform": 2.5,
    "enemy": 6.0,
}

# ─── Level Progression ───────────────────────────────────
OBSTACLES_TO_CAGE = 20           # Clear this many obstacles to reach the Cage

# ─── Level 1: Memory Test ────────────────────────────────
MEMORY_STUDY_TIME = 8            # seconds to memorize words
MEMORY_RECALL_TIME = 30          # seconds to type back words

# ─── Level 3: Cage Riddles ───────────────────────────────
RIDDLE_TIME = 20                 # seconds per riddle

# ─── Level 4: Old Woman & Monkey ─────────────────────────
MONKEY_SPEED = 2.0
MONKEY_SCARE_RADIUS = 80         # pixels — player within this scares monkey
MONKEY_APPROACH_RADIUS = 200     # pixels — monkey starts approaching woman
MONKEY_FLEE_TIME = 180           # frames monkey stays scared (~3 seconds)
WOMAN_SPEED = 1.2
ROAD_WIDTH = 400                 # pixel width of the road to cross

# ─── Level 5: Exam Gate ──────────────────────────────────
EXAM_GATE_TIME = 45              # seconds to recall words
EXAM_GATE_TOTAL = 5              # total words to recall
EXAM_GATE_PASS = 4               # minimum correct words to pass (4 out of 5)

# ─── Debug ────────────────────────────────────────────────
DEBUG_FONT_SIZE = 16
DEBUG_COLOR = YELLOW
