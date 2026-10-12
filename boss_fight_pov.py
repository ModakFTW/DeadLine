# boss_fight_pov.py — Standalone First-Person POV Boss Encounter Launcher
"""
Standalone POV Boss Fight Launcher (DOOM-Style First-Person Arena):
Allows testing the First-Person POV Q-Learning Boss Encounter immediately:

    python boss_fight_pov.py

Controls:
- Mouse: Aim crosshair directly
- Left Mouse Button (LMB): Primary Attack
    * Phase 1: Slingshot pebble
    * Phase 2: Steel Ruler Slash
    * Phase 3: Slingshot pebble
- Right Mouse Button (RMB) or U / C: Secondary Attack
    * Phase 2 & 3: Steel Ruler Slash
- A / D or Left / Right: Lateral Strafe
- C / Left Ctrl / S: Duck behind Lecture Desks (Cover blocks incoming fireballs!)
- K or Left Shift: Rapid Evasive Dodge Roll (i-frames)
- Number Keys 1-4: Answer CAT Exam Portal Questions during Phase Intermissions
- ESC: Exit to Desktop
"""

import sys
import pygame
from settings import DISPLAY_WIDTH, DISPLAY_HEIGHT, FPS, TITLE
from game_state import GameState
from boss_combat_pov import BossArenaPOVLevel


def main():
    pygame.init()
    pygame.font.init()
    display = pygame.display.set_mode((DISPLAY_WIDTH, DISPLAY_HEIGHT))
    pygame.display.set_caption(f"{TITLE} — [DOOM-STYLE FIRST-PERSON Q-LEARNING BOSS]")
    clock = pygame.time.Clock()

    game_state = GameState()
    arena = BossArenaPOVLevel(game_state)

    print("\n" + "=" * 70)
    print("  [DEADLINE] FIRST-PERSON POV (DOOM-STYLE) BOSS ENCOUNTER LAUNCHED")
    print("  * Perspective: 3D Projected Grand Exam Hall")
    print("  * Aiming: Mouse Cursor controls the HUD Crosshair")
    print("  * Controls: [A/D] Strafe | [C/Ctrl] Duck in Cover | [LMB] Shoot/Slash | [Shift] Dodge")
    print("  * Boss AI: Tabular Q-Learning Agent (9 States x 4 Actions, Live Bellman updates)")
    print("=" * 70 + "\n")

    running = True
    while running:
        clock.tick(FPS)
        events = pygame.event.get()

        for event in events:
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE and not arena.in_quiz:
                    running = False

        if not running:
            break

        # Arena input & update
        transition = arena.handle_events(events)
        if transition is None:
            transition = arena.update()

        # Render POV arena
        arena.draw(display)
        pygame.display.flip()

        if transition is not None:
            print(f"\n[ENCOUNTER RESULT] Transition signal received: {transition.upper()}")
            if transition == "win":
                print("★ VICTORY! Professor Terminus defeated in First-Person Combat!")
            elif transition == "game_over":
                print("GAME OVER! Fallen in combat against the Q-Learning Boss.")
            pygame.time.wait(1500)
            running = False

    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    main()
