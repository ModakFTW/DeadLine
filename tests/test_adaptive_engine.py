"""tests/test_adaptive_engine.py - Automated unit tests for rule-based adaptive logic."""
import unittest
from adaptive_quiz.questions import QUESTIONS, validate_questions
from adaptive_quiz.engine import AdaptiveQuizEngine


class TestAdaptiveQuizEngine(unittest.TestCase):
    def setUp(self):
        validate_questions(QUESTIONS)
        self.engine = AdaptiveQuizEngine(QUESTIONS, start_level=1)

    def test_question_bank_validation(self):
        """Question bank must have >= 15 items, valid schemas, and cover levels 1-3."""
        self.assertGreaterEqual(len(QUESTIONS), 15)
        for q in QUESTIONS:
            self.assertEqual(len(q["options"]), 4)
            self.assertIn(q["answer"], [0, 1, 2, 3])
            self.assertIn(q["level"], [1, 2, 3])
            self.assertTrue(len(q["explanation"]) > 0)

    def test_level_increase_after_two_correct(self):
        """Two consecutive correct answers increase difficulty level by 1, clamped at 3."""
        self.assertEqual(self.engine.current_level, 1)

        # 1st correct
        q1 = self.engine.get_next_question()
        is_c, pts, _ = self.engine.submit_answer(q1["answer"], time_remaining=10.0)
        self.assertTrue(is_c)
        self.assertEqual(self.engine.current_level, 1)
        self.assertEqual(self.engine.correct_streak, 1)

        # 2nd correct -> level increases to 2
        q2 = self.engine.get_next_question()
        is_c, pts, _ = self.engine.submit_answer(q2["answer"], time_remaining=10.0)
        self.assertTrue(is_c)
        self.assertEqual(self.engine.current_level, 2)
        self.assertEqual(self.engine.correct_streak, 0)

        # 3rd & 4th correct -> level increases to 3
        q3 = self.engine.get_next_question()
        self.engine.submit_answer(q3["answer"], time_remaining=10.0)
        q4 = self.engine.get_next_question()
        self.engine.submit_answer(q4["answer"], time_remaining=10.0)
        self.assertEqual(self.engine.current_level, 3)

        # 5th & 6th correct -> clamped at level 3
        q5 = self.engine.get_next_question()
        self.engine.submit_answer(q5["answer"], time_remaining=10.0)
        q6 = self.engine.get_next_question()
        self.engine.submit_answer(q6["answer"], time_remaining=10.0)
        self.assertEqual(self.engine.current_level, 3)

    def test_level_decrease_after_two_incorrect(self):
        """Two consecutive incorrect answers decrease difficulty level by 1, clamped at 1."""
        engine = AdaptiveQuizEngine(QUESTIONS, start_level=3)
        self.assertEqual(engine.current_level, 3)

        # 1st wrong
        q1 = engine.get_next_question()
        wrong_opt = (q1["answer"] + 1) % 4
        is_c, pts, _ = engine.submit_answer(wrong_opt, time_remaining=10.0)
        self.assertFalse(is_c)
        self.assertEqual(engine.current_level, 3)
        self.assertEqual(engine.wrong_streak, 1)

        # 2nd wrong -> drops to 2
        q2 = engine.get_next_question()
        wrong_opt = (q2["answer"] + 1) % 4
        engine.submit_answer(wrong_opt, time_remaining=10.0)
        self.assertEqual(engine.current_level, 2)
        self.assertEqual(engine.wrong_streak, 0)

        # 3rd & 4th wrong -> drops to 1
        q3 = engine.get_next_question()
        engine.submit_answer((q3["answer"] + 1) % 4, 10.0)
        q4 = engine.get_next_question()
        engine.submit_answer((q4["answer"] + 1) % 4, 10.0)
        self.assertEqual(engine.current_level, 1)

        # 5th & 6th wrong -> clamped at 1
        q5 = engine.get_next_question()
        engine.submit_answer((q5["answer"] + 1) % 4, 10.0)
        q6 = engine.get_next_question()
        engine.submit_answer((q6["answer"] + 1) % 4, 10.0)
        self.assertEqual(engine.current_level, 1)

    def test_streak_resets_on_opposite_answer(self):
        """Opposite answer must reset the active streak."""
        # 1 correct
        q1 = self.engine.get_next_question()
        self.engine.submit_answer(q1["answer"], 10.0)
        self.assertEqual(self.engine.correct_streak, 1)

        # 1 wrong -> resets correct_streak
        q2 = self.engine.get_next_question()
        self.engine.submit_answer((q2["answer"] + 1) % 4, 10.0)
        self.assertEqual(self.engine.correct_streak, 0)
        self.assertEqual(self.engine.wrong_streak, 1)

        # 1 correct -> resets wrong_streak
        q3 = self.engine.get_next_question()
        self.engine.submit_answer(q3["answer"], 10.0)
        self.assertEqual(self.engine.correct_streak, 1)
        self.assertEqual(self.engine.wrong_streak, 0)

    def test_timeout_resets_both_streaks_without_level_drop(self):
        """Timeout resets both streaks and does not apply an adaptation level penalty."""
        engine = AdaptiveQuizEngine(QUESTIONS, start_level=2)
        # Set 1 wrong streak
        q1 = engine.get_next_question()
        engine.submit_answer((q1["answer"] + 1) % 4, 5.0)
        self.assertEqual(engine.wrong_streak, 1)

        # Timeout occurs on next question
        q2 = engine.get_next_question()
        engine.handle_timeout()
        self.assertEqual(engine.current_level, 2)  # Level unchanged!
        self.assertEqual(engine.wrong_streak, 0)   # Streaks reset!
        self.assertEqual(engine.correct_streak, 0)
        self.assertEqual(engine.timeout_count, 1)

    def test_scoring_and_accuracy(self):
        """Correct answers earn 100 + int(10 * time_rem); timeouts & wrongs earn 0."""
        # Correct with 8.5s remaining -> 100 + 85 = 185
        q1 = self.engine.get_next_question()
        _, pts, _ = self.engine.submit_answer(q1["answer"], time_remaining=8.5)
        self.assertEqual(pts, 185)
        self.assertEqual(self.engine.score, 185)

        # Wrong answer -> 0 pts
        q2 = self.engine.get_next_question()
        _, pts, _ = self.engine.submit_answer((q2["answer"] + 1) % 4, time_remaining=12.0)
        self.assertEqual(pts, 0)
        self.assertEqual(self.engine.score, 185)

        # Timeout -> 0 pts
        q3 = self.engine.get_next_question()
        _, pts, _ = self.engine.handle_timeout()
        self.assertEqual(pts, 0)
        self.assertEqual(self.engine.score, 185)

        # Accuracy = 1 correct / (1 correct + 1 wrong) = 50.0% (timeout excluded)
        self.assertAlmostEqual(self.engine.get_accuracy(), 50.0)

    def test_full_session_and_restart(self):
        """Session concludes after 10 questions and resets cleanly."""
        for _ in range(10):
            q = self.engine.get_next_question()
            self.assertIsNotNone(q)
            self.engine.submit_answer(q["answer"], 10.0)

        self.assertTrue(self.engine.is_finished())
        self.assertIsNone(self.engine.get_next_question())
        summary = self.engine.get_summary()
        self.assertEqual(summary["total_questions"], 10)
        self.assertEqual(summary["correct_count"], 10)

        # Reset
        self.engine.reset()
        self.assertEqual(self.engine.score, 0)
        self.assertEqual(self.engine.correct_count, 0)
        self.assertEqual(self.engine.questions_answered_count, 0)
        self.assertFalse(self.engine.is_finished())
        q_new = self.engine.get_next_question()
        self.assertIsNotNone(q_new)


if __name__ == "__main__":
    unittest.main()
