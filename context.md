# CONTEXT: DeadLine (Adaptive AI Platformer)

## 1. Project Overview
- **Game Title**: DeadLine
- **Core Theme**: An Indian engineering student rushes to college facing civic street obstacles, cognitive riddles, and an acrobatic thief monkey to reach the semester examination hall.
- **Tech Stack**: Python 3.12, Pygame 2.6.1 (pure Python, zero external ML dependencies for full academic explainability).
- **Display Resolution**: High-Definition UI & Menus at 1280x720 (`DISPLAY_WIDTH` x `DISPLAY_HEIGHT`), with an internal 640x360 2x zoom rendering canvas for platformer gameplay.

---

## 2. Core Game Architecture & Level Pipeline

```
[Main Menu] (Clean direct start: Press ENTER to Begin)
    ↓
[Level 1: Diagnostic Evaluation] (General Knowledge: 5 randomized questions → Knowledge Score 0-10; scoring ≥4/5 unlocks Auto-Rickshaw Powerup in Level 2)
    ↓
[Level 2: Adaptive Platformer] (Markov Chain level generator seeded by Knowledge Score + Elo Tracker; blurred & dimmed Indian City Street parallax background)
    ↓
[Level 3: The Cage] (3 Riddles on ancient parchment → determines escape route)
    ↓
[Level 3 Exit: Escape] (Route A: Portal / Route B/C: Tunnel; dynamic fill-in-the-blank question randomized every run)
    ↓
[Level 4: Old Woman & Monkey] (Civic empathy escort with reactive acrobatic Monkey AI; proportionate street crossing avenue)
    ↓
[Level 5: The Exam Terminal — Wordle Cipher] (Information-Theoretic Wordle puzzle; balanced single-letter clue with max 1 hint limit)
    ↓
[Win / Game Over Screen] (Displays final Elo progression curve, clears, and deaths)
```

### Standalone Arenas
- `boss_combat.py` / `boss_fight_pov.py`: Tabular Q-Learning Professor Terminus boss combat with Computerized Adaptive Testing (CAT) intermissions.

---

## 3. AI / Machine Learning Models

1. **Model 1: Markov Chain (`ai/obstacle_generator.py`)**
   - Trained on 20 transition sequences in `data/training_sequences.json`.
   - Generates obstacle sequences (`gap`, `spike`, `moving_platform`, `enemy`) across three transition matrices (`easy`, `medium`, `hard`).

2. **Model 2: Elo Rating Tracker (`ai/difficulty_tracker.py`)**
   - Continuously monitors player success/failure when encountering obstacles.
   - Adjusts skill rating in real-time with an Elo K-factor (`SKILL_K = 0.5`).
   - Dynamically modulates obstacle spacing and pitfall gap widths (2-tile gaps on easy vs 3-tile gaps on medium/hard).

3. **Model 3: Acrobatic Spatial Monkey AI (`ai/monkey_ai.py`)**
   - Reactive agent modeling spatial proximity, player occlusion, and possession of loot.
   - Performs mid-air vaults over the player to snatch grandmother's handbag, and retreats when player shouts/jumps nearby.

4. **Model 4: Shannon Entropy Wordle Engine (`ai/wordle_engine.py`)**
   - Implements Information Theory constraint satisfaction over ternary pattern outcomes (Green/Yellow/Gray).
   - Computes expected information gain in bits: $E[I(g)] = \sum_p P(p) \log_2(1 / P(p))$.
   - Recommends optimal entropy hint on demand [Press H] to assist the student in pruning the candidate space.

---

## 4. Subject Dataset (`data/subjects/`)

- `general_knowledge.json`: 50 diverse GK questions (randomly sampled to 5 each game run), 3 riddles, escape keyword `KNOWLEDGE`. Single unified subject curriculum for seamless gameplay.

---

## 5. File Inventory & Roles

