# AI Arena: reusable Tron foundation

Python 3.10+; no dependencies. These are heuristic bots, not trained neural networks.

## Run

From this folder:

```bash
python tron.py --seed 42 --output replay.json
python -m unittest discover -v
```

Open viewer.html in a browser and select replay.json. The viewer works offline.

## Initial assignments (editable, not permanent personalities)

| Color | Algorithm | Decision rule |
|---|---|---|
| Red | aggressive | Close distance to opponents while retaining space |
| Blue | defensive | Maximize reachable space, mobility, and separation |
| Green | territory | Prefer cells it can reach before opponents |
| Yellow | lookahead | Bounded beam search through its own possible future trails |

Every algorithm includes immediate collision avoidance. Aggressive currently pursues opponents; it does not explicitly search for traps. Territory uses shortest-path ownership as an estimate, not guaranteed captured land. Lookahead models its own future trail with stationary opponents; it is not adversarial minimax. Depth 6 and beam width 12 are the default. Depth 10 is configurable but does not exhaustively examine every 10-move continuation. Algorithm strength has not been benchmarked.

## Reuse and roster

teams.json keeps rider ID, team, color, algorithm, spawn, heading, and search depth separate. Change only algorithm to swap strategies. Add or remove rider entries for 1v1 or free-for-all matches. Keep at least two unique IDs and distinct valid spawn cells. Heading: 0 up, 1 right, 2 down, 3 left.

Reserve red_1 through red_3 (and equivalent IDs for other colors) for the three-member rosters. Use the ID as the persistent character identity; assign strategy per episode. The default duel activates Red and Blue only. The viewer requires exactly two riders and renders continuous glowing trails with interpolated movement; the simulation still uses grid turns. Teammates currently collide like opponents, and the engine declares an individual survivor; cooperative team scoring is a future extension.

## Rules and architecture

Arena owns board state and simultaneous collision resolution. choose reads the same pre-move board for each rider. run supplies a seeded random generator, stops at one survivor or a tick limit, and saves a replay. The viewer consumes the replay without running AI.

Trails persist after death. Wall/trail collision kills a rider. Multiple riders entering the same cell all die. Swapping occupied head cells kills both. Reversing is illegal. Tick-limit matches are draws; no arbitrary space-based winner is awarded.

Replay JSON includes schema version, seed, configuration, initial state, per-tick positions/alive IDs/actions/deaths, and result. Record the code version alongside replays when changing algorithms; seed alone cannot reproduce results across code changes.

## Production next steps

1. Benchmark strategies with rotated spawn positions and swapped colors, using a fixed seed schedule.
2. Add character faces and event-triggered reactions to rendering.
3. Build a vertical video renderer using the same replay, then add audio and publishing copy.
4. Target 45–60 second edits using multiple rounds or selective pacing. Simulation length and viewer playback do not enforce video duration; this starter does not export MP4.
5. Track individual and team records from actual played results.

For 1-step versus 10-step experiments, assign lookahead to both riders and set depth to 1 versus 10. Keep search width, other settings, and spawn rotation consistent. Other evaluation heuristics still contribute to both bots' decisions, so describe this as search depth rather than claiming one bot only perceives a single cell.
