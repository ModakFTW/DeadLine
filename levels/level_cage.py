import pygame
import math
import time
from levels.base_level import BaseLevel
from settings import (
    DISPLAY_WIDTH, DISPLAY_HEIGHT, CAGE_IRON, DUNGEON_BG,
    RIDDLE_TIME, WHITE, RED, GREEN, FPS
)

class LevelCage(BaseLevel):
    def __init__(self, game_state):
        self.game_state = game_state
        self.phase = 'riddle_1'
        self.current_index = 0
        self.correct_count = 0
        self.start_time = time.time()
        self.input_text = ""
        
        self.font_large = pygame.font.SysFont("segoeui, arial, sans-serif", 64, bold=True)
        self.font_medium = pygame.font.SysFont("segoeui, arial, sans-serif", 32)
        self.font_small = pygame.font.SysFont("segoeui, arial, sans-serif", 24)
        
        self.feedback_msg = ""
        self.feedback_color = WHITE
        self.feedback_timer = 0
        
        self.anim_timer = 0
        self.anim_duration = 90  # frames
        
        # Fallback riddles if empty
        if not self.game_state.riddles or len(self.game_state.riddles) < 3:
            self.game_state.riddles = [
                {"question": "I speak without a mouth and hear without ears.", "answer": "echo"},
                {"question": "The more of this there is, the less you see.", "answer": "darkness"},
                {"question": "I have keys but no locks.", "answer": "keyboard"}
            ]

        # Atmospheric dungeon background
        import sprite_loader
        self.bg = sprite_loader.load_background("bg_level3_cage.jpg", DISPLAY_WIDTH, DISPLAY_HEIGHT)

    def handle_events(self, events):
        for event in events:
            if event.type == pygame.KEYDOWN:
                if self.phase.startswith('riddle_'):
                    if event.key == pygame.K_BACKSPACE:
                        self.input_text = self.input_text[:-1]
                    elif event.key == pygame.K_RETURN:
                        self.check_answer()
                    else:
                        if event.unicode.isalnum() or event.unicode.isspace():
                            self.input_text += event.unicode
        return None

    def check_answer(self, timeout=False):
        if timeout:
            self.set_feedback("TIME UP!", RED)
        else:
            ans = self.input_text.strip().lower()
            correct_ans = self.game_state.riddles[self.current_index]['answer'].strip().lower()
            if ans == correct_ans:
                self.correct_count += 1
                self.set_feedback("CORRECT!", GREEN)
            else:
                self.set_feedback("WRONG!", RED)
                
        self.input_text = ""
        self.current_index += 1
        
        if self.current_index >= 3:
            self.phase = 'result_animation'
            self.game_state.riddles_correct = self.correct_count
            if self.correct_count == 3:
                self.game_state.route = 'A'  # Pure mastery: Portal exit, 3 attempts
            elif self.correct_count == 2:
                self.game_state.route = 'B'  # Standard tunnel exit: 2 attempts
            else:
                self.game_state.route = 'C'  # Narrow escape tunnel: 1 attempt
        else:
            self.phase = f'riddle_{self.current_index + 1}'
            self.start_time = time.time()

    def set_feedback(self, msg, color):
        self.feedback_msg = msg
        self.feedback_color = color
        self.feedback_timer = 45

    def update(self):
        if self.feedback_timer > 0:
            self.feedback_timer -= 1
            
        if self.phase.startswith('riddle_'):
            elapsed = time.time() - self.start_time
            if elapsed >= RIDDLE_TIME:
                self.check_answer(timeout=True)
        elif self.phase == 'result_animation':
            self.anim_timer += 1
            if self.anim_timer >= self.anim_duration:
                self.phase = 'done'
                self.game_state.riddles_correct = self.correct_count
                if self.correct_count >= 3:
                    self.game_state.route = 'A'
                elif self.correct_count == 2:
                    self.game_state.route = 'B'
                else:
                    self.game_state.route = 'C'

                # 1/3, 2/3, and 3/3 can all reach Escape to proceed to the Old Woman level
                if self.correct_count >= 1:
                    return 'escape'
                else:
                    return 'game_over'
        return None



    def draw(self, surface):
        if self.bg:
            surface.blit(self.bg, (0, 0))
        else:
            surface.fill(DUNGEON_BG)
        
        # Torch glow
        t = time.time()
        glow_radius = 100 + math.sin(t * 5) * 10
        glow_surf = pygame.Surface((glow_radius * 2, glow_radius * 2), pygame.SRCALPHA)
        pygame.draw.circle(glow_surf, (255, 140, 0, 50), (glow_radius, glow_radius), glow_radius)
        surface.blit(glow_surf, (100 - glow_radius, DISPLAY_HEIGHT//2 - glow_radius))
        surface.blit(glow_surf, (DISPLAY_WIDTH - 100 - glow_radius, DISPLAY_HEIGHT//2 - glow_radius))
        
        # Draw cage bars
        bar_width = 30
        bar_spacing = 150
        num_bars = DISPLAY_WIDTH // bar_spacing + 1
        
        anim_offset_a = 0
        anim_offset_b = 0
        
        if self.phase == 'result_animation' or self.phase == 'done':
            progress = min(1.0, self.anim_timer / self.anim_duration)
            if self.correct_count == 3: # Route A: bars slide apart
                anim_offset_a = progress * DISPLAY_WIDTH
            elif self.correct_count == 2: # Route B: tunnel appears
                anim_offset_b = progress * 200
        
        # Floor panel for Route B
        if self.correct_count == 2 and (self.phase == 'result_animation' or self.phase == 'done'):
            pygame.draw.rect(surface, (10, 10, 10), (DISPLAY_WIDTH//2 - 150, DISPLAY_HEIGHT - anim_offset_b, 300, anim_offset_b))
            
        for i in range(num_bars):
            bx = i * bar_spacing
            
            if self.correct_count == 3 and (self.phase == 'result_animation' or self.phase == 'done'):
                if bx < DISPLAY_WIDTH // 2:
                    bx -= anim_offset_a
                else:
                    bx += anim_offset_a
                    
            if -bar_width < bx < DISPLAY_WIDTH:
                pygame.draw.rect(surface, CAGE_IRON, (bx, 0, bar_width, DISPLAY_HEIGHT))
                # Gradient effect
                pygame.draw.line(surface, (150, 155, 165), (bx + 2, 0), (bx + 2, DISPLAY_HEIGHT))
                pygame.draw.line(surface, (40, 45, 55), (bx + bar_width - 2, 0), (bx + bar_width - 2, DISPLAY_HEIGHT))

        # Horizontal bars
        if self.correct_count != 3 or (self.phase != 'result_animation' and self.phase != 'done'):
            pygame.draw.rect(surface, CAGE_IRON, (0, 100, DISPLAY_WIDTH, 20))
            pygame.draw.rect(surface, CAGE_IRON, (0, DISPLAY_HEIGHT - 120, DISPLAY_WIDTH, 20))
            
        if self.phase.startswith('riddle_'):
            # Score circles
            for i in range(3):
                cx = DISPLAY_WIDTH//2 - 60 + i * 60
                cy = 50
                color = GREEN if i < self.correct_count else (100, 100, 100)
                if i < self.current_index:
                    pygame.draw.circle(surface, color, (cx, cy), 15)
                else:
                    pygame.draw.circle(surface, WHITE, (cx, cy), 15, 2)
                    
            riddle_text = f"RIDDLE {self.current_index + 1} of 3"
            rt_surf = self.font_medium.render(riddle_text, True, WHITE)
            surface.blit(rt_surf, (DISPLAY_WIDTH//2 - rt_surf.get_width()//2, 90))
            
            elapsed = time.time() - self.start_time
            rem_time = max(0, int(RIDDLE_TIME - elapsed))
            timer_text = self.font_medium.render(f"Time: {rem_time}s", True, WHITE)
            surface.blit(timer_text, (DISPLAY_WIDTH - 150, 40))
            
            # Parchment
            parch_w, parch_h = 800, 200
            parch_x = DISPLAY_WIDTH//2 - parch_w//2
            parch_y = 150
            pygame.draw.rect(surface, (240, 230, 200), (parch_x, parch_y, parch_w, parch_h), border_radius=10)
            pygame.draw.rect(surface, (100, 80, 50), (parch_x, parch_y, parch_w, parch_h), 4, border_radius=10)
            
            q_text = self.game_state.riddles[self.current_index]['question']
            q_surf = self.font_medium.render(q_text, True, (0, 0, 0))
            surface.blit(q_surf, (parch_x + parch_w//2 - q_surf.get_width()//2, parch_y + parch_h//2 - q_surf.get_height()//2))
            
            # Input box
            input_box_w, input_box_h = 500, 60
            input_x = DISPLAY_WIDTH//2 - input_box_w//2
            input_y = 400
            pygame.draw.rect(surface, WHITE, (input_x, input_y, input_box_w, input_box_h), border_radius=5)
            pygame.draw.rect(surface, (150, 150, 150), (input_x, input_y, input_box_w, input_box_h), 2, border_radius=5)
            
            txt_surf = self.font_medium.render(self.input_text, True, (0, 0, 0))
            surface.blit(txt_surf, (input_x + 10, input_y + input_box_h//2 - txt_surf.get_height()//2))

        if self.feedback_timer > 0:
            fb_surf = self.font_large.render(self.feedback_msg, True, self.feedback_color)
            surface.blit(fb_surf, (DISPLAY_WIDTH//2 - fb_surf.get_width()//2, DISPLAY_HEIGHT//2 - fb_surf.get_height()//2 + 100))
            if self.feedback_color == RED:
                flash = pygame.Surface((DISPLAY_WIDTH, DISPLAY_HEIGHT))
                flash.set_alpha(30)
                flash.fill(RED)
                surface.blit(flash, (0, 0))
            elif self.feedback_color == GREEN:
                flash = pygame.Surface((DISPLAY_WIDTH, DISPLAY_HEIGHT))
                flash.set_alpha(30)
                flash.fill(GREEN)
                surface.blit(flash, (0, 0))
