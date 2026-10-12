import pygame
from settings import SCREEN_WIDTH

class Camera:
    """
    A smooth scrolling camera that follows the player along the x-axis.
    Does not backtrack, and keeps a fixed y-axis.
    """
    def __init__(self) -> None:
        self.offset_x = 0.0
        self.offset_y = 0.0

    def update(self, player) -> None:
        """
        Update camera offset to follow the player.
        """
        target_x = player.rect.centerx - SCREEN_WIDTH // 3
        # Smooth follow
        if target_x > self.offset_x:
            self.offset_x += (target_x - self.offset_x) * 0.1

    def apply(self, rect: pygame.Rect) -> tuple:
        """
        Returns a tuple of the screen coordinates.
        """
        return (rect.x - int(self.offset_x), rect.y - int(self.offset_y))

    def apply_rect(self, rect: pygame.Rect) -> pygame.Rect:
        """
        Returns a new Rect shifted by camera offset.
        """
        return pygame.Rect(
            rect.x - int(self.offset_x),
            rect.y - int(self.offset_y),
            rect.width,
            rect.height
        )

    def get_world_right(self) -> float:
        """
        Returns the rightmost visible world x coordinate.
        """
        return self.offset_x + SCREEN_WIDTH
