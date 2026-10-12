"""adaptive_quiz/engine.py - Pure rule-based adaptive engine according to DEADLINE brief."""
import random
from typing import Optional, Dict, Any


class AdaptiveQuizEngine:
    """Manages session state, scoring, metrics, and rule-based difficulty adaptation.

    Rules from DEADLINE brief:
    - 3 difficulty levels: 1 (easy), 2 (medium), 3 (hard).
    - Increase level after 2 consecutive correct answers (clamped at 3).
    - Decrease level after 2 consecutive incorrect answers (clamped at 1).
    - Submitting an answer resets the opposite streak.
    - Timeout resets both streaks without triggering a wrong-answer adaptation penalty.
    - Total session length: 10 questions.
    - Question selection: select unused questions matching current difficulty.
      If none available, select unused question from another level.
      Only reuse questions once all questions in the bank are exhausted.
    - Score: Correct answer = 100 + int(10 * remaining_time).
      Wrong / Timeout = 0 points.
    - Accuracy: correct / (correct + incorrect), excluding timeouts.
    """

    TOTAL_QUESTIONS = 10
    QUESTION_TIME = 15.0  # seconds

    def __init__(self, questions: list[dict], start_level: int = 1):
        self.questions = questions
        self.start_level = start_level
        self.reset()

    def reset(self) -> None:
        """Resets all session variables for a clean restart."""
        self.current_level: int = self.start_level
        self.correct_streak: int = 0
        self.wrong_streak: int = 0

        self.correct_count: int = 0
        self.incorrect_count: int = 0
        self.timeout_count: int = 0
        self.score: int = 0

        self.questions_answered_count: int = 0  # Number of completed questions (0 to 10)
        self.used_question_indices: set[int] = set()

        self.current_question: Optional[Dict[str, Any]] = None
        self.current_question_index: int = -1
        self.session_finished: bool = False

    def is_finished(self) -> bool:
        return self.questions_answered_count >= self.TOTAL_QUESTIONS or self.session_finished

    def get_next_question(self) -> Optional[Dict[str, Any]]:
        """Selects the next question according to the adaptation rules."""
        if self.is_finished():
            self.session_finished = True
            return None

        # 1. Look for unused questions at current level
        matching = [
            i for i, q in enumerate(self.questions)
            if i not in self.used_question_indices and q["level"] == self.current_level
        ]

        # 2. Fall back to unused questions at any other level
        if not matching:
            matching = [
                i for i, q in enumerate(self.questions)
                if i not in self.used_question_indices
            ]

        # 3. If all questions in the entire bank are exhausted, reset used tracking
        if not matching:
            self.used_question_indices.clear()
            matching = [
                i for i, q in enumerate(self.questions)
                if q["level"] == self.current_level
            ]
            if not matching:
                matching = list(range(len(self.questions)))

        chosen_idx = random.choice(matching)
        self.used_question_indices.add(chosen_idx)
        self.current_question_index = chosen_idx
        self.current_question = self.questions[chosen_idx]
        return self.current_question

    def submit_answer(self, option_index: int, time_remaining: float) -> tuple[bool, int, str]:
        """Submits an answer option (0..3).

        Returns: (is_correct, points_awarded, feedback_message)
        """
        if self.current_question is None:
            raise RuntimeError("No active question to answer.")

        is_correct = (option_index == self.current_question["answer"])
        time_rem = max(0.0, min(self.QUESTION_TIME, float(time_remaining)))

        if is_correct:
            self.correct_count += 1
            self.correct_streak += 1
            self.wrong_streak = 0  # Reset opposing streak

            points = 100 + int(10 * time_rem)
            self.score += points

            # Check adaptation: increase difficulty after 2 consecutive correct
            if self.correct_streak >= 2:
                if self.current_level < 3:
                    self.current_level += 1
                self.correct_streak = 0  # Reset after adapting

            fb = f"CORRECT! (+{points} pts)"
        else:
            self.incorrect_count += 1
            self.wrong_streak += 1
            self.correct_streak = 0  # Reset opposing streak
            points = 0

            # Check adaptation: decrease difficulty after 2 consecutive wrong
            if self.wrong_streak >= 2:
                if self.current_level > 1:
                    self.current_level -= 1
                self.wrong_streak = 0  # Reset after adapting

            correct_ans_text = self.current_question["options"][self.current_question["answer"]]
            fb = f"INCORRECT — Correct: {correct_ans_text}"

        self.questions_answered_count += 1
        if self.questions_answered_count >= self.TOTAL_QUESTIONS:
            self.session_finished = True

        return is_correct, points, fb

    def handle_timeout(self) -> tuple[bool, int, str]:
        """Handles 15s timer expiration.

        Resets both streaks without applying a wrong-answer penalty to difficulty.
        Tracked separately.
        """
        if self.current_question is None:
            raise RuntimeError("No active question to timeout.")

        self.timeout_count += 1
        self.correct_streak = 0
        self.wrong_streak = 0

        correct_ans_text = self.current_question["options"][self.current_question["answer"]]
        fb = f"TIME'S UP! — Correct: {correct_ans_text}"

        self.questions_answered_count += 1
        if self.questions_answered_count >= self.TOTAL_QUESTIONS:
            self.session_finished = True

        return False, 0, fb

    def get_accuracy(self) -> float:
        """Returns accuracy as correct / (correct + incorrect), excluding timeouts."""
        evaluated = self.correct_count + self.incorrect_count
        if evaluated == 0:
            return 0.0
        return (self.correct_count / evaluated) * 100.0

    def get_summary(self) -> Dict[str, Any]:
        """Returns complete statistics required for the Results screen."""
        return {
            "score": self.score,
            "correct_count": self.correct_count,
            "incorrect_count": self.incorrect_count,
            "timeout_count": self.timeout_count,
            "accuracy": self.get_accuracy(),
            "final_level": self.current_level,
            "total_questions": self.questions_answered_count,
        }
