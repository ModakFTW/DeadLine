# boss_combat_pov.py — Standalone DOOM-Style First-Person POV Boss Combat Arena (Refined)
"""
Refined First-Person Perspective (POV) Boss Arena for DeadLine.
------------------------------------------------------------------
Inspired by classic 90s DOOM / Arcade tactical combat:
- Tactical Pacing & Telegraphs: Readable attack windups and balanced projectile speeds.
- In-Hand Clipboard Shield: Hold RMB or Space to raise a heavy metal-bracket binder shield
  that blocks 100% damage on hit and enters a temporary cooldown.
- Environmental Cover: 2 Gothic Stone Pillars on the arena flanks.
- Strict Phase-Matching for Boss Combat:
    * Phase 1 (100% - 70%): Pure Ranged (Boss stays at safe depth Z >= 250, casting telegraphed fireballs).
    * Phase 2 (70% - 30%): Pure Melee (Boss enters duel range Z: 135-180 with telegraphed ruler strikes).
    * Phase 3 (30% - 0%): Hybrid Escalation (Artillery barrage + sudden gap-closing lunges).
- 100% AI Logic Parity: Directly uses tabular Q-learning BossAgent from ai/boss_agent.py.
- DOOM Status Bar HUD: Reactive student face portrait, health, shield cooldown gauge, and live CRT Q-matrix.
"""

import math
import random
import time
from typing import Optional, Tuple, Dict, List

import pygame

from settings import (
    DISPLAY_WIDTH, DISPLAY_HEIGHT, FPS,
    WHITE, BLACK, RED, GREEN, BLUE, YELLOW, CYAN, GOLD, PURPLE, ORANGE, DARK_GRAY
)
from levels.base_level import BaseLevel
from game_state import GameState
from ai.boss_agent import BossAgent, ACTIONS, discretize_distance
from text_utils import draw_wrapped_text
import sprite_loader

# Re-use the CAT questions from the original boss fight
from boss_combat import CAT_QUESTIONS


