# ai/boss_agent.py — Tabular Q-Learning Boss AI Agent
"""
Academic AI/ML Mini-Project: Tabular Q-Learning Agent for 2D Platformer Boss Fight.
----------------------------------------------------------------------------------
Pure Python Implementation (Zero External ML Libraries — No TensorFlow/sklearn).
Demonstrates the fundamental Reinforcement Learning (RL) concept:
An agent learns an optimal policy through repeated trial-and-error interactions
with an environment, guided by scalar rewards and the Bellman Optimality Equation.

Theoretical Background for Viva / Evaluator Defense:
1. Markov Decision Process (MDP):
   Defined by (S, A, P, R, gamma). Here, transition probabilities P are unknown
   to the agent, making Q-Learning a Model-Free, Off-Policy Temporal Difference algorithm.

2. State Space (S):
   Discretized 2D tuple (Distance to Player, Player Last Action).
   Distance: {'near', 'medium', 'far'}
   Player Action: {'attack', 'dodge', 'idle'}
   Total discrete states = 3 x 3 = 9 states.

3. Action Space (A):
   4 discrete boss actions: {'attack', 'dodge', 'retreat', 'wait'}

4. Bellman Q-Learning Update Equation:
   Q(s, a) <- Q(s, a) + alpha * [ r + gamma * max_{a'} Q(s', a') - Q(s, a) ]
   where:
     - alpha : Learning Rate (determines how much new feedback overrides old estimate)
     - gamma : Discount Factor (importance of future rewards vs immediate rewards)
     - delta = r + gamma * max_{a'} Q(s', a') - Q(s, a) : Temporal Difference (TD) Error

5. Epsilon-Greedy Policy:
   Balances the Exploration vs. Exploitation dilemma:
     - With probability epsilon: take a random exploratory action (discover new tactics)
     - With probability 1 - epsilon: exploit the best known action (argmax_a Q(s,a))
   Epsilon decays smoothly over time, shifting from high exploration early in the fight
   to high mastery/exploitation in later phases.
"""

import random
from typing import Tuple, Dict, List, Optional


