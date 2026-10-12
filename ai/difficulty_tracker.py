import math
import sys
import os

# Add parent directory to path to import settings if run directly
if __name__ == '__main__':
    sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from settings import (
    SKILL_START,
    SKILL_K,
    EASY_THRESHOLD,
    HARD_THRESHOLD,
    OBSTACLE_DIFFICULTY
)

class DifficultyTracker:
    """An Elo-style skill model that tracks player performance."""
    
    def __init__(self) -> None:
        """Initializes the difficulty tracker with default values."""
        self.skill_score: float = SKILL_START
        self.history: list[float] = [SKILL_START]
        self.deaths_total: int = 0
        self.clears_total: int = 0
        self.current_streak: int = 0
        
    def update(self, obstacle_type: str, cleared: bool) -> None:
        """Updates the skill score based on whether the obstacle was cleared."""
        obstacle_diff = OBSTACLE_DIFFICULTY.get(obstacle_type, 3.0)
        
        # Calculate expected outcome
        expected = 1.0 / (1.0 + math.exp(-(self.skill_score - obstacle_diff)))
        
        # Actual outcome
        actual = 1.0 if cleared else 0.0
        
        # Update skill score
        self.skill_score += SKILL_K * (actual - expected)
        
        # Clamp between 0 and 10
        self.skill_score = max(0.0, min(10.0, self.skill_score))
        
        # Update stats
        if cleared:
            self.clears_total += 1
            if self.current_streak < 0:
                self.current_streak = 0
            self.current_streak += 1
        else:
            self.deaths_total += 1
            if self.current_streak > 0:
                self.current_streak = 0
            self.current_streak -= 1
            
        self.history.append(self.skill_score)

    def get_difficulty_tier(self) -> str:
        """Returns the current difficulty tier based on skill score."""
        if self.skill_score < EASY_THRESHOLD:
            return 'easy'
        elif self.skill_score > HARD_THRESHOLD:
            return 'hard'
        return 'medium'
        
    def get_stats(self) -> dict:
        """Returns a dictionary of current tracker stats."""
        return {
            'skill_score': self.skill_score,
            'tier': self.get_difficulty_tier(),
            'deaths': self.deaths_total,
            'clears': self.clears_total,
            'streak': self.current_streak
        }
        
    def reset(self) -> None:
        """Resets everything to initial state."""
        self.skill_score = SKILL_START
        self.history = [SKILL_START]
        self.deaths_total = 0
        self.clears_total = 0
        self.current_streak = 0

if __name__ == '__main__':
    import random
    
    tracker = DifficultyTracker()
    obstacles = list(OBSTACLE_DIFFICULTY.keys())
    
    print(f"Initial State: Score={tracker.skill_score:.2f}, Tier={tracker.get_difficulty_tier()}")
    
    # Simulate 20 obstacle encounters
    for i in range(1, 21):
        obs = random.choice(obstacles)
        # Randomly decide if player cleared or died (e.g. 70% chance to clear)
        cleared = random.random() < 0.70
        tracker.update(obs, cleared)
        
        status = "CLEARED" if cleared else "DIED"
        print(f"Encounter {i:2d}: {obs:15s} | {status:7s} -> Score: {tracker.skill_score:.2f}, Tier: {tracker.get_difficulty_tier():6s}, Streak: {tracker.current_streak:2d}")
