# levels/level_memory.py — Level 1: Interactive Mixed-Domain Diagnostic Quiz (Establishes Knowledge Score)
import pygame
import random
import time
from levels.base_level import BaseLevel
from settings import (
    DISPLAY_WIDTH, DISPLAY_HEIGHT, CHALKBOARD_GREEN, CHALK_WHITE,
    WHITE, BLACK, RED, GREEN, YELLOW, BLUE, GOLD, DARK_GRAY, LIGHT_GRAY, FPS
)
from text_utils import draw_wrapped_text



class LevelMemory(BaseLevel):
    """
    Level 1 — Diagnostic Mixed-Domain Quiz.
    Presents questions (Question 1, Question 2, etc.) from Networks, Operating Systems, and DBMS.
    Players answer using keys A/B/C/D, 1/2/3/4, or mouse click.
    Score directly establishes Knowledge Score (0 to 10) driving Level 2 AI difficulty.
    """

    def __init__(self, game_state) -> None:
        self.game_state = game_state
        pool = list(self.game_state.quiz)

        # Fallback questions if subject quiz is not provided
        if not pool:
            pool = [
                {
                    "question": "Which protocol provides reliable, connection-oriented packet delivery?",
                    "options": ["UDP", "TCP", "IP", "ICMP"],
                    "correct": 1,
                    "term": "TCP",
                    "domain": "Networks"
                }
            ]

        # Shuffle and pick 5 random questions so every play session is distinct.
        # random.sample gives a fresh non-repeating subset each run, and per-question
        # option shuffling randomizes the correct-answer position (A/B/C/D).
        num_questions = min(5, len(pool))
        picked = random.sample(pool, num_questions) if len(pool) > num_questions else list(pool)
        random.shuffle(picked)
        self.questions = []
        for q in picked:
            q_copy = {
                "question": q["question"],
                "options": list(q["options"]),
                "correct": q["correct"],
            }
            # Preserve extra metadata (term/domain) if present
            if "term" in q:
                q_copy["term"] = q["term"]
            if "domain" in q:
                q_copy["domain"] = q["domain"]
            # Shuffle option order so the answer slot varies run-to-run
            correct_text = q_copy["options"][q_copy["correct"]]
            random.shuffle(q_copy["options"])
            q_copy["correct"] = q_copy["options"].index(correct_text)
            self.questions.append(q_copy)


        self.total_questions = len(self.questions)
        self.current_index = 0
        self.correct_count = 0
        self.selected_option = -1
        self.answer_revealed = False
        self.reveal_timer = 0
        self.quiz_finished = False

        # Visuals
        self.particles = [
            {
                "x": random.randint(0, DISPLAY_WIDTH),
                "y": random.randint(0, DISPLAY_HEIGHT),
                "speed": random.uniform(0.3, 1.2),
                "size": random.randint(1, 3)
            }
            for _ in range(35)
        ]

        # Fonts
        self.font_title = pygame.font.SysFont("segoeui, arial, sans-serif", 36, bold=True)
        self.font_q_num = pygame.font.SysFont("segoeui, arial, sans-serif", 20, bold=True)
        self.font_question = pygame.font.SysFont("segoeui, arial, sans-serif", 24, bold=True)
        self.font_option = pygame.font.SysFont("segoeui, arial, sans-serif", 21)
        self.font_feedback = pygame.font.SysFont("segoeui, arial, sans-serif", 26, bold=True)
        self.font_summary = pygame.font.SysFont("segoeui, arial, sans-serif", 20)
        self.font_domain = pygame.font.SysFont("segoeui, arial, sans-serif", 15, bold=True)

        # Option Card Rects (calculated on draw/mouse check)
        self.option_rects: list[pygame.Rect] = []
        self.mouse_pos = (0, 0)
        self.unlocked_terms: list[str] = []

    def handle_events(self, events: list[pygame.event.Event]) -> str | None:
        for event in events:
            if event.type == pygame.MOUSEMOTION:
                self.mouse_pos = event.pos

            elif event.type == pygame.KEYDOWN:
                if self.quiz_finished:
                    if event.key in (pygame.K_RETURN, pygame.K_SPACE):
                        return "platformer"
                    elif event.key == pygame.K_ESCAPE:
                        return "platformer"
                else:
                    if not self.answer_revealed:
                        if event.key in (pygame.K_a, pygame.K_1):
                            self._choose_option(0)
                        elif event.key in (pygame.K_b, pygame.K_2):
                            self._choose_option(1)
                        elif event.key in (pygame.K_c, pygame.K_3):
                            self._choose_option(2)
                        elif event.key in (pygame.K_d, pygame.K_4):
                            self._choose_option(3)

            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if self.quiz_finished:
                    return "platformer"
                elif not self.answer_revealed:
                    for i, rect in enumerate(self.option_rects):
                        if rect.collidepoint(event.pos):
                            self._choose_option(i)
                            break
        return None

    def _choose_option(self, option_index: int) -> None:
        q = self.questions[self.current_index]
        if option_index < 0 or option_index >= len(q["options"]):
            return

        self.selected_option = option_index
        self.answer_revealed = True
        self.reveal_timer = 70  # ~1.15 seconds delay to see feedback

        is_correct = (option_index == q["correct"])
        if is_correct:
            self.correct_count += 1
            term = q.get("term", q["options"][option_index])
            if term not in self.unlocked_terms:
                self.unlocked_terms.append(term)

    def update(self) -> str | None:
        # Floating dust particles
        for p in self.particles:
            p["y"] += p["speed"]
            if p["y"] > DISPLAY_HEIGHT:
                p["y"] = -5
                p["x"] = random.randint(0, DISPLAY_WIDTH)

        if self.answer_revealed and not self.quiz_finished:
            self.reveal_timer -= 1
            if self.reveal_timer <= 0:
                self.current_index += 1
                if self.current_index >= self.total_questions:
                    self._finish_quiz()
                else:
                    self.selected_option = -1
                    self.answer_revealed = False

        return None

    def _finish_quiz(self) -> None:
        """Calculate Knowledge Score and update GameState."""
        self.quiz_finished = True
        score_ratio = self.correct_count / max(1, self.total_questions)
        self.game_state.knowledge_score = int(round(score_ratio * 10))
        # Ensure words_remembered and game_state.words match the 5 questions presented
        question_terms = [q.get("term", q["options"][q["correct"]]) for q in self.questions]
        self.game_state.words = list(question_terms)
        self.game_state.words_remembered = list(self.unlocked_terms)

    def draw(self, surface: pygame.Surface) -> None:
        surface.fill(CHALKBOARD_GREEN)

        # Draw chalk particles
        for p in self.particles:
            pygame.draw.circle(surface, CHALK_WHITE, (int(p["x"]), int(p["y"])), p["size"])

        # Top Wooden Chalkboard Border
        pygame.draw.rect(surface, (105, 68, 38), (0, 0, DISPLAY_WIDTH, 14))
        pygame.draw.rect(surface, (75, 45, 22), (0, 14, DISPLAY_WIDTH, 4))
        # Bottom Wooden Tray
        pygame.draw.rect(surface, (105, 68, 38), (0, DISPLAY_HEIGHT - 30, DISPLAY_WIDTH, 30))
        pygame.draw.rect(surface, (75, 45, 22), (0, DISPLAY_HEIGHT - 32, DISPLAY_WIDTH, 4))

        if self.quiz_finished:
            self._draw_summary(surface)
        else:
            self._draw_quiz(surface)

    def _draw_quiz(self, surface: pygame.Surface) -> None:
        q = self.questions[self.current_index]

        # ── Header ──
        subj_name = self.game_state.subject_name or "GENERAL KNOWLEDGE"
        subj_title = f"{subj_name.upper()} EVALUATION"
        title_s = self.font_title.render(subj_title, True, GOLD)
        surface.blit(title_s, (DISPLAY_WIDTH // 2 - title_s.get_width() // 2, 28))

        # Domain badge
        domain = q.get("domain", subj_name)
        domain_colors = {
            "Networks": (40, 110, 190),
            "Operating Systems": (180, 80, 40),
            "Databases": (40, 140, 90),
            "General Knowledge": (40, 120, 160)
        }
        badge_color = domain_colors.get(domain, (60, 90, 120))
        domain_text = f"SUBJECT: {domain.upper()}"

        d_surf = self.font_domain.render(domain_text, True, WHITE)
        d_badge = pygame.Rect(DISPLAY_WIDTH // 2 - d_surf.get_width() // 2 - 12, 72, d_surf.get_width() + 24, 24)
        pygame.draw.rect(surface, badge_color, d_badge, border_radius=12)
        pygame.draw.rect(surface, (220, 235, 255), d_badge, 1, border_radius=12)
        surface.blit(d_surf, (d_badge.centerx - d_surf.get_width() // 2, d_badge.centery - d_surf.get_height() // 2))

        q_num_text = f"QUESTION {self.current_index + 1} OF {self.total_questions}"
        q_num_s = self.font_q_num.render(q_num_text, True, (190, 240, 210))
        surface.blit(q_num_s, (DISPLAY_WIDTH // 2 - q_num_s.get_width() // 2, 102))

        # Progress bar
        bar_w = 520
        bar_h = 10
        bar_x = DISPLAY_WIDTH // 2 - bar_w // 2
        bar_y = 130
        pygame.draw.rect(surface, (20, 48, 32), (bar_x, bar_y, bar_w, bar_h), border_radius=5)
        fill_w = int(bar_w * ((self.current_index) / self.total_questions))
        if fill_w > 0:
            pygame.draw.rect(surface, (60, 210, 120), (bar_x, bar_y, fill_w, bar_h), border_radius=5)
        pygame.draw.rect(surface, (140, 190, 160), (bar_x, bar_y, bar_w, bar_h), 1, border_radius=5)

        # ── Question Box ──
        q_box = pygame.Rect(DISPLAY_WIDTH // 2 - 490, 155, 980, 115)
        # Shadow
        pygame.draw.rect(surface, (15, 38, 25), (q_box.x + 6, q_box.y + 6, q_box.w, q_box.h), border_radius=12)
        # Card
        pygame.draw.rect(surface, (245, 245, 235), q_box, border_radius=12)
        pygame.draw.rect(surface, (200, 195, 175), q_box, 2, border_radius=12)

        # Render question text (wrapped cleanly using draw_wrapped_text)
        q_text = q["question"]
        draw_wrapped_text(
            surface,
            q_text,
            self.font_question,
            (25, 25, 35),
            max_width=q_box.w - 60,
            center_x=q_box.centerx,
            center_y=q_box.centery,
            align="center"
        )

        # ── Options Cards ──

        self.option_rects = []
        card_w = 470
        card_h = 74
        gap_x = 40
        gap_y = 18
        start_x = DISPLAY_WIDTH // 2 - card_w - gap_x // 2
        start_y = 295

        letters = ["A", "B", "C", "D"]
        for i, opt in enumerate(q["options"]):
            row = i // 2
            col = i % 2
            x = start_x + col * (card_w + gap_x)
            y = start_y + row * (card_h + gap_y)
            rect = pygame.Rect(x, y, card_w, card_h)
            self.option_rects.append(rect)

            hovered = rect.collidepoint(self.mouse_pos) and not self.answer_revealed

            # Determine colors based on state
            bg_color = (25, 30, 42)
            border_color = (70, 90, 120)
            text_color = WHITE
            letter_bg = (40, 50, 70)

            if self.answer_revealed:
                if i == q["correct"]:
                    bg_color = (25, 80, 45)
                    border_color = (60, 220, 110)
                    letter_bg = (40, 130, 70)
                    text_color = (220, 255, 230)
                elif i == self.selected_option and i != q["correct"]:
                    bg_color = (80, 30, 30)
                    border_color = (240, 70, 70)
                    letter_bg = (130, 45, 45)
                    text_color = (255, 210, 210)
            elif hovered:
                bg_color = (40, 55, 80)
                border_color = (100, 180, 255)
                letter_bg = (60, 100, 160)

            # Card Shadow
            pygame.draw.rect(surface, (12, 28, 18), (rect.x + 4, rect.y + 4, rect.w, rect.h), border_radius=10)
            # Card Base
            pygame.draw.rect(surface, bg_color, rect, border_radius=10)
            pygame.draw.rect(surface, border_color, rect, 2 if not (hovered or self.answer_revealed) else 3, border_radius=10)

            # Option Letter badge
            badge_r = pygame.Rect(rect.x + 14, rect.centery - 20, 40, 40)
            pygame.draw.rect(surface, letter_bg, badge_r, border_radius=8)
            lbl = self.font_q_num.render(letters[i], True, WHITE)
            surface.blit(lbl, (badge_r.centerx - lbl.get_width() // 2, badge_r.centery - lbl.get_height() // 2))

            # Option Text
            draw_wrapped_text(
                surface,
                opt,
                self.font_option,
                text_color,
                max_width=card_w - 82,
                left_x=rect.x + 68,
                center_y=rect.centery,
                align="left"
            )

        # ── Instant Feedback Banner ──

        if self.answer_revealed:
            is_correct = (self.selected_option == q["correct"])
            fb_text = "CORRECT!" if is_correct else f"INCORRECT — Correct Answer: {q['options'][q['correct']]}"
            fb_color = GREEN if is_correct else RED
            fb_s = self.font_feedback.render(fb_text, True, fb_color)
            surface.blit(fb_s, (DISPLAY_WIDTH // 2 - fb_s.get_width() // 2, 492))

            term_hint = f"Key Concept: {q.get('term', q['options'][q['correct']])} (Save to memory for Cage & Final Gate!)"
            th_s = self.font_summary.render(term_hint, True, GOLD)
            surface.blit(th_s, (DISPLAY_WIDTH // 2 - th_s.get_width() // 2, 532))
        else:
            hint = self.font_summary.render("Press A, B, C, D (or 1, 2, 3, 4) — or click the card with your mouse", True, (190, 220, 200))
            surface.blit(hint, (DISPLAY_WIDTH // 2 - hint.get_width() // 2, 510))

    def _draw_summary(self, surface: pygame.Surface) -> None:
        """Draws end-of-quiz score card and AI difficulty tier mapping."""
        t = self.font_title.render("DIAGNOSTIC QUIZ COMPLETE!", True, (60, 220, 120))
        surface.blit(t, (DISPLAY_WIDTH // 2 - t.get_width() // 2, 45))

        # Card container
        card = pygame.Rect(DISPLAY_WIDTH // 2 - 420, 105, 840, 500)
        pygame.draw.rect(surface, (15, 25, 38), (card.x + 6, card.y + 6, card.w, card.h), border_radius=14)
        pygame.draw.rect(surface, (24, 34, 52), card, border_radius=14)
        pygame.draw.rect(surface, (65, 95, 140), card, 2, border_radius=14)

        # Score line
        pct = int((self.correct_count / max(1, self.total_questions)) * 100)
        score_str = f"You answered {self.correct_count} of {self.total_questions} questions correctly ({pct}%)"
        s_surf = self.font_question.render(score_str, True, WHITE)
        surface.blit(s_surf, (card.centerx - s_surf.get_width() // 2, card.y + 30))

        k_score = self.game_state.knowledge_score
        tier = self.game_state.get_difficulty_tier()
        tier_colors = {"easy": (70, 220, 110), "medium": (250, 200, 50), "hard": (240, 70, 70)}

        k_surf = self.font_question.render(f"Established Knowledge Score: {k_score} / 10", True, GOLD)
        surface.blit(k_surf, (card.centerx - k_surf.get_width() // 2, card.y + 70))

        tier_surf = self.font_question.render(f"AI Difficulty Level: {tier.upper()} TIER", True, tier_colors.get(tier, WHITE))
        surface.blit(tier_surf, (card.centerx - tier_surf.get_width() // 2, card.y + 110))

        # Divider
        pygame.draw.line(surface, (60, 80, 110), (card.x + 40, card.y + 155), (card.right - 40, card.y + 155), 1)

        # AI connection explanation
        lines = [
            "HOW THE AI ENGINE ADAPTS TO YOUR SCORE:",
            f"• Level 2 (The Platformer) Markov Chain will seed obstacles for the {tier.upper()} tier.",
            "• High Knowledge → Dense, challenging hazard combinations to test your reflexes.",
            "• Lower Knowledge → Moderate, accessible terrain with elevated metro platforms.",
            "• Your learned terms have been registered for Level 3 (The Cage) and Level 5 (Exam Gate)!",
        ]
        y_cursor = card.y + 175
        for line in lines:
            color = YELLOW if "HOW THE AI" in line else (200, 215, 235)
            f = self.font_q_num if "HOW THE AI" in line else self.font_summary
            surf = f.render(line, True, color)
            surface.blit(surf, (card.x + 45, y_cursor))
            y_cursor += 36

        # Call to action button
        btn = pygame.Rect(DISPLAY_WIDTH // 2 - 250, card.bottom - 72, 500, 52)
        pygame.draw.rect(surface, (40, 120, 60), btn, border_radius=8)
        pygame.draw.rect(surface, (80, 220, 120), btn, 2, border_radius=8)
        btn_text = self.font_question.render("START LEVEL 2: THE PLATFORMER »", True, WHITE)
        surface.blit(btn_text, (btn.centerx - btn_text.get_width() // 2, btn.centery - btn_text.get_height() // 2))

        hint = self.font_summary.render("Press ENTER, SPACE, or Click to Begin Running", True, (180, 210, 230))
        surface.blit(hint, (DISPLAY_WIDTH // 2 - hint.get_width() // 2, DISPLAY_HEIGHT - 38))
