import time
import pygame
from game_state import GameState
from levels.base_level import BaseLevel
import settings

class ExamGateLevel(BaseLevel):
    def __init__(self, game_state: GameState):
        self.game_state = game_state
        self.font_title = pygame.font.SysFont("segoeui, arial, sans-serif", 40)

        self.font_word = pygame.font.SysFont("segoeui, arial, sans-serif", 32)
        self.font_timer = pygame.font.SysFont("segoeui, arial, sans-serif", 48)
        
        self.input_text = ""
        self.correct_words = []
        self.start_time = time.time()
        self.message = ""
        self.message_color = settings.WHITE
        self.message_time = 0
        
        self.gate_opening = False
        self.gate_open_start_time = 0
        self.gate_open_duration = 2.0

        # Campus gate background
        import sprite_loader
        self.bg = sprite_loader.load_background("bg_level5_gate.jpg", settings.DISPLAY_WIDTH, settings.DISPLAY_HEIGHT)
        
    def handle_events(self, events: list[pygame.event.Event]) -> str | None:
        if self.gate_opening:
            return None
            
        for event in events:
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    return self._finish_level()
                elif event.key == pygame.K_RETURN:
                    self._check_word()
                elif event.key == pygame.K_BACKSPACE:
                    self.input_text = self.input_text[:-1]
                else:
                    if event.unicode.isalnum() or event.unicode == " ":
                        self.input_text += event.unicode
        return None
        
    def _check_word(self):
        if not self.input_text.strip():
            return
            
        word_typed = self.input_text.strip().lower()
        self.input_text = ""
        
        if word_typed in [w.lower() for w in self.correct_words]:
            self._set_message("Already entered!", settings.YELLOW)
            return
            
        target_words_lower = [w.lower() for w in self.game_state.words]
        if word_typed in target_words_lower:
            # find original case
            idx = target_words_lower.index(word_typed)
            self.correct_words.append(self.game_state.words[idx])
            self._set_message("Correct!", settings.GREEN)
            
            if len(self.correct_words) >= settings.EXAM_GATE_PASS:
                self.gate_opening = True
                self.gate_open_start_time = time.time()
        else:
            self._set_message("Wrong!", settings.RED)
            
    def _set_message(self, text, color):
        self.message = text
        self.message_color = color
        self.message_time = time.time()
        
    def _finish_level(self) -> str | None:
        if len(self.correct_words) >= settings.EXAM_GATE_PASS:
            self.gate_opening = True
            self.gate_open_start_time = time.time()
            return None
        else:
            return "game_over"
            
    def update(self) -> str | None:
        if self.gate_opening:
            if time.time() - self.gate_open_start_time >= self.gate_open_duration:
                return "win"
            return None
            
        elapsed = time.time() - self.start_time
        if elapsed >= settings.EXAM_GATE_TIME:
            return self._finish_level()
            
        if self.message and time.time() - self.message_time > 1.5:
            self.message = ""
            
        return None
        
    def draw(self, surface: pygame.Surface) -> None:
        if self.bg:
            surface.blit(self.bg, (0, 0))
        else:
            surface.fill(settings.DARK_GRAY)
        
        # Background light (shining through gate)
        if self.gate_opening:
            progress = min(1.0, (time.time() - self.gate_open_start_time) / self.gate_open_duration)
            light_radius = int(800 * progress)
            pygame.draw.circle(surface, (255, 255, 200), (settings.DISPLAY_WIDTH // 2, settings.DISPLAY_HEIGHT // 2), light_radius)
        
        # Pillars
        pygame.draw.rect(surface, (100, 100, 100), (0, 0, 200, settings.DISPLAY_HEIGHT))
        pygame.draw.rect(surface, (100, 100, 100), (settings.DISPLAY_WIDTH - 200, 0, 200, settings.DISPLAY_HEIGHT))
        
        # Gate
        gate_rect = pygame.Rect(200, 150, settings.DISPLAY_WIDTH - 400, settings.DISPLAY_HEIGHT - 150)
        
        # If gate opening, slide bars horizontally
        slide_dist = 0
        if self.gate_opening:
            progress = min(1.0, (time.time() - self.gate_open_start_time) / self.gate_open_duration)
            slide_dist = (settings.DISPLAY_WIDTH // 2) * progress
            
        for x in range(250, settings.DISPLAY_WIDTH - 200, 80):
            # Left half slides left, right half slides right
            if x < settings.DISPLAY_WIDTH // 2:
                bar_x = x - slide_dist
            else:
                bar_x = x + slide_dist
                
            if 200 <= bar_x <= settings.DISPLAY_WIDTH - 200:
                pygame.draw.rect(surface, (50, 50, 50), (bar_x, 150, 20, settings.DISPLAY_HEIGHT - 150))
                
        # Top bar of gate
        pygame.draw.rect(surface, (50, 50, 50), (200, 150, settings.DISPLAY_WIDTH - 400, 40))
        
        # Padlock
        if not self.gate_opening:
            padlock_rect = pygame.Rect(0, 0, 80, 80)
            padlock_rect.center = (settings.DISPLAY_WIDTH // 2, settings.DISPLAY_HEIGHT // 2)
            pygame.draw.rect(surface, settings.GOLD, padlock_rect, border_radius=10)
            pygame.draw.circle(surface, settings.BLACK, padlock_rect.center, 15)
            pygame.draw.rect(surface, settings.BLACK, (padlock_rect.centerx - 5, padlock_rect.centery, 10, 20))
            
        # Display Board
        board_rect = pygame.Rect(settings.DISPLAY_WIDTH // 2 - 450, 20, 900, 100)
        pygame.draw.rect(surface, settings.BLACK, board_rect)
        pygame.draw.rect(surface, settings.GOLD, board_rect, 4)
        
        title_surf = self.font_title.render(f"PROVE YOUR KNOWLEDGE - Enter the {settings.EXAM_GATE_TOTAL} words you studied.", True, settings.WHITE)
        surface.blit(title_surf, title_surf.get_rect(center=(board_rect.centerx, board_rect.centery - 15)))
        
        # Timer
        elapsed = time.time() - self.start_time
        remaining = max(0, int(settings.EXAM_GATE_TIME - elapsed))
        time_surf = self.font_timer.render(f"Time: {remaining}s", True, settings.RED if remaining <= 10 else settings.WHITE)
        surface.blit(time_surf, time_surf.get_rect(center=(board_rect.centerx, board_rect.centery + 25)))
        
        if not self.gate_opening:
            # Input Box
            input_box = pygame.Rect(settings.DISPLAY_WIDTH // 2 - 250, settings.DISPLAY_HEIGHT - 100, 500, 60)
            pygame.draw.rect(surface, settings.WHITE, input_box)
            pygame.draw.rect(surface, settings.BLACK, input_box, 3)
            
            display_text = self.input_text + ("|" if time.time() % 1.0 > 0.5 else "")
            text_surf = self.font_word.render(display_text, True, settings.BLACK)
            surface.blit(text_surf, text_surf.get_rect(center=input_box.center))
            
            # Progress Bar
            progress_y = input_box.top - 40
            pygame.draw.rect(surface, settings.BLACK, (settings.DISPLAY_WIDTH // 2 - 200, progress_y, 400, 20))
            ratio = min(1.0, len(self.correct_words) / settings.EXAM_GATE_TOTAL)
            pygame.draw.rect(surface, settings.GREEN, (settings.DISPLAY_WIDTH // 2 - 200, progress_y, int(400 * ratio), 20))
            
            # Threshold line (Pass at 4/5)
            pass_x = settings.DISPLAY_WIDTH // 2 - 200 + int(400 * (settings.EXAM_GATE_PASS / settings.EXAM_GATE_TOTAL))
            pygame.draw.line(surface, settings.RED, (pass_x, progress_y - 10), (pass_x, progress_y + 30), 4)
            
            prog_text = self.font_word.render(f"{len(self.correct_words)}/{settings.EXAM_GATE_TOTAL}", True, settings.WHITE)
            surface.blit(prog_text, prog_text.get_rect(center=(settings.DISPLAY_WIDTH // 2, progress_y - 20)))
            
            # Message
            if self.message:
                msg_surf = self.font_word.render(self.message, True, self.message_color)
                surface.blit(msg_surf, msg_surf.get_rect(center=(settings.DISPLAY_WIDTH // 2, input_box.top - 70)))
                
        # Words on Gate
        start_x = 220
        start_y = 220
        for i, word in enumerate(self.correct_words):
            col = i % 5
            row = i // 5
            word_x = start_x + col * ((settings.DISPLAY_WIDTH - 440) // 5)
            word_y = start_y + row * 80
            
            word_surf = self.font_word.render(word, True, settings.GREEN)
            surface.blit(word_surf, (word_x, word_y))

LevelExamGate = ExamGateLevel

