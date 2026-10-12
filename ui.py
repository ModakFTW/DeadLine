# ui.py — HUD, debug overlay, menus, subject select, win screen, and game over
import math
import pygame
from settings import (
    DISPLAY_WIDTH, DISPLAY_HEIGHT, WHITE, BLACK, YELLOW, RED, GREEN,
    DARK_GRAY, LIGHT_GRAY, PLAYER_MAX_HP, ORANGE, CYAN, GOLD
)


class UI:
    """
    Handles all UI and presentation layers:
    1. Player HUD (hearts + distance)
    2. F3 Debug AI Telemetry Panel
    3. Subject Select Screen
    4. Win Screen (Elo curve + Markov matrix display)
    5. Menu, Pause, Game Over screens
    """

    def __init__(self) -> None:
        pygame.font.init()
        self.font_tiny = pygame.font.SysFont("segoeui, arial", 13)
        self.font_small = pygame.font.SysFont("segoeui, arial, sans-serif", 16, bold=True)
        self.font_medium = pygame.font.SysFont("segoeui, arial, sans-serif", 24)
        self.font_large = pygame.font.SysFont("segoeui, arial, sans-serif", 44, bold=True)
        self.font_title = pygame.font.SysFont("impact, segoeui, arial", 70)
        self.debug_visible = False

    def toggle_debug(self) -> None:
        """Toggle the debug overlay on/off."""
        self.debug_visible = not self.debug_visible

    # ──────────────────────────────────────────────
    # In-Game HUD
    # ──────────────────────────────────────────────

    def draw_hud(self, surface: pygame.Surface, hp: int, distance: int,
                 obstacle_count: int, has_rickshaw: bool = False,
                 boost_active: bool = False, boost_seconds: int = 0) -> None:
        """Draw player hearts, distance, and active powerups."""
        # Hearts
        for i in range(PLAYER_MAX_HP):
            x = 24 + i * 36
            y = 20
            color = RED if i < hp else (80, 80, 90)
            pygame.draw.circle(surface, color, (x + 8, y + 8), 9)
            pygame.draw.circle(surface, color, (x + 22, y + 8), 9)
            pygame.draw.polygon(surface, color, [
                (x, y + 12), (x + 30, y + 12), (x + 15, y + 27)
            ])
            if i < hp:
                pygame.draw.circle(surface, (255, 170, 170), (x + 7, y + 7), 3)

        # Distance & Obstacle stats
        dist_text = self.font_small.render(
            f"Distance: {distance}m   |   Obstacles Passed: {obstacle_count}",
            True, WHITE
        )
        shadow = self.font_small.render(
            f"Distance: {distance}m   |   Obstacles Passed: {obstacle_count}",
            True, BLACK
        )
        pos_x = DISPLAY_WIDTH - dist_text.get_width() - 28
        surface.blit(shadow, (pos_x + 1, 21))
        surface.blit(dist_text, (pos_x, 20))

        # Rickshaw Powerup Badge
        if has_rickshaw:
            badge_rect = pygame.Rect(24, 56, 360, 28)
            pygame.draw.rect(surface, (20, 24, 34, 220), badge_rect, border_radius=6)
            border = (80, 220, 255) if boost_active else (250, 205, 45)
            pygame.draw.rect(surface, border, badge_rect, 2, border_radius=6)
            if boost_active:
                txt = self.font_small.render(f"⚡ BOOST ACTIVE: {boost_seconds}s invincible + speed!", True, (120, 230, 255))
            else:
                txt = self.font_small.render("⚡ Press V: Rickshaw Boost (6s shield + speed)", True, (250, 215, 60))
            surface.blit(txt, (badge_rect.x + 10, badge_rect.y + 4))

    # ──────────────────────────────────────────────
    # Debug Telemetry (F3)
    # ──────────────────────────────────────────────

    def draw_debug(self, surface: pygame.Surface, stats: dict,
                   tier: str, last_obstacle: str, fps: float) -> None:
        """Draw the debug overlay showing AI internals with crisp text."""
        if not self.debug_visible:
            return

        lines = [
            f"FPS: {fps:.0f}",
            "",
            "=== AI DIFFICULTY ENGINE ===",
            f"Skill Rating: {stats['skill_score']:.2f} / 10.0",
            f"Adaptive Tier: {tier.upper()}",
            f"Last Generated: {last_obstacle}",
            "",
            f"Clears: {stats['clears']}   Deaths: {stats['deaths']}",
            f"Streak: {stats['streak']:+d}",
        ]

        panel_width = 300
        line_height = 20
        panel_height = len(lines) * line_height + 34
        panel = pygame.Surface((panel_width, panel_height), pygame.SRCALPHA)
        panel.fill((15, 18, 26, 220))
        surface.blit(panel, (18, 65))
        pygame.draw.rect(surface, (60, 80, 110), (18, 65, panel_width, panel_height), 1, border_radius=4)

        tier_colors = {"easy": (70, 220, 110), "medium": (250, 200, 50), "hard": (240, 60, 60)}
        tier_color = tier_colors.get(tier, WHITE)

        y = 75
        for line in lines:
            color = tier_color if "Tier:" in line else (230, 230, 240)
            if "FPS" in line:
                color = (160, 200, 255)
            elif "ENGINE" in line:
                color = YELLOW

            sh = self.font_small.render(line, True, BLACK)
            t = self.font_small.render(line, True, color)
            surface.blit(sh, (31, y + 1))
            surface.blit(t, (30, y))
            y += line_height

        bar_x = 30
        bar_y = y + 4
        bar_width = 276
        bar_height = 10
        pygame.draw.rect(surface, (40, 45, 55), (bar_x, bar_y, bar_width, bar_height), border_radius=3)
        fill_width = max(4, int(bar_width * (stats['skill_score'] / 10.0)))
        pygame.draw.rect(surface, tier_color, (bar_x, bar_y, fill_width, bar_height), border_radius=3)
        pygame.draw.rect(surface, (140, 150, 170), (bar_x, bar_y, bar_width, bar_height), 1, border_radius=3)

    # ──────────────────────────────────────────────
    # Subject Select Screen
    # ──────────────────────────────────────────────

    def draw_subject_select(self, surface: pygame.Surface, subjects: list[dict],
                            selected_index: int) -> None:
        """Draw the subject selection screen."""
        surface.fill((12, 14, 22))

        title = self.font_large.render("CHOOSE YOUR SUBJECT", True, (60, 210, 255))
        title_rect = title.get_rect(center=(DISPLAY_WIDTH // 2, 100))
        surface.blit(title, title_rect)

        sub = self.font_small.render(
            "Your chosen subject determines the flashcard words and riddles.",
            True, (180, 190, 210)
        )
        surface.blit(sub, (DISPLAY_WIDTH // 2 - sub.get_width() // 2, 155))

        card_w = 340
        card_h = 80
        start_y = 220
        for i, subj in enumerate(subjects):
            cx = DISPLAY_WIDTH // 2 - card_w // 2
            cy = start_y + i * (card_h + 20)
            rect = pygame.Rect(cx, cy, card_w, card_h)

            if i == selected_index:
                pygame.draw.rect(surface, (30, 55, 85), rect, border_radius=10)
                pygame.draw.rect(surface, (60, 180, 255), rect, 3, border_radius=10)
            else:
                pygame.draw.rect(surface, (25, 28, 40), rect, border_radius=10)
                pygame.draw.rect(surface, (60, 65, 80), rect, 1, border_radius=10)

            name = self.font_medium.render(subj["name"], True, WHITE if i == selected_index else LIGHT_GRAY)
            surface.blit(name, (cx + 20, cy + 12))

            hint = self.font_tiny.render(
                f"Words: {', '.join(subj['words'][:4])}...",
                True, (140, 155, 180)
            )
            surface.blit(hint, (cx + 20, cy + 48))

        nav = self.font_small.render(
            "↑↓ to select  |  ENTER to confirm  |  ESC for menu",
            True, YELLOW
        )
        surface.blit(nav, (DISPLAY_WIDTH // 2 - nav.get_width() // 2, DISPLAY_HEIGHT - 45))

    # ──────────────────────────────────────────────
    # Win Screen (replaces Twist Reveal)
    # ──────────────────────────────────────────────

    def draw_win_screen(self, surface: pygame.Surface, game_state) -> None:
        """
        Renders the final Win Screen with AI analytics.
        Shows Elo skill progression curve and Markov transition matrix.
        """
        surface.fill((12, 14, 22))

        # Header
        title = self.font_large.render("EXAM COMPLETE — YOU PASSED!", True, (60, 220, 120))
        title_rect = title.get_rect(center=(DISPLAY_WIDTH // 2, 36))
        surface.blit(title, title_rect)

        # Stats summary bar
        summary_lines = [
            f"Subject: {game_state.subject_name}",
            f"Knowledge Score: {game_state.knowledge_score}/10  |  "
            f"Difficulty: {game_state.final_tier.upper()}  |  "
            f"Route: {'Cage Exit (A)' if game_state.route == 'A' else 'Tunnel (B)'}",
        ]
        sy = 80
        for line in summary_lines:
            t = self.font_small.render(line, True, (210, 220, 240))
            surface.blit(t, (DISPLAY_WIDTH // 2 - t.get_width() // 2, sy))
            sy += 24

        # ── Left Panel: Elo Skill Curve ──
        card1 = pygame.Rect(40, 140, 570, 480)
        pygame.draw.rect(surface, (20, 24, 38), card1, border_radius=10)
        pygame.draw.rect(surface, (60, 80, 115), card1, 2, border_radius=10)

        c1_title = self.font_small.render("Model 2: Live Elo Skill Trajectory (0 to 10)", True, GOLD)
        surface.blit(c1_title, (card1.x + 20, card1.y + 16))

        # Graph
        gx = card1.x + 45
        gy = card1.y + 60
        gw = card1.width - 70
        gh = 280

        pygame.draw.rect(surface, (14, 16, 26), (gx, gy, gw, gh))
        for level in [2.5, 5.0, 7.5, 10.0]:
            ly = gy + gh - int((level / 10.0) * gh)
            pygame.draw.line(surface, (40, 50, 70), (gx, ly), (gx + gw, ly), 1)
            lbl = self.font_tiny.render(f"{level:.1f}", True, (110, 120, 145))
            surface.blit(lbl, (gx - 32, ly - 8))

        easy_lbl = self.font_tiny.render("EASY TIER (<4.0)", True, (50, 180, 90))
        hard_lbl = self.font_tiny.render("HARD TIER (>7.0)", True, (240, 70, 70))
        surface.blit(easy_lbl, (gx + 10, gy + gh - 40))
        surface.blit(hard_lbl, (gx + 10, gy + 15))

        history = game_state.elo_history
        if len(history) > 1:
            pts = []
            for i, val in enumerate(history):
                px = gx + int((i / (len(history) - 1)) * gw)
                py = gy + gh - int((max(0.0, min(10.0, val)) / 10.0) * gh)
                pts.append((px, py))

            pygame.draw.lines(surface, (60, 210, 255), False, pts, 3)
            for pt in pts:
                pygame.draw.circle(surface, GOLD, pt, 4)

        initial_elo = history[0] if history else 5.0
        c1_desc = self.font_tiny.render(
            f"Initial: {initial_elo:.2f}  |  Final: {game_state.final_elo:.2f}  |  "
            f"Clears: {game_state.clears}  |  Deaths: {game_state.deaths}",
            True, (220, 225, 240)
        )
        surface.blit(c1_desc, (gx, gy + gh + 18))


        # AI explanation
        ai_title = self.font_small.render("How The AI Worked:", True, (80, 220, 140))
        surface.blit(ai_title, (card1.x + 20, gy + gh + 50))
        notes = [
            "• Model 1: Memory test → Knowledge Score → Markov chain tier.",
            "• Model 2: Elo rating adapts difficulty in real-time as you play.",
            "• Model 3: Rule-based monkey AI reacts to your proximity.",
        ]
        ny = gy + gh + 78
        for n in notes:
            surface.blit(self.font_tiny.render(n, True, (190, 200, 220)), (card1.x + 20, ny))
            ny += 20

        # ── Right Panel: Knowledge Score & Route ──
        card2 = pygame.Rect(640, 140, 600, 480)
        pygame.draw.rect(surface, (20, 24, 38), card2, border_radius=10)
        pygame.draw.rect(surface, (60, 80, 115), card2, 2, border_radius=10)

        c2_title = self.font_small.render("Model 1: Knowledge Estimation & Closed Loop", True, GOLD)
        surface.blit(c2_title, (card2.x + 20, card2.y + 16))

        # Level-by-level recap
        recap_y = card2.y + 55
        recap_items = [
            ("Level 1 — Memory Test", f"Memorized {game_state.knowledge_score}/10 words → {game_state.get_difficulty_tier().upper()} difficulty"),
            ("Level 2 — Platformer", f"Adaptive obstacles via Markov chain (Elo: {game_state.final_elo:.2f})"),
            ("Level 3 — The Cage", f"Answered {game_state.riddles_correct}/3 riddles → Route {game_state.route}"),
            ("Level 4 — Old Woman", "Escort puzzle with rule-based Monkey AI"),
            ("Level 5 — Exam Gate", f"Recalled words from Level 1 → PASSED!"),
        ]
        for title_str, desc_str in recap_items:
            t = self.font_small.render(title_str, True, (240, 200, 60))
            surface.blit(t, (card2.x + 20, recap_y))
            d = self.font_tiny.render(desc_str, True, (200, 210, 230))
            surface.blit(d, (card2.x + 24, recap_y + 22))
            recap_y += 58

        # Viva defense section
        viva_y = recap_y + 20
        viva_title = self.font_small.render("Viva Defensible Points:", True, (80, 220, 140))
        surface.blit(viva_title, (card2.x + 20, viva_y))
        viva_notes = [
            "• Pure statistical PCG: Zero black-box dependencies.",
            "• Dynamic Elo feedback adapts to player skill in real time.",
            "• Closed learning loop: same knowledge tested at start and end.",
            "• Rule-based FSM agent demonstrates reactive NPC AI.",
        ]
        vy = viva_y + 28
        for n in viva_notes:
            surface.blit(self.font_tiny.render(n, True, (190, 200, 220)), (card2.x + 20, vy))
            vy += 22

        # Bottom nav
        restart = self.font_small.render("PRESS R TO PLAY AGAIN  |  ESC TO RETURN TO MENU", True, YELLOW)
        surface.blit(restart, (DISPLAY_WIDTH // 2 - restart.get_width() // 2, DISPLAY_HEIGHT - 38))

    # ──────────────────────────────────────────────
    # Menus and Overlays
    # ──────────────────────────────────────────────

    def draw_menu(self, surface: pygame.Surface) -> None:
        """Draw crisp high-res main menu screen."""
        surface.fill((18, 20, 32))

        title_sh = self.font_title.render("DEADLINE", True, BLACK)
        title = self.font_title.render("DEADLINE", True, (60, 210, 255))
        rect = title.get_rect(center=(DISPLAY_WIDTH // 2, DISPLAY_HEIGHT // 3 - 20))
        surface.blit(title_sh, (rect.x + 3, rect.y + 3))
        surface.blit(title, rect)

        sub = self.font_medium.render(
            "An AI-Driven Adaptive 2D Platformer", True, GOLD
        )
        sub_rect = sub.get_rect(center=(DISPLAY_WIDTH // 2, DISPLAY_HEIGHT // 3 + 55))
        surface.blit(sub, sub_rect)

        tag = self.font_small.render(
            "Memorize • Run • Solve • Escape • Prove Your Knowledge",
            True, (180, 190, 210)
        )
        surface.blit(tag, (DISPLAY_WIDTH // 2 - tag.get_width() // 2, DISPLAY_HEIGHT // 3 + 95))

        instr_box = pygame.Rect(DISPLAY_WIDTH // 2 - 240, DISPLAY_HEIGHT * 2 // 3 - 10, 480, 56)
        pygame.draw.rect(surface, (35, 40, 60), instr_box, border_radius=8)
        pygame.draw.rect(surface, (70, 130, 200), instr_box, 2, border_radius=8)

        instr = self.font_medium.render("Press ENTER to Begin Story Mode", True, WHITE)
        instr_rect = instr.get_rect(center=instr_box.center)
        surface.blit(instr, instr_rect)

        controls = self.font_small.render(
            "WASD / Arrows: Move  |  Space: Jump  |  F3: AI Telemetry  |  ESC: Pause",
            True, (150, 160, 180)
        )
        ctrl_rect = controls.get_rect(center=(DISPLAY_WIDTH // 2, DISPLAY_HEIGHT - 35))
        surface.blit(controls, ctrl_rect)


    def draw_pause(self, surface: pygame.Surface) -> None:
        """Draw crisp pause overlay."""
        overlay = pygame.Surface((DISPLAY_WIDTH, DISPLAY_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 160))
        surface.blit(overlay, (0, 0))

        text = self.font_large.render("PAUSED", True, WHITE)
        rect = text.get_rect(center=(DISPLAY_WIDTH // 2, DISPLAY_HEIGHT // 2 - 35))
        surface.blit(text, rect)

        hint = self.font_medium.render("Press ESC to resume", True, LIGHT_GRAY)
        hint_rect = hint.get_rect(center=(DISPLAY_WIDTH // 2, DISPLAY_HEIGHT // 2 + 25))
        surface.blit(hint, hint_rect)

    def draw_game_over(self, surface: pygame.Surface, stats: dict = None) -> None:
        """Draw crisp game-over screen with optional stats."""
        overlay = pygame.Surface((DISPLAY_WIDTH, DISPLAY_HEIGHT), pygame.SRCALPHA)
        overlay.fill((10, 10, 15, 210))
        surface.blit(overlay, (0, 0))

        text = self.font_large.render("GAME OVER", True, (240, 60, 60))
        rect = text.get_rect(center=(DISPLAY_WIDTH // 2, DISPLAY_HEIGHT // 3 - 20))
        surface.blit(text, rect)

        if stats:
            stat_lines = [
                f"Final Skill Score: {stats.get('skill_score', 0):.2f} / 10.0",
                f"Adaptive Tier Reached: {stats.get('tier', '?').upper()}",
                f"Obstacles Cleared: {stats.get('clears', 0)}   |   Deaths: {stats.get('deaths', 0)}",
            ]
            y = DISPLAY_HEIGHT // 2 - 20
            for line in stat_lines:
                t = self.font_medium.render(line, True, (230, 235, 245))
                r = t.get_rect(center=(DISPLAY_WIDTH // 2, y))
                surface.blit(t, r)
                y += 40
        else:
            msg = self.font_medium.render("You couldn't prove your knowledge...", True, (200, 200, 210))
            msg_rect = msg.get_rect(center=(DISPLAY_WIDTH // 2, DISPLAY_HEIGHT // 2))
            surface.blit(msg, msg_rect)

        retry = self.font_medium.render("Press R to Retry  |  ESC for Menu", True, YELLOW)
        retry_rect = retry.get_rect(center=(DISPLAY_WIDTH // 2, DISPLAY_HEIGHT * 3 // 4 + 20))
        surface.blit(retry, retry_rect)
