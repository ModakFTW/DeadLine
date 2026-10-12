"""deadline_quiz.py - Standalone playable MVP runner for DEADLINE Adaptive Learning Game."""
import sys
import time
import pygame
from typing import Optional

from adaptive_quiz.questions import QUESTIONS, validate_questions
from adaptive_quiz.engine import AdaptiveQuizEngine
from text_utils import draw_wrapped_text

# ── Window & Color Configuration ──
WINDOW_WIDTH = 960
WINDOW_HEIGHT = 640
FPS = 60
TITLE = "DEADLINE — Adaptive Learning"

# Palette
BG_DARK = (18, 22, 32)
CARD_BG = (28, 34, 48)
CARD_BORDER = (55, 70, 95)
WHITE = (245, 245, 250)
GOLD = (245, 200, 60)
GREEN = (45, 195, 105)
GREEN_DARK = (20, 80, 45)
RED = (235, 75, 75)
RED_DARK = (90, 25, 25)
YELLOW = (245, 180, 40)
BLUE = (60, 140, 240)
LIGHT_GRAY = (180, 190, 210)
DARK_GRAY = (40, 48, 65)


class DeadlineQuizApp:
    def __init__(self):
        pygame.init()
        pygame.font.init()

        validate_questions(QUESTIONS)
        self.engine = AdaptiveQuizEngine(QUESTIONS, start_level=1)

        self.screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
        pygame.display.set_caption(TITLE)
        self.clock = pygame.time.Clock()
        self.running = True

        # Fonts
        self.font_title = pygame.font.SysFont("segoeui, arial", 28, bold=True)
        self.font_header = pygame.font.SysFont("segoeui, arial", 18, bold=True)
        self.font_question = pygame.font.SysFont("segoeui, arial", 24, bold=True)
        self.font_option = pygame.font.SysFont("segoeui, arial", 20)
        self.font_feedback = pygame.font.SysFont("segoeui, arial", 22, bold=True)
        self.font_explanation = pygame.font.SysFont("segoeui, arial", 17)
        self.font_results = pygame.font.SysFont("segoeui, arial", 22)
        self.font_results_title = pygame.font.SysFont("segoeui, arial", 34, bold=True)

        # Session state
        self.state = "QUESTION"  # "QUESTION", "FEEDBACK", "RESULTS"
        self.question_start_time: float = 0.0
        self.time_remaining: float = 15.0

        # Feedback state
        self.feedback_text: str = ""
        self.feedback_color: tuple = WHITE
        self.feedback_start_time: float = 0.0
        self.feedback_duration: float = 2.2  # seconds
        self.selected_option_index: int = -1
        self.correct_option_index: int = -1

        # Interactive rects
        self.option_rects: list[pygame.Rect] = []
        self.restart_btn_rect = pygame.Rect(WINDOW_WIDTH // 2 - 140, 520, 280, 52)

        # Advance to first question
        self._load_next_question()

    def _load_next_question(self):
        q = self.engine.get_next_question()
        if q is None:
            self.state = "RESULTS"
            return

        self.state = "QUESTION"
        self.selected_option_index = -1
        self.correct_option_index = q["answer"]
        self.question_start_time = time.time()
        self.time_remaining = self.engine.QUESTION_TIME

    def run(self):
        while self.running:
            self.clock.tick(FPS)
            events = pygame.event.get()

            for event in events:
                if event.type == pygame.QUIT:
                    self.running = False
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        self.running = False
                    elif self.state == "RESULTS" and event.key == pygame.K_r:
                        self._restart_session()
                    elif self.state == "QUESTION":
                        # Keyboard shortcuts 1..4
                        if event.key in (pygame.K_1, pygame.K_KP1):
                            self._submit_answer(0)
                        elif event.key in (pygame.K_2, pygame.K_KP2):
                            self._submit_answer(1)
                        elif event.key in (pygame.K_3, pygame.K_KP3):
                            self._submit_answer(2)
                        elif event.key in (pygame.K_4, pygame.K_KP4):
                            self._submit_answer(3)

                elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    if self.state == "QUESTION":
                        for idx, rect in enumerate(self.option_rects):
                            if rect.collidepoint(event.pos):
                                self._submit_answer(idx)
                                break
                    elif self.state == "RESULTS":
                        if self.restart_btn_rect.collidepoint(event.pos):
                            self._restart_session()

            self._update()
            self._draw()
            pygame.display.flip()

        pygame.quit()
        sys.exit()

    def _submit_answer(self, option_idx: int):
        if self.state != "QUESTION":
            return  # Prevent multiple answers from double-clicks

        self.selected_option_index = option_idx
        is_correct, pts, fb = self.engine.submit_answer(option_idx, self.time_remaining)

        self.feedback_text = fb
        self.feedback_color = GREEN if is_correct else RED
        self.feedback_start_time = time.time()
        self.state = "FEEDBACK"

    def _handle_timeout(self):
        if self.state != "QUESTION":
            return

        self.selected_option_index = -1
        _, _, fb = self.engine.handle_timeout()
        self.feedback_text = fb
        self.feedback_color = YELLOW
        self.feedback_start_time = time.time()
        self.state = "FEEDBACK"

    def _restart_session(self):
        self.engine.reset()
        self._load_next_question()

    def _update(self):
        now = time.time()

        if self.state == "QUESTION":
            elapsed = now - self.question_start_time
            self.time_remaining = max(0.0, self.engine.QUESTION_TIME - elapsed)
            if self.time_remaining <= 0.0:
                self._handle_timeout()

        elif self.state == "FEEDBACK":
            if now - self.feedback_start_time >= self.feedback_duration:
                if self.engine.is_finished():
                    self.state = "RESULTS"
                else:
                    self._load_next_question()

    # ── Rendering ──

    def _draw(self):
        self.screen.fill(BG_DARK)

        if self.state in ("QUESTION", "FEEDBACK"):
            self._draw_hud()
            self._draw_question_card()
            self._draw_options()
            if self.state == "FEEDBACK":
                self._draw_feedback_overlay()
        elif self.state == "RESULTS":
            self._draw_results()

    def _draw_hud(self):
        # Header bar
        header_y = 18
        # App Title
        t_surf = self.font_title.render("DEADLINE", True, GOLD)
        self.screen.blit(t_surf, (30, header_y))

        # Progress (Question X of 10)
        curr_q = min(10, self.engine.questions_answered_count + (1 if self.state == "QUESTION" else 0))
        prog_text = f"Question: {curr_q} / {self.engine.TOTAL_QUESTIONS}"
        p_surf = self.font_header.render(prog_text, True, WHITE)
        self.screen.blit(p_surf, (220, header_y + 8))

        # Difficulty Tier
        tier_names = {1: "Level 1 (Easy)", 2: "Level 2 (Medium)", 3: "Level 3 (Hard)"}
        tier_colors = {1: GREEN, 2: YELLOW, 3: RED}
        tier_text = f"Difficulty: {tier_names.get(self.engine.current_level, 'Level 1')}"
        tier_color = tier_colors.get(self.engine.current_level, WHITE)
        d_surf = self.font_header.render(tier_text, True, tier_color)
        self.screen.blit(d_surf, (440, header_y + 8))

        # Score
        s_text = f"Score: {self.engine.score}"
        s_surf = self.font_header.render(s_text, True, GOLD)
        self.screen.blit(s_surf, (WINDOW_WIDTH - s_surf.get_width() - 30, header_y + 8))

        # ── 15s Countdown Timer Bar ──
        bar_x = 30
        bar_y = 65
        bar_w = WINDOW_WIDTH - 60
        bar_h = 10

        # Background track
        pygame.draw.rect(self.screen, DARK_GRAY, (bar_x, bar_y, bar_w, bar_h), border_radius=5)

        # Timer fill ratio
        ratio = max(0.0, min(1.0, self.time_remaining / self.engine.QUESTION_TIME))
        fill_w = int(bar_w * ratio)

        # Color changes based on urgency (< 5s yellow, < 3s flashing red)
        if self.time_remaining < 3.0:
            flash = (int(time.time() * 6) % 2 == 0)
            t_color = RED if flash else (255, 140, 140)
        elif self.time_remaining < 5.0:
            t_color = YELLOW
        else:
            t_color = GREEN

        if fill_w > 0:
            pygame.draw.rect(self.screen, t_color, (bar_x, bar_y, fill_w, bar_h), border_radius=5)

        # Seconds label
        time_lbl = f"{self.time_remaining:.1f}s"
        tl_surf = self.font_header.render(time_lbl, True, t_color)
        self.screen.blit(tl_surf, (WINDOW_WIDTH - tl_surf.get_width() - 30, bar_y + 14))

    def _draw_question_card(self):
        q = self.engine.current_question
        if not q:
            return

        card_rect = pygame.Rect(30, 105, WINDOW_WIDTH - 60, 130)
        pygame.draw.rect(self.screen, CARD_BG, card_rect, border_radius=12)
        pygame.draw.rect(self.screen, CARD_BORDER, card_rect, 2, border_radius=12)

        draw_wrapped_text(
            surface=self.screen,
            text=q["question"],
            font=self.font_question,
            color=WHITE,
            max_width=card_rect.width - 50,
            center_x=card_rect.centerx,
            center_y=card_rect.centery,
            align="center"
        )

    def _draw_options(self):
        q = self.engine.current_question
        if not q:
            return

        self.option_rects = []
        card_w = 425
        card_h = 80
        gap_x = 50
        gap_y = 20
        start_x = (WINDOW_WIDTH - (card_w * 2 + gap_x)) // 2
        start_y = 265

        mouse_pos = pygame.mouse.get_pos()
        labels = ["1", "2", "3", "4"]

        for i, opt_text in enumerate(q["options"]):
            row = i // 2
            col = i % 2
            rx = start_x + col * (card_w + gap_x)
            ry = start_y + row * (card_h + gap_y)
            rect = pygame.Rect(rx, ry, card_w, card_h)
            self.option_rects.append(rect)

            hovered = rect.collidepoint(mouse_pos) and (self.state == "QUESTION")

            # Default styling
            bg = (38, 46, 64) if hovered else (28, 34, 48)
            border = (90, 150, 240) if hovered else CARD_BORDER
            text_c = WHITE

            # State styling during feedback
            if self.state == "FEEDBACK":
                if i == self.correct_option_index:
                    bg = GREEN_DARK
                    border = GREEN
                    text_c = (220, 255, 230)
                elif i == self.selected_option_index and i != self.correct_option_index:
                    bg = RED_DARK
                    border = RED
                    text_c = (255, 210, 210)

            pygame.draw.rect(self.screen, bg, rect, border_radius=10)
            pygame.draw.rect(self.screen, border, rect, 2 if not hovered else 3, border_radius=10)


            # Key badge
            badge_r = pygame.Rect(rect.x + 14, rect.centery - 18, 36, 36)
            pygame.draw.rect(self.screen, (45, 55, 75), badge_r, border_radius=6)
            b_lbl = self.font_header.render(labels[i], True, GOLD)
            self.screen.blit(b_lbl, (badge_r.centerx - b_lbl.get_width() // 2, badge_r.centery - b_lbl.get_height() // 2))

            # Option text (wrapped cleanly)
            draw_wrapped_text(
                surface=self.screen,
                text=opt_text,
                font=self.font_option,
                color=text_c,
                max_width=card_w - 75,
                left_x=rect.x + 62,
                center_y=rect.centery,
                align="left"
            )

    def _draw_feedback_overlay(self):
        q = self.engine.current_question
        if not q:
            return

        box_rect = pygame.Rect(30, 465, WINDOW_WIDTH - 60, 145)
        pygame.draw.rect(self.screen, (22, 28, 40), box_rect, border_radius=10)
        pygame.draw.rect(self.screen, self.feedback_color, box_rect, 2, border_radius=10)

        # Status text
        fb_s = self.font_feedback.render(self.feedback_text, True, self.feedback_color)
        self.screen.blit(fb_s, (box_rect.centerx - fb_s.get_width() // 2, box_rect.y + 16))

        # Explanation text
        expl = f"Explanation: {q.get('explanation', '')}"
        draw_wrapped_text(
            surface=self.screen,
            text=expl,
            font=self.font_explanation,
            color=LIGHT_GRAY,
            max_width=box_rect.width - 40,
            center_x=box_rect.centerx,
            top_y=box_rect.y + 58,
            align="center"
        )

    def _draw_results(self):
        summary = self.engine.get_summary()

        # Title
        t = self.font_results_title.render("SESSION COMPLETE", True, GOLD)
        self.screen.blit(t, (WINDOW_WIDTH // 2 - t.get_width() // 2, 45))

        # Container Card
        card = pygame.Rect(WINDOW_WIDTH // 2 - 320, 110, 640, 380)
        pygame.draw.rect(self.screen, CARD_BG, card, border_radius=14)
        pygame.draw.rect(self.screen, CARD_BORDER, card, 2, border_radius=14)

        # Results metrics list
        tier_names = {1: "Level 1 (Easy)", 2: "Level 2 (Medium)", 3: "Level 3 (Hard)"}
        metrics = [
            ("Final Score", f"{summary['score']} pts", GOLD),
            ("Correct Answers", f"{summary['correct_count']} / {summary['total_questions']}", GREEN),
            ("Incorrect Answers", f"{summary['incorrect_count']}", RED),
            ("Timeouts", f"{summary['timeout_count']}", YELLOW),
            ("Accuracy (Excluding Timeouts)", f"{summary['accuracy']:.1f}%", BLUE),
            ("Final Difficulty Level", f"{tier_names.get(summary['final_level'], 'Level 1')}", WHITE),
        ]

        start_y = card.y + 30
        for label, val, val_color in metrics:
            lbl_s = self.font_results.render(label, True, LIGHT_GRAY)
            val_s = self.font_results.render(val, True, val_color)

            self.screen.blit(lbl_s, (card.x + 40, start_y))
            self.screen.blit(val_s, (card.right - val_s.get_width() - 40, start_y))
            start_y += 50

        # Restart Button
        mouse_pos = pygame.mouse.get_pos()
        hovered = self.restart_btn_rect.collidepoint(mouse_pos)
        btn_bg = (40, 130, 70) if hovered else (30, 105, 55)
        pygame.draw.rect(self.screen, btn_bg, self.restart_btn_rect, border_radius=8)
        pygame.draw.rect(self.screen, GREEN, self.restart_btn_rect, 2, border_radius=8)

        btn_t = self.font_header.render("PLAY AGAIN [R]", True, WHITE)
        self.screen.blit(btn_t, (self.restart_btn_rect.centerx - btn_t.get_width() // 2, self.restart_btn_rect.centery - btn_t.get_height() // 2))

        # Quit note
        esc_t = self.font_explanation.render("Press [Esc] to quit cleanly", True, (140, 150, 170))
        self.screen.blit(esc_t, (WINDOW_WIDTH // 2 - esc_t.get_width() // 2, 590))


if __name__ == "__main__":
    app = DeadlineQuizApp()
    app.run()
