# levels/base_level.py — Abstract interface for all game levels
import pygame
from typing import Optional


class BaseLevel:
    """
    Abstract base class for all game levels.
    Each level implements handle_events, update, and draw.
    Returning a string from handle_events or update triggers a state transition.
    """

    def handle_events(self, events: list[pygame.event.Event]) -> Optional[str]:
        """
        Process input events. Return a state name string to transition,
        or None to stay in the current level.
        """
        return None

    def update(self) -> Optional[str]:
        """
        Update game logic each frame. Return a state name string to transition,
        or None to stay in the current level.
        """
        return None

    def draw(self, surface: pygame.Surface) -> None:
        """Draw the level to the given display surface."""
        pass
