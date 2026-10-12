# game_state.py — Shared state that persists across all 5 levels
from dataclasses import dataclass, field


@dataclass
class GameState:
    """
    Cross-level data container passed between all 5 levels.
    Level 1 populates knowledge data; subsequent levels read it.
    """
    # Subject selection (set in Subject Select screen)
    subject_name: str = ""
    words: list[str] = field(default_factory=list)
    quiz: list[dict] = field(default_factory=list)
    riddles: list[dict] = field(default_factory=list)
    escape_keyword: str = ""
    escape_riddle: dict = field(default_factory=dict)


    # Level 1 results
    knowledge_score: int = 0              # 0-10 (how many words recalled)
    words_remembered: list[str] = field(default_factory=list)

    # Level 3 results
    riddles_correct: int = 0              # 0-3 from the Cage
    route: str = ""                       # "A" (cage opens) or "B" (tunnel)

    # Platformer AI stats (populated during Level 2)
    elo_history: list[float] = field(default_factory=list)
    final_elo: float = 5.0
    final_tier: str = "medium"
    clears: int = 0
    deaths: int = 0

    def get_difficulty_tier(self) -> str:
        """Maps knowledge_score to Markov chain difficulty tier."""
        if self.knowledge_score <= 3:
            return "easy"
        elif self.knowledge_score >= 8:
            return "hard"
        return "medium"

    def reset(self) -> None:
        """Reset all state for a new game."""
        self.subject_name = ""
        self.words = []
        self.quiz = []
        self.riddles = []

        self.escape_keyword = ""
        self.escape_riddle = {}
        self.knowledge_score = 0
        self.words_remembered = []
        self.riddles_correct = 0
        self.route = ""
        self.elo_history = []
        self.final_elo = 5.0
        self.final_tier = "medium"
        self.clears = 0
        self.deaths = 0
