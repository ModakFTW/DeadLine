# DEADLINE — Agent Implementation Brief

## Your role

You are the coding agent responsible for implementing **DEADLINE**, a small adaptive educational game using **Python + Pygame**.

**Time limit:** 4–6 hours  
**Team:** 2–3 people  
**Current question storage:** Questions are hardcoded in source code. Keep this approach for the MVP.  
**Primary objective:** Deliver a complete, stable, demo-ready playable game. Prioritize working gameplay and tested adaptive behavior over extra features.

Do not stop at giving advice or snippets. Inspect the existing repository, implement the game in the project files, run it or run available tests, fix problems, and report exactly what works and what remains.

## 1. First actions

1. Inspect the current project and identify existing code, assets, controls, and dependencies.
2. Preserve useful existing work. Do not overwrite working code without a reason.
3. If the repository is empty, create the simple structure below.
4. Check whether Pygame is installed. Add `requirements.txt` if needed.
5. Implement the MVP in small steps and verify each step.
6. If the intended educational subject is not specified in the repository, use clearly marked sample mathematics questions and make it easy to replace them. Do not block progress waiting for clarification.
7. Keep the implementation simple enough to finish within the time limit.

Suggested starting structure:

```text
DEADLINE/
├── main.py
├── requirements.txt
└── README.md
```

Start with a single-file implementation unless the existing project already has a useful module structure. Avoid unnecessary architecture.

## 2. Required MVP features

### Gameplay
- Launch a Pygame window with a clear title and readable UI.
- Show one multiple-choice question at a time.
- Support mouse clicks and keyboard keys `1`–`4` for answering.
- Show whether the answer was correct and reveal the correct option after a wrong answer or timeout.
- Prevent multiple answers from being registered for the same question.
- Advance automatically after a short feedback delay.
- Finish after 10 questions and display a results screen.
- Allow the player to restart without restarting the process.
- Allow quitting cleanly with the window close button or `Esc`.

### Adaptive learning
Use a transparent rule-based algorithm; machine learning is out of scope.

- Three difficulty levels: 1 (easy), 2 (medium), 3 (hard).
- Increase the level after 2 consecutive correct answers.
- Decrease the level after 2 consecutive incorrect answers.
- Clamp the level between 1 and 3.
- Reset the opposite streak when an answer is submitted.
- A timeout resets both streaks but does not count as a wrong answer for adaptation.
- Select questions matching the current difficulty when possible.
- Avoid repeating a question in the same session until all suitable questions have been used.
- If there are no unused questions at the current level, select an unused question from another level. Reuse questions only when all questions have been exhausted.
- Make the current difficulty visible to the player.

### Timer and score
- Give each question a 15-second countdown.
- Display remaining time clearly and make the timer visually urgent near zero.
- Correct answers earn 100 points plus a small speed bonus based on remaining time.
- Incorrect answers and timeouts earn no points.
- Timeouts should be tracked separately from incorrect answers.
- Keep timer calculations based on elapsed time, not frame counts, so the timer remains accurate at different frame rates.

### Results
Show at least:
- Final score
- Number of correct answers
- Number of incorrect answers
- Number of timeouts
- Accuracy, clearly defined as correct answers divided by questions answered, excluding timeouts
- Final difficulty level

## 3. Question data format

Keep questions hardcoded in Python. Use a consistent structure such as:

```python
QUESTIONS = [
    {
        "question": "What is 7 + 5?",
        "options": ["10", "11", "12", "13"],
        "answer": 2,  # zero-based index
        "level": 1,   # 1, 2, or 3
        "explanation": "7 + 5 = 12."
    },
]
```

Requirements:
- `options` must contain exactly four options.
- `answer` must be an integer from 0 to 3.
- `level` must be 1, 2, or 3.
- Every question should include an explanation.
- Validate question data at startup and fail with a clear, helpful error if invalid.
- Include enough sample questions for a 10-question session, ideally 15 or more spread across all levels.
- Keep sample questions clearly identifiable so they can be replaced with the actual curriculum.
- Do not add a database, external API, or online question generation.

## 4. UI and design

Aim for a polished but achievable design:
- Window around 960 × 640, adaptable if the existing project has a different size.
- Dark, high-contrast theme with readable text.
- Clear title: `DEADLINE`.
- Show question number, score, difficulty, and timer.
- Render long questions without clipping; wrap question and explanation text.
- Use four large answer buttons in a 2 × 2 layout.
- Distinguish correct, incorrect, and timeout feedback using both text and color.
- Provide a visible progress indicator.
- Results screen should include a restart button and keyboard shortcut.
- Avoid unnecessary animations or assets. Do not spend time on elaborate visual effects before the MVP is stable.
- Keep UI event handling responsive and ensure feedback cannot be skipped by accidental extra clicks.