class BossArenaPOVLevel(BaseLevel):
    """
    First-Person POV Boss Arena against Professor Terminus with tactical pacing,
    in-hand Clipboard Shield, 2 stone arena pillars, and phase-matched combat.
    """

    def __init__(self, game_state: Optional[GameState] = None):
        self.game_state = game_state if game_state is not None else GameState()

        # Horizon and 3D Viewport Geometry
        self.view_w = DISPLAY_WIDTH
        self.status_bar_h = 135
        self.view_h = DISPLAY_HEIGHT - self.status_bar_h
        self.cx = self.view_w // 2
        self.cy = 280  # Horizon line
        self.focal_len = 450.0

        # Preload Background
        self.bg = sprite_loader.load_background("bg_level3.jpg", DISPLAY_WIDTH, DISPLAY_HEIGHT)
        if not self.bg:
            self.bg = sprite_loader.load_background("bg_level5.jpg", DISPLAY_WIDTH, DISPLAY_HEIGHT)

        # Load Boss Sprites
        self.boss_sprites = sprite_loader.load_boss_sprites(140, 140)

        # --- Player POV State ---
        self.player_x = 0.0          # Lateral position in arena [-250, 250]
        self.player_z = 0.0          # Depth plane
        self.player_eye_y = 0.0      # Eye elevation
        self.player_speed = 6.2

        # In-Hand Clipboard Shield
        self.shield_held = False
        self.shield_cooldown = 0
        self.shield_max_cooldown = 85  # ~1.4s cooldown on hit
        self.shield_raise_anim = 0.0   # 0.0 (lowered) to 1.0 (raised)

        # Dodge / Roll
        self.player_is_dodging = False
        self.player_dodge_timer = 0
        self.player_dodge_dir = 0.0
        self.player_dodge_cooldown = 0
        self.player_invincible_timer = 0

        # Health & Stats
        self.player_hp = 100
        self.player_max_hp = 100

        # Combat Actions & Cooldowns
        self.player_last_action = "idle"
        self.player_action_timer = 0
        self.player_attack_cooldown = 0
        self.player_is_attacking = False
        self.player_weapon = "slingshot"  # "slingshot" or "ruler"

        # Slingshot Draw & Fire
        self.slingshot_recoil = 0.0
        self.slingshot_damage = 18

        # Steel Ruler Melee Swing
        self.ruler_swinging = False
        self.ruler_swing_timer = 0
        self.ruler_damage = 38

        # Mouse Crosshair
        self.mouse_x = self.cx
        self.mouse_y = self.cy

        # 2 Arena Pillars (Left & Right flanking cover)
        self.pillars = [
            {"x": -175.0, "z": 80.0, "w": 46.0, "h": 220.0, "label": "West Pillar"},
            {"x":  175.0, "z": 80.0, "w": 46.0, "h": 220.0, "label": "East Pillar"}
        ]

        # --- Boss 3D Position & State ---
        self.boss_x = 0.0
        self.boss_y = -30.0          # Standing on ground plane
        self.boss_z = 340.0          # Starts safely at medium/far distance
        self.boss_vel_x = 0.0
        self.boss_vel_z = 0.0

        self.boss_hp = 100
        self.boss_max_hp = 100
        self.current_phase = 1
        self.boss_flash_hit_timer = 0

        # AI Agent (Tabular Q-Learning)
        self.boss_agent = BossAgent(alpha=0.15, gamma=0.90, epsilon=0.85, epsilon_min=0.05, epsilon_decay=0.985)
        self.boss_current_action = "wait"
        self.boss_action_timer = 0
        self.boss_action_duration = 42  # Slower, more deliberate action cycles (was 24)
        self.boss_prev_state = None
        self.boss_prev_action = None
        self.boss_accumulated_reward = 0.0

        # Attack Telegraph / Windup States
        self.boss_windup_timer = 0      # Charge frames before attack connects or fires
        self.boss_windup_type = "none"   # "fireball" or "melee"
        self.boss_is_attacking = False
        self.boss_is_dodging = False
        self.boss_is_casting = False
        self.boss_fireball_cooldown = 50

        # Projectiles & Particles
        self.player_pebbles: List[Dict] = []
        self.boss_fireballs: List[Dict] = []
        self.particles_3d: List[Dict] = []
        self.hit_markers: List[Dict] = []
        self.combat_logs: List[str] = [
            "TACTICAL POV ARENA INITIALIZED",
            "Hold [RMB] or [SPACE] to raise Clipboard Shield!",
            "Take cover behind Left & Right Stone Pillars."
        ]

        # Screen Shakes & Flashes
        self.screen_shake = 0
        self.damage_flash = 0
        self.shield_block_popup = 0

        # Face Cam Animation States
        self.face_state = "neutral"
        self.face_timer = 0

        # Intermission & Quiz (CAT)
        self.in_quiz = False
        self.quiz_data = None
        self.quiz_difficulty = "medium"
        self.quiz_selected = None
        self.quiz_answered = False
        self.quiz_feedback_timer = 0
        self.player_buff_name = "None"
        self.player_buff_timer = 0

        # Win / Loss Transitions
        self.win_timer = 0
        self.game_over_timer = 0

        # Fonts
        pygame.font.init()
        self.font_title = pygame.font.SysFont("impact", 28)
        self.font_hud = pygame.font.SysFont("consolas", 16, bold=True)
        self.font_hud_big = pygame.font.SysFont("impact", 22)
        self.font_qtable = pygame.font.SysFont("consolas", 12, bold=True)
        self.font_qheader = pygame.font.SysFont("consolas", 13, bold=True)
        self.font_quiz = pygame.font.SysFont("arial", 18, bold=True)
        self.font_banner = pygame.font.SysFont("impact", 44)

    # -------------------------------------------------------------------
    # 3D Perspective Projection
    # -------------------------------------------------------------------
    def project(self, x: float, y: float, z: float) -> Tuple[float, float, float]:
        rel_z = max(12.0, z - self.player_z)
        scale = self.focal_len / rel_z
        sx = self.cx + (x - self.player_x) * scale
        sy = self.cy - (y - self.player_eye_y) * scale
        return sx, sy, scale

    # -------------------------------------------------------------------
    # Event Handling
    # -------------------------------------------------------------------
    def handle_events(self, events: list[pygame.event.Event]) -> Optional[str]:
        for event in events:
            if event.type == pygame.MOUSEMOTION:
                self.mouse_x, self.mouse_y = event.pos

            if self.in_quiz:
                if event.type == pygame.KEYDOWN and not self.quiz_answered:
                    if event.key in (pygame.K_1, pygame.K_2, pygame.K_3, pygame.K_4):
                        choice = event.key - pygame.K_1
                        self._process_quiz_answer(choice)
                continue

            if event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:  # Left Mouse Button: Primary Attack
                    # Can only attack if shield isn't actively blocking
                    if self.current_phase == 1:
                        self._fire_slingshot()
                    elif self.current_phase == 2:
                        self._trigger_steel_ruler_slash()
                    elif self.current_phase == 3:
                        self._fire_slingshot()

            elif event.type == pygame.KEYDOWN:
                # Dodge Roll: K or Left Shift
                if event.key in (pygame.K_k, pygame.K_LSHIFT) and self.player_dodge_cooldown <= 0:
                    self._start_dodge()

                # Weapon Swap / Secondary Attack (Phase 3)
                elif event.key == pygame.K_q and self.current_phase == 3:
                    self.player_weapon = "ruler" if self.player_weapon == "slingshot" else "slingshot"

                elif event.key in (pygame.K_u, pygame.K_c):
                    if self.current_phase in (2, 3):
                        self._trigger_steel_ruler_slash()

                elif event.key in (pygame.K_j, pygame.K_z):
                    if self.current_phase == 1:
                        self._fire_slingshot()
                    else:
                        self._trigger_steel_ruler_slash()

        return None

    # -------------------------------------------------------------------
    # Player Actions & Attacks
    # -------------------------------------------------------------------
    def _fire_slingshot(self) -> None:
        if self.player_attack_cooldown > 0 or self.player_is_dodging or self.shield_held:
            return

        self.player_is_attacking = True
        self.player_last_action = "attack"
        self.player_action_timer = 24
        self.player_attack_cooldown = 20
        self.slingshot_recoil = 18.0

        rel_sx = self.mouse_x - self.cx
        rel_sy = self.mouse_y - self.cy

        target_z = max(self.boss_z, 220.0)
        aim_x = self.player_x + (rel_sx * target_z) / self.focal_len
        aim_y = self.player_eye_y - (rel_sy * target_z) / self.focal_len

        dx = aim_x - self.player_x
        dy = aim_y - self.player_eye_y
        dz = target_z

        dist = math.sqrt(dx * dx + dy * dy + dz * dz)
        speed = 26.0

        self.player_pebbles.append({
            "x": self.player_x + 8.0,
            "y": self.player_eye_y - 10.0,
            "z": 18.0,
            "vx": (dx / dist) * speed,
            "vy": (dy / dist) * speed,
            "vz": (dz / dist) * speed,
            "life": 60
        })

        self.face_state = "grin"
        self.face_timer = 20
        self.combat_logs.append("Player shot Slingshot pebble!")
        if len(self.combat_logs) > 6:
            self.combat_logs.pop(0)

    def _trigger_steel_ruler_slash(self) -> None:
        if self.player_attack_cooldown > 0 or self.player_is_dodging:
            return

        self.player_is_attacking = True
        self.player_last_action = "attack"
        self.player_action_timer = 28
        self.player_attack_cooldown = 24
        self.ruler_swinging = True
        self.ruler_swing_timer = 18
        self.screen_shake = 5

        # Check melee hit against Boss
        dist_3d = math.sqrt((self.boss_x - self.player_x) ** 2 + self.boss_z ** 2)
        if dist_3d < 195.0:
            dmg = self.ruler_damage
            if self.player_buff_name == "Damage Boost (+50%)":
                dmg = int(dmg * 1.5)

            self.boss_hp = max(0, self.boss_hp - dmg)
            self.boss_flash_hit_timer = 22
            self.boss_accumulated_reward -= 1.0
            self.boss_z += 30.0  # Melee stagger knockback
            self.screen_shake = 12

            self.hit_markers.append({"text": f"-{dmg} CRIT!", "x": self.cx, "y": self.cy - 50, "life": 32, "color": CYAN})
            self._spawn_slash_sparks(self.cx, self.cy)

            self.face_state = "grin"
            self.face_timer = 24
            self.combat_logs.append(f"STEEL RULER SLASH connected for {dmg} DMG! (Q-Reward: -1.0)")
            if len(self.combat_logs) > 6:
                self.combat_logs.pop(0)

            if self.boss_hp <= 0:
                self.combat_logs.append("★ PROFESSOR TERMINUS DEFEATED! ★")
                self.win_timer = 90
        else:
            self.combat_logs.append("Steel Ruler slashed the air!")
            if len(self.combat_logs) > 6:
                self.combat_logs.pop(0)

    def _start_dodge(self) -> None:
        self.player_is_dodging = True
        self.player_dodge_timer = 16
        self.player_dodge_cooldown = 44
        self.player_invincible_timer = 20
        self.player_last_action = "dodge"
        self.player_action_timer = 26

        keys = pygame.key.get_pressed()
        if keys[pygame.K_a] or keys[pygame.K_LEFT]:
            self.player_dodge_dir = -1.0
        elif keys[pygame.K_d] or keys[pygame.K_RIGHT]:
            self.player_dodge_dir = 1.0
        else:
            self.player_dodge_dir = -1.0 if (self.mouse_x < self.cx) else 1.0

        self.combat_logs.append("Player executed rapid Evasive Roll!")
        if len(self.combat_logs) > 6:
            self.combat_logs.pop(0)

    # -------------------------------------------------------------------
    # Main Update Loop
    # -------------------------------------------------------------------
    def update(self) -> Optional[str]:
        if self.win_timer > 0:
            self.win_timer -= 1
            if self.win_timer <= 0:
                return "win"
            return None

        if self.game_over_timer > 0:
            self.game_over_timer -= 1
            if self.game_over_timer <= 0:
                return "game_over"
            return None

        if self.in_quiz:
            if self.quiz_feedback_timer > 0:
                self.quiz_feedback_timer -= 1
                if self.quiz_feedback_timer <= 0:
                    self.in_quiz = False
                    self.quiz_answered = False
            return None

        if self.screen_shake > 0:
            self.screen_shake -= 1
        if self.damage_flash > 0:
            self.damage_flash -= 1
        if self.shield_block_popup > 0:
            self.shield_block_popup -= 1

        if self.player_buff_timer > 0:
            self.player_buff_timer -= 1
            if self.player_buff_timer <= 0:
                self.player_buff_name = "None"

        if self.face_timer > 0:
            self.face_timer -= 1
            if self.face_timer <= 0:
                self.face_state = "neutral"

        # Update Player Movement & Shield
        self._update_player_movement()

        # Update Projectiles
        self._update_player_pebbles()
        self._update_boss_fireballs()

        # Update Boss AI & Combat Logic
        self._update_boss_ai()

        # Update Particles
        self._update_particles()

        # Check Phase Transitions
        self._check_phase_transitions()

        return None

    def _update_player_movement(self) -> None:
        keys = pygame.key.get_pressed()
        mouse_buttons = pygame.mouse.get_pressed()

        if self.player_action_timer > 0:
            self.player_action_timer -= 1
            if self.player_action_timer <= 0:
                self.player_last_action = "idle"

        if self.player_attack_cooldown > 0:
            self.player_attack_cooldown -= 1
        if self.player_dodge_cooldown > 0:
            self.player_dodge_cooldown -= 1
        if self.player_invincible_timer > 0:
            self.player_invincible_timer -= 1
        if self.slingshot_recoil > 0:
            self.slingshot_recoil *= 0.85

        if self.ruler_swinging:
            self.ruler_swing_timer -= 1
            if self.ruler_swing_timer <= 0:
                self.ruler_swinging = False

        # In-Hand Shield Input (Hold RMB or Space)
        if self.shield_cooldown > 0:
            self.shield_cooldown -= 1
            self.shield_held = False
        else:
            # Player raises shield by holding Right Mouse Button or Space
            wants_shield = mouse_buttons[2] or keys[pygame.K_SPACE]
            self.shield_held = wants_shield and not self.player_is_dodging

        # Smooth shield raising animation
        target_anim = 1.0 if self.shield_held else 0.0
        self.shield_raise_anim += (target_anim - self.shield_raise_anim) * 0.28

        # Dodge movement
        if self.player_is_dodging:
            self.player_x += self.player_dodge_dir * 13.0
            self.player_dodge_timer -= 1
            if self.player_dodge_timer <= 0:
                self.player_is_dodging = False
        else:
            # Lateral strafing (A / D)
            move_x = 0.0
            if keys[pygame.K_a] or keys[pygame.K_LEFT]:
                move_x -= 1.0
            if keys[pygame.K_d] or keys[pygame.K_RIGHT]:
                move_x += 1.0

            speed = self.player_speed
            if self.player_buff_name == "Speed Boost":
                speed *= 1.3
            if self.shield_held:
                speed *= 0.65  # Slightly slower while actively holding shield

            self.player_x += move_x * speed

        self.player_x = max(-250.0, min(250.0, self.player_x))

        # Face gaze direction
        if self.face_state not in ("grin", "hurt"):
            if self.boss_x - self.player_x < -40:
                self.face_state = "look_left"
            elif self.boss_x - self.player_x > 40:
                self.face_state = "look_right"
            else:
                self.face_state = "neutral"

    # -------------------------------------------------------------------
    # Projectile Updates
    # -------------------------------------------------------------------
    def _update_player_pebbles(self) -> None:
        active = []
        for p in self.player_pebbles:
            p["x"] += p["vx"]
            p["y"] += p["vy"]
            p["z"] += p["vz"]
            p["life"] -= 1

            dist_to_boss_z = abs(p["z"] - self.boss_z)
            if dist_to_boss_z < 30.0 and p["life"] > 0:
                dist_xy = math.sqrt((p["x"] - self.boss_x) ** 2 + (p["y"] - self.boss_y) ** 2)
                boss_hit_radius = 48.0

                if dist_xy < boss_hit_radius:
                    dmg = self.slingshot_damage
                    if self.player_buff_name == "Damage Boost (+50%)":
                        dmg = int(dmg * 1.5)

                    self.boss_hp = max(0, self.boss_hp - dmg)
                    self.boss_flash_hit_timer = 18
                    self.boss_accumulated_reward -= 1.0
                    self.boss_z += 8.0

                    bsx, bsy, _ = self.project(self.boss_x, self.boss_y + 40, self.boss_z)
                    self.hit_markers.append({"text": f"-{dmg}", "x": bsx, "y": bsy - 20, "life": 26, "color": GOLD})
                    self._spawn_3d_hit_spark(self.boss_x, self.boss_y + 35, self.boss_z, GOLD)

                    self.combat_logs.append(f"Slingshot struck Boss for {dmg} DMG! (Q-Reward: -1.0)")
                    if len(self.combat_logs) > 6:
                        self.combat_logs.pop(0)

                    if self.boss_hp <= 0:
                        self.combat_logs.append("★ PROFESSOR TERMINUS DEFEATED! ★")
                        self.win_timer = 90
                    continue

            if p["z"] < 700.0 and p["life"] > 0:
                active.append(p)
            else:
                self._spawn_3d_dust(p["x"], p["y"], p["z"])

        self.player_pebbles = active

    def _update_boss_fireballs(self) -> None:
        active = []
        for fb in self.boss_fireballs:
            fb["x"] += fb["vx"]
            fb["y"] += fb["vy"]
            fb["z"] += fb["vz"]
            fb["life"] -= 1

            # Trail flame particles
            if random.random() < 0.5:
                self.particles_3d.append({
                    "x": fb["x"] + random.uniform(-5, 5),
                    "y": fb["y"] + random.uniform(-5, 5),
                    "z": fb["z"],
                    "vx": random.uniform(-0.8, 0.8),
                    "vy": random.uniform(-0.8, 0.8),
                    "vz": random.uniform(-0.8, 0.8),
                    "life": 12,
                    "color": (255, random.randint(90, 220), 30),
                    "size": random.uniform(3, 6)
                })

            # Check Pillar Collisions (Pillar absorbs fireball)
            hit_pillar = False
            for pil in self.pillars:
                if abs(fb["z"] - pil["z"]) < 20.0 and abs(fb["x"] - pil["x"]) < (pil["w"] / 2.0 + 10.0):
                    hit_pillar = True
                    self._spawn_3d_dust(pil["x"], -20.0, pil["z"])
                    self.combat_logs.append("🛡️ Fireball impacted Stone Pillar cover!")
                    if len(self.combat_logs) > 6:
                        self.combat_logs.pop(0)
                    break
            if hit_pillar:
                continue

            # Check collision with Player Screen (Z near camera)
            if fb["z"] <= 20.0 and fb["life"] > 0:
                lat_dist = abs(fb["x"] - self.player_x)
                if lat_dist < 65.0:
                    # 1. In-Hand Shield Block!
                    if self.shield_held:
                        self.shield_block_popup = 26
                        self.shield_cooldown = self.shield_max_cooldown
                        self.shield_held = False
                        self.screen_shake = 5
                        self._spawn_slash_sparks(self.cx, self.cy + 60)
                        self.combat_logs.append("🛡️ CLANG! Clipboard Shield BLOCKED the Fireball!")
                        if len(self.combat_logs) > 6:
                            self.combat_logs.pop(0)
                        continue

                    # 2. Check Dodge i-frames
                    if self.player_invincible_timer > 0 or self.player_is_dodging:
                        self.combat_logs.append("💨 Fireball whizzed past during Dodge Roll!")
                        if len(self.combat_logs) > 6:
                            self.combat_logs.pop(0)
                        continue

                    # 3. Direct Hit on Player
                    fb_dmg = 14 + (self.current_phase * 4)
                    if self.player_buff_name == "Iron Armor (-50% dmg)":
                        fb_dmg = max(1, fb_dmg // 2)

                    self.player_hp = max(0, self.player_hp - fb_dmg)
                    self.player_invincible_timer = 36
                    self.damage_flash = 16
                    self.screen_shake = 10
                    self.boss_accumulated_reward += 1.0

                    self.face_state = "hurt"
                    self.face_timer = 26
                    self.combat_logs.append(f"🔥 Arcane Fireball scorched Player for {fb_dmg} DMG! (Q-Reward: +1.0)")
                    if len(self.combat_logs) > 6:
                        self.combat_logs.pop(0)

                    if self.player_hp <= 0:
                        self.game_state.failed_level = "boss_arena_pov"
                        self.game_state.failure_reason = "DOOM Arena Defeat: Incinerated by Professor Terminus."
                        self.game_over_timer = 90
                    continue

            if fb["z"] > 5.0 and fb["life"] > 0:
                active.append(fb)
            else:
                self._spawn_3d_dust(fb["x"], fb["y"], fb["z"])

        self.boss_fireballs = active

    # -------------------------------------------------------------------
    # Boss AI & Strict Phase Combat Logic
    # -------------------------------------------------------------------
    def _update_boss_ai(self) -> None:
        dist_3d = math.sqrt((self.boss_x - self.player_x) ** 2 + self.boss_z ** 2)
        current_state = self.boss_agent.get_state(dist_3d, self.player_last_action)

        if self.boss_flash_hit_timer > 0:
            self.boss_flash_hit_timer -= 1

        # Handle Attack Windup / Telegraph Tells
        if self.boss_windup_timer > 0:
            self.boss_windup_timer -= 1
            if self.boss_windup_timer <= 0:
                # Windup finished -> Deliver the attack!
                if self.boss_windup_type == "fireball":
                    self._cast_boss_fireball()
                elif self.boss_windup_type == "melee":
                    self._boss_melee_strike()
                self.boss_windup_type = "none"

        # Action Decision Cycle (Slower, 42-48 frame intervals)
        self.boss_action_timer -= 1
        if self.boss_action_timer <= 0:
            # 1. Bellman Update
            if self.boss_prev_state is not None and self.boss_prev_action is not None:
                if self.boss_accumulated_reward == 0.0:
                    if self.boss_prev_action == "wait" and dist_3d > 180:
                        reward = 0.05
                    else:
                        reward = -0.10
                else:
                    reward = self.boss_accumulated_reward

                self.boss_agent.learn(
                    self.boss_prev_state,
                    self.boss_prev_action,
                    reward,
                    current_state
                )
                self.boss_accumulated_reward = 0.0

            # 2. Choose Action
            chosen_action = self.boss_agent.choose_action(current_state)
            self.boss_prev_state = current_state
            self.boss_prev_action = chosen_action
            self.boss_current_action = chosen_action

            # Pacing durations by phase
            if chosen_action == "attack":
                self.boss_action_duration = 44 if self.current_phase == 1 else (38 if self.current_phase == 2 else 32)
                self.boss_is_attacking = True
            elif chosen_action == "dodge":
                self.boss_action_duration = 26 if self.current_phase == 1 else (22 if self.current_phase == 2 else 18)
                self.boss_is_dodging = True
            elif chosen_action == "retreat":
                self.boss_action_duration = 32 if self.current_phase == 1 else (26 if self.current_phase == 2 else 20)
            else:  # wait
                self.boss_action_duration = 30 if self.current_phase == 1 else (24 if self.current_phase == 2 else 18)

            self.boss_action_timer = self.boss_action_duration

            # Initiate Telegraphed Attack Windup when action is 'attack'
            if chosen_action == "attack" and self.boss_windup_timer <= 0:
                if self.current_phase == 1:
                    # Phase 1: Pure Ranged Telegraph
                    self.boss_windup_timer = 24  # Clear 24 frame warning charge
                    self.boss_windup_type = "fireball"
                    self.boss_is_casting = True
                elif self.current_phase == 2:
                    # Phase 2: Pure Melee Windup
                    self.boss_windup_timer = 26  # Clear 26 frame windup swing
                    self.boss_windup_type = "melee"
                else:
                    # Phase 3: Hybrid (Melee if close, Fireball if far)
                    if self.boss_z < 200.0:
                        self.boss_windup_timer = 22
                        self.boss_windup_type = "melee"
                    else:
                        self.boss_windup_timer = 20
                        self.boss_windup_type = "fireball"
                        self.boss_is_casting = True

        # Phase 1 Fireball Timer Check (Supplementary spellcast if waiting/retreating)
        if self.current_phase in (1, 3):
            if self.boss_fireball_cooldown > 0:
                self.boss_fireball_cooldown -= 1
            elif self.boss_windup_timer <= 0 and self.boss_current_action in ("retreat", "wait"):
                self.boss_windup_timer = 22
                self.boss_windup_type = "fireball"
                self.boss_is_casting = True
                self.boss_fireball_cooldown = 70 if self.current_phase == 1 else 45

        # ----------------------------------------------------------------
        # Strict Phase-Based 3D Movement
        # ----------------------------------------------------------------
        if self.current_phase == 1:
            # PHASE 1: PURE RANGED. Boss strictly stays back! (Z in [260, 420])
            # Even when attacking, he does NOT advance into melee range.
            target_z = 320.0
            self.boss_z += (target_z - self.boss_z) * 0.05

            if self.boss_current_action == "dodge":
                dodge_dir = 1.0 if (self.boss_x < 0) else -1.0
                self.boss_x += dodge_dir * 6.0
            elif self.boss_current_action == "retreat":
                self.boss_z = min(420.0, self.boss_z + 4.0)
            else:
                self.boss_x += math.sin(time.time() * 2.0) * 1.8

        elif self.current_phase == 2:
            # PHASE 2: PURE MELEE DUEL. Boss advances into duel range! (Z in [140, 190])
            target_z = 160.0
            self.boss_z += (target_z - self.boss_z) * 0.08

            # Lateral tracking towards player
            dir_x = 1.0 if (self.player_x > self.boss_x) else -1.0
            self.boss_x += dir_x * 2.8

            if self.boss_current_action == "dodge":
                dodge_dir = 1.0 if (self.boss_x < self.player_x) else -1.0
                self.boss_x += dodge_dir * 7.0

        else:
            # PHASE 3: HYBRID. Aggressive gap-closing and retreating cycles
            if self.boss_current_action == "attack":
                self.boss_z = max(130.0, self.boss_z - 6.5)
                dir_x = 1.0 if (self.player_x > self.boss_x) else -1.0
                self.boss_x += dir_x * 3.2
            elif self.boss_current_action == "retreat":
                self.boss_z = min(400.0, self.boss_z + 5.5)
            elif self.boss_current_action == "dodge":
                dodge_dir = 1.0 if (self.boss_x < 0) else -1.0
                self.boss_x += dodge_dir * 7.5
            else:
                self.boss_x += math.sin(time.time() * 2.5) * 2.4

        # Bounds clamping
        self.boss_x = max(-230.0, min(230.0, self.boss_x))
        if self.current_phase == 1:
            self.boss_z = max(250.0, min(430.0, self.boss_z))
        else:
            self.boss_z = max(125.0, min(430.0, self.boss_z))

    def _cast_boss_fireball(self) -> None:
        """Launch slower, readable 3D Arcane Fireball."""
        dx = self.player_x - self.boss_x
        dy = self.player_eye_y - (self.boss_y + 35.0)
        dz = 0.0 - self.boss_z

        dist = math.sqrt(dx * dx + dy * dy + dz * dz)
        # Slower, readable travel speed (~5.8 frames instead of 10+)
        speed = 5.6 + (self.current_phase * 0.9)

        if self.current_phase == 3:
            for offset_x in (-20.0, 20.0):
                self.boss_fireballs.append({
                    "x": self.boss_x + offset_x,
                    "y": self.boss_y + 35.0,
                    "z": self.boss_z - 15.0,
                    "vx": (dx / dist) * speed,
                    "vy": (dy / dist) * speed,
                    "vz": (dz / dist) * speed,
                    "life": 140
                })
        else:
            self.boss_fireballs.append({
                "x": self.boss_x,
                "y": self.boss_y + 35.0,
                "z": self.boss_z - 15.0,
                "vx": (dx / dist) * speed,
                "vy": (dy / dist) * speed,
                "vz": (dz / dist) * speed,
                "life": 140
            })

        self.combat_logs.append("🔥 Professor Terminus launched Arcane Fireball!")
        if len(self.combat_logs) > 6:
            self.combat_logs.pop(0)

    def _boss_melee_strike(self) -> None:
        """Close-range melee ruler strike from Professor Terminus."""
        dist_3d = math.sqrt((self.boss_x - self.player_x) ** 2 + self.boss_z ** 2)
        if dist_3d > 210.0:
            return  # Missed (player moved back or dodged)

        # 1. In-Hand Shield Block!
        if self.shield_held:
            self.shield_block_popup = 26
            self.shield_cooldown = self.shield_max_cooldown
            self.shield_held = False
            self.screen_shake = 6
            self._spawn_slash_sparks(self.cx, self.cy + 60)
            self.combat_logs.append("🛡️ CLANG! Shield BLOCKED Professor Terminus's Melee Strike!")
            if len(self.combat_logs) > 6:
                self.combat_logs.pop(0)
            return

        # 2. Dodge i-frames check
        if self.player_invincible_timer > 0 or self.player_is_dodging:
            self.combat_logs.append("💨 Evaded Professor Terminus's Melee Strike!")
            if len(self.combat_logs) > 6:
                self.combat_logs.pop(0)
            return

        # 3. Direct Strike
        dmg = 18 + (self.current_phase * 5)
        if self.player_buff_name == "Iron Armor (-50% dmg)":
            dmg = max(1, dmg // 2)

        self.player_hp = max(0, self.player_hp - dmg)
        self.player_invincible_timer = 36
        self.damage_flash = 18
        self.screen_shake = 14
        self.boss_accumulated_reward += 1.0

        self.face_state = "hurt"
        self.face_timer = 28
        self.combat_logs.append(f"⚔️ Professor Terminus MELEE SWING struck for {dmg} DMG!")
        if len(self.combat_logs) > 6:
            self.combat_logs.pop(0)

        if self.player_hp <= 0:
            self.game_state.failed_level = "boss_arena_pov"
            self.game_state.failure_reason = "DOOM Arena Defeat: Struck down by Professor Terminus."
            self.game_over_timer = 90

    # -------------------------------------------------------------------
    # Phase Progression & CAT Quiz Intermissions
    # -------------------------------------------------------------------
    def _check_phase_transitions(self) -> None:
        if self.current_phase == 1 and self.boss_hp <= 70:
            self.current_phase = 2
            self.player_weapon = "ruler"
            self.combat_logs.append("★★★ PHASE 2: CLOSE-RANGE STEEL RULER DUEL! ★★★")
            self._trigger_cat_intermission("medium")

        elif self.current_phase == 2 and self.boss_hp <= 30:
            self.current_phase = 3
            self.combat_logs.append("★★★ PHASE 3: HYBRID ARSENAL & ENRAGED BOSS! ★★★")
            self._trigger_cat_intermission("hard")

    def _trigger_cat_intermission(self, difficulty: str) -> None:
        self.in_quiz = True
        self.quiz_difficulty = difficulty
        q_list = CAT_QUESTIONS.get(difficulty, CAT_QUESTIONS["easy"])
        self.quiz_data = random.choice(q_list)
        self.quiz_selected = None
        self.quiz_answered = False
        self.quiz_feedback_timer = 0

    def _process_quiz_answer(self, choice_idx: int) -> None:
        if self.quiz_answered or not self.quiz_data:
            return

        self.quiz_selected = choice_idx
        self.quiz_answered = True
        self.quiz_feedback_timer = 110

        if choice_idx == self.quiz_data["correct"]:
            if self.quiz_difficulty == "medium":
                self.player_buff_name = "Damage Boost (+50%)"
                self.player_buff_timer = 450
            else:
                self.player_buff_name = "Iron Armor (-50% dmg)"
                self.player_buff_timer = 500
                self.player_hp = min(self.player_max_hp, self.player_hp + 35)

            self.combat_logs.append(f"CAT Quiz Correct! Buff Granted: {self.player_buff_name}")
        else:
            self.combat_logs.append("CAT Quiz Incorrect. No bonus buff granted.")

        if len(self.combat_logs) > 6:
            self.combat_logs.pop(0)

    # -------------------------------------------------------------------
    # Particle & Visual FX
    # -------------------------------------------------------------------
    def _update_particles(self) -> None:
        active_p = []
        for p in self.particles_3d:
            p["x"] += p.get("vx", 0)
            p["y"] += p.get("vy", 0)
            p["z"] += p.get("vz", 0)
            p["life"] -= 1
            if p["life"] > 0:
                active_p.append(p)
        self.particles_3d = active_p

        active_m = []
        for m in self.hit_markers:
            m["y"] -= 1.2
            m["life"] -= 1
            if m["life"] > 0:
                active_m.append(m)
        self.hit_markers = active_m

    def _spawn_3d_hit_spark(self, x: float, y: float, z: float, color: Tuple[int, int, int]) -> None:
        for _ in range(12):
            self.particles_3d.append({
                "x": x, "y": y, "z": z,
                "vx": random.uniform(-4, 4),
                "vy": random.uniform(-3, 5),
                "vz": random.uniform(-4, 4),
                "life": random.randint(10, 20),
                "color": color,
                "size": random.uniform(3, 6)
            })

    def _spawn_3d_dust(self, x: float, y: float, z: float) -> None:
        for _ in range(6):
            self.particles_3d.append({
                "x": x, "y": y, "z": z,
                "vx": random.uniform(-2, 2),
                "vy": random.uniform(0.5, 3.0),
                "vz": random.uniform(-2, 2),
                "life": 12,
                "color": (150, 155, 165),
                "size": random.uniform(3, 5)
            })

    def _spawn_slash_sparks(self, sx: float, sy: float) -> None:
        for _ in range(16):
            self.particles_3d.append({
                "x": self.player_x + random.uniform(-20, 20),
                "y": self.player_eye_y + random.uniform(-20, 20),
                "z": 40.0,
                "vx": random.uniform(-5, 5),
                "vy": random.uniform(-4, 6),
                "vz": random.uniform(2, 8),
                "life": 16,
                "color": (100, 230, 255),
                "size": random.uniform(4, 7)
            })

    # -------------------------------------------------------------------
    # Rendering Pipeline
    # -------------------------------------------------------------------
    def draw(self, surface: pygame.Surface) -> None:
        ox = random.randint(-self.screen_shake, self.screen_shake) if self.screen_shake > 0 else 0
        oy = random.randint(-self.screen_shake, self.screen_shake) if self.screen_shake > 0 else 0

        view_surf = pygame.Surface((self.view_w, self.view_h))
        view_surf.fill((14, 12, 20))

        self._draw_hall_background(view_surf)
        self._draw_3d_environment(view_surf)

        # Render Queue sorted by depth Z
        render_queue = []
        render_queue.append({"type": "boss", "z": self.boss_z})

        for idx, pil in enumerate(self.pillars):
            render_queue.append({"type": "pillar", "z": pil["z"], "data": pil, "idx": idx})

        for p in self.player_pebbles:
            render_queue.append({"type": "pebble", "z": p["z"], "data": p})
        for fb in self.boss_fireballs:
            render_queue.append({"type": "fireball", "z": fb["z"], "data": fb})

        for pt in self.particles_3d:
            render_queue.append({"type": "particle", "z": pt["z"], "data": pt})

        render_queue.sort(key=lambda item: item["z"], reverse=True)

        for item in render_queue:
            t = item["type"]
            if t == "boss":
                self._draw_boss_3d(view_surf)
            elif t == "pillar":
                self._draw_pillar_3d(view_surf, item["data"])
            elif t == "pebble":
                self._draw_pebble_3d(view_surf, item["data"])
            elif t == "fireball":
                self._draw_fireball_3d(view_surf, item["data"])
            elif t == "particle":
                self._draw_particle_3d(view_surf, item["data"])

        # First-Person Weapons & Shield Viewmodel
        self._draw_weapon_viewmodel(view_surf)
        self._draw_shield_viewmodel(view_surf)

        # Crosshair & Hit Markers
        self._draw_crosshair(view_surf)
        for m in self.hit_markers:
            txt = self.font_hud_big.render(m["text"], True, m["color"])
            view_surf.blit(txt, (int(m["x"] - txt.get_width() // 2), int(m["y"])))

        # Screen Vignettes
        if self.damage_flash > 0:
            red_vig = pygame.Surface((self.view_w, self.view_h), pygame.SRCALPHA)
            alpha = min(160, self.damage_flash * 12)
            red_vig.fill((230, 20, 20, alpha))
            view_surf.blit(red_vig, (0, 0))

        if self.shield_block_popup > 0:
            block_txt = self.font_banner.render("SHIELD BLOCKED!", True, CYAN)
            bx = (self.view_w - block_txt.get_width()) // 2
            by = self.cy + 40
            view_surf.blit(block_txt, (bx, by))

        surface.blit(view_surf, (ox, oy))

        # Bottom DOOM Status Bar HUD
        self._draw_doom_status_bar(surface)

        # Top Boss Bar
        self._draw_boss_header(surface)

        if self.in_quiz:
            self._draw_quiz_modal(surface)

        if self.boss_hp <= 0:
            self._draw_victory_banner(surface)
        elif self.player_hp <= 0:
            self._draw_defeat_banner(surface)

    def _draw_hall_background(self, surface: pygame.Surface) -> None:
        if self.bg:
            pan_x = int(-self.player_x * 0.22)
            surface.blit(self.bg, (pan_x, 0))
            if pan_x > 0:
                surface.blit(self.bg, (pan_x - DISPLAY_WIDTH, 0))
            elif pan_x < 0:
                surface.blit(self.bg, (pan_x + DISPLAY_WIDTH, 0))
        else:
            for y in range(self.cy):
                ratio = y / self.cy
                col = (int(15 * (1 - ratio) + 30 * ratio), int(10 * (1 - ratio) + 20 * ratio), int(25 * (1 - ratio) + 40 * ratio))
                pygame.draw.line(surface, col, (0, y), (self.view_w, y))

        horizon_fade = pygame.Surface((self.view_w, 60), pygame.SRCALPHA)
        horizon_fade.fill((10, 8, 16, 170))
        surface.blit(horizon_fade, (0, self.cy - 30))

    def _draw_3d_environment(self, surface: pygame.Surface) -> None:
        floor_rect = pygame.Rect(0, self.cy, self.view_w, self.view_h - self.cy)
        pygame.draw.rect(surface, (22, 24, 34), floor_rect)

        for x_lane in range(-600, 700, 100):
            p1 = self.project(x_lane, -40.0, 500.0)
            p2 = self.project(x_lane, -40.0, 20.0)
            pygame.draw.line(surface, (42, 48, 65), (p1[0], p1[1]), (p2[0], p2[1]), 1)

        for z_line in (50, 80, 120, 170, 240, 330, 440):
            p_left = self.project(-400.0, -40.0, z_line)
            p_right = self.project(400.0, -40.0, z_line)
            pygame.draw.line(surface, (36, 42, 58), (p_left[0], p_left[1]), (p_right[0], p_right[1]), 1)

    def _draw_boss_3d(self, surface: pygame.Surface) -> None:
        bsx, bsy, scale = self.project(self.boss_x, self.boss_y, self.boss_z)

        base_w = 140
        base_h = 140
        w = max(32, int(base_w * scale))
        h = max(32, int(base_h * scale))

        shadow_w = int(w * 0.75)
        shadow_h = int(18 * scale)
        pygame.draw.ellipse(surface, (8, 8, 12, 180), (int(bsx - shadow_w // 2), int(bsy - shadow_h // 2), shadow_w, shadow_h))

        side = "left" if (self.boss_x < self.player_x) else "right"
        if self.boss_flash_hit_timer > 0:
            spr = self.boss_sprites.get(f"hurt_{side}")
        elif self.boss_is_attacking or self.boss_windup_type == "melee":
            spr = self.boss_sprites.get(f"attack_{side}")
        elif self.boss_is_casting or self.boss_windup_type == "fireball":
            spr = self.boss_sprites.get(f"cast_{side}")
        else:
            spr = self.boss_sprites.get(f"idle_{side}")

        if spr:
            scaled_spr = pygame.transform.scale(spr, (w, h))
            top_x = int(bsx - w // 2)
            top_y = int(bsy - h)
            surface.blit(scaled_spr, (top_x, top_y))

            # Phase Aura Glow
            if self.current_phase == 3:
                aura_s = pygame.Surface((w + 20, h + 20), pygame.SRCALPHA)
                pygame.draw.ellipse(aura_s, (240, 40, 40, 75), aura_s.get_rect())
                surface.blit(aura_s, (top_x - 10, top_y - 10))
        else:
            box_rect = pygame.Rect(int(bsx - w // 2), int(bsy - h), w, h)
            pygame.draw.rect(surface, PURPLE if self.current_phase == 1 else (ORANGE if self.current_phase == 2 else RED), box_rect, border_radius=6)
            pygame.draw.rect(surface, GOLD, box_rect, 2, border_radius=6)

        # ATTACK TELEGRAPH CHARGE TELL (Warning visual)
        if self.boss_windup_timer > 0:
            # Pulsing warning glow around boss
            pulse_rad = int(h * 0.55 + math.sin(time.time() * 15.0) * 8)
            tell_color = (255, 60, 40) if self.boss_windup_type == "fireball" else (255, 210, 40)

            warn_s = pygame.Surface((pulse_rad * 2, pulse_rad * 2), pygame.SRCALPHA)
            pygame.draw.circle(warn_s, (tell_color[0], tell_color[1], tell_color[2], 90), (pulse_rad, pulse_rad), pulse_rad, 4)
            surface.blit(warn_s, (int(bsx - pulse_rad), int(bsy - h // 2 - pulse_rad)))

            # Exclamation / Warning Icon above head
            warn_txt = "! INCOMING SPELL !" if self.boss_windup_type == "fireball" else "! MELEE STRIKE !"
            warn_lbl = self.font_hud.render(warn_txt, True, tell_color)
            surface.blit(warn_lbl, (int(bsx - warn_lbl.get_width() // 2), int(bsy - h - 45)))

        # Tag above Boss Head
        tag = f"PROF. TERMINUS [{self.boss_current_action.upper()}]"
        tag_color = GREEN if self.boss_current_action == "attack" else (YELLOW if self.boss_current_action == "dodge" else WHITE)
        tag_s = self.font_hud.render(tag, True, tag_color)
        surface.blit(tag_s, (int(bsx - tag_s.get_width() // 2), int(bsy - h - 24)))

    def _draw_pillar_3d(self, surface: pygame.Surface, pillar: Dict) -> None:
        psx, psy, scale = self.project(pillar["x"], -40.0, pillar["z"])
        pw = int(pillar["w"] * scale)
        ph = int(pillar["h"] * scale)

        pillar_rect = pygame.Rect(int(psx - pw // 2), int(psy - ph), pw, ph)

        # Stone Pillar Body & Shading
        pygame.draw.rect(surface, (45, 50, 65), pillar_rect)
        pygame.draw.rect(surface, (70, 78, 98), (pillar_rect.x, pillar_rect.y, int(pw * 0.4), ph))
        pygame.draw.rect(surface, (25, 28, 38), pillar_rect, 2)

        # Capital & Base
        base_h = int(16 * scale)
        pygame.draw.rect(surface, (60, 68, 86), (int(psx - pw * 0.65), int(psy - base_h), int(pw * 1.3), base_h))
        pygame.draw.rect(surface, (60, 68, 86), (int(psx - pw * 0.65), int(psy - ph), int(pw * 1.3), base_h))

        # Pillar Tag
        lbl = self.font_qtable.render(pillar["label"], True, (160, 175, 200))
        surface.blit(lbl, (int(psx - lbl.get_width() // 2), int(psy - ph - 16)))

    def _draw_pebble_3d(self, surface: pygame.Surface, p: Dict) -> None:
        sx, sy, scale = self.project(p["x"], p["y"], p["z"])
        rad = max(3, int(6 * scale))
        pygame.draw.circle(surface, (235, 235, 245), (int(sx), int(sy)), rad)
        pygame.draw.circle(surface, GOLD, (int(sx), int(sy)), rad, 1)

    def _draw_fireball_3d(self, surface: pygame.Surface, fb: Dict) -> None:
        sx, sy, scale = self.project(fb["x"], fb["y"], fb["z"])
        rad = max(6, int(18 * scale))

        glow_s = pygame.Surface((rad * 4, rad * 4), pygame.SRCALPHA)
        pygame.draw.circle(glow_s, (255, 80, 20, 85), (rad * 2, rad * 2), rad * 2)
        surface.blit(glow_s, (int(sx - rad * 2), int(sy - rad * 2)))

        pygame.draw.circle(surface, (255, 140, 40), (int(sx), int(sy)), rad)
        pygame.draw.circle(surface, (255, 255, 180), (int(sx), int(sy)), max(2, rad // 2))

    def _draw_particle_3d(self, surface: pygame.Surface, pt: Dict) -> None:
        sx, sy, scale = self.project(pt["x"], pt["y"], pt["z"])
        sz = max(2, int(pt.get("size", 4) * scale))
        pygame.draw.circle(surface, pt["color"], (int(sx), int(sy)), sz)

    # -------------------------------------------------------------------
    # Weapon & Shield Viewmodels
    # -------------------------------------------------------------------
    def _draw_weapon_viewmodel(self, surface: pygame.Surface) -> None:
        bottom_y = self.view_h

        # Slingshot (Phase 1 & Phase 3)
        if self.current_phase in (1, 3) and self.player_weapon == "slingshot":
            # If shield is raised, slingshot tucks away slightly
            sling_offset_x = int(-self.shield_raise_anim * 80)
            sling_x = self.cx + 50 + sling_offset_x + int(self.slingshot_recoil * 0.4)
            sling_y = bottom_y + int(self.slingshot_recoil) + int(self.shield_raise_anim * 40)

            fork_w = 110
            fork_h = 125
            base_pt = (sling_x, sling_y)
            left_fork = (sling_x - fork_w // 2, sling_y - fork_h)
            right_fork = (sling_x + fork_w // 2, sling_y - fork_h)

            pygame.draw.line(surface, (135, 85, 45), base_pt, left_fork, 16)
            pygame.draw.line(surface, (135, 85, 45), base_pt, right_fork, 16)
            pygame.draw.line(surface, (185, 125, 75), base_pt, left_fork, 7)
            pygame.draw.line(surface, (185, 125, 75), base_pt, right_fork, 7)

            band_pull_y = sling_y - 40 + int(self.slingshot_recoil * 1.5)
            pygame.draw.line(surface, (210, 45, 45), left_fork, (sling_x, band_pull_y), 4)
            pygame.draw.line(surface, (210, 45, 45), right_fork, (sling_x, band_pull_y), 4)
            pygame.draw.circle(surface, (220, 220, 230), (sling_x, band_pull_y), 8)

        # Steel Ruler (Phase 2 & Phase 3)
        if self.current_phase in (2, 3) and (self.player_weapon == "ruler" or self.ruler_swinging):
            ruler_x = self.cx + 220
            ruler_y = bottom_y - 20

            if self.ruler_swinging:
                progress = 1.0 - (self.ruler_swing_timer / 18.0)
                angle = -45.0 + progress * 110.0
                slash_cx = self.cx - 50 + int(progress * 180)
                slash_cy = self.cy + 30

                arc_s = pygame.Surface((320, 160), pygame.SRCALPHA)
                pygame.draw.ellipse(arc_s, (60, 220, 255, 140), (0, 20, 300, 100), 12)
                surface.blit(arc_s, (slash_cx - 150, slash_cy - 80))

                blade_end_x = slash_cx + int(math.cos(math.radians(angle)) * 170)
                blade_end_y = slash_cy + int(math.sin(math.radians(angle)) * 170)
                pygame.draw.line(surface, (220, 230, 245), (slash_cx, slash_cy), (blade_end_x, blade_end_y), 10)
                pygame.draw.line(surface, WHITE, (slash_cx, slash_cy), (blade_end_x, blade_end_y), 4)
            else:
                pygame.draw.line(surface, (190, 200, 215), (ruler_x, ruler_y), (ruler_x - 70, ruler_y - 140), 12)
                pygame.draw.line(surface, WHITE, (ruler_x, ruler_y), (ruler_x - 70, ruler_y - 140), 4)

    def _draw_shield_viewmodel(self, surface: pygame.Surface) -> None:
        """Draw the in-hand Clipboard Shield on the left/center screen."""
        if self.shield_raise_anim <= 0.05:
            return

        # Interpolate position from lower screen up to center defensive guard
        guard_y = int((self.view_h + 120) - (self.shield_raise_anim * 260))
        guard_x = int(self.cx - 160 + (self.shield_raise_anim * 40))

        sh_w = 210
        sh_h = 270
        shield_rect = pygame.Rect(guard_x - sh_w // 2, guard_y - sh_h // 2, sh_w, sh_h)

        # Thick Clipboard Wood/Hardboard
        pygame.draw.rect(surface, (140, 95, 55), shield_rect, border_radius=10)
        pygame.draw.rect(surface, (110, 70, 40), shield_rect, 4, border_radius=10)

        # Steel Reinforcement Brackets & Corner Guards
        pygame.draw.rect(surface, (180, 190, 205), (shield_rect.x, shield_rect.y, 40, 14), border_radius=4)
        pygame.draw.rect(surface, (180, 190, 205), (shield_rect.right - 40, shield_rect.y, 40, 14), border_radius=4)
        pygame.draw.rect(surface, (180, 190, 205), (shield_rect.x, shield_rect.bottom - 14, 40, 14), border_radius=4)
        pygame.draw.rect(surface, (180, 190, 205), (shield_rect.right - 40, shield_rect.bottom - 14, 40, 14), border_radius=4)

        # Heavy Metal Clip at Top
        clip_rect = pygame.Rect(guard_x - 45, shield_rect.y - 10, 90, 28)
        pygame.draw.rect(surface, (200, 210, 225), clip_rect, border_radius=5)
        pygame.draw.rect(surface, (90, 100, 115), clip_rect, 2, border_radius=5)

        # Clipped Exam Hall Blueprint Sheet
        sheet_rect = pygame.Rect(shield_rect.x + 18, shield_rect.y + 26, sh_w - 36, sh_h - 48)
        pygame.draw.rect(surface, (245, 242, 230), sheet_rect, border_radius=4)
        pygame.draw.line(surface, (90, 130, 190), (sheet_rect.x + 12, sheet_rect.y + 20), (sheet_rect.right - 12, sheet_rect.y + 20), 2)
        pygame.draw.line(surface, (160, 165, 175), (sheet_rect.x + 12, sheet_rect.y + 36), (sheet_rect.right - 25, sheet_rect.y + 36), 2)
        pygame.draw.line(surface, (160, 165, 175), (sheet_rect.x + 12, sheet_rect.y + 50), (sheet_rect.right - 40, sheet_rect.y + 50), 2)

        # Shield Status Label on the board
        sh_lbl = self.font_hud.render("CLIPBOARD SHIELD: GUARDING", True, (40, 90, 160))
        surface.blit(sh_lbl, (sheet_rect.x + 8, sheet_rect.y + 80))

    def _draw_crosshair(self, surface: pygame.Surface) -> None:
        mx, my = self.mouse_x, min(self.view_h - 10, self.mouse_y)
        ch_col = CYAN if self.current_phase == 1 else (GOLD if self.current_phase == 3 else RED)

        pygame.draw.circle(surface, ch_col, (mx, my), 14, 2)
        pygame.draw.circle(surface, WHITE, (mx, my), 2)

        pygame.draw.line(surface, ch_col, (mx - 22, my), (mx - 15, my), 2)
        pygame.draw.line(surface, ch_col, (mx + 15, my), (mx + 22, my), 2)
        pygame.draw.line(surface, ch_col, (mx, my - 22), (mx, my - 15), 2)
        pygame.draw.line(surface, ch_col, (mx, my + 15), (mx, my + 22), 2)

    # -------------------------------------------------------------------
    # DOOM Retro Status Bar HUD (Bottom Screen)
    # -------------------------------------------------------------------
    def _draw_doom_status_bar(self, surface: pygame.Surface) -> None:
        bar_y = DISPLAY_HEIGHT - self.status_bar_h
        bar_rect = pygame.Rect(0, bar_y, DISPLAY_WIDTH, self.status_bar_h)

        pygame.draw.rect(surface, (28, 30, 38), bar_rect)
        pygame.draw.line(surface, (65, 75, 95), (0, bar_y), (DISPLAY_WIDTH, bar_y), 3)

        pygame.draw.line(surface, (50, 55, 70), (280, bar_y), (280, DISPLAY_HEIGHT), 2)
        pygame.draw.line(surface, (50, 55, 70), (510, bar_y), (510, DISPLAY_HEIGHT), 2)
        pygame.draw.line(surface, (50, 55, 70), (810, bar_y), (810, DISPLAY_HEIGHT), 2)

        # 1. Left Block: Health & Shield Cooldown
        hp_title = self.font_hud.render("HEALTH", True, RED)
        surface.blit(hp_title, (30, bar_y + 12))
        hp_val_col = GREEN if self.player_hp > 40 else (YELLOW if self.player_hp > 20 else RED)
        hp_str = f"{self.player_hp}%"
        hp_big = self.font_title.render(hp_str, True, hp_val_col)
        surface.blit(hp_big, (30, bar_y + 32))

        # Shield Status Indicator
        sh_title = self.font_hud.render("CLIPBOARD SHIELD", True, CYAN)
        surface.blit(sh_title, (130, bar_y + 12))

        if self.shield_cooldown > 0:
            cd_pct = self.shield_cooldown / self.shield_max_cooldown
            sh_status = f"RECHARGING {int((1.0 - cd_pct) * 100)}%"
            sh_col = YELLOW
        elif self.shield_held:
            sh_status = "GUARDING [100%]"
            sh_col = GREEN
        else:
            sh_status = "READY (HOLD RMB)"
            sh_col = CYAN

        surface.blit(self.font_qtable.render(sh_status, True, sh_col), (130, bar_y + 40))

        # Cooldown progress bar
        bar_w = 130
        pygame.draw.rect(surface, DARK_GRAY, (130, bar_y + 60, bar_w, 10), border_radius=3)
        if self.shield_cooldown == 0:
            pygame.draw.rect(surface, GREEN, (130, bar_y + 60, bar_w, 10), border_radius=3)
        else:
            ready_w = int(bar_w * (1.0 - (self.shield_cooldown / self.shield_max_cooldown)))
            pygame.draw.rect(surface, YELLOW, (130, bar_y + 60, ready_w, 10), border_radius=3)

        buff_col = GOLD if self.player_buff_name != "None" else (120, 130, 150)
        buff_txt = self.font_qtable.render(f"BUFF: {self.player_buff_name}", True, buff_col)
        surface.blit(buff_txt, (30, bar_y + 90))

        # 2. Face Cam
        face_x = 360
        face_y = bar_y + 20
        face_w, face_h = 75, 85

        face_frame = pygame.Rect(face_x, face_y, face_w, face_h)
        pygame.draw.rect(surface, (15, 16, 22), face_frame)
        pygame.draw.rect(surface, (80, 90, 110), face_frame, 2)

        self._draw_student_face_cam(surface, face_x + face_w // 2, face_y + face_h // 2)

        face_lbl = self.font_qtable.render("HERO CAM", True, (160, 170, 190))
        surface.blit(face_lbl, (face_x + 12, face_y + face_h + 4))

        # 3. Tactical Controls
        w_title = self.font_hud.render("TACTICAL CONTROLS", True, GOLD)
        surface.blit(w_title, (530, bar_y + 12))

        ctrl_1 = "LMB: Shoot Slingshot" if self.current_phase == 1 else ("LMB: Steel Ruler Slash" if self.current_phase == 2 else "LMB: Slingshot | U/C: Slash")
        ctrl_2 = "RMB / SPACE: Hold Clipboard Shield (100% Block)"
        ctrl_3 = "A / D: Strafe behind Pillars | SHIFT: Dodge"

        surface.blit(self.font_qtable.render(ctrl_1, True, WHITE), (530, bar_y + 38))
        surface.blit(self.font_qtable.render(ctrl_2, True, CYAN), (530, bar_y + 58))
        surface.blit(self.font_qtable.render(ctrl_3, True, YELLOW), (530, bar_y + 78))

        # 4. Q-Matrix CRT Monitor
        crt_x = 830
        crt_y = bar_y + 10
        crt_w = 430
        crt_h = self.status_bar_h - 20

        crt_rect = pygame.Rect(crt_x, crt_y, crt_w, crt_h)
        pygame.draw.rect(surface, (8, 24, 12), crt_rect)
        pygame.draw.rect(surface, (40, 160, 60), crt_rect, 2)

        crt_hdr = self.font_qheader.render(f"Q-MATRIX CRT [Step {self.boss_agent.total_steps} | Epsilon: {self.boss_agent.epsilon:.2f}]", True, (60, 240, 80))
        surface.blit(crt_hdr, (crt_x + 10, crt_y + 6))

        sub_hdr = self.font_qtable.render("STATE (Dist|Plr)  | ATK    DODGE  RETR   WAIT", True, (130, 220, 150))
        surface.blit(sub_hdr, (crt_x + 10, crt_y + 24))

        dist_3d = math.sqrt((self.boss_x - self.player_x) ** 2 + self.boss_z ** 2)
        curr_dist = discretize_distance(dist_3d)
        curr_state_key = (curr_dist, self.player_last_action)

        row_y = crt_y + 42
        display_states = [
            ("near", self.player_last_action),
            ("medium", self.player_last_action),
            ("far", self.player_last_action)
        ]

        for st in display_states:
            is_active = (st == curr_state_key)
            d, pa = st
            st_lbl = f"{d[:3].upper():<3}|{pa[:3].upper():<3}"
            q_vals = [self.boss_agent.get_q_value(st, a) for a in ACTIONS]
            val_strs = [f"{v:+0.2f}" for v in q_vals]

            line = f"{st_lbl} | {val_strs[0]:>5} {val_strs[1]:>5} {val_strs[2]:>5} {val_strs[3]:>5}"

            if is_active:
                hl = pygame.Surface((crt_w - 20, 16), pygame.SRCALPHA)
                hl.fill((40, 210, 80, 70))
                surface.blit(hl, (crt_x + 10, row_y - 1))
                col = YELLOW
            else:
                col = (140, 230, 160)

            surface.blit(self.font_qtable.render(line, True, col), (crt_x + 10, row_y))
            row_y += 18

    def _draw_student_face_cam(self, surface: pygame.Surface, cx: int, cy: int) -> None:
        skin_color = (245, 195, 155) if self.player_hp > 30 else (215, 160, 140)
        head_rect = pygame.Rect(cx - 24, cy - 26, 48, 52)
        pygame.draw.rect(surface, skin_color, head_rect, border_radius=8)

        hair_rect = pygame.Rect(cx - 26, cy - 30, 52, 18)
        pygame.draw.rect(surface, (30, 25, 30), hair_rect, border_radius=6)

        eye_y = cy - 8
        left_eye_x = cx - 12
        right_eye_x = cx + 6

        pygame.draw.rect(surface, WHITE, (left_eye_x, eye_y, 8, 8))
        pygame.draw.rect(surface, WHITE, (right_eye_x, eye_y, 8, 8))

        p_offset_x = 0
        p_offset_y = 0
        if self.face_state == "look_left":
            p_offset_x = -2
        elif self.face_state == "look_right":
            p_offset_x = 2
        elif self.face_state == "hurt":
            p_offset_y = -2

        pygame.draw.rect(surface, BLACK, (left_eye_x + 2 + p_offset_x, eye_y + 2 + p_offset_y, 4, 4))
        pygame.draw.rect(surface, BLACK, (right_eye_x + 2 + p_offset_x, eye_y + 2 + p_offset_y, 4, 4))

        mouth_y = cy + 12
        if self.face_state == "grin":
            pygame.draw.line(surface, (140, 30, 30), (cx - 10, mouth_y - 2), (cx + 10, mouth_y - 2), 3)
            pygame.draw.line(surface, WHITE, (cx - 8, mouth_y - 1), (cx + 8, mouth_y - 1), 2)
        elif self.face_state == "hurt" or self.player_hp <= 30:
            pygame.draw.rect(surface, (120, 20, 20), (cx - 10, mouth_y - 2, 20, 6))
            pygame.draw.rect(surface, WHITE, (cx - 8, mouth_y - 1, 16, 4))
            pygame.draw.circle(surface, (160, 60, 60), (cx - 16, cy + 2), 4)
        else:
            pygame.draw.line(surface, (130, 40, 40), (cx - 8, mouth_y), (cx + 8, mouth_y), 3)

    def _draw_boss_header(self, surface: pygame.Surface) -> None:
        bar_w = 480
        bar_h = 24
        bar_x = (DISPLAY_WIDTH - bar_w) // 2
        bar_y = 18

        pygame.draw.rect(surface, (20, 22, 30), (bar_x, bar_y, bar_w, bar_h), border_radius=4)

        pct = max(0.0, self.boss_hp / self.boss_max_hp)
        fill_w = int(bar_w * pct)
        bar_col = RED if self.current_phase == 3 else (ORANGE if self.current_phase == 2 else PURPLE)

        if fill_w > 0:
            pygame.draw.rect(surface, bar_col, (bar_x, bar_y, fill_w, bar_h), border_radius=4)
        pygame.draw.rect(surface, GOLD if self.current_phase == 3 else WHITE, (bar_x, bar_y, bar_w, bar_h), 2, border_radius=4)

        p70_x = bar_x + int(bar_w * 0.70)
        p30_x = bar_x + int(bar_w * 0.30)
        pygame.draw.line(surface, WHITE, (p70_x, bar_y - 2), (p70_x, bar_y + bar_h + 2), 2)
        pygame.draw.line(surface, WHITE, (p30_x, bar_y - 2), (p30_x, bar_y + bar_h + 2), 2)

        phase_mode = "RANGED" if self.current_phase == 1 else ("MELEE DUEL" if self.current_phase == 2 else "HYBRID")
        title = f"PROFESSOR TERMINUS [PHASE {self.current_phase}: {phase_mode}] — HP: {self.boss_hp}/{self.boss_max_hp}"
        lbl = self.font_hud.render(title, True, WHITE)
        surface.blit(lbl, (bar_x + (bar_w - lbl.get_width()) // 2, bar_y + 4))

    def _draw_quiz_modal(self, surface: pygame.Surface) -> None:
        dim_s = pygame.Surface((DISPLAY_WIDTH, DISPLAY_HEIGHT), pygame.SRCALPHA)
        dim_s.fill((5, 8, 15, 235))
        surface.blit(dim_s, (0, 0))

        card_w = 780
        card_h = 440
        card_x = (DISPLAY_WIDTH - card_w) // 2
        card_y = 70

        pygame.draw.rect(surface, (18, 24, 36), (card_x, card_y, card_w, card_h), border_radius=8)
        pygame.draw.rect(surface, CYAN, (card_x, card_y, card_w, card_h), 3, border_radius=8)

        hdr_txt = self.font_banner.render("CAT EXAM PORTAL INTERMISSION", True, GOLD)
        surface.blit(hdr_txt, (card_x + (card_w - hdr_txt.get_width()) // 2, card_y + 18))

        sub_txt = self.font_hud.render(f"Difficulty: {self.quiz_difficulty.upper()} | Keys [1, 2, 3, 4] for Combat Buffs!", True, (180, 210, 240))
        surface.blit(sub_txt, (card_x + (card_w - sub_txt.get_width()) // 2, card_y + 68))

        pygame.draw.line(surface, (50, 80, 120), (card_x + 30, card_y + 92), (card_x + card_w - 30, card_y + 92), 2)

        draw_wrapped_text(surface, self.quiz_data["question"], self.font_quiz, WHITE, card_x + 40, card_y + 110, card_w - 80)

        opt_y = card_y + 180
        for i, opt in enumerate(self.quiz_data["options"]):
            btn_rect = pygame.Rect(card_x + 40, opt_y, card_w - 80, 42)
            bg_col = (28, 36, 52)
            border_col = (70, 95, 140)

            if self.quiz_answered:
                if i == self.quiz_data["correct"]:
                    bg_col = (25, 90, 45)
                    border_col = GREEN
                elif i == self.quiz_selected:
                    bg_col = (110, 30, 30)
                    border_col = RED

            pygame.draw.rect(surface, bg_col, btn_rect, border_radius=6)
            pygame.draw.rect(surface, border_col, btn_rect, 2, border_radius=6)

            opt_lbl = self.font_hud.render(f"[{i + 1}]  {opt}", True, WHITE)
            surface.blit(opt_lbl, (btn_rect.x + 18, btn_rect.y + 12))
            opt_y += 52

        if self.quiz_answered:
            exp_col = GREEN if self.quiz_selected == self.quiz_data["correct"] else RED
            res_txt = "CORRECT! Buff Activated!" if self.quiz_selected == self.quiz_data["correct"] else "INCORRECT!"
            lbl_res = self.font_hud.render(f"{res_txt} — {self.quiz_data['explanation']}", True, exp_col)
            surface.blit(lbl_res, (card_x + 40, card_y + 395))

    def _draw_victory_banner(self, surface: pygame.Surface) -> None:
        dim = pygame.Surface((DISPLAY_WIDTH, DISPLAY_HEIGHT), pygame.SRCALPHA)
        dim.fill((5, 15, 25, 190))
        surface.blit(dim, (0, 0))

        v_txt = self.font_banner.render("VICTORY! PROFESSOR TERMINUS DEFEATED!", True, GOLD)
        surface.blit(v_txt, ((DISPLAY_WIDTH - v_txt.get_width()) // 2, 220))

        sub = self.font_hud_big.render("First-Person Q-Learning Model Successfully Validated!", True, WHITE)
        surface.blit(sub, ((DISPLAY_WIDTH - sub.get_width()) // 2, 280))

    def _draw_defeat_banner(self, surface: pygame.Surface) -> None:
        dim = pygame.Surface((DISPLAY_WIDTH, DISPLAY_HEIGHT), pygame.SRCALPHA)
        dim.fill((25, 5, 5, 200))
        surface.blit(dim, (0, 0))

        d_txt = self.font_banner.render("YOU FELL IN COMBAT!", True, RED)
        surface.blit(d_txt, ((DISPLAY_WIDTH - d_txt.get_width()) // 2, 220))

        sub = self.font_hud_big.render("Professor Terminus's Tabular Policy Overwhelmed the Defense.", True, WHITE)
        surface.blit(sub, ((DISPLAY_WIDTH - sub.get_width()) // 2, 280))
