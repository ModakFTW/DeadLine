# DeadLine — Project Architecture & Restoration Notes

## 1. Structure Restored
- **Core Engine & States**:
  - `main.py`: Full state machine covering all 10 states:
    - `menu` -> `subject_select` -> `memory` (Level 1) -> `platformer` (Level 2) -> `cage` (Level 3) -> `escape` (Level 3 Exit) -> `old_woman` (Level 4) -> `exam_gate` (Level 5) -> `win` / `game_over`
  - `game_state.py`: Cross-level data persistence container holding subject keywords, diagnostic quiz results, route choices, and Elo history.
  - `level_manager.py`: Procedural level builder integrating Markov chain generation and real-time Elo difficulty tracking with safe tutorial start and cage threshold.
  - `settings.py`: High-resolution display (1280x720) with 2x zoom internal rendering pipeline (640x360).
  - `ui.py`: Full UI system with heads-up display, subject selection menus, pause screens, and real-time F3 debug overlay.

## 2. AI / ML Components
- **Model 1: Markov Chain (`ai/obstacle_generator.py`)**:
  - Trained on 20 authentic training sequences in `data/training_sequences.json`.
  - Produces obstacle sequences across 3 difficulty tiers (`easy`, `medium`, `hard`).
- **Model 2: Elo Skill Rating Tracker (`ai/difficulty_tracker.py`)**:
  - Dynamically updates player skill score based on obstacle encounters with Elo K-factor (`SKILL_K = 0.5`).
- **Model 3: Monkey Decision Agent (`ai/monkey_ai.py`)**:
  - Proximity-based AI driving monkey state transitions (`idle`, `approach`, `steal`, `flee`).
- **Standalone Boss Fight (`boss_combat.py`, `boss.py`, `ai/boss_agent.py`)**:
  - Tabular Q-Learning boss agent with Computerized Adaptive Testing (CAT) intermissions.

## 3. Data & Assets
- `data/training_sequences.json`: Authentic Markov chain training sequences.
- `data/subjects/`:
  - `general_knowledge.json` (50 curated General Knowledge questions, distinct every run)
  - `computer_networks.json`
  - `database_management_systems.json`
  - `operating_systems.json`
- **Quiz Randomization**: `LevelMemory` dynamically shuffles and samples 10 distinct questions from the active subject bank so each game session presents a varied question set.
- **Bug Fix (Level 1 Quiz Rendering)**: Replaced fragile manual word-splitting and unconstrained rendering with robust `draw_wrapped_text` from `text_utils.py` across all question cards and option buttons in `LevelMemory`. Tested all 4 subject banks across all questions with zero crashes.