class BossAgent:
    """
    Tabular Q-Learning Agent controlling the boss combat decisions.
    Maintains a dictionary-based Q-table and updates values via TD learning.
    """

    # 4 Discrete Actions available to the Boss
    ACTIONS: List[str] = ["attack", "dodge", "retreat", "wait"]

    # Distance discretization thresholds (in screen pixels)
    DIST_NEAR: float = 120.0
    DIST_MEDIUM: float = 280.0

    def __init__(self,
                 alpha: float = 0.15,
                 gamma: float = 0.90,
                 epsilon: float = 0.85,
                 epsilon_min: float = 0.05,
                 epsilon_decay: float = 0.985) -> None:
        """
        Initialize the Q-Learning Boss Agent.

        Args:
            alpha: Learning rate (0.0 to 1.0). Higher values adapt faster.
            gamma: Discount factor (0.0 to 1.0). Weights long-term strategic rewards.
            epsilon: Initial exploration probability (0.85 = 85% random exploration at start).
            epsilon_min: Minimum exploration floor (prevents agent from ever freezing entirely).
            epsilon_decay: Multiplicative decay factor applied after each learning step.
        """
        self.alpha: float = alpha
        self.gamma: float = gamma
        self.epsilon: float = epsilon
        self.epsilon_min: float = epsilon_min
        self.epsilon_decay: float = epsilon_decay

        # Performance and training metrics
        self.total_steps: int = 0
        self.total_hits_dealt: int = 0
        self.total_hits_received: int = 0
        self.cumulative_reward: float = 0.0

        # Tabular Q-Table: dictionary mapping state tuple -> {action: q_value}
        # e.g., { ("near", "attack"): {"attack": -0.2, "dodge": 0.8, ...} }
        self.q_table: Dict[Tuple[str, str], Dict[str, float]] = {}

        # Pre-initialize all 9 possible canonical states with 0.0 Q-values
        self._initialize_known_states()

    def _initialize_known_states(self) -> None:
        """Populate the canonical 3x3 state space with initial neutral Q-values (0.0)."""
        distances = ["near", "medium", "far"]
        player_actions = ["attack", "dodge", "idle"]
        for d in distances:
            for pa in player_actions:
                state = (d, pa)
                self.q_table[state] = {action: 0.0 for action in self.ACTIONS}

    # ─────────────────────────────────────────────────────────────
    # State Discretization & Representation
    # ─────────────────────────────────────────────────────────────

    @classmethod
    def discretize_distance(cls, distance_px: float) -> str:
        """
        Map continuous pixel distance between boss and player into 3 discrete categories.

        Args:
            distance_px: Euclidean or horizontal pixel distance.
        Returns:
            'near' (< 120px), 'medium' (120 - 280px), or 'far' (> 280px).
        """
        abs_dist = abs(distance_px)
        if abs_dist < cls.DIST_NEAR:
            return "near"
        elif abs_dist <= cls.DIST_MEDIUM:
            return "medium"
        else:
            return "far"

    @classmethod
    def get_state(cls, distance_px: float, player_action: str) -> Tuple[str, str]:
        """
        Construct a discrete state representation tuple.

        Args:
            distance_px: Distance between boss and player.
            player_action: 'attack', 'dodge', or 'idle'.
        Returns:
            Tuple: (distance_category, player_action), e.g. ('near', 'attack').
        """
        dist_cat = cls.discretize_distance(distance_px)
        # Sanitize player action
        valid_actions = {"attack", "dodge", "idle"}
        p_act = player_action if player_action in valid_actions else "idle"
        return (dist_cat, p_act)

    def _ensure_state_exists(self, state: Tuple[str, str]) -> None:
        """
        Safe Fallback Mechanism:
        Ensures that if an unseen or unexpected state is ever encountered,
        it is cleanly initialized in the Q-table so the agent never crashes.
        """
        if state not in self.q_table:
            # Fallback initialization: 0.0 for all actions
            self.q_table[state] = {action: 0.0 for action in self.ACTIONS}

    # ─────────────────────────────────────────────────────────────
    # Epsilon-Greedy Action Selection (Policy)
    # ─────────────────────────────────────────────────────────────

    def choose_action(self, state: Tuple[str, str]) -> str:
        """
        Select an action using the Epsilon-Greedy policy.

        - Exploration (random action) with probability epsilon.
        - Exploitation (greedy max Q-value action) with probability 1 - epsilon.

        Args:
            state: Current environment state tuple (distance, player_action).
        Returns:
            One of the 4 actions: 'attack', 'dodge', 'retreat', or 'wait'.
        """
        self._ensure_state_exists(state)

        # 1. Exploration Step (Random Action)
        if random.random() < self.epsilon:
            return random.choice(self.ACTIONS)

        # 2. Exploitation Step (Greedy argmax_a Q(s, a))
        action_values = self.q_table[state]
        max_q = max(action_values.values())

        # If multiple actions share the same maximum Q-value, break ties randomly
        best_actions = [a for a, q in action_values.items() if q == max_q]
        return random.choice(best_actions)

    # ─────────────────────────────────────────────────────────────
    # Bellman Q-Learning Update
    # ─────────────────────────────────────────────────────────────

    def learn(self,
              state: Tuple[str, str],
              action: str,
              reward: float,
              next_state: Tuple[str, str]) -> float:
        """
        Apply the Bellman Temporal Difference update rule:
        Q(s, a) <- Q(s, a) + alpha * [ r + gamma * max_{a'} Q(s', a') - Q(s, a) ]

        Also decays exploration parameter epsilon towards epsilon_min.

        Args:
            state: Previous state (s)
            action: Action taken (a)
            reward: Immediate scalar reward received (r)
            next_state: Resulting new state (s')
        Returns:
            The Temporal Difference (TD) error magnitude.
        """
        self._ensure_state_exists(state)
        self._ensure_state_exists(next_state)

        # Current Q-value estimate: Q(s, a)
        old_q = self.q_table[state].get(action, 0.0)

        # Best estimated future reward: max_{a'} Q(s', a')
        next_max_q = max(self.q_table[next_state].values())

        # TD Target = r + gamma * max Q(s', a')
        td_target = reward + self.gamma * next_max_q

        # TD Error = TD Target - old_q
        td_error = td_target - old_q

        # Gradient update rule
        new_q = old_q + self.alpha * td_error
        self.q_table[state][action] = round(new_q, 4)

        # Decay exploration rate (epsilon)
        self.epsilon = max(self.epsilon_min, self.epsilon * self.epsilon_decay)
        self.total_steps += 1
        self.cumulative_reward += reward

        if reward >= 1.0:
            self.total_hits_dealt += 1
        elif reward <= -1.0:
            self.total_hits_received += 1

        return td_error

    # ─────────────────────────────────────────────────────────────
    # Live Telemetry & Evaluator Demonstration Helpers
    # ─────────────────────────────────────────────────────────────

    def get_q_table_snapshot(self) -> Dict[str, Dict[str, float]]:
        """
        Return a formatted dictionary representation of the Q-table
        suitable for live rendering in the UI or JSON export.
        """
        snapshot = {}
        for (dist, p_act), actions in self.q_table.items():
            state_key = f"{dist.upper()} | {p_act.upper()}"
            snapshot[state_key] = dict(actions)
        return snapshot

    def print_q_table(self, title: str = "CURRENT Q-TABLE SNAPSHOT") -> None:
        """
        Prints a neat, human-readable terminal table showing the learned Q-values.
        Perfect for live terminal demonstration during project review.
        """
        print(f"\n{'=' * 68}")
        print(f"  [Q-LEARNING BOSS AI] {title}")
        print(f"  Steps: {self.total_steps:3d} | Epsilon: {self.epsilon:.3f} | Total Reward: {self.cumulative_reward:+.2f}")
        print(f"{'=' * 68}")
        print(f"  {'STATE (Dist | Player)':<24} | {'ATTACK':>8} {'DODGE':>8} {'RETREAT':>8} {'WAIT':>8} | {'BEST':>7}")
        print(f"  {'-' * 64}")

        for (dist, p_act) in sorted(self.q_table.keys()):
            actions = self.q_table[(dist, p_act)]
            best_a = max(actions, key=actions.get)
            row_str = f"  {dist.upper():<7} | {p_act.upper():<12} | "
            for a in self.ACTIONS:
                val = actions[a]
                row_str += f"{val:+7.2f} "
            row_str += f"| {best_a.upper():>7}"
            print(row_str)
        print(f"{'=' * 68}\n")

    def get_stats(self) -> dict:
        """Returns key metrics for on-screen HUD telemetry."""
        return {
            "steps": self.total_steps,
            "epsilon": self.epsilon,
            "cumulative_reward": self.cumulative_reward,
            "hits_dealt": self.total_hits_dealt,
            "hits_received": self.total_hits_received,
            "alpha": self.alpha,
            "gamma": self.gamma
        }