## 5. Suggested implementation sequence

Follow this order; do not begin optional features before all required MVP features work.

### Phase A — Inspect and plan (10–15 minutes)
- Inspect repository and existing setup.
- Identify the main entry point and current status.
- Choose the smallest implementation path.

### Phase B — Playable loop (45–60 minutes)
- Create or fix the Pygame window and main loop.
- Render question, options, score, timer, and progress.
- Implement mouse and keyboard answer input.
- Add correct/incorrect feedback and question progression.

### Phase C — Adaptive behavior (30–45 minutes)
- Implement level changes and streak resets.
- Add level-aware question selection and repeat avoidance.
- Track correct, incorrect, and timeout outcomes separately.
- Verify lower and upper difficulty boundaries.

### Phase D — Results and restart (20–30 minutes)
- Add final results screen.
- Add restart behavior that resets every session variable.
- Confirm all counters and score reset correctly.

### Phase E — Testing and integration (30–45 minutes)
- Run the game if the environment supports a display.
- Otherwise run static checks and automated unit tests for the game logic.
- Fix all critical bugs before adding polish.

### Phase F — Polish and handoff (remaining time)
- Improve spacing, text wrapping, button states, and feedback.
- Write concise README instructions.
- Test the demo flow from launch to results and restart.
- Stop adding features when there is one hour remaining; focus on stability.

## 6. Team split

For a 2-person team:
- **Person A:** Pygame UI, event handling, timer, feedback, results screen.
- **Person B:** Question bank, validation, adaptation rules, scoring, tests.
- Agree on data structures and function interfaces before parallel changes. Have one person own integration.

For a 3-person team:
- **Person A:** Pygame UI and visual polish.
- **Person B:** Question bank and adaptive game logic.
- **Person C:** Automated/manual testing, README, demo preparation, integration support.

Avoid having multiple people edit the same file simultaneously unless using branches or clear ownership.

## 7. Testing checklist

Verify each item and fix failures:

- [ ] Game starts and displays a question.
- [ ] Mouse selection works.
- [ ] Keyboard `1`–`4` selection works.
- [ ] Correct answer adds points and displays positive feedback.
- [ ] Wrong answer adds no points and reveals the correct option and explanation.
- [ ] Two consecutive correct answers increase difficulty by one.
- [ ] Two consecutive wrong answers decrease difficulty by one.
- [ ] Difficulty never goes below 1 or above 3.
- [ ] Correct answers reset the wrong-answer streak.
- [ ] Wrong answers reset the correct-answer streak.
- [ ] Timeout does not count as incorrect and resets both streaks.
- [ ] Timer does not continue to affect a question after it has been answered.
- [ ] Repeated clicks cannot answer one question more than once.
- [ ] Question selection avoids repeats until the bank is exhausted.
- [ ] A 10-question session reaches the results screen.
- [ ] Results counters and accuracy are correct.
- [ ] Restart resets score, timer, difficulty, counters, streaks, and used-question tracking.
- [ ] Closing the window or pressing `Esc` exits cleanly.
- [ ] Long question text and explanations do not overlap or clip.
- [ ] No uncaught exceptions occur during a complete demo.

If practical, isolate the adaptive logic into simple functions or a class so it can be unit-tested without opening a Pygame window.

## 8. Out of scope unless everything else is done

Do not implement these until the required MVP is complete and tested:
- Multiplayer or networking
- Accounts or authentication
- Database integration
- AI-generated questions
- Question editor
- Online leaderboards
- Complex animations or sound systems
- Large refactors or architectural patterns without clear value

Optional improvements, in order:
1. Show explanations after each answer.
2. Add a learning summary identifying missed questions.
3. Track performance by topic if questions have topic labels.
4. Save a high score locally in JSON.
5. Add small UI polish.

## 9. Definition of done

The MVP is complete when:
1. A user can launch the game, answer questions, see feedback, and finish a 10-question session.
2. Difficulty adapts according to the specified streak rules and stays within bounds.
3. Timer expiration is handled distinctly from a wrong answer.
4. Score and result statistics are correct.
5. Restart starts a genuinely fresh session.
6. The code runs without critical errors and the README explains setup and launch.
7. The agent reports which tests were run, which passed, and any known limitations.

## 10. Final instructions to the coding agent

- Start by inspecting the existing project; do not assume it is empty.
- Make actual code changes rather than returning only a plan.
- Prefer simple, readable Python over abstractions that slow delivery.
- Do not install unnecessary dependencies.
- Do not silently claim tests passed if they were not run.
- If a display is unavailable, use unit tests or headless checks for the game logic and clearly state that the interactive UI was not manually verified.
- Keep the core game playable at every milestone.
- At completion, summarize:
  - Files created or changed
  - Features implemented
  - Commands used to run and test
  - Test results
  - Remaining bugs or limitations
