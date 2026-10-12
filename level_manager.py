# level_manager.py — Manages the world: ground, obstacles, checkpoints, procedural generation & cage trigger
import json
import os
import random
import pygame

from settings import (
    TILE_SIZE, GROUND_Y, SCREEN_WIDTH, SCREEN_HEIGHT,
    GAP_WIDTH_TILES, MIN_OBSTACLE_SPACING, MAX_OBSTACLE_SPACING,
    TUTORIAL_LENGTH, CHUNK_WIDTH, CLEANUP_DISTANCE,
    MOVING_PLATFORM_RANGE, OBSTACLES_TO_CAGE
)
from obstacles import Ground, Spike, Gap, MovingPlatform, Enemy
import sprite_loader
from ai.obstacle_generator import MarkovChain
from ai.difficulty_tracker import DifficultyTracker


class LevelManager:
    """
    Manages the game world: ground tiles, obstacles, checkpoints.
    
    Phase 1: Tutorial sequence.
    Phase 2: Markov chain procedural generation driven by the DifficultyTracker.
    Phase 3: At OBSTACLES_TO_CAGE, spawns the Cage trigger and ends the platformer section.
    """

    def __init__(self, initial_tier: str = "medium") -> None:
        # Sprite groups
        self.ground_tiles = pygame.sprite.Group()
        self.hazards = pygame.sprite.Group()        # spikes, enemies
        self.platforms = pygame.sprite.Group()       # moving platforms (player can stand on)
        self.all_obstacles = pygame.sprite.Group()   # hazards + platforms

        # AI systems
        self.markov = MarkovChain()
        self.difficulty = DifficultyTracker()

        # Seed initial Elo from Knowledge Score tier
        self.initial_tier = initial_tier
        self._seed_difficulty(initial_tier)

        # Generation state
        self.generated_up_to_x = 0.0     # rightmost x-coord of generated content
        self.last_obstacle_type = "gap"   # seed for the Markov chain
        self.obstacle_count = 0
        self.tutorial_done = False
        self.gaps: list[Gap] = []         # track gaps so ground isn't placed there
        self.ground_coords: set[tuple[int, int]] = set() # track placed ground tiles

        # Cage trigger state (replaces old boss gate)
        self.cage_spawned = False
        self.cage_x = 0.0
        self.cage_triggered = False

        # Load training data and train Markov chain
        self._train_markov()

        # Build initial world
        self._build_initial_world()

    def _seed_difficulty(self, tier: str) -> None:
        """Seed the Elo skill score based on Level 1 Knowledge Score."""
        if tier == "easy":
            self.difficulty.skill_score = 3.0
        elif tier == "hard":
            self.difficulty.skill_score = 7.5
        else:
            self.difficulty.skill_score = 5.0
        self.difficulty.history = [self.difficulty.skill_score]

    def _train_markov(self) -> None:
        """Load training sequences and train the Markov chain."""
        data_path = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                 'data', 'training_sequences.json')
        try:
            with open(data_path, 'r') as f:
                sequences = json.load(f)
            self.markov.train(sequences)
        except FileNotFoundError:
            fallback = [["spike", "gap", "moving_platform", "enemy"]] * 5
            self.markov.train(fallback)

    def _build_initial_world(self) -> None:
        """Build ground for the starting area and place tutorial obstacles."""
        start_length = SCREEN_WIDTH * 3
        self._fill_ground(0, start_length)
        self.generated_up_to_x = start_length

        tutorial_sequence = [
            "spike", "moving_platform", "gap", "enemy", "spike", "moving_platform"
        ]
        x_cursor = SCREEN_WIDTH

        for obs_type in tutorial_sequence[:TUTORIAL_LENGTH]:
            x_cursor = self._place_obstacle(obs_type, x_cursor)
            self.obstacle_count += 1

        self.tutorial_done = True
        self.last_obstacle_type = tutorial_sequence[-1]

    def _fill_ground(self, start_x: float, end_x: float) -> None:
        """Fill ground tiles from start_x to end_x, skipping gap regions."""
        tile_start = int(start_x) // TILE_SIZE * TILE_SIZE
        tile_end = int(end_x)

        for tx in range(tile_start, tile_end, TILE_SIZE):
            in_gap = False
            for gap in self.gaps:
                gap_end = gap.x + gap.width_tiles * TILE_SIZE
                if gap.x <= tx < gap_end:
                    in_gap = True
                    break
            if not in_gap:
                for row in range(3):
                    gy = GROUND_Y + row * TILE_SIZE
                    if (tx, gy) not in self.ground_coords:
                        tile = Ground(tx, gy)
                        self.ground_tiles.add(tile)
                        self.ground_coords.add((tx, gy))

    def _place_obstacle(self, obs_type: str, x: float) -> float:
        """
        Place an obstacle of the given type at approximately x.
        Returns the x position for the NEXT obstacle.
        """
        tier = self.difficulty.get_difficulty_tier()
        
        # Adapt spacing to difficulty tier
        if tier == "easy":
            spacing = random.randint(MIN_OBSTACLE_SPACING + 40, MAX_OBSTACLE_SPACING + 60)
        elif tier == "hard":
            spacing = random.randint(MIN_OBSTACLE_SPACING - 30, MAX_OBSTACLE_SPACING - 30)
        else:
            spacing = random.randint(MIN_OBSTACLE_SPACING, MAX_OBSTACLE_SPACING)

        if obs_type == "spike":
            spike = Spike(int(x))
            self.hazards.add(spike)
            self.all_obstacles.add(spike)

        elif obs_type == "gap":
            gap_x = (int(x) // TILE_SIZE) * TILE_SIZE
            # Adapt gap width: 2 tiles on easy, 3 tiles on medium/hard
            gap_tiles = 2 if tier == "easy" else GAP_WIDTH_TILES
            gap = Gap(gap_x, gap_tiles)
            self.gaps.append(gap)
            gap_end = gap.x + gap.width_tiles * TILE_SIZE
            to_remove = [t for t in self.ground_tiles
                         if t.rect.x >= gap.x and t.rect.x < gap_end]
            for t in to_remove:
                self.ground_coords.discard((t.rect.x, t.rect.y))
                self.ground_tiles.remove(t)

        elif obs_type == "moving_platform":
            # Floating Metro platform at comfortable jump height
            platform_y = GROUND_Y - 72
            mp = MovingPlatform(int(x), platform_y)
            self.platforms.add(mp)
            self.all_obstacles.add(mp)

        elif obs_type == "enemy":
            enemy = Enemy(int(x))
            self.hazards.add(enemy)
            self.all_obstacles.add(enemy)

        return x + spacing


    def update(self, camera_world_right: float, player_x: float) -> None:
        """
        Called every frame. Extends level until reaching OBSTACLES_TO_CAGE,
        then spawns the cage trigger point.
        """
        if not self.cage_spawned:
            if self.obstacle_count >= OBSTACLES_TO_CAGE:
                # Spawn cage trigger zone
                self.cage_spawned = True
                self.cage_x = self.generated_up_to_x + 100
                # Guarantee solid ground into the cage area
                self._fill_ground(self.generated_up_to_x - 100, self.cage_x + SCREEN_WIDTH)
                self.generated_up_to_x = self.cage_x + SCREEN_WIDTH
            else:
                while self.generated_up_to_x < camera_world_right + CHUNK_WIDTH:
                    tier = self.difficulty.get_difficulty_tier()
                    next_obs = self.markov.generate_next(self.last_obstacle_type, tier)

                    self.generated_up_to_x = self._place_obstacle(
                        next_obs, self.generated_up_to_x
                    )
                    self._fill_ground(self.generated_up_to_x - MAX_OBSTACLE_SPACING,
                                      self.generated_up_to_x + TILE_SIZE)

                    self.last_obstacle_type = next_obs
                    self.obstacle_count += 1
                    if self.obstacle_count >= OBSTACLES_TO_CAGE:
                        break

        # Check if player crossed the cage trigger
        if self.cage_spawned and player_x >= self.cage_x and not self.cage_triggered:
            self.cage_triggered = True

        # Update animated obstacles
        for obs in self.all_obstacles:
            obs.update()

    def cleanup(self, camera_offset_x: float) -> None:
        """Remove entities far behind the camera."""
        cutoff = camera_offset_x - CLEANUP_DISTANCE
        for tile in list(self.ground_tiles):
            if tile.rect.right < cutoff:
                self.ground_coords.discard((tile.rect.x, tile.rect.y))
                self.ground_tiles.remove(tile)
        for obs in list(self.all_obstacles):
            if obs.rect.right < cutoff:
                self.all_obstacles.remove(obs)
                self.hazards.remove(obs)
                self.platforms.remove(obs)
        self.gaps = [g for g in self.gaps
                     if g.x + g.width_tiles * TILE_SIZE > cutoff]


    def report_obstacle_result(self, obstacle_type: str, cleared: bool) -> None:
        """Feeds result into the DifficultyTracker."""
        self.difficulty.update(obstacle_type, cleared)

    def get_platform_rects(self) -> pygame.sprite.Group:
        """Returns solid surfaces player can stand on."""
        combined = pygame.sprite.Group()
        combined.add(self.ground_tiles)
        combined.add(self.platforms)
        return combined

    def draw(self, surface: pygame.Surface, camera_offset: tuple) -> None:
        """Draw ground tiles, obstacles, and cage trigger zone."""
        screen_left = camera_offset[0] - TILE_SIZE
        screen_right = camera_offset[0] + SCREEN_WIDTH + TILE_SIZE

        # Draw pothole cavities for gaps
        for gap in self.gaps:
            gap_left = gap.x - camera_offset[0]
            gap_w = gap.width_tiles * TILE_SIZE
            gap_top_y = GROUND_Y - camera_offset[1]

            if -gap_w <= gap_left <= SCREEN_WIDTH:
                pit_rect = pygame.Rect(gap_left, gap_top_y, gap_w, SCREEN_HEIGHT - GROUND_Y + 40)
                pygame.draw.rect(surface, (18, 18, 24), pit_rect)
                shade_rect = pygame.Rect(gap_left, gap_top_y, gap_w, 18)
                pygame.draw.rect(surface, (36, 32, 28), shade_rect)

                stripe_w = 8
                for i in range(gap_w // stripe_w):
                    color = (250, 210, 45) if i % 2 == 0 else (22, 22, 28)
                    pygame.draw.rect(surface, color, (gap_left + i * stripe_w, gap_top_y, stripe_w, 4))

                cone_sprite = sprite_loader.load_traffic_cone()
                if cone_sprite:
                    surface.blit(cone_sprite, (gap_left - 18, gap_top_y - 36))
                    surface.blit(cone_sprite, (gap_left + gap_w - 14, gap_top_y - 36))

        for tile in self.ground_tiles:
            if screen_left <= tile.rect.x <= screen_right:
                tile.draw(surface, camera_offset)

        for obs in self.all_obstacles:
            if screen_left <= obs.rect.x <= screen_right:
                obs.draw(surface, camera_offset)

        # Draw Cage Entrance if visible
        if self.cage_spawned:
            gx = self.cage_x - camera_offset[0]
            if -120 <= gx <= SCREEN_WIDTH + 120:
                gate_top = GROUND_Y - camera_offset[1] - 120
                # Stone pillars
                pygame.draw.rect(surface, (70, 75, 90), (gx - 16, gate_top, 24, 120))
                pygame.draw.rect(surface, (70, 75, 90), (gx + 100, gate_top, 24, 120))
                # Arch
                pygame.draw.rect(surface, (45, 50, 65), (gx - 24, gate_top - 20, 156, 26), border_radius=4)
                pygame.draw.rect(surface, (200, 60, 60), (gx - 20, gate_top - 16, 148, 18), border_radius=2)
                
                font = pygame.font.SysFont("segoeui, arial", 11, bold=True)
                txt = font.render("THE CAGE AWAITS...", True, (230, 220, 200))
                surface.blit(txt, (gx - 6, gate_top - 14))
