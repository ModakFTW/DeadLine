# PROJECT REBUILD BRIEF: Engineering Student Platformer (pygame)

You are rebuilding a pygame project that I accidentally deleted. Part of it was recovered. Follow this brief exactly. **Credits are very limited, so read the "Credit Rules" section first.**

---

## 0. Credit Rules (most important)

1. **Do NOT read the whole chat history.** A previous attempt did that and used up all my credits before writing any code.
2. **Do NOT scan or re-read the whole project every step.** Only open the files you need for the current task.
3. Work **one file at a time**. Write the file, run a quick check, then move on. Do not plan the whole game in long reasoning blocks.
4. Keep replies short. No long summaries, no re-explaining what you did. One or two lines per finished file.
5. Do not rewrite files that already work. Only edit what is broken or missing.
6. After each file works, tell me so I can commit it with git.

---

## 1. Game Description

A 2D platformer in **pygame**. An engineering student is trying to reach college and faces obstacles on the way. There are 6 levels:

| # | Type | Description |
|---|------|-------------|
| 1 | Quiz | Short revision quiz, only a few questions. **Save the player's answers**, since level 6 needs them. |
| 2 | Platformer | Run and jump through an Indian street setting, avoiding hazards. |
| 3 | Quiz | Another quiz round. |
| 4 | Platformer | Second platformer, harder than level 2. |
| 5 | Boss fight | Professor Terminus. Player attacks with a slingshot and a steel ruler slash. |
| 6 | Quiz | Final quiz. The player must **remember answers from level 1** to pass. |

An adaptive difficulty system exists in `ai/difficulty_tracker.py`.

---

## 2. What Already Exists (recovered, do not rewrite)

Read these only when needed:

- `sprite_loader.py`: complete. Loads and caches sprites and backgrounds. Imports `PLAYER_WIDTH, PLAYER_HEIGHT, SPIKE_WIDTH, SPIKE_HEIGHT, ENEMY_WIDTH, ENEMY_HEIGHT, TILE_SIZE` from `settings`.
- `camera.py`: complete, small.
- `ai/difficulty_tracker.py`: complete, small.
- `assets/sprites/`: `student_run_0..3.png`, `stray_dog_0.png`, `stray_dog_1.png`, `stray_dog_solo.png`, `traffic_cone.png`, `auto_rickshaw.png`, `student.jpg`, `ground_tiles.jpg`.
- Files with " 1" in the name (like `camera 1.py`) are duplicates. Ignore them or delete them.

## 3. What Is Missing (must be rebuilt)

- `settings.py` (constants, screen size, colors, physics values)
- `main.py` (game loop, state and level flow)
- `player.py` (movement, jump, gravity, collisions, health, combat)
- `levels/` (quiz levels, platformer levels, boss level)
- `data/subjects/` (question bank)
- Enemy and hazard classes: stray dog, traffic cone, auto rickshaw, grandma, monkey
- Boss class (Professor Terminus)
- Missing art: student combat sprites (idle, run, slingshot, ruler slash), grandma, monkey, boss, backgrounds

**Missing art rule:** `sprite_loader.py` already returns `None` when a PNG is missing. Draw simple colored rectangles or shapes as placeholders so the game runs now. Do not generate images.

---

## 4. Build Order (do in this order, stop after each step)

1. **`settings.py`**: infer constants from `sprite_loader.py` and `camera.py`. Suggested starting values: screen 1280x720, FPS 60, TILE_SIZE 48, PLAYER_WIDTH 56, PLAYER_HEIGHT 80, SPIKE 40x40, ENEMY 70x50.
2. **`player.py`**: movement, jump, gravity, tile collision, health, facing direction. Use `load_student_frames()` and `load_student_idle()`.
3. **Platformer level 2**: tile map, cone and dog and rickshaw hazards, camera follow, goal flag. Check it runs.
4. **Quiz engine + `data/subjects/`**: loads questions from JSON, 4 options each, shows score. **Stores level 1 answers in a shared save dict** (for example `game_state["level1_answers"]`).
5. **Level 1 and 3 quizzes** using the engine.
6. **Platformer level 4**: reuse level 2 code, add grandma and monkey hazards, more difficulty.
7. **Boss fight (level 5)**: Professor Terminus, player slingshot (ranged) and ruler slash (melee), boss health bar, attack and cast patterns.
8. **Level 6 final quiz**: questions generated from the saved level 1 answers.
9. **`main.py`**: state machine (menu, level 1 to 6, game over, win). Hook up `difficulty_tracker`.

After each step: run the game, fix errors, then say "step N done" and wait.

---

## 5. If You Get Stuck (history lookup, cheap method only)

Only look at chat history if you are **truly stuck** and cannot infer the answer from the code or this brief.

Do it like this:

1. **Never load the full history.** Search or skim for **one specific keyword** (for example `"level 6"`, `"difficulty"`, `"boss attack"`, `"questions"`).
2. Read only the **few messages around the match**, not the whole conversation.
3. Prefer **final code blocks and plan or walkthrough files** over long reasoning and tool output.
4. Stop reading as soon as you find the needed detail. Do not keep browsing.
5. If it is not found after **2 targeted lookups**, make a sensible assumption, write it down in one line, and ask me.
6. Never re-read a chat you already looked at. Note what you found in `NOTES.md` instead (one or two lines per item).

---

## 6. Rules for Output

- Python 3, pygame only. No extra libraries unless I approve.
- Keep each file readable and commented lightly, in the same style as `sprite_loader.py`.
- Keep a short `NOTES.md` with decisions made and assumptions, so nothing needs re-deriving later.
- Remind me to `git add . && git commit -m "..."` after each working step.

**Start with step 1 (`settings.py`) now. Do not read any history yet.**
