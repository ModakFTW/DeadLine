"""levels/level_final_quiz.py - Level 6: Final memory gate (must recall Level 1 answers, 4/6 to win)."""
import random
from levels.quiz_engine import QuizEngine
from settings import FINAL_QUIZ_PASS_THRESHOLD, FINAL_QUIZ_TOTAL_QUESTIONS


class LevelFinalQuiz(QuizEngine):
    """Recalls up to 6 questions seeded from Level 1 answers.
    Player must get >= FINAL_QUIZ_PASS_THRESHOLD correct to win.
    """

    def __init__(self, game_state: dict):
        self.game_state = game_state
        level1_records = game_state.get("level1_answers", [])

        questions = []
        pool_distractors = [
            "Ohm", "Volt", "Ampere", "Quick Sort", "Bubble Sort",
            "AND Gate", "OR Gate", "Stack", "Cache", "Kernel",
            "Mass × Acceleration", "Velocity", "CPU", "Queue"
        ]

        for rec in level1_records[:FINAL_QUIZ_TOTAL_QUESTIONS]:
            correct_ans = rec["chosen_text"]
            distractors = [w for w in pool_distractors if w != correct_ans]
            random.shuffle(distractors)
            opts = distractors[:3] + [correct_ans]
            random.shuffle(opts)
            questions.append({
                "question": f"Recall: '{rec['question']}'",
                "options": opts,
                "correct": opts.index(correct_ans)
            })

        # Pad to FINAL_QUIZ_TOTAL_QUESTIONS with fallback if Level 1 answers are sparse
        fallback = [
            {"question": "The Markov chain obstacle generator selects the next obstacle using:",
             "options": ["Player score", "Random dice", "Previous obstacle type", "Boss phase"],
             "correct": 2},
            {"question": "The Elo difficulty tracker's K-factor controls:",
             "options": ["Boss HP", "Speed of skill adjustment", "Quiz timer", "Number of questions"],
             "correct": 1},
        ]
        while len(questions) < FINAL_QUIZ_TOTAL_QUESTIONS and fallback:
            questions.append(fallback.pop(0))

        # Store pass threshold in game_state so main.py can read result
        self.pass_threshold = FINAL_QUIZ_PASS_THRESHOLD
        super().__init__(questions, level_id=6, game_state=game_state)

    @property
    def passed(self) -> bool:
        return self.completed and self.score >= self.pass_threshold

    @property
    def failed_quiz(self) -> bool:
        return self.completed and self.score < self.pass_threshold
