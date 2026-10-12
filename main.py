# main.py — DeadLine entry point: 5-level game loop with state machine
import sys
import os
import json
import traceback
import pygame


from settings import DISPLAY_WIDTH, DISPLAY_HEIGHT, FPS, TITLE
from game_state import GameState
from ui import UI


# ═══════════════════════════════════════════════════
# Game states
# ═══════════════════════════════════════════════════
STATE_MENU = "menu"
STATE_SUBJECT_SELECT = "subject_select"
STATE_MEMORY = "memory"
STATE_PLATFORMER = "platformer"
STATE_CAGE = "cage"
STATE_ESCAPE = "escape"
STATE_OLD_WOMAN = "old_woman"
STATE_EXAM_GATE = "exam_gate"
STATE_WIN = "win"
STATE_GAME_OVER = "game_over"


class Game:
    """
    Main game class. Manages the Pygame window, game loop,
    state transitions, and delegates to individual Level classes.
    """

    def __init__(self) -> None:
        pygame.init()
        self.display = pygame.display.set_mode((DISPLAY_WIDTH, DISPLAY_HEIGHT))
        pygame.display.set_caption(TITLE)
        self.clock = pygame.time.Clock()
        self.state = STATE_MENU
        self.running = True

        # Core systems
        self.ui = UI()
        self.game_state = GameState()
        self.current_level = None

        # Subject data (loaded once)
        self.subjects = self._load_subjects()
        self.selected_subject_index = 0

    def _load_subjects(self) -> list[dict]:
        """Load all subject JSON files from data/subjects/."""
        subjects_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                     'data', 'subjects')
        subjects = []
        if os.path.isdir(subjects_dir):
            for fname in sorted(os.listdir(subjects_dir)):
                if fname.endswith('.json'):
                    path = os.path.join(subjects_dir, fname)
                    with open(path, 'r') as f:
                        subjects.append(json.load(f))
        if not subjects:
            # Fallback
            subjects.append({
                "name": "General Knowledge",
                "words": ["Alpha", "Beta", "Gamma", "Delta", "Epsilon",
                          "Zeta", "Eta", "Theta", "Iota", "Kappa"],
                "riddles": [
                    {"question": "First letter of the Greek alphabet?", "answer": "ALPHA"},
                    {"question": "Second letter of the Greek alphabet?", "answer": "BETA"},
                    {"question": "Third letter of the Greek alphabet?", "answer": "GAMMA"},
                ],
                "escape_keyword": "GREEK",
                "escape_riddle": {"question": "Alpha, Beta, Gamma are _____ letters.", "answer": "GREEK"}
            })
        return subjects

    def _transition_to(self, new_state: str) -> None:
        """Transition to a new game state, instantiating the appropriate level."""
        self.state = new_state
        self.current_level = None

        if new_state == STATE_MEMORY:
            from levels.level_memory import LevelMemory
            self.current_level = LevelMemory(self.game_state)

        elif new_state == STATE_PLATFORMER:
            from levels.level_platformer import LevelPlatformer
            self.current_level = LevelPlatformer(self.game_state)

        elif new_state == STATE_CAGE:
            from levels.level_cage import LevelCage
            self.current_level = LevelCage(self.game_state)

        elif new_state == STATE_ESCAPE:
            from levels.level_escape import LevelEscape
            self.current_level = LevelEscape(self.game_state)

        elif new_state == STATE_OLD_WOMAN:
            from levels.level_oldwoman import LevelOldWoman
            self.current_level = LevelOldWoman(self.game_state)

        elif new_state in (STATE_EXAM_GATE, "wordle"):
            from levels.level_wordle import LevelWordle
            self.current_level = LevelWordle(self.game_state)

    def _start_new_game(self) -> None:
        """Reset game state, load General Knowledge directly, and start Level 1."""
        self.game_state.reset()
        subj = self.subjects[0] if self.subjects else {
            "name": "General Knowledge",
            "words": ["Paris", "Oxygen", "Everest", "Jupiter", "Gold"],
            "quiz": [],
            "riddles": [],
            "escape_keyword": "KNOWLEDGE",
            "escape_riddle": {"question": "The pursuit of truth gives you ______.", "answer": "KNOWLEDGE"}
        }
        self.game_state.subject_name = subj["name"]
        self.game_state.words = list(subj.get("words", []))
        self.game_state.quiz = list(subj.get("quiz", []))
        self.game_state.riddles = list(subj.get("riddles", []))
        self.game_state.escape_keyword = subj.get("escape_keyword", "KNOWLEDGE")
        self.game_state.escape_riddle = dict(subj.get("escape_riddle", {}))
        self._transition_to(STATE_MEMORY)


    def run(self) -> None:
        """The main game loop."""
        while self.running:
            dt = self.clock.tick(FPS)
            events = pygame.event.get()

            # Global quit check
            for event in events:
                if event.type == pygame.QUIT:
                    self.running = False

            if not self.running:
                break

            # ── State Handling ──
            if self.state == STATE_MENU:
                self._handle_menu(events)
                self.ui.draw_menu(self.display)

            elif self.state == STATE_SUBJECT_SELECT:
                self._handle_subject_select(events)
                self.ui.draw_subject_select(
                    self.display, self.subjects, self.selected_subject_index
                )

            elif self.state == STATE_WIN:
                self._handle_win(events)
                self.ui.draw_win_screen(self.display, self.game_state)

            elif self.state == STATE_GAME_OVER:
                self._handle_game_over(events)
                self.ui.draw_game_over(self.display)

            elif self.current_level is not None:
                # Delegate to the active level
                next_state = self.current_level.handle_events(events)
                if next_state is None:
                    next_state = self.current_level.update()
                self.current_level.draw(self.display)

                if next_state is not None:
                    if next_state == "win":
                        self.state = STATE_WIN
                        self.current_level = None
                    elif next_state == "game_over":
                        self.state = STATE_GAME_OVER
                        self.current_level = None
                    else:
                        self._transition_to(next_state)

            pygame.display.flip()

        pygame.quit()
        sys.exit()

    # ── Event Handlers for Non-Level States ──

    def _handle_menu(self, events: list) -> None:
        for event in events:
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_RETURN:
                    self._start_new_game()
                elif event.key == pygame.K_ESCAPE:
                    self.running = False


    def _handle_subject_select(self, events: list) -> None:
        for event in events:
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_UP:
                    self.selected_subject_index = (self.selected_subject_index - 1) % len(self.subjects)
                elif event.key == pygame.K_DOWN:
                    self.selected_subject_index = (self.selected_subject_index + 1) % len(self.subjects)
                elif event.key == pygame.K_RETURN:
                    self._select_subject()
                elif event.key == pygame.K_ESCAPE:
                    self.state = STATE_MENU

    def _handle_win(self, events: list) -> None:
        for event in events:
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_r:
                    self._start_new_game()
                elif event.key == pygame.K_ESCAPE:
                    self.state = STATE_MENU

    def _handle_game_over(self, events: list) -> None:
        for event in events:
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_r:
                    self._start_new_game()
                elif event.key == pygame.K_ESCAPE:
                    self.state = STATE_MENU


if __name__ == "__main__":
    try:
        game = Game()
        game.run()
    except Exception as e:
        print("\n" + "=" * 60)
        print("CRITICAL ERROR ENCOUNTERED IN GAME LOOP:")
        traceback.print_exc()
        print("=" * 60 + "\n")
        try:
            with open("crash_log.txt", "w", encoding="utf-8") as f:
                traceback.print_exc(file=f)
        except Exception:
            pass
        input("Press Enter to close window...")
        sys.exit(1)