# ─────────────────────────────────────────────────────────────
# Standalone Unit Test & Learning Simulation
# ─────────────────────────────────────────────────────────────
if __name__ == "__main__":
    print("Initializing Q-Learning Boss Agent standalone test...")
    agent = BossAgent(alpha=0.2, gamma=0.9, epsilon=0.9, epsilon_decay=0.97)

    # Display initial blank Q-table
    agent.print_q_table("INITIAL Q-TABLE (NO PRIOR EXPERIENCE)")

    # Simulate 60 combat encounters to prove that Q-learning converges:
    # Rule 1: When player attacks near, boss dodging should yield positive reward, attacking should hurt.
    # Rule 2: When player is near and idle, boss attacking should yield positive reward (+1.0).
    # Rule 3: Attacking while far yields negative reward (-0.1).
    print("Simulating 60 training encounters in the combat environment...")
    for episode in range(60):
        # Pick random state
        dist = random.choice(["near", "medium", "far"])
        p_act = random.choice(["attack", "dodge", "idle"])
        state = (dist, p_act)

        action = agent.choose_action(state)

        # Environment Reward Function
        if dist == "near" and p_act == "attack":
            if action == "dodge" or action == "retreat":
                reward = +1.0  # Successfully evaded player strike!
            elif action == "attack":
                reward = -1.0  # Traded hit and got interrupted
            else:
                reward = -0.5  # Just stood there and got hit
        elif dist == "near" and p_act == "idle":
            if action == "attack":
                reward = +1.0  # Punished vulnerable player!
            elif action == "wait":
                reward = -0.1
            else:
                reward = 0.0
        elif dist == "far":
            if action == "attack":
                reward = -0.2  # Whiffed swing from distance (wasted energy)
            else:
                reward = +0.1  # Repositioned or waited
        else:
            reward = 0.0

        # Simulate next state
        next_dist = random.choice(["near", "medium"]) if action in ("attack", "wait") else "far"
        next_p_act = random.choice(["attack", "dodge", "idle"])
        next_state = (next_dist, next_p_act)

        # Bellman update
        agent.learn(state, action, reward, next_state)

    # Display learned Q-table
    agent.print_q_table("LEARNED Q-TABLE (AFTER 60 ENCOUNTERS)")

    # Check key assertions
    near_att = agent.q_table[("near", "attack")]
    best_counter_to_attack = max(near_att, key=near_att.get)
    print(f"Learned optimal counter when player attacks at close range: {best_counter_to_attack.upper()}")
    assert best_counter_to_attack in ("dodge", "retreat"), "Boss should learn to evade attack!"

    near_idle = agent.q_table[("near", "idle")]
    best_counter_to_idle = max(near_idle, key=near_idle.get)
    print(f"Learned optimal counter when player is idle at close range: {best_counter_to_idle.upper()}")
    assert best_counter_to_idle == "attack", "Boss should learn to strike when player is idle!"

    print("\n✓ ALL AGENT Q-LEARNING TESTS PASSED SUCCESSFULLY!")
