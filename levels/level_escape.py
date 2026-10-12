import random
import time
import pygame
from game_state import GameState
from levels.base_level import BaseLevel
import settings

class EscapeLevel(BaseLevel):
    def __init__(self, game_state: GameState):
        self.game_state = game_state
        self.route = self.game_state.route
        self.font_large = pygame.font.SysFont("segoeui, arial, sans-serif", 48)

        self.font_medium = pygame.font.SysFont("segoeui, arial, sans-serif", 32)
        self.font_small = pygame.font.SysFont("segoeui, arial, sans-serif", 24)
        
        self.input_text = ""
        # Route A = 3 attempts, Route B = 2 attempts, Route C = 1 attempt
        if self.route == "A":
            self.attempts = 3
        elif self.route == "B":
            self.attempts = 2
        else:
            self.attempts = 1

        # Dynamic question selection every run — ask a short random sequence
        # (3 fill-in-the-blank code words, sampled without replacement) so the
        # tunnel feels different each playthrough.
        self.num_tunnel_questions = 3
        tunnel_pool = [
            {"question": "The force that pulls all objects toward the center of the Earth is ________.", "answer": "GRAVITY"},
            {"question": "Plants breathe out oxygen and take in ________ dioxide.", "answer": "CARBON"},
            {"question": "The primary source of light and heat for all life on Earth is the ________.", "answer": "SUN"},
            {"question": "Water turns to ice at zero degrees Celsius; this is its ________ point.", "answer": "FREEZING"},
            {"question": "The speed of light travels through vacuum faster than the speed of ________.", "answer": "SOUND"},
            {"question": "The layer of atmosphere that protects Earth from harmful ultraviolet rays is ________.", "answer": "OZONE"},
            {"question": "The ancient red planet fourth in order from the Sun is ________.", "answer": "MARS"},
            {"question": "The organ in the human body responsible for pumping oxygenated blood is the ________.", "answer": "HEART"},
            {"question": "The largest and deepest body of water on planet Earth is the ________ Ocean.", "answer": "PACIFIC"},
            {"question": "The pursuit of facts, learning, and truth gives you ________.", "answer": "KNOWLEDGE"},
            {"question": "The natural satellite orbiting Earth that pulls the ocean tides is the ________.", "answer": "MOON"},
            {"question": "Liquid water rising as vapor into the air is called ________.", "answer": "EVAPORATION"},
            {"question": "The green pigment in leaves that captures sunlight is called ________.", "answer": "CHLOROPHYLL"},
            {"question": "The scientist who proposed the three laws of motion was Isaac ________.", "answer": "NEWTON"},
            {"question": "The device that converts sunlight directly into electricity is the solar ________.", "answer": "PANEL"},
        ]
        # random.sample = no repeats within a run; reshuffled order each run
        self.tunnel_questions = random.sample(tunnel_pool, k=min(self.num_tunnel_questions, len(tunnel_pool)))
        self.question_index = 0
        self.question_text_str = self.tunnel_questions[self.question_index]["question"]
        self.target_answer = self.tunnel_questions[self.question_index]["answer"].upper()

        self.message = ""
        self.message_time = 0
        
    def handle_events(self, events: list[pygame.event.Event]) -> str | None:
        for event in events:
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_RETURN:
                    return self._check_answer()
                elif event.key == pygame.K_BACKSPACE:
                    self.input_text = self.input_text[:-1]
                else:
                    if event.unicode.isalnum() or event.unicode == " ":
                        self.input_text += event.unicode
        return None
        
    def _check_answer(self) -> str | None:
        typed = self.input_text.strip().lower()
        if not typed:
            return None
            
        keyword = (self.game_state.escape_keyword or "").strip().lower()
        riddle_ans = (self.game_state.escape_riddle.get("answer", "") or "").strip().lower()
        dynamic_ans = self.target_answer.lower()

        # Valid targets: accept dynamic tunnel question answer, keyword, or base riddle answer
        valid_targets = {t for t in (dynamic_ans, keyword, riddle_ans) if t}
        
        if typed in valid_targets:
            # Advance through the random question sequence
            self.question_index += 1
            if self.question_index >= len(self.tunnel_questions):
                return "old_woman"
            self.question_text_str = self.tunnel_questions[self.question_index]["question"]
            self.target_answer = self.tunnel_questions[self.question_index]["answer"].upper()
            self.input_text = ""
            self.message = f"CORRECT! CODE {self.question_index + 1} OF {len(self.tunnel_questions)}"
            self.message_time = time.time()
            return None
        else:
            self.attempts -= 1
            if self.attempts <= 0:
                return "game_over"
            else:
                self.input_text = ""
                self.message = "TRY AGAIN"
                self.message_time = time.time()
                return None

                
    def update(self) -> str | None:
        if self.message and time.time() - self.message_time > 2:
            self.message = ""
        return None
        
    def draw(self, surface: pygame.Surface) -> None:
        progress_label = f"CODE {min(self.question_index + 1, len(self.tunnel_questions))} OF {len(self.tunnel_questions)}"
        if self.route == "A":
            surface.fill((255, 255, 220)) # pale yellow
            # Light beams
            pygame.draw.polygon(surface, (255, 255, 255), [(400, 0), (880, 0), (1280, 720), (0, 720)])
            title_text = self.font_large.render("The cage has opened. A glowing exit portal.", True, settings.BLACK)
            instruction_text = self.font_medium.render(f"Fill in the blank to unlock the portal ({progress_label}):", True, settings.BLACK)
            question_text = self.font_medium.render(self.question_text_str, True, (80, 60, 20))
        else:
            surface.fill((10, 10, 15)) # near black
            # single light source
            light_rect = pygame.Rect(0, 0, 400, 400)
            light_rect.center = (settings.DISPLAY_WIDTH // 2, settings.DISPLAY_HEIGHT // 2 - 50)
            
            # draw radial gradient for tunnel light
            pygame.draw.ellipse(surface, (30, 30, 40), light_rect.inflate(200, 200))
            pygame.draw.ellipse(surface, (40, 40, 50), light_rect.inflate(100, 100))
            pygame.draw.ellipse(surface, (50, 50, 60), light_rect)
            
            title_text = self.font_large.render("A dark tunnel.", True, settings.WHITE)
            instruction_text = self.font_medium.render(f"Fill in the blank to find the code word ({progress_label}):", True, settings.LIGHT_GRAY)
            question_text = self.font_medium.render(self.question_text_str, True, settings.YELLOW)
            
        title_rect = title_text.get_rect(center=(settings.DISPLAY_WIDTH // 2, 80))
        surface.blit(title_text, title_rect)
        
        inst_rect = instruction_text.get_rect(center=(settings.DISPLAY_WIDTH // 2, 140))
        surface.blit(instruction_text, inst_rect)
        
        q_rect = question_text.get_rect(center=(settings.DISPLAY_WIDTH // 2, 200))
        surface.blit(question_text, q_rect)
        
        # Draw input box

        box_width = 600
        box_height = 80
        box_rect = pygame.Rect(settings.DISPLAY_WIDTH // 2 - box_width // 2, 320, box_width, box_height)
        
        pygame.draw.rect(surface, settings.WHITE, box_rect)
        pygame.draw.rect(surface, settings.BLACK if self.route == "A" else settings.LIGHT_GRAY, box_rect, 4)
        
        # Draw text + blinking cursor
        display_text = self.input_text
        if time.time() % 1.0 > 0.5:
            display_text += "|"
            
        text_surf = self.font_large.render(display_text, True, settings.BLACK)
        text_rect = text_surf.get_rect(center=box_rect.center)
        surface.blit(text_surf, text_rect)
        
        # Draw attempts
        dot_y = 450
        dot_spacing = 40
        start_x = settings.DISPLAY_WIDTH // 2 - (self.attempts - 1) * dot_spacing // 2
        for i in range(self.attempts):
            color = settings.RED if self.route == "B" else settings.GREEN
            pygame.draw.circle(surface, color, (start_x + i * dot_spacing, dot_y), 10)
            
        if self.message:
            msg_surf = self.font_medium.render(self.message, True, settings.RED)
            msg_rect = msg_surf.get_rect(center=(settings.DISPLAY_WIDTH // 2, 520))
            surface.blit(msg_surf, msg_rect)

LevelEscape = EscapeLevel

