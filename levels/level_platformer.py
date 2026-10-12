# levels/level_platformer.py — Level 2: Markov Chain Adaptive Platformer
import pygame

from settings import (
    SCREEN_WIDTH, SCREEN_HEIGHT, DISPLAY_WIDTH, DISPLAY_HEIGHT,
    SCALE_FACTOR, PLAYER_START_X, PLAYER_START_Y, GROUND_Y, SKY_BLUE,
    TILE_SIZE, PLAYER_WIDTH, PLAYER_HEIGHT, WHITE, BLACK, YELLOW
)
from levels.base_level import BaseLevel
from game_state import GameState
from player import Player
from camera import Camera
from level_manager import LevelManager
from ui import UI
import sprite_loader
from typing import Optional


class LevelPlatformer(BaseLevel):
    """
    Level 2: The adaptive AI platformer section.
    Uses Markov chain (Model 1) for obstacle generation and
    Elo rating (Model 2) for real-time difficulty tracking.
    The initial difficulty tier is seeded from the Knowledge Score (Level 1).
    """

    def __init__(self, game_state: GameState) -> None:
        self.gs = game_state
        self.player = Player(PLAYER_START_X, PLAYER_START_Y)
        self.camera = Camera()
        self.level = LevelManager(initial_tier=game_state.get_difficulty_tier())
        self.ui = UI()

        # Background (Indian City Street parallax) - blurred and dimmed to reduce visual clutter
        self.bg = sprite_loader.load_background(
            "bg_level2_street.jpg", SCREEN_WIDTH, SCREEN_HEIGHT,
            blur=True, dim_alpha=85
        )

        # Rickshaw powerup unlock check (if player scored 4/5 or 5/5 in Level 1)
        # Note: knowledge_score is scaled to 10 in Level 1 (e.g. 4/5 -> 8, 5/5 -> 10)
        # or checking len(words_remembered) >= 4
        if len(self.gs.words_remembered) >= 4 or self.gs.knowledge_score >= 8:
            self.player.enable_rickshaw_mode()

        # Internal rendering surfaces (2x zoom pipeline)
        self.screen = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))

        # Tracking
        self.passed_obstacles: set[int] = set()
        self.death_obstacle_type: Optional[str] = None
        self.paused = False

    def handle_events(self, events: list[pygame.event.Event]) -> Optional[str]:
        for event in events:
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    self.paused = not self.paused
                elif event.key == pygame.K_F3:
                    self.ui.toggle_debug()
                elif event.key == pygame.K_v:
                    # Auto-rickshaw powerup: 6s invincibility + speed
                    self.player.try_activate_rickshaw_boost()
        return None

    def update(self) -> Optional[str]:
        if self.paused:
            return None

        keys = pygame.key.get_pressed()
        self.player.handle_input(keys)

        platforms = self.level.get_platform_rects()
        self.player.update(platforms)
        self.camera.update(self.player)

        # Update level & Markov chain generation
        world_right = self.camera.get_world_right()
        self.level.update(world_right, self.player.rect.x)
        self.level.cleanup(self.camera.offset_x)

        # Collision checks
        self._check_hazard_collisions()
        self._check_obstacle_clears()

        # Handle pothole fall (lose 1 life, not all)
        if self.player.rect.top > SCREEN_HEIGHT + 60:
            self._handle_gap_fall()
        elif self.player.on_ground:
            self._update_checkpoint()

        # Player died
        if not self.player.alive:
            self._save_stats()
            return "game_over"

        # Reached cage trigger
        if self.level.cage_triggered:
            self._save_stats()
            return "cage"

        return None

    def draw(self, surface: pygame.Surface) -> None:
        # 1. Draw world onto internal 640x360 canvas
        if self.bg:
            # Parallax background scrolling (moves at 25% camera speed)
            bg_offset_x = int(self.camera.offset_x * 0.25) % SCREEN_WIDTH
            self.screen.blit(self.bg, (-bg_offset_x, 0))
            if bg_offset_x > 0:
                self.screen.blit(self.bg, (SCREEN_WIDTH - bg_offset_x, 0))
        else:
            self.screen.fill(SKY_BLUE)

        cam_offset = (int(self.camera.offset_x), int(self.camera.offset_y))

        self.level.draw(self.screen, cam_offset)
        self.player.draw(self.screen, cam_offset)

        # 2. Scale 2x to display
        scaled = pygame.transform.scale(self.screen, (DISPLAY_WIDTH, DISPLAY_HEIGHT))
        surface.blit(scaled, (0, 0))

        # 3. Crisp HD UI overlays
        distance = int(self.player.rect.x / 50)
        self.ui.draw_hud(surface, self.player.hp, distance, self.level.obstacle_count,
                         has_rickshaw=self.player.has_rickshaw,
                         boost_active=self.player.powerup_timer > 0,
                         boost_seconds=self.player.powerup_timer // 60)

        # Debug overlay (F3)
        if self.ui.debug_visible and self.level:
            stats = self.level.difficulty.get_stats()
            tier = self.level.difficulty.get_difficulty_tier()
            self.ui.draw_debug(
                surface, stats, tier,
                self.level.last_obstacle_type,
                pygame.time.Clock().get_fps()
            )

        if self.paused:
            self.ui.draw_pause(surface)

    # ── Collision Helpers ──

    def _handle_gap_fall(self) -> None:
        self.death_obstacle_type = 'gap'
        self.level.report_obstacle_result('gap', False)
        self.player.take_damage()
        if not self.player.alive:
            return
        self.player.rect.topleft = self.player.checkpoint_pos
        self.player.vel_x = 0
        self.player.vel_y = 0
        self.player.on_ground = True
        self.player.invincible_timer = 60
        self.death_obstacle_type = None

    def _update_checkpoint(self) -> None:
        target_x = max(PLAYER_START_X, self.player.rect.x - 40)
        tile_x = (int(target_x) // TILE_SIZE) * TILE_SIZE
        while tile_x >= PLAYER_START_X:
            if (tile_x, GROUND_Y) in self.level.ground_coords:
                if (tile_x + TILE_SIZE, GROUND_Y) in self.level.ground_coords:
                    self.player.set_checkpoint(tile_x + 4, GROUND_Y - PLAYER_HEIGHT)
                    return
            tile_x -= TILE_SIZE
        self.player.set_checkpoint(PLAYER_START_X, GROUND_Y - PLAYER_HEIGHT)

    def _check_hazard_collisions(self) -> None:
        if self.player.invincible_timer > 0 or self.player.powerup_timer > 0:
            return

        for hazard in self.level.hazards:
            if not self.player.rect.colliderect(hazard.rect):
                continue

            if hazard.obstacle_type == 'enemy':
                if not hazard.alive:
                    continue
                if self.player.vel_y > 0 and self.player.rect.bottom <= hazard.rect.top + 15:
                    hazard.alive = False
                    self.player.vel_y = -8
                    self.level.report_obstacle_result('enemy', True)
                else:
                    self.death_obstacle_type = 'enemy'
                    self.player.take_damage()

            elif hazard.obstacle_type == 'spike':
                self.death_obstacle_type = 'spike'
                self.player.take_damage()

    def _check_obstacle_clears(self) -> None:
        for obs in self.level.all_obstacles:
            obs_id = id(obs)
            if obs_id in self.passed_obstacles:
                continue
            if self.player.rect.left > obs.rect.right + 20:
                self.passed_obstacles.add(obs_id)
                if hasattr(obs, 'obstacle_type') and obs.obstacle_type in ('spike', 'enemy'):
                    if obs.obstacle_type == 'enemy' and hasattr(obs, 'alive') and not obs.alive:
                        continue
                    self.level.report_obstacle_result(obs.obstacle_type, True)

        for gap in self.level.gaps:
            gap_id = id(gap)
            if gap_id in self.passed_obstacles:
                continue
            gap_end = gap.x + gap.width_tiles * TILE_SIZE
            if self.player.rect.left > gap_end + 20:
                self.passed_obstacles.add(gap_id)
                self.level.report_obstacle_result('gap', True)

    def _save_stats(self) -> None:
        """Persist platformer AI stats to GameState for the win screen."""
        self.gs.elo_history = list(self.level.difficulty.history)
        stats = self.level.difficulty.get_stats()
        self.gs.final_elo = stats['skill_score']
        self.gs.final_tier = stats['tier']
        self.gs.clears = stats['clears']
        self.gs.deaths = stats['deaths']