| File | Purpose |
| :--- | :--- |
| `main.py` | State machine controller, global exception logger, game loop |
| `game_state.py` | Persistent cross-level dataclass container |
| `settings.py` | Game constants, colors, physics values, and difficulty parameters |
| `ui.py` | UI renderer (HUD, menus, pause overlay, F3 debug overlay, win/loss screens) |
| `player.py` | Player physics, movement, coyote time, and platform collision handling |
| `camera.py` | Smooth horizontal camera follower |
| `sprite_loader.py` | Caching sprite loader with fallback geometric shapes |
| `obstacles.py` | Ground, spike, gap, floating moving platform, and stray dog hazard classes |
| `level_manager.py` | Platformer world builder connecting Markov Chain and Elo tracker |
| `text_utils.py` | Multi-line text wrapping and auto-fitting utility |
| `ai/obstacle_generator.py` | Markov Chain sequence generator with tiered probability tables |
| `ai/difficulty_tracker.py` | Real-time Elo skill rating and difficulty tracker |
| `ai/monkey_ai.py` | Spatial decision agent for Level 4 monkey |
| `levels/base_level.py` | Base abstract level interface (`handle_events`, `update`, `draw`) |
| `levels/level_memory.py` | Level 1: Diagnostic evaluation quiz |
| `levels/level_platformer.py`| Level 2: Adaptive street platformer |
| `levels/level_cage.py` | Level 3: Dungeon cage with 3 riddles |
| `levels/level_escape.py` | Level 3 Exit: Route A/B/C riddle keyword entry |
| `levels/level_oldwoman.py` | Level 4: Grandmother street escort with monkey AI |
| `levels/level_examgate.py` | Level 5: College exam gate word recall challenge |

---

## 6. How to Run & Controls

```bash
python main.py
```

- **Movement**: Arrow Keys or `A` / `D`
- **Jump**: `Space`, `W`, or `Up Arrow`
- **Quiz / Riddles**: Keys `1`–`4` / `A`–`D`, mouse click, or type answer + `Enter`
- **Debug Info**: Press `F3` during the platformer to view real-time Elo rating and Markov states
- **Pause**: `Esc`

---

## 7. DEADLINE Adaptive Educational Game MVP (Completed)

Implemented strictly according to the specifications in `DEADLINE_AGENT_BRIEF.md`:

### Implemented Architecture
- `adaptive_quiz/questions.py`:
  - 21 hardcoded questions (Math, Logic, Computer Architecture, Data Structures, Algorithms) across Levels 1, 2, and 3.
  - Startup schema validation (`validate_questions`) ensuring $\ge 15$ questions, 4 options, valid 0-3 index answer, level 1-3, and explanations.
- `adaptive_quiz/engine.py`:
  - Transparent rule-based adaptive engine decoupled from Pygame for headless testability.
  - Streak tracking: 2 consecutive correct $\rightarrow$ level + 1 (max 3); 2 consecutive incorrect $\rightarrow$ level - 1 (min 1).
  - Opposite streak resets on answer; timeout resets both streaks with no level drop.
  - Non-repeating question selection matching current difficulty before falling back across tiers.
  - Scoring: 100 base points + speed bonus ($\text{int}(10 \times \text{time\_remaining})$).
  - Accuracy calculation: $\frac{\text{Correct}}{\text{Correct} + \text{Incorrect}}$ excluding timeouts.
- `deadline_quiz.py`:
  - Standalone 960x640 Pygame application.
  - 15-second wall-clock countdown timer with visual urgency (yellow $< 5\text{s}$, flashing red $< 3\text{s}$).
  - 2x2 responsive button layout with keyboard `1`–`4` and mouse click answering.
  - Click-lock preventing multiple answers per question.
  - Feedback overlay showing correct answer, explanation, and point rewards without text clipping.
  - Results screen with complete metrics, restart via `R` or button, and clean exit via `Esc`.
- `main.py` & `ui.py`:
  - Main menu provides one-key access (`Q`) to launch the Standalone Adaptive Quiz Mode directly alongside Story Mode.

### Verification & Test Suite
- `tests/test_adaptive_engine.py`: 7 automated unit tests covering streak transitions, clamping at bounds, opposing streak resets, timeout streak handling, scoring formula, accuracy calculation, and clean session restarts.
- Run tests:
  ```bash
  python -m unittest tests/test_adaptive_engine.py
  ```
- Run standalone quiz:
  ```bash
  python deadline_quiz.py
  ```


