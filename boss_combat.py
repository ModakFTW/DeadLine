# boss_combat.py — Level 6 / Boss Fight Arena with Tabular Q-Learning Boss AI
import time
import math
import random
import pygame
from typing import Optional, Tuple, Dict, List

from settings import (
    DISPLAY_WIDTH, DISPLAY_HEIGHT, FPS,
    WHITE, BLACK, RED, GREEN, BLUE, YELLOW, CYAN, GOLD, PURPLE, ORANGE, DARK_GRAY
)
from levels.base_level import BaseLevel
from game_state import GameState
from ai.boss_agent import BossAgent, ACTIONS, discretize_distance
from text_utils import draw_wrapped_text
import sprite_loader


# ═══════════════════════════════════════════════════════════════════
# CAT (Computerized Adaptive Testing) Question Bank for Boss Intermissions
# ═══════════════════════════════════════════════════════════════════
CAT_QUESTIONS = {
    "easy": [
        {
            "question": "Which layer of the OSI model does an IP router primarily operate on?",
            "options": ["Layer 1 (Physical)", "Layer 2 (Data Link)", "Layer 3 (Network)", "Layer 4 (Transport)"],
            "correct": 2,
            "explanation": "Routers make forwarding decisions based on Layer 3 IP logical addresses."
        },
        {
            "question": "What is the decimal equivalent of the binary byte 00001010?",
            "options": ["8", "10", "12", "14"],
            "correct": 1,
            "explanation": "8 + 2 = 10."
        },
        {
            "question": "Which SQL statement is used to extract data from a relational database?",
            "options": ["EXTRACT", "GET", "SELECT", "OPEN"],
            "correct": 2,
            "explanation": "SELECT is the declarative standard for retrieving rows."
        }
    ],
    "medium": [
        {
            "question": "In Q-Learning, what parameter controls the balance between exploration and exploitation?",
            "options": ["Alpha (Learning Rate)", "Gamma (Discount Factor)", "Epsilon (Greedy Rate)", "Lambda (Decay)"],
            "correct": 2,
            "explanation": "Epsilon (ε) determines the probability of picking a random exploratory action."
        },
        {
            "question": "Which condition is NOT one of Coffman's four conditions required for deadlock?",
            "options": ["Mutual Exclusion", "Hold and Wait", "Preemption Allowed", "Circular Wait"],
            "correct": 2,
            "explanation": "Deadlock requires NO preemption; allowing preemption prevents deadlock."
        },
        {
            "question": "What is the time complexity of searching a balanced Binary Search Tree (AVL / Red-Black)?",
            "options": ["O(1)", "O(log n)", "O(n)", "O(n log n)"],
            "correct": 1,
            "explanation": "Tree height is bounded by O(log n)."
        }
    ],
    "hard": [
        {
            "question": "In the Bellman equation Q(s,a) update, what does the term [r + γ * max Q(s',a') - Q(s,a)] represent?",
            "options": ["Reward Discount", "Temporal Difference (TD) Error", "State Transition Loss", "Markov Entropy"],
            "correct": 1,
            "explanation": "This difference is the TD Error, measuring surprise between expected and observed return."
        },
        {
            "question": "Which isolation level in SQL ANSI standard prevents dirty reads, non-repeatable reads, AND phantom reads?",
            "options": ["Read Committed", "Repeatable Read", "Serializable", "Snapshot Isolation"],
            "correct": 2,
            "explanation": "Serializable provides full strict serializability, eliminating phantom rows."
        },
        {
            "question": "Why does TCP Reno experience throughput collapse during bursts of multi-packet drops in a single window?",
            "options": ["Checksum corruption", "Go-Back-N retransmits everything", "Tahoe timeout reset to ssthresh=1", "Fast Recovery exits on first partial ACK"],
            "correct": 3,
            "explanation": "TCP NewReno solves this by remaining in Fast Recovery until all lost packets are retransmitted."
        }
    ]
}


