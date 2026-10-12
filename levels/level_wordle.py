# levels/level_wordle.py — Level 5: The Exam Hall Terminal Wordle Puzzle
import random
import time
import pygame

from levels.base_level import BaseLevel
from game_state import GameState
import settings
import sprite_loader
import ai.wordle_engine as we


# Wordle Colors
TILE_EMPTY = (40, 48, 64)
TILE_BORDER = (80, 95, 125)
TILE_FILLED_BORDER = (160, 180, 210)
COLOR_GREEN = (60, 175, 95)
COLOR_YELLOW = (225, 180, 40)
COLOR_SLATE = (75, 82, 95)
TEXT_WHITE = (245, 245, 250)
KEY_DEFAULT = (55, 65, 85)


class LevelWordle(BaseLevel):
    """
    Level 5: The Exam Hall Terminal.
    Replaces the old recall typing test with a full Information-Theoretic Wordle.
    Features:
    - 6-attempt 5-letter grid with animations.
    - Full QWERTY keyboard with dynamic color tracking.
    - Live Shannon Entropy (Information Gain) telemetry meter.
    - AI Co-Pilot Hint button [Press H].
    """

    def __init__(self, game_state: GameState):
        self.game_state = game_state
        self.max_attempts = 6
        self.current_attempt = 0
        self.current_guess = ""
        self.guesses: list[str] = []
        self.patterns: list[tuple[int, ...]] = []
        self.game_over = False
        self.won = False
        self.win_timer = 0
        self.start_time = time.time()

        # Keyboard letter color statuses
        self.key_status: dict[str, int] = {}

        # ── Pick 5-Letter Secret Target ──
        # Find any 5-letter words among Level 1 remembered words
        gk_5_letters = [
            w.upper() for w in self.game_state.words
            if len(w) == 5 and w.isalpha()
        ]
        if gk_5_letters:
            self.target_word = random.choice(gk_5_letters)
        else:
            self.target_word = random.choice(we.GK_WORDLE_TARGETS)

        # Candidates pool for AI entropy tracking
        self.candidates = list(we.GK_WORDLE_TARGETS)
        if self.target_word not in self.candidates:
            self.candidates.append(self.target_word)

        # Telemetry & feedback
        self.last_entropy = 0.0
        self.last_eliminated = 0
        self.ai_hint = ""
        self.hints_used = 0
        self.max_hints = 1
        self.toast_msg = ""
        self.toast_timer = 0
        self.shake_row = -1
        self.shake_timer = 0

        # Assets
        self.bg = sprite_loader.load_background("bg_level5_gate.jpg", settings.DISPLAY_WIDTH, settings.DISPLAY_HEIGHT)

        # Fonts
        self.font_title = pygame.font.SysFont("impact, segoeui, arial", 34)
        self.font_sub = pygame.font.SysFont("segoeui, arial", 16)
        self.font_tile = pygame.font.SysFont("segoeui, arial, sans-serif", 32, bold=True)
        self.font_key = pygame.font.SysFont("segoeui, arial, sans-serif", 16, bold=True)
        self.font_ai = pygame.font.SysFont("segoeui, arial, sans-serif", 15, bold=True)
        self.font_toast = pygame.font.SysFont("segoeui, arial, sans-serif", 20, bold=True)

        # Key rects for mouse clicks
        self.key_rects: dict[str, pygame.Rect] = {}

    def handle_events(self, events: list[pygame.event.Event]) -> str | None:
        if self.won and self.win_timer > 90:
            return "win"
        if self.game_over and not self.won:
            for event in events:
                if event.type == pygame.KEYDOWN and event.key in (pygame.K_SPACE, pygame.K_RETURN, pygame.K_r):
                    return "game_over"

        for event in events:
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    return "game_over" if not self.won else "win"
                elif event.key == pygame.K_RETURN:
                    self._submit_guess()
                elif event.key == pygame.K_BACKSPACE:
                    if len(self.current_guess) > 0 and not self.game_over:
                        self.current_guess = self.current_guess[:-1]
                elif event.key == pygame.K_h:
                    self._request_ai_hint()
                else:
                    if len(self.current_guess) < 5 and not self.game_over:
                        char = event.unicode.upper()
                        if char.isalpha() and len(char) == 1:
                            self.current_guess += char

            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                mouse_pos = event.pos
                for key_char, rect in self.key_rects.items():
                    if rect.collidepoint(mouse_pos):
                        if key_char == "ENTER":
                            self._submit_guess()
                        elif key_char == "BACK":
                            if len(self.current_guess) > 0 and not self.game_over:
                                self.current_guess = self.current_guess[:-1]
                        elif key_char == "HINT":
                            self._request_ai_hint()
                        else:
                            if len(self.current_guess) < 5 and not self.game_over:
                                self.current_guess += key_char
                        break

        return None

    def _submit_guess(self) -> None:
        if self.game_over:
            return
        if len(self.current_guess) < 5:
            self._set_toast("WORD MUST BE 5 LETTERS!", (240, 80, 80))
            self.shake_row = self.current_attempt
            self.shake_timer = 15
            return

        guess = self.current_guess.upper()
        if guess not in we.ALLOWED_GUESSES and guess not in self.candidates:
            self._set_toast("NOT IN EXAM WORD LIST!", (240, 80, 80))
            self.shake_row = self.current_attempt
            self.shake_timer = 15
            return

        # Evaluate pattern
        pat = we.evaluate_guess(guess, self.target_word)
        self.guesses.append(guess)
        self.patterns.append(pat)

        # Update keyboard key colors (greens override yellows, etc.)
        for i, char in enumerate(guess):
            new_val = pat[i]
            cur_val = self.key_status.get(char, -1)
            if new_val > cur_val:
                self.key_status[char] = new_val

        # Information Theory Telemetry calculation
        initial_cand_count = len(self.candidates)
        ent = we.calculate_entropy(guess, self.candidates)
        self.candidates = we.filter_candidates(self.candidates, guess, pat)
        if self.target_word not in self.candidates:
            self.candidates.append(self.target_word)

        eliminated = max(0, initial_cand_count - len(self.candidates))
        self.last_entropy = ent
        self.last_eliminated = eliminated

        self.current_attempt += 1
        self.current_guess = ""

        # Check win or lose
        if guess == self.target_word:
            self.won = True
            self.game_over = True
            self.win_timer = 1
            self._set_toast("★ TERMINAL UNLOCKED! ACCESS GRANTED! ★", COLOR_GREEN)
        elif self.current_attempt >= self.max_attempts:
            self.game_over = True
            self._set_toast(f"EXAM FAILED! Word was: {self.target_word}", (240, 70, 70))

    def _request_ai_hint(self) -> None:
        if self.game_over:
            return
        if self.hints_used >= self.max_hints:
            self._set_toast("MAX 1 HINT PER EXAM!", (240, 160, 60))
            return
        if not self.candidates or len(self.candidates) <= 1:
            self._set_toast("NO CANDIDATES REMAINING!", (240, 160, 60))
            return

        # Find best exploration letter among unverified letters that provides high entropy
        guessed_letters = set("".join(self.guesses))
        target_remaining = set(self.target_word) - guessed_letters

        if target_remaining:
            # Pick a letter that actually appears in the secret word but hasn't been guessed yet
            hint_char = random.choice(sorted(list(target_remaining)))
            self.hints_used += 1
            self.ai_hint = f"Letter '{hint_char}' is in the word"
            self._set_toast(f"HINT: One of the secret letters is '{hint_char}'", (60, 210, 255))
        else:
            # All letters discovered, give position hint
            self.hints_used += 1
            self.ai_hint = f"Starts with '{self.target_word[0]}'"
            self._set_toast(f"HINT: The secret word begins with '{self.target_word[0]}'", (60, 210, 255))

    def _set_toast(self, msg: str, color: tuple) -> None:
        self.toast_msg = msg
        self.toast_color = color
        self.toast_timer = 90

    def update(self) -> str | None:
        if self.toast_timer > 0:
            self.toast_timer -= 1
        if self.shake_timer > 0:
            self.shake_timer -= 1

        if self.won:
            self.win_timer += 1
            if self.win_timer > 90:
                return "win"

        return None

    def draw(self, surface: pygame.Surface) -> None:
        # Background
        if self.bg:
            surface.blit(self.bg, (0, 0))
            # Semi-transparent terminal overlay
            overlay = pygame.Surface((settings.DISPLAY_WIDTH, settings.DISPLAY_HEIGHT), pygame.SRCALPHA)
            overlay.fill((12, 16, 24, 210))
            surface.blit(overlay, (0, 0))
        else:
            surface.fill((18, 22, 32))

        # ── Header ──
        title = self.font_title.render("FINAL EXAM TERMINAL: KNOWLEDGE CIPHER", True, settings.GOLD)
        surface.blit(title, (settings.DISPLAY_WIDTH // 2 - title.get_width() // 2, 14))

        sub = self.font_sub.render(
            "Crack the 5-letter General Knowledge keyword to submit your exam! (Information Theory Co-Pilot Active)",
            True, (200, 215, 235)
        )
        surface.blit(sub, (settings.DISPLAY_WIDTH // 2 - sub.get_width() // 2, 54))

        # ── Left / Side Telemetry Card (Shannon Information Theory) ──
        card_w = 310
        card_h = 420
        card_x = 70
        card_y = 100
        pygame.draw.rect(surface, (18, 24, 36), (card_x, card_y, card_w, card_h), border_radius=10)
        pygame.draw.rect(surface, (50, 70, 105), (card_x, card_y, card_w, card_h), 2, border_radius=10)

        ai_header = self.font_ai.render("SHANNON ENTROPY AI TELEMETRY", True, (60, 210, 255))
        surface.blit(ai_header, (card_x + 18, card_y + 16))
        pygame.draw.line(surface, (45, 60, 90), (card_x + 15, card_y + 40), (card_x + card_w - 15, card_y + 40), 1)

        lines = [
            f"Target Length: 5 Letters",
            f"Attempts Remaining: {self.max_attempts - self.current_attempt} / {self.max_attempts}",
            f"Active Candidates: {len(self.candidates)}",
            "",
            "LAST GUESS METRICS:",
            f"• Information Gain: {self.last_entropy:.2f} bits",
            f"• Eliminated Space: {self.last_eliminated} words",
            "",
            "AI CO-PILOT ASSISTANT:",
            f"Clue: {self.ai_hint if self.ai_hint else ('[Press H for 1 Letter Clue]' if self.hints_used < self.max_hints else '[No Hints Left]')}",
            "",
            "HOW THE AI WORKS:",
            "Calculates Shannon Entropy E[I]",
            "to maximize bit reduction across",
            "the 3^5 ternary pattern space."
        ]
        ty = card_y + 50
        for l in lines:
            c = (250, 215, 60) if "LAST GUESS" in l or "AI CO-PILOT" in l or "HOW THE" in l else (190, 210, 230)
            txt = self.font_sub.render(l, True, c)
            surface.blit(txt, (card_x + 18, ty))
            ty += 22

        # ── Center 5x6 Wordle Grid ──
        grid_start_x = settings.DISPLAY_WIDTH // 2 - 145
        grid_start_y = 90
        tile_size = 56
        gap = 8

        for row in range(self.max_attempts):
            shake_offset = 0
            if row == self.shake_row and self.shake_timer > 0:
                shake_offset = int((self.shake_timer % 4 - 2) * 3)

            for col in range(5):
                tx = grid_start_x + col * (tile_size + gap) + shake_offset
                ty = grid_start_y + row * (tile_size + gap)
                t_rect = pygame.Rect(tx, ty, tile_size, tile_size)

                # Determine tile color & letter
                if row < len(self.guesses):
                    letter = self.guesses[row][col]
                    pat_val = self.patterns[row][col]
                    if pat_val == we.COLOR_CORRECT:
                        bg_col = COLOR_GREEN
                    elif pat_val == we.COLOR_PRESENT:
                        bg_col = COLOR_YELLOW
                    else:
                        bg_col = COLOR_SLATE
                    border_col = bg_col
                else:
                    bg_col = TILE_EMPTY
                    if row == self.current_attempt and col < len(self.current_guess):
                        letter = self.current_guess[col]
                        border_col = TILE_FILLED_BORDER
                    else:
                        letter = ""
                        border_col = TILE_BORDER

                pygame.draw.rect(surface, bg_col, t_rect, border_radius=6)
                pygame.draw.rect(surface, border_col, t_rect, 2, border_radius=6)

                if letter:
                    l_surf = self.font_tile.render(letter, True, TEXT_WHITE)
                    surface.blit(l_surf, l_surf.get_rect(center=t_rect.center))

        # ── Interactive On-Screen QWERTY Keyboard ──
        self._draw_keyboard(surface, grid_start_y + 6 * (tile_size + gap) + 12)

        # ── Toast Message ──
        if self.toast_timer > 0:
            toast_surf = self.font_toast.render(self.toast_msg, True, getattr(self, "toast_color", TEXT_WHITE))
            tbox = pygame.Rect(settings.DISPLAY_WIDTH // 2 - toast_surf.get_width() // 2 - 16, 510, toast_surf.get_width() + 32, 40)
            pygame.draw.rect(surface, (15, 20, 30, 240), tbox, border_radius=8)
            pygame.draw.rect(surface, getattr(self, "toast_color", settings.GOLD), tbox, 2, border_radius=8)
            surface.blit(toast_surf, toast_surf.get_rect(center=tbox.center))

    def _draw_keyboard(self, surface: pygame.Surface, start_y: int) -> None:
        keyboard_rows = [
            ["Q", "W", "E", "R", "T", "Y", "U", "I", "O", "P"],
            ["A", "S", "D", "F", "G", "H", "J", "K", "L"],
            ["ENTER", "Z", "X", "C", "V", "B", "N", "M", "BACK", "HINT"]
        ]
        key_w = 44
        key_h = 42
        gap = 6

        self.key_rects.clear()

        for r_idx, row in enumerate(keyboard_rows):
            total_w = sum(68 if k in ("ENTER", "BACK", "HINT") else key_w for k in row) + (len(row) - 1) * gap
            rx = settings.DISPLAY_WIDTH // 2 - total_w // 2
            ry = start_y + r_idx * (key_h + gap)

            for key in row:
                w = 68 if key in ("ENTER", "BACK", "HINT") else key_w
                k_rect = pygame.Rect(rx, ry, w, key_h)
                self.key_rects[key] = k_rect

                # Determine key color based on status
                st = self.key_status.get(key, -1)
                if key == "HINT":
                    bg = (40, 95, 140)
                elif st == we.COLOR_CORRECT:
                    bg = COLOR_GREEN
                elif st == we.COLOR_PRESENT:
                    bg = COLOR_YELLOW
                elif st == we.COLOR_ABSENT:
                    bg = (45, 50, 60)
                else:
                    bg = KEY_DEFAULT

                pygame.draw.rect(surface, bg, k_rect, border_radius=5)
                pygame.draw.rect(surface, (80, 95, 120), k_rect, 1, border_radius=5)

                k_surf = self.font_key.render(key, True, TEXT_WHITE)
                surface.blit(k_surf, k_surf.get_rect(center=k_rect.center))

                rx += w + gap
