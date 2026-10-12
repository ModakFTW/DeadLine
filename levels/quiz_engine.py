import json
import os
import pygame
from settings import (
    SCREEN_WIDTH, SCREEN_HEIGHT, COLOR_WHITE, COLOR_BLACK,
    COLOR_DARK_GRAY, COLOR_LIGHT_GRAY, COLOR_GREEN, COLOR_RED,
    COLOR_BLUE, COLOR_YELLOW
)

class QuizEngine:
    """Renders and manages interactive 4-option quiz rounds."""
    def __init__(self, questions: list[dict], level_id: int, game_state: dict):
        self.questions = questions
        self.level_id = level_id
        self.game_state = game_state
        self.current_q_idx = 0
        self.selected_option = -1
        self.feedback_timer = 0
        self.is_correct = False
        self.completed = False
        self.score = 0

        # UI Layout
        self.font_q = pygame.font.SysFont("segoeui, arial", 32, bold=True)
        self.font_opt = pygame.font.SysFont("segoeui, arial", 26)
        self.font_info = pygame.font.SysFont("segoeui, arial", 22)

    @classmethod
    def from_subject_file(cls, filepath: str, round_key: str, level_id: int, game_state: dict):
        if not os.path.isabs(filepath):
            base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            filepath = os.path.join(base_dir, filepath)

        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)
        return cls(data.get(round_key, []), level_id, game_state)

    def handle_input(self):
        if self.feedback_timer > 0 or self.completed:
            return

        # Key shortcuts: 1, 2, 3, 4
        keys = pygame.key.get_pressed()
        key_map = [pygame.K_1, pygame.K_2, pygame.K_3, pygame.K_4]
        for opt_idx, k in enumerate(key_map):
            if keys[k]:
                self._submit_answer(opt_idx)
                return

        # Mouse clicks
        mouse_pressed = pygame.mouse.get_pressed()
        if mouse_pressed[0]:
            mx, my = pygame.mouse.get_pos()
            for opt_idx, rect in enumerate(self._get_option_rects()):
                if rect.collidepoint(mx, my):
                    self._submit_answer(opt_idx)
                    return

    def _submit_answer(self, opt_idx: int):
        q = self.questions[self.current_q_idx]
        self.selected_option = opt_idx
        self.is_correct = (opt_idx == q["correct"])
        if self.is_correct:
            self.score += 1

        # Store player's answer in shared game_state
        if "player_answers" not in self.game_state:
            self.game_state["player_answers"] = {}

        if self.level_id == 1:
            if "level1_answers" not in self.game_state:
                self.game_state["level1_answers"] = []
            self.game_state["level1_answers"].append({
                "question": q["question"],
                "chosen_text": q["options"][opt_idx],
                "chosen_idx": opt_idx,
                "correct_text": q["options"][q["correct"]],
                "is_correct": self.is_correct
            })

        self.game_state["player_answers"][f"L{self.level_id}_Q{self.current_q_idx}"] = {
            "chosen": opt_idx,
            "correct": q["correct"]
        }

        self.feedback_timer = 50  # ~0.8s display delay

    def update(self):
        if self.completed:
            return

        if self.feedback_timer > 0:
            self.feedback_timer -= 1
            if self.feedback_timer == 0:
                self.current_q_idx += 1
                self.selected_option = -1
                if self.current_q_idx >= len(self.questions):
                    self.completed = True

    def _get_option_rects(self):
        rects = []
        start_y = 260
        box_w, box_h = 800, 60
        start_x = (SCREEN_WIDTH - box_w) // 2
        for i in range(4):
            rects.append(pygame.Rect(start_x, start_y + i * 85, box_w, box_h))
        return rects

    def draw(self, surface: pygame.Surface):
        surface.fill(COLOR_DARK_GRAY)

        if self.completed:
            txt = self.font_q.render(f"Quiz Complete! Score: {self.score}/{len(self.questions)}", True, COLOR_YELLOW)
            surface.blit(txt, ((SCREEN_WIDTH - txt.get_width()) // 2, SCREEN_HEIGHT // 2 - 30))
            return

        q = self.questions[self.current_q_idx]

        # Header info
        header = self.font_info.render(
            f"Level {self.level_id} Revision Quiz — Question {self.current_q_idx + 1} of {len(self.questions)}",
            True, COLOR_LIGHT_GRAY
        )
        surface.blit(header, (60, 40))

        # Question card
        q_card = pygame.Rect(60, 90, SCREEN_WIDTH - 120, 120)
        pygame.draw.rect(surface, (25, 25, 30), q_card, border_radius=8)
        pygame.draw.rect(surface, COLOR_BLUE, q_card, 2, border_radius=8)

        q_surf = self.font_q.render(q["question"], True, COLOR_WHITE)
        surface.blit(q_surf, (q_card.x + 30, q_card.y + 40))

        # 4 Options
        rects = self._get_option_rects()
        for idx, (rect, opt_text) in enumerate(zip(rects, q["options"])):
            bg_color = (45, 48, 56)
            border_color = COLOR_LIGHT_GRAY

            if self.feedback_timer > 0:
                if idx == q["correct"]:
                    bg_color = COLOR_GREEN
                elif idx == self.selected_option:
                    bg_color = COLOR_RED
            else:
                mx, my = pygame.mouse.get_pos()
                if rect.collidepoint(mx, my):
                    bg_color = (60, 70, 90)

            pygame.draw.rect(surface, bg_color, rect, border_radius=6)
            pygame.draw.rect(surface, border_color, rect, 2, border_radius=6)

            badge = self.font_opt.render(f"{idx + 1}.", True, COLOR_YELLOW)
            surface.blit(badge, (rect.x + 18, rect.y + 14))

            txt_surf = self.font_opt.render(opt_text, True, COLOR_WHITE)
            surface.blit(txt_surf, (rect.x + 60, rect.y + 14))