class BossArenaLevel(BaseLevel):
    """
    Boss Combat Arena featuring:
    1. Player melee combat (WASD + J/Z Attack, K/X/LSHIFT Dodge roll with i-frames).
    2. Boss entity driven in real-time by pure tabular Q-learning (BossAgent).
    3. Live Bellman equation updates on every action transition.
    4. Real-time Q-table matrix HUD overlay (9 states x 4 actions) with color heatmaps.
    5. 3 Combat HP Phases (Phase 1: 100-70%, Phase 2: 70-30%, Phase 3: 30-0%).
    6. Adaptive Computerized Adaptive Testing (CAT) quiz pauses between phases granting buffs.
    """

    def __init__(self, game_state: GameState):
        self.game_state = game_state

        # Preload Arena background (Dungeon Chamber / Grand Exam Hall)
        self.bg = sprite_loader.load_background("bg_level3.jpg", DISPLAY_WIDTH, DISPLAY_HEIGHT)
        if not self.bg:
            self.bg = sprite_loader.load_background("bg_level5.jpg", DISPLAY_WIDTH, DISPLAY_HEIGHT)

        # Ground level
        self.ground_y = float(DISPLAY_HEIGHT - 110)

        # ─── Player Combat State ───
        self.player_x = 220.0
        self.player_y = float(self.ground_y)
        self.player_vel_x = 0.0
        self.player_vel_y = 0.0
        self.player_on_ground = True
        self.player_facing_right = True

        self.player_hp = 100
        self.player_max_hp = 100
        self.player_attack_power = 22

        # Player actions & cooldowns
        self.player_last_action = "idle"   # "attack" | "dodge" | "idle"
        self.player_action_timer = 0       # frames remaining for current action tag

        self.player_is_attacking = False
        self.player_attack_timer = 0
        self.player_attack_cooldown = 0    # frames until next attack allowed
        self.player_attack_box: Optional[pygame.Rect] = None

        self.player_is_dodging = False
        self.player_dodge_timer = 0
        self.player_dodge_cooldown = 0     # frames until next dodge allowed
        self.player_invincible_timer = 0

        # Buffs earned from CAT quiz
        self.player_buff_name = "None"
        self.player_buff_timer = 0

        # ─── Q-Learning Boss State ───
        self.boss_x = float(DISPLAY_WIDTH - 280)
        self.boss_y = float(self.ground_y)
        self.boss_vel_x = 0.0
        self.boss_vel_y = 0.0
        self.boss_on_ground = True
        self.boss_facing_right = False

        self.boss_hp = 300
        self.boss_max_hp = 300
        self.boss_attack_power = 14

        self.boss_agent = BossAgent(alpha=0.25, gamma=0.85, epsilon=0.85, epsilon_decay=0.994, epsilon_min=0.08)

        # Current action execution state
        self.boss_current_action = "wait"
        self.boss_action_timer = 0
        self.boss_action_duration = 24     # frames to commit to an action
        self.boss_attack_hitbox: Optional[pygame.Rect] = None
        self.boss_is_attacking = False
        self.boss_is_dodging = False
        self.boss_flash_hit_timer = 0

        # State transition tracking for Q-Learning step: (s, a, r, s')
        self.boss_prev_state: Optional[Tuple[str, str]] = None
        self.boss_prev_action: Optional[str] = None
        self.boss_accumulated_reward: float = 0.0

        # ─── Phase & CAT Quiz Controller ───
        # Phase 1: 100% -> 70% (HP 300 -> 210)
        # Phase 2: 70% -> 30%  (HP 210 -> 90)
        # Phase 3: 30% -> 0%   (HP 90 -> 0)
        self.current_phase = 1
        self.phase_threshold_70_triggered = False
        self.phase_threshold_30_triggered = False

        self.in_quiz = False
        self.quiz_difficulty = "medium"
        self.quiz_question_index = 0
        self.quiz_total_questions = 2
        self.quiz_correct_count = 0
        self.current_quiz_item: Optional[Dict] = None
        self.quiz_feedback = ""
        self.quiz_feedback_timer = 0
        self.quiz_selected_option: Optional[int] = None

        # Victory / Defeat timers
        self.game_over_timer = 0
        self.win_timer = 0

        # UI Fonts
        self.font_title = pygame.font.SysFont("segoeui, arial, sans-serif", 32, bold=True)
        self.font_hud = pygame.font.SysFont("segoeui, arial, sans-serif", 20, bold=True)
        self.font_qtable = pygame.font.SysFont("consolas, monospace", 13)
        self.font_qheader = pygame.font.SysFont("consolas, monospace", 14, bold=True)
        self.font_quiz_q = pygame.font.SysFont("segoeui, arial, sans-serif", 24, bold=True)
        self.font_quiz_opt = pygame.font.SysFont("segoeui, arial, sans-serif", 20)

        # Particles & Effects
        self.particles: List[Dict] = []
        self.combat_logs: List[str] = ["Combat arena initialized. Q-Learning Boss active!"]

        # Input keys map
        self.keys = {}

        # Log initial Q-table snapshot to terminal
        print("\n" + "=" * 60)
        print("  [BOSS COMBAT ARENA STARTED]")
        print(f"  Player HP: {self.player_hp} | Boss HP: {self.boss_hp} (Phase 1)")
        print("=" * 60)
        self.boss_agent.print_q_table()

    # ═══════════════════════════════════════════════════════════════════
    # Input Handling
    # ═══════════════════════════════════════════════════════════════════

    def handle_events(self, events: list[pygame.event.Event]) -> Optional[str]:
        for event in events:
            if event.type == pygame.KEYDOWN:
                if self.in_quiz:
                    self._handle_quiz_input(event.key)
                else:
                    self._handle_combat_keydown(event.key)

        return None

    def _handle_combat_keydown(self, key: int) -> None:
        # Player Melee Attack: J or Z
        if key in (pygame.K_j, pygame.K_z):
            if not self.player_is_attacking and self.player_attack_cooldown <= 0:
                self.player_is_attacking = True
                self.player_attack_timer = 14     # 14 frames strike animation
                self.player_attack_cooldown = 24  # 0.4s cooldown
                self.player_last_action = "attack"
                self.player_action_timer = 30

                # Slash particles
                self._spawn_slash_particles(self.player_x, self.player_y - 35, self.player_facing_right)

        # Player Dodge Roll: K, X, or Left Shift
        elif key in (pygame.K_k, pygame.K_x, pygame.K_LSHIFT):
            if not self.player_is_dodging and self.player_dodge_cooldown <= 0:
                self.player_is_dodging = True
                self.player_dodge_timer = 16       # 16 frames roll
                self.player_dodge_cooldown = 32    # 0.53s cooldown
                self.player_invincible_timer = 18  # i-frames for entire roll
                self.player_last_action = "dodge"
                self.player_action_timer = 30

                # Roll burst velocity
                roll_dir = 1.0 if self.player_facing_right else -1.0
                self.player_vel_x = roll_dir * 11.0

                # Dust particles
                self._spawn_dust_particles(self.player_x, self.player_y)

        # Jump: W, UP, or SPACE
        elif key in (pygame.K_w, pygame.K_UP, pygame.K_SPACE):
            if self.player_on_ground and not self.player_is_dodging:
                self.player_vel_y = -14.0
                self.player_on_ground = False

    def _handle_quiz_input(self, key: int) -> None:
        if self.current_quiz_item is None:
            return

        # Choose 1, 2, 3, or 4
        choice = None
        if key in (pygame.K_1, pygame.K_KP1): choice = 0
        elif key in (pygame.K_2, pygame.K_KP2): choice = 1
        elif key in (pygame.K_3, pygame.K_KP3): choice = 2
        elif key in (pygame.K_4, pygame.K_KP4): choice = 3

        if choice is not None and choice < len(self.current_quiz_item["options"]):
            self._submit_quiz_answer(choice)

    # ═══════════════════════════════════════════════════════════════════
    # Update Loop
    # ═══════════════════════════════════════════════════════════════════

    def update(self) -> Optional[str]:
        # Handle Quiz Intermission
        if self.in_quiz:
            return self._update_quiz()

        # Handle Game Over / Win Transitions
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

        # Read keys for continuous movement
        keys_pressed = pygame.key.get_pressed()

        # ── 1. Update Player ──
        self._update_player(keys_pressed)

        # ── 2. Update Boss AI (Q-Learning) ──
        self._update_boss_ai()

        # ── 3. Combat Hit Detection ──
        self._check_combat_hits()

        # ── 4. Update Buffs & Cooldowns ──
        self._update_buffs_and_timers()

        # ── 5. Check HP Phase Transitions ──
        self._check_phase_thresholds()

        # ── 6. Update Visual Particles ──
        self._update_particles()

        return None

    def _update_player(self, keys) -> None:
        # Action tag decays back to idle
        if self.player_action_timer > 0:
            self.player_action_timer -= 1
            if self.player_action_timer <= 0:
                self.player_last_action = "idle"

        # Cooldowns
        if self.player_attack_cooldown > 0:
            self.player_attack_cooldown -= 1
        if self.player_dodge_cooldown > 0:
            self.player_dodge_cooldown -= 1
        if self.player_invincible_timer > 0:
            self.player_invincible_timer -= 1

        # Dodge state
        if self.player_is_dodging:
            self.player_dodge_timer -= 1
            self.player_vel_x *= 0.88  # friction
            if self.player_dodge_timer <= 0:
                self.player_is_dodging = False
                self.player_vel_x = 0.0
        else:
            # Normal movement input
            move_x = 0.0
            if keys[pygame.K_a] or keys[pygame.K_LEFT]:
                move_x -= 1.0
                self.player_facing_right = False
            if keys[pygame.K_d] or keys[pygame.K_RIGHT]:
                move_x += 1.0
                self.player_facing_right = True

            speed = 6.0
            if self.player_buff_name == "Speed Boost":
                speed = 8.5
            self.player_vel_x = move_x * speed

        # Attack animation
        if self.player_is_attacking:
            self.player_attack_timer -= 1
            # Compute attack hitbox on active frames
            if 4 <= self.player_attack_timer <= 12:
                box_w = 64
                box_h = 50
                box_x = (self.player_x + 12) if self.player_facing_right else (self.player_x - 12 - box_w)
                box_y = self.player_y - 60
                self.player_attack_box = pygame.Rect(int(box_x), int(box_y), box_w, box_h)
            else:
                self.player_attack_box = None

            if self.player_attack_timer <= 0:
                self.player_is_attacking = False
                self.player_attack_box = None
        else:
            self.player_attack_box = None

        # Apply Player Physics
        self.player_vel_y += 0.8  # gravity
        self.player_x += self.player_vel_x
        self.player_y += self.player_vel_y

        # Ground collision
        if self.player_y >= self.ground_y:
            self.player_y = self.ground_y
            self.player_vel_y = 0.0
            self.player_on_ground = True

        # Clamp screen bounds
        self.player_x = max(50.0, min(float(DISPLAY_WIDTH - 50), self.player_x))

    def _update_boss_ai(self) -> None:
        """
        Runs the Q-Learning decision cycle for the boss entity:
        1. Formulate current state: (distance_discretized, player_last_action).
        2. If previous action completed, record transition (s, a, r, s') and call learn().
        3. Choose new action via epsilon-greedy policy.
        4. Execute action movement & animations.
        """
        # Calculate current spatial state
        dist_px = abs(self.boss_x - self.player_x)
        current_state = self.boss_agent.get_state(dist_px, self.player_last_action)

        # Face the player unless dodging away
        if not self.boss_is_dodging:
            self.boss_facing_right = (self.boss_x < self.player_x)

        # Flash timer when damaged
        if self.boss_flash_hit_timer > 0:
            self.boss_flash_hit_timer -= 1

        # Check if previous action duration expired -> Trigger Q-Learning update
        self.boss_action_timer -= 1
        if self.boss_action_timer <= 0:
            # If we had a prior state & action, finalize the Bellman update!
            if self.boss_prev_state is not None and self.boss_prev_action is not None:
                # Small penalty for wasted/idle actions if no damage occurred
                if self.boss_accumulated_reward == 0.0:
                    if self.boss_prev_action == "wait" and dist_px > 120:
                        reward = 0.05   # waiting at range is sensible
                    else:
                        reward = -0.10  # idle penalty
                else:
                    reward = self.boss_accumulated_reward

                # Execute Q-Learning Bellman equation
                td_error = self.boss_agent.learn(
                    self.boss_prev_state,
                    self.boss_prev_action,
                    reward,
                    current_state
                )

                # Reset reward accumulator
                self.boss_accumulated_reward = 0.0

            # Select NEW action using Epsilon-Greedy policy
            chosen_action = self.boss_agent.choose_action(current_state)

            self.boss_prev_state = current_state
            self.boss_prev_action = chosen_action
            self.boss_current_action = chosen_action

            # Set action duration based on action type
            if chosen_action == "attack":
                self.boss_action_duration = 26
                self.boss_is_attacking = True
            elif chosen_action == "dodge":
                self.boss_action_duration = 18
                self.boss_is_dodging = True
            elif chosen_action == "retreat":
                self.boss_action_duration = 24
            else:  # wait
                self.boss_action_duration = 20

            self.boss_action_timer = self.boss_action_duration

            # Periodic console snapshot every 15 updates
            if self.boss_agent.total_steps % 15 == 0:
                print(f"[Q-LEARN SNAPSHOT] Step: {self.boss_agent.total_steps} | Epsilon: {self.boss_agent.epsilon:.3f}")
                self.boss_agent.print_q_table()

        # ── Execute Boss Physical Movement based on current action ──
        dir_to_player = 1.0 if (self.player_x > self.boss_x) else -1.0

        if self.boss_current_action == "attack":
            # Lunge forward toward player
            lunge_speed = 7.5 if self.current_phase == 3 else 5.8
            self.boss_vel_x = dir_to_player * lunge_speed
            # Generate attack hitbox during mid-frames
            if 8 <= self.boss_action_timer <= 20:
                box_w = 70
                box_h = 60
                box_x = (self.boss_x + 15) if (dir_to_player > 0) else (self.boss_x - 15 - box_w)
                box_y = self.boss_y - 75
                self.boss_attack_hitbox = pygame.Rect(int(box_x), int(box_y), box_w, box_h)
            else:
                self.boss_attack_hitbox = None

        elif self.boss_current_action == "dodge":
            # Quick evasive slide away from player
            dodge_speed = 9.0
            self.boss_vel_x = -dir_to_player * dodge_speed
            self.boss_attack_hitbox = None

        elif self.boss_current_action == "retreat":
            # Methodical step backwards
            self.boss_vel_x = -dir_to_player * 3.8
            self.boss_attack_hitbox = None

        else:  # "wait"
            # Steady defensive posture
            self.boss_vel_x = 0.0
            self.boss_attack_hitbox = None

        # Apply Boss Physics
        self.boss_vel_y += 0.8
        self.boss_x += self.boss_vel_x
        self.boss_y += self.boss_vel_y

        if self.boss_y >= self.ground_y:
            self.boss_y = self.ground_y
            self.boss_vel_y = 0.0
            self.boss_on_ground = True

        # Clamp within arena walls
        self.boss_x = max(100.0, min(float(DISPLAY_WIDTH - 100), self.boss_x))

    def _check_combat_hits(self) -> None:
        """Process hit collisions between player and boss."""
        # 1. Check Player hitting Boss
        if self.player_attack_box is not None and self.boss_flash_hit_timer <= 0:
            boss_body_rect = pygame.Rect(int(self.boss_x - 30), int(self.boss_y - 80), 60, 80)
            if self.player_attack_box.colliderect(boss_body_rect):
                # Calculate damage
                damage = self.player_attack_power
                if self.player_buff_name == "Damage Boost (+50%)":
                    damage = int(damage * 1.5)

                self.boss_hp = max(0, self.boss_hp - damage)
                self.boss_flash_hit_timer = 18
                self._spawn_hit_spark(self.boss_x, self.boss_y - 45, RED)

                # Boss punishment reward for Q-Learning
                self.boss_accumulated_reward -= 1.0

                self.combat_logs.append(f"Player struck Boss for {damage} dmg! Q-Reward: -1.0")
                if len(self.combat_logs) > 6:
                    self.combat_logs.pop(0)

                # Boss stagger
                knockback = 5.0 if self.player_facing_right else -5.0
                self.boss_x += knockback

                # Check Boss Defeat
                if self.boss_hp <= 0:
                    self.combat_logs.append("★ BOSS DEFEATED! ADVANCING TO FINAL EXAM GATE! ★")
                    self.win_timer = 120  # 2 seconds victory celebration
                    return

        # 2. Check Boss hitting Player
        if self.boss_attack_hitbox is not None and self.player_invincible_timer <= 0:
            player_body_rect = pygame.Rect(int(self.player_x - 20), int(self.player_y - 65), 40, 65)
            if self.boss_attack_hitbox.colliderect(player_body_rect):
                # Player struck!
                damage = self.boss_attack_power
                if self.player_buff_name == "Iron Armor (-50% dmg)":
                    damage = max(1, damage // 2)

                self.player_hp = max(0, self.player_hp - damage)
                self.player_invincible_timer = 36  # i-frames after taking hit
                self._spawn_hit_spark(self.player_x, self.player_y - 35, YELLOW)

                # Boss positive reward for successful strike!
                self.boss_accumulated_reward += 1.0

                self.combat_logs.append(f"Boss struck Player for {damage} dmg! Q-Reward: +1.0")
                if len(self.combat_logs) > 6:
                    self.combat_logs.pop(0)

                # Player knockback
                knockback = 6.0 if self.boss_facing_right else -6.0
                self.player_x += knockback

                # Check Player Defeat
                if self.player_hp <= 0:
                    self.game_state.failed_level = "boss_arena"
                    self.game_state.failure_reason = "Boss Combat Defeat: Outmaneuvered by the Q-Learning Boss AI."
                    self.game_over_timer = 90
                    return

    def _update_buffs_and_timers(self) -> None:
        if self.player_buff_timer > 0:
            self.player_buff_timer -= 1
            if self.player_buff_timer <= 0:
                self.player_buff_name = "None"

    def _check_phase_thresholds(self) -> None:
        """Trigger adaptive CAT quiz pauses at 70% and 30% Boss HP."""
        # 70% HP threshold = 210 HP
        if self.boss_hp <= 210 and not self.phase_threshold_70_triggered and self.boss_hp > 0:
            self.phase_threshold_70_triggered = True
            self.current_phase = 2
            self._start_cat_quiz(phase=2)

        # 30% HP threshold = 90 HP
        elif self.boss_hp <= 90 and not self.phase_threshold_30_triggered and self.boss_hp > 0:
            self.phase_threshold_30_triggered = True
            self.current_phase = 3
            self._start_cat_quiz(phase=3)

    # ═══════════════════════════════════════════════════════════════════
    # Adaptive CAT Quiz System (Intermission)
    # ═══════════════════════════════════════════════════════════════════

    def _start_cat_quiz(self, phase: int) -> None:
        """Pauses combat and launches Computerized Adaptive Testing quiz."""
        self.in_quiz = True
        self.quiz_difficulty = "medium"  # CAT always starts at medium
        self.quiz_question_index = 0
        self.quiz_total_questions = 2
        self.quiz_correct_count = 0
        self.quiz_selected_option = None
        self.quiz_feedback = ""
        self.quiz_feedback_timer = 0
        self._load_next_quiz_question()

        print(f"\n[PHASE {phase} INTERMISSION] Boss HP threshold reached. Launching Adaptive CAT Quiz...")

    def _load_next_quiz_question(self) -> None:
        pool = CAT_QUESTIONS.get(self.quiz_difficulty, CAT_QUESTIONS["medium"])
        self.current_quiz_item = random.choice(pool)
        self.quiz_selected_option = None
        self.quiz_feedback = ""

    def _submit_quiz_answer(self, choice_idx: int) -> None:
        if self.quiz_feedback_timer > 0 or self.current_quiz_item is None:
            return

        self.quiz_selected_option = choice_idx
        is_correct = (choice_idx == self.current_quiz_item["correct"])

        if is_correct:
            self.quiz_correct_count += 1
            self.quiz_feedback = "CORRECT! Adapting difficulty higher..."
            # CAT adaptation: Correct -> step up difficulty
            if self.quiz_difficulty == "easy":
                self.quiz_difficulty = "medium"
            elif self.quiz_difficulty == "medium":
                self.quiz_difficulty = "hard"
        else:
            self.quiz_feedback = "INCORRECT. Adapting difficulty lower..."
            # CAT adaptation: Wrong -> step down difficulty
            if self.quiz_difficulty == "hard":
                self.quiz_difficulty = "medium"
            elif self.quiz_difficulty == "medium":
                self.quiz_difficulty = "easy"

        self.quiz_feedback_timer = 45  # frames to show result before proceeding

    def _update_quiz(self) -> Optional[str]:
        if self.quiz_feedback_timer > 0:
            self.quiz_feedback_timer -= 1
            if self.quiz_feedback_timer <= 0:
                self.quiz_question_index += 1
                if self.quiz_question_index >= self.quiz_total_questions:
                    # Quiz complete! Apply phase buff
                    self._apply_phase_buff()
                    self.in_quiz = False
                    self.current_quiz_item = None
                else:
                    self._load_next_quiz_question()

        return None

    def _apply_phase_buff(self) -> None:
        """Grant temporary player combat buff based on CAT quiz performance."""
        # 60 FPS * 12 seconds = 720 frames
        buff_duration = 720

        if self.quiz_correct_count == 2:
            # 2/2 Perfect Score -> Massive Damage Boost
            self.player_buff_name = "Damage Boost (+50%)"
            self.player_buff_timer = buff_duration
            msg = "★ PERFECT SCORE! Gained 'Damage Boost (+50%)' for 12 seconds!"
        elif self.quiz_correct_count == 1:
            # 1/2 Pass -> Speed / Dodge Boost
            self.player_buff_name = "Speed Boost"
            self.player_buff_timer = buff_duration
            msg = "★ GOOD SCORE! Gained 'Speed Boost' for 12 seconds!"
        else:
            # 0/2 Fail -> Defensive Iron Armor
            self.player_buff_name = "Iron Armor (-50% dmg)"
            self.player_buff_timer = buff_duration
            msg = "★ QUIZ FAILED! Gained defensive 'Iron Armor' to survive!"

        self.combat_logs.append(msg)
        print(f"[CAT QUIZ COMPLETE] Score: {self.quiz_correct_count}/{self.quiz_total_questions} | Buff applied: {self.player_buff_name}")

    # ═══════════════════════════════════════════════════════════════════
    # Particles & Visual Effects
    # ═══════════════════════════════════════════════════════════════════

    def _spawn_slash_particles(self, x: float, y: float, facing_right: bool) -> None:
        for _ in range(12):
            vx = random.uniform(3.0, 7.0) * (1.0 if facing_right else -1.0)
            vy = random.uniform(-3.0, 3.0)
            self.particles.append({
                "x": x, "y": y, "vx": vx, "vy": vy,
                "life": 14, "max_life": 14, "color": CYAN, "size": random.randint(3, 6)
            })

    def _spawn_dust_particles(self, x: float, y: float) -> None:
        for _ in range(8):
            vx = random.uniform(-2.5, 2.5)
            vy = random.uniform(-1.0, -3.5)
            self.particles.append({
                "x": x, "y": y, "vx": vx, "vy": vy,
                "life": 16, "max_life": 16, "color": (190, 190, 190), "size": random.randint(3, 5)
            })

    def _spawn_hit_spark(self, x: float, y: float, color: tuple) -> None:
        for _ in range(16):
            angle = random.uniform(0, 2 * math.pi)
            spd = random.uniform(2.5, 8.0)
            self.particles.append({
                "x": x, "y": y, "vx": math.cos(angle) * spd, "vy": math.sin(angle) * spd,
                "life": 18, "max_life": 18, "color": color, "size": random.randint(3, 6)
            })

    def _update_particles(self) -> None:
        alive = []
        for p in self.particles:
            p["x"] += p["vx"]
            p["y"] += p["vy"]
            p["life"] -= 1
            if p["life"] > 0:
                alive.append(p)
        self.particles = alive

    # ═══════════════════════════════════════════════════════════════════
    # Rendering
    # ═══════════════════════════════════════════════════════════════════

    def draw(self, surface: pygame.Surface) -> None:
        # 1. Background
        if self.bg:
            surface.blit(self.bg, (0, 0))
        else:
            surface.fill((20, 22, 30))

        # Ground platform line & shadow
        pygame.draw.rect(surface, (25, 28, 38), (0, int(self.ground_y), DISPLAY_WIDTH, DISPLAY_HEIGHT - int(self.ground_y)))
        pygame.draw.line(surface, (70, 85, 120), (0, int(self.ground_y)), (DISPLAY_WIDTH, int(self.ground_y)), 3)

        # 2. Draw Particles
        for p in self.particles:
            alpha_ratio = p["life"] / p["max_life"]
            r = int(p["size"] * alpha_ratio)
            if r > 0:
                pygame.draw.circle(surface, p["color"], (int(p["x"]), int(p["y"])), r)

        # 3. Draw Player Entity
        self._draw_player(surface)

        # 4. Draw Boss Entity
        self._draw_boss(surface)

        # 5. Draw Top HUD (Health Bars, Phase, Buffs)
        self._draw_combat_hud(surface)

        # 6. Draw Live Q-Table Heatmap Matrix Overlay (Academic Proof)
        self._draw_q_table_hud(surface)

        # 7. Draw Combat Log Ticker
        self._draw_combat_logs(surface)

        # 8. Render Quiz Modal if paused
        if self.in_quiz:
            self._draw_quiz_modal(surface)

        # 9. Victory / Game Over Overlay
        if self.win_timer > 0:
            self._draw_victory_banner(surface)
        elif self.game_over_timer > 0:
            self._draw_defeat_banner(surface)

    def _draw_player(self, surface: pygame.Surface) -> None:
        px = int(self.player_x)
        py = int(self.player_y)

        # Shadow
        pygame.draw.ellipse(surface, (10, 10, 15, 120), (px - 25, py - 6, 50, 14))

        # Invincibility flicker
        if self.player_invincible_timer > 0 and (self.player_invincible_timer // 3) % 2 == 1:
            return

        # Player body (Blue Knight / Student)
        body_color = CYAN if self.player_is_dodging else BLUE
        body_rect = pygame.Rect(px - 18, py - 65, 36, 65)
        pygame.draw.rect(surface, body_color, body_rect, border_radius=6)
        pygame.draw.rect(surface, WHITE, body_rect, 2, border_radius=6)

        # Head / Scarf
        head_rect = pygame.Rect(px - 12, py - 85, 24, 22)
        pygame.draw.rect(surface, (230, 200, 160), head_rect, border_radius=4)
        # Eye facing direction
        eye_x = (px + 4) if self.player_facing_right else (px - 8)
        pygame.draw.rect(surface, BLACK, (eye_x, py - 78, 4, 4))

        # Melee Weapon / Slash Arc
        if self.player_is_attacking and self.player_attack_box is not None:
            # Draw glowing slash hitbox
            slash_s = pygame.Surface((self.player_attack_box.width, self.player_attack_box.height), pygame.SRCALPHA)
            slash_s.fill((60, 220, 255, 110))
            surface.blit(slash_s, (self.player_attack_box.x, self.player_attack_box.y))
            pygame.draw.rect(surface, WHITE, self.player_attack_box, 2, border_radius=4)

        # Player name tag & active state
        tag = f"PLAYER [{self.player_last_action.upper()}]"
        lbl = self.font_hud.render(tag, True, WHITE)
        surface.blit(lbl, (px - lbl.get_width() // 2, py - 110))

    def _draw_boss(self, surface: pygame.Surface) -> None:
        bx = int(self.boss_x)
        by = int(self.boss_y)

        # Shadow
        pygame.draw.ellipse(surface, (10, 10, 15, 160), (bx - 35, by - 8, 70, 16))

        # Boss color shifts by Phase: Phase 1 (Purple) -> Phase 2 (Orange) -> Phase 3 (Crimson Red)
        if self.boss_flash_hit_timer > 0 and (self.boss_flash_hit_timer // 2) % 2 == 1:
            boss_color = WHITE
        elif self.current_phase == 3:
            boss_color = (240, 40, 40)
        elif self.current_phase == 2:
            boss_color = (255, 130, 30)
        else:
            boss_color = (160, 60, 210)

        # Boss main chassis
        body_rect = pygame.Rect(bx - 30, by - 85, 60, 85)
        pygame.draw.rect(surface, boss_color, body_rect, border_radius=8)
        pygame.draw.rect(surface, GOLD if self.current_phase == 3 else WHITE, body_rect, 3, border_radius=8)

        # Boss Horns / Crown
        pygame.draw.polygon(surface, GOLD, [
            (bx - 26, by - 85), (bx - 36, by - 105), (bx - 16, by - 85)
        ])
        pygame.draw.polygon(surface, GOLD, [
            (bx + 26, by - 85), (bx + 36, by - 105), (bx + 16, by - 85)
        ])

        # Boss Eyes (glow red)
        eye_x = (bx + 10) if self.boss_facing_right else (bx - 18)
        pygame.draw.rect(surface, RED, (eye_x, by - 70, 8, 6))

        # Boss attack hitbox visual
        if self.boss_attack_hitbox is not None:
            atk_s = pygame.Surface((self.boss_attack_hitbox.width, self.boss_attack_hitbox.height), pygame.SRCALPHA)
            atk_s.fill((255, 50, 50, 120))
            surface.blit(atk_s, (self.boss_attack_hitbox.x, self.boss_attack_hitbox.y))
            pygame.draw.rect(surface, GOLD, self.boss_attack_hitbox, 2, border_radius=4)

        # Boss action indicator above head
        act_color = GREEN if self.boss_current_action == "attack" else (YELLOW if self.boss_current_action == "dodge" else WHITE)
        tag = f"BOSS: {self.boss_current_action.upper()}"
        lbl = self.font_hud.render(tag, True, act_color)
        surface.blit(lbl, (bx - lbl.get_width() // 2, by - 128))

    def _draw_combat_hud(self, surface: pygame.Surface) -> None:
        # Top banner background
        hud_bg = pygame.Surface((DISPLAY_WIDTH, 70), pygame.SRCALPHA)
        hud_bg.fill((15, 18, 26, 210))
        surface.blit(hud_bg, (0, 0))
        pygame.draw.line(surface, (50, 60, 80), (0, 70), (DISPLAY_WIDTH, 70), 2)

        # ── Player HP Bar (Left) ──
        p_pct = max(0.0, self.player_hp / self.player_max_hp)
        p_bar_w = 260
        p_fill_w = int(p_bar_w * p_pct)
        pygame.draw.rect(surface, DARK_GRAY, (40, 20, p_bar_w, 24), border_radius=4)
        p_bar_color = GREEN if p_pct > 0.4 else (YELLOW if p_pct > 0.2 else RED)
        if p_fill_w > 0:
            pygame.draw.rect(surface, p_bar_color, (40, 20, p_fill_w, 24), border_radius=4)
        pygame.draw.rect(surface, WHITE, (40, 20, p_bar_w, 24), 2, border_radius=4)

        p_txt = self.font_hud.render(f"PLAYER HP: {self.player_hp}/{self.player_max_hp}", True, WHITE)
        surface.blit(p_txt, (45, 22))

        # Player Buff indicator
        if self.player_buff_name != "None":
            secs = self.player_buff_timer // 60
            buff_txt = self.font_hud.render(f"BUFF: {self.player_buff_name} ({secs}s)", True, GOLD)
            surface.blit(buff_txt, (40, 48))
        else:
            ctrl_txt = self.font_hud.render("Attack: [J / Z]  |  Dodge Roll: [K / X / SHIFT]", True, (160, 175, 200))
            surface.blit(ctrl_txt, (40, 48))

        # ── Boss HP Bar (Center-Right) ──
        b_pct = max(0.0, self.boss_hp / self.boss_max_hp)
        b_bar_w = 340
        b_fill_w = int(b_bar_w * b_pct)
        bx_start = 380
        pygame.draw.rect(surface, DARK_GRAY, (bx_start, 20, b_bar_w, 24), border_radius=4)

        # Phase segment lines at 70% (238px) and 30% (102px)
        b_color = RED if self.current_phase == 3 else (ORANGE if self.current_phase == 2 else PURPLE)
        if b_fill_w > 0:
            pygame.draw.rect(surface, b_color, (bx_start, 20, b_fill_w, 24), border_radius=4)
        pygame.draw.rect(surface, GOLD if self.current_phase == 3 else WHITE, (bx_start, 20, b_bar_w, 24), 2, border_radius=4)

        # Phase markers
        p70_x = bx_start + int(b_bar_w * 0.70)
        p30_x = bx_start + int(b_bar_w * 0.30)
        pygame.draw.line(surface, WHITE, (p70_x, 18), (p70_x, 46), 2)
        pygame.draw.line(surface, WHITE, (p30_x, 18), (p30_x, 46), 2)

        boss_label = f"PROFESSOR TERMINUS (PHASE {self.current_phase}) - HP: {self.boss_hp}/{self.boss_max_hp}"
        b_txt = self.font_hud.render(boss_label, True, WHITE)
        surface.blit(b_txt, (bx_start + 5, 22))

        # Boss Phase subtitle
        phase_sub = f"Phase {self.current_phase}/3  |  Epsilon (Exploration): {self.boss_agent.epsilon:.3f}"
        phase_txt = self.font_hud.render(phase_sub, True, (210, 215, 230))
        surface.blit(phase_txt, (bx_start, 48))

    def _draw_q_table_hud(self, surface: pygame.Surface) -> None:
        """
        Renders the Tabular Q-Learning Matrix directly on screen in the top right.
        Evaluators can see all 9 states and 4 action values updating live in color!
        """
        hud_w = 460
        hud_h = 230
        hud_x = DISPLAY_WIDTH - hud_w - 15
        hud_y = 80

        # Background card
        card_s = pygame.Surface((hud_w, hud_h), pygame.SRCALPHA)
        card_s.fill((15, 18, 28, 225))
        surface.blit(card_s, (hud_x, hud_y))
        pygame.draw.rect(surface, (60, 110, 190), (hud_x, hud_y, hud_w, hud_h), 2, border_radius=6)

        # Title
        title_txt = self.font_qheader.render(f"LIVE Q-LEARNING MATRIX [Step {self.boss_agent.total_steps}]", True, GOLD)
        surface.blit(title_txt, (hud_x + 10, hud_y + 8))

        # Header columns
        header_line = "STATE (Dist|Plr)  | ATK    DODGE  RETR   WAIT  | BEST"
        hdr_s = self.font_qtable.render(header_line, True, CYAN)
        surface.blit(hdr_s, (hud_x + 10, hud_y + 28))
        pygame.draw.line(surface, (50, 75, 110), (hud_x + 10, hud_y + 44), (hud_x + hud_w - 10, hud_y + 44), 1)

        # Current state for highlight
        dist_px = abs(self.boss_x - self.player_x)
        curr_dist = discretize_distance(dist_px)
        current_state_key = (curr_dist, self.player_last_action)

        row_y = hud_y + 48
        # Order rows systematically
        distances = ["near", "medium", "far"]
        player_actions = ["attack", "dodge", "idle"]

        for d in distances:
            for pa in player_actions:
                st = (d, pa)
                is_active_state = (st == current_state_key)

                # State label
                st_lbl = f"{d[:3].upper():<3}|{pa[:3].upper():<3}"

                # Action values
                q_vals = [self.boss_agent.get_q_value(st, a) for a in ACTIONS]
                best_act = self.boss_agent.get_best_action(st)

                # Format values
                val_strs = [f"{v:+0.2f}" for v in q_vals]

                line_str = f"{st_lbl} | {val_strs[0]:>5} {val_strs[1]:>5} {val_strs[2]:>5} {val_strs[3]:>5} | {best_act[:4].upper()}"

                # Highlight active row
                if is_active_state:
                    bg_highlight = pygame.Surface((hud_w - 20, 16), pygame.SRCALPHA)
                    bg_highlight.fill((60, 130, 240, 80))
                    surface.blit(bg_highlight, (hud_x + 10, row_y - 1))
                    text_color = YELLOW
                else:
                    text_color = (200, 205, 215)

                row_s = self.font_qtable.render(line_str, True, text_color)
                surface.blit(row_s, (hud_x + 10, row_y))
                row_y += 18

    def _draw_combat_logs(self, surface: pygame.Surface) -> None:
        """Draw combat events ticker at the bottom left."""
        box_w = 520
        box_h = 100
        box_x = 20
        box_y = DISPLAY_HEIGHT - box_h - 15

        card_s = pygame.Surface((box_w, box_h), pygame.SRCALPHA)
        card_s.fill((10, 12, 18, 190))
        surface.blit(card_s, (box_x, box_y))
        pygame.draw.rect(surface, (50, 60, 80), (box_x, box_y, box_w, box_h), 1, border_radius=4)

        header = self.font_qheader.render("COMBAT & Q-UPDATE TICKER", True, (130, 160, 200))
        surface.blit(header, (box_x + 10, box_y + 6))

        log_y = box_y + 26
        for log in self.combat_logs[-4:]:
            col = GOLD if "★" in log else ((80, 230, 120) if "+1.0" in log else ((240, 80, 80) if "-1.0" in log else WHITE))
            txt_s = self.font_qtable.render(f"> {log}", True, col)
            surface.blit(txt_s, (box_x + 10, log_y))
            log_y += 17

    def _draw_quiz_modal(self, surface: pygame.Surface) -> None:
        """Render Computerized Adaptive Testing quiz overlay when combat pauses."""
        # Dim background
        dim_s = pygame.Surface((DISPLAY_WIDTH, DISPLAY_HEIGHT), pygame.SRCALPHA)
        dim_s.fill((5, 8, 15, 230))
        surface.blit(dim_s, (0, 0))

        # Center Card
        card_w = 780
        card_h = 420
        card_x = (DISPLAY_WIDTH - card_w) // 2
        card_y = (DISPLAY_HEIGHT - card_h) // 2

        pygame.draw.rect(surface, (20, 25, 38), (card_x, card_y, card_w, card_h), border_radius=10)
        pygame.draw.rect(surface, (80, 140, 240), (card_x, card_y, card_w, card_h), 3, border_radius=10)

        # Header banner
        header_text = f"PHASE INTERMISSION: COMPUTERIZED ADAPTIVE TEST (CAT)"
        hdr = self.font_title.render(header_text, True, GOLD)
        surface.blit(hdr, (card_x + 30, card_y + 24))

        sub_info = f"Question {self.quiz_question_index + 1} of {self.quiz_total_questions}  |  Current CAT Difficulty: {self.quiz_difficulty.upper()}"
        sub_s = self.font_hud.render(sub_info, True, CYAN)
        surface.blit(sub_s, (card_x + 30, card_y + 65))

        if self.current_quiz_item:
            # Question text
            q_text = self.current_quiz_item["question"]
            draw_wrapped_text(surface, q_text, card_x + 30, card_y + 105, card_w - 60, self.font_quiz_q, WHITE)

            # Options
            opt_y = card_y + 175
            for i, opt in enumerate(self.current_quiz_item["options"]):
                # Highlight if selected
                if self.quiz_selected_option is not None:
                    if i == self.current_quiz_item["correct"]:
                        opt_bg_col = (40, 120, 60)
                        border_col = GREEN
                    elif i == self.quiz_selected_option:
                        opt_bg_col = (140, 40, 40)
                        border_col = RED
                    else:
                        opt_bg_col = (30, 35, 48)
                        border_col = (60, 70, 90)
                else:
                    opt_bg_col = (30, 35, 48)
                    border_col = (70, 85, 110)

                opt_rect = pygame.Rect(card_x + 30, opt_y, card_w - 60, 42)
                pygame.draw.rect(surface, opt_bg_col, opt_rect, border_radius=6)
                pygame.draw.rect(surface, border_col, opt_rect, 2, border_radius=6)

                lbl = self.font_quiz_opt.render(f"[{i + 1}]  {opt}", True, WHITE)
                surface.blit(lbl, (card_x + 45, opt_y + 8))
                opt_y += 50

            # Feedback message
            if self.quiz_feedback:
                feed_col = GREEN if "CORRECT" in self.quiz_feedback else RED
                feed_s = self.font_hud.render(self.quiz_feedback, True, feed_col)
                surface.blit(feed_s, (card_x + 30, card_y + card_h - 40))

    def _draw_victory_banner(self, surface: pygame.Surface) -> None:
        dim = pygame.Surface((DISPLAY_WIDTH, DISPLAY_HEIGHT), pygame.SRCALPHA)
        dim.fill((0, 0, 0, 160))
        surface.blit(dim, (0, 0))

        v_s = self.font_title.render("★ PROFESSOR TERMINUS DEFEATED! ★", True, GOLD)
        sub = self.font_hud.render("ADVANCING TO THE FINAL EXAM HALL...", True, WHITE)
        surface.blit(v_s, ((DISPLAY_WIDTH - v_s.get_width()) // 2, 280))
        surface.blit(sub, ((DISPLAY_WIDTH - sub.get_width()) // 2, 330))

    def _draw_defeat_banner(self, surface: pygame.Surface) -> None:
        dim = pygame.Surface((DISPLAY_WIDTH, DISPLAY_HEIGHT), pygame.SRCALPHA)
        dim.fill((0, 0, 0, 180))
        surface.blit(dim, (0, 0))

        d_s = self.font_title.render("DEFEAT — BOSS OUTMANEUVERED YOU", True, RED)
        sub = self.font_hud.render("The Q-Learning Boss adapted to your combat patterns.", True, WHITE)
        surface.blit(d_s, ((DISPLAY_WIDTH - d_s.get_width()) // 2, 280))
        surface.blit(sub, ((DISPLAY_WIDTH - sub.get_width()) // 2, 330))
