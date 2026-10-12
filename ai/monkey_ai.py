# ai/monkey_ai.py
import math
from settings import MONKEY_SCARE_RADIUS, MONKEY_APPROACH_RADIUS

class MonkeyAI:
    """
    Model 3: Reactive Multi-Agent Spatial AI.
    Features acrobatic obstacle vaulting (jumping over the player),
    bag snatching, and agile hit-and-run evasion tactics.
    """
    def __init__(self):
        self.state = 'idle'
        self.jump_cooldown = 0

    def decide_action(self, monkey_x: float, monkey_y: float,
                      player_x: float, player_y: float,
                      woman_x: float, woman_y: float,
                      has_bag: bool = False,
                      on_ground: bool = True) -> str:
        """
        Calculates reactive decision based on spatial proximity vectors,
        player occlusion of target, and possession of loot.
        """
        if self.jump_cooldown > 0:
            self.jump_cooldown -= 1

        dist_player = math.hypot(monkey_x - player_x, monkey_y - player_y)
        dist_woman = math.hypot(monkey_x - woman_x, monkey_y - woman_y)

        # If holding stolen bag, focus purely on escaping with the loot
        if has_bag:
            self.state = 'flee_with_bag'
            return 'flee_with_bag'

        # Close enough to snatch grandmother's bag
        if dist_woman < 36:
            self.state = 'steal'
            return 'steal'

        # Player is standing directly between monkey and grandmother:
        # Check if player is blocking the path to woman
        player_between = (monkey_x > player_x > woman_x) or (monkey_x < player_x < woman_x)
        if player_between and 60 <= dist_player <= 180 and on_ground and self.jump_cooldown == 0:
            self.state = 'vault'
            self.jump_cooldown = 120  # Cooldown between vault attempts
            return 'vault'

        # Player is right on top of monkey on the ground: flee
        if dist_player <= MONKEY_SCARE_RADIUS and on_ground:
            self.state = 'flee'
            return 'flee'

        # Player is far enough, approach grandmother
        if dist_player > 130 or not player_between:
            self.state = 'approach'
            return 'approach'

        self.state = 'idle'
        return 'idle'

    def get_flee_direction(self, monkey_x: float, player_x: float) -> int:
        return 1 if monkey_x >= player_x else -1

    def get_approach_direction(self, monkey_x: float, woman_x: float) -> int:
        return 1 if monkey_x < woman_x else -1
