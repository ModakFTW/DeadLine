# ai/boss_ai.py — Model 3: Reactive Rule-Based Agent for the Boss Encounter
import random
from collections import deque


class BossAI:
    """
    Model 3: Rule-Based Reactive Agent (PRD Section 5.3).
    
    Observes player behavior during the boss fight:
    1. Tracks player dodge history (left vs right vs jump).
    2. Adjusts attack weights based on player patterns (e.g. if player dodged left 3+ times,
       biases attack toward 'attack_right' to trap them).
    3. Health-adaptive pressure:
       - If player HP is high (3 HP) -> aggressive barrage attacks.
       - If player HP is low (1 HP) -> grants 'breather' window for fairness.
    """

    def __init__(self) -> None:
        # History of recent player dodge directions ('left', 'right', 'jump', 'ground')
        self.player_move_history = deque(maxlen=6)
        
        # Base attack types
        self.attack_types = [
            "question_paper_barrage",   # targeted projectile spread
            "exam_bell_slam",           # ground shockwave forcing a high jump
            "deadline_dash",            # horizontal rush attack across arena
            "breather"                  # vulnerable cooldown state
        ]
        self.last_attack = "breather"

    def record_player_action(self, action: str) -> None:
        """Records a detected player action ('left', 'right', 'jump')."""
        self.player_move_history.append(action)

    def decide_next_attack(self, player_hp: int, boss_hp: int,
                           player_pos_x: float, boss_pos_x: float) -> str:
        """
        Dynamically calculates attack probabilities and samples the next move.
        Returns the chosen attack string.
        """
        # Base attack weights
        weights = {
            "question_paper_barrage": 35.0,
            "exam_bell_slam": 30.0,
            "deadline_dash": 25.0,
            "breather": 10.0
        }

        # ── 1. Counter-Play: Detect Dodge Direction Biases ──
        left_count = sum(1 for a in self.player_move_history if a == "left")
        right_count = sum(1 for a in self.player_move_history if a == "right")
        jump_count = sum(1 for a in self.player_move_history if a == "jump")

        # If player tends to dodge left repeatedly, increase pressure on the left with barrage
        if left_count >= 3:
            weights["question_paper_barrage"] += 25.0
            weights["deadline_dash"] += 15.0

        # If player stays grounded too much, force jumps via exam bell shockwave
        if jump_count == 0:
            weights["exam_bell_slam"] += 25.0
        elif jump_count >= 3:
            # If player is jump-happy, catch them with flying question papers
            weights["question_paper_barrage"] += 20.0

        # ── 2. Player Health Adaptation ──
        if player_hp >= 3:
            # High HP -> Boss becomes relentless
            weights["deadline_dash"] += 15.0
            weights["question_paper_barrage"] += 10.0
            weights["breather"] = max(2.0, weights["breather"] - 8.0)
        elif player_hp == 1:
            # Critical HP -> Give breathing room for dramatic clutch comeback
            weights["breather"] += 25.0
            weights["deadline_dash"] = max(5.0, weights["deadline_dash"] - 15.0)

        # ── 3. Boss Rage Phase (Boss HP <= 3) ──
        if boss_hp <= 3:
            weights["deadline_dash"] += 20.0
            weights["exam_bell_slam"] += 15.0
            weights["breather"] = max(5.0, weights["breather"] - 5.0)

        # Avoid repeating the exact same heavy attack twice in a row
        if self.last_attack in weights and self.last_attack != "breather":
            weights[self.last_attack] *= 0.4

        population = list(weights.keys())
        prob_weights = [weights[k] for k in population]
        
        chosen = random.choices(population, weights=prob_weights, k=1)[0]
        self.last_attack = chosen
        return chosen

    def get_last_weights_display(self, player_hp: int, boss_hp: int) -> dict:
        """Returns normalized percentages of current decision weights for debug inspection."""
        # Simulated run to inspect current probability distribution
        weights = {
            "Paper Barrage": 35.0,
            "Bell Slam": 30.0,
            "Deadline Dash": 25.0,
            "Breather": 10.0
        }
        if player_hp == 1:
            weights["Breather"] += 25.0
            weights["Deadline Dash"] -= 15.0
        if boss_hp <= 3:
            weights["Deadline Dash"] += 20.0
        total = sum(weights.values())
        return {k: f"{(v / total * 100):.1f}%" for k, v in weights.items()}
