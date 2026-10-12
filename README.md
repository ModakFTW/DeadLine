# DEADLINE — Adaptive Educational Game

DEADLINE is an educational Pygame application featuring rule-based adaptive learning, real-time question timers, and multiple game modes.

---

## 1. Quick Start

### Prerequisites
- Python 3.10+
- Pygame (`pip install -r requirements.txt`)

### Run the Standalone Adaptive Learning Quiz (MVP)
```bash
python deadline_quiz.py
```

### Run the Full 5-Level Adaptive Adventure Game
```bash
python main.py
```
*(You can also launch the Adaptive Learning Quiz directly from the Main Menu by pressing `Q`.)*

### Run Automated Unit Tests
```bash
python -m unittest tests/test_adaptive_engine.py
```

---

## 2. Gameplay & Controls (Adaptive Quiz MVP)

- **Answering Questions**: Click answer buttons or press keyboard keys `1`, `2`, `3`, or `4`.
- **Timer**: 15 seconds per question with visual urgency cues (turns yellow under 5s, flashes red under 3s).
- **Adaptive Difficulty**:
  - Starts at Level 1 (Easy).
  - 2 consecutive correct answers $\rightarrow$ increases difficulty to Level 2 (Medium) or Level 3 (Hard).
  - 2 consecutive incorrect answers $\rightarrow$ decreases difficulty.
  - A timeout resets streaks without penalizing difficulty tier.
  - Opposite answers reset the active streak.
  - Questions are selected to match your current difficulty, falling back to other tiers before repeating.
- **Scoring**:
  - Correct answers award 100 base points plus a speed bonus based on remaining time.
  - Incorrect answers and timeouts award 0 points.
- **Session Results**:
  - After 10 questions, view final score, correct/incorrect counts, timeouts, accuracy percentage, and final difficulty.
  - Press `R` or click the button to play again.
  - Press `Esc` or close window to quit cleanly.

---

## 3. Project Structure

```text
DEADLINE/
├── deadline_quiz.py           # Standalone adaptive quiz MVP runner
├── main.py                    # 5-level adventure game main entry point
├── requirements.txt           # Project dependencies
├── README.md                  # Setup & usage instructions
├── context.md                 # Complete system architecture documentation
├── text_utils.py              # Text wrapping & UI text helper
│
├── adaptive_quiz/             # Rule-based adaptive quiz package
│   ├── __init__.py
│   ├── engine.py              # Decoupled AdaptiveQuizEngine class
│   └── questions.py           # Hardcoded question bank & schema validator
│
├── tests/
│   └── test_adaptive_engine.py # Automated unit tests
│
├── ai/                        # Story mode AI modules (Markov chain, Elo, Monkey AI)
├── levels/                    # Story mode level stages
└── data/                      # Training sequences & subject question datasets
```
