# RiverRank
RiverRank is a free-to-play multiplayer poker platform built around skill-based matchmaking and a distinctive ranked ladder.

# Motivation
Most online poker sites fall into one of two categories:
1. Play-money platforms, with virtual chips where players have limited incentive to play seriously due to chips having little long-term significance
2. Real-money platforms, which are either undesirable or inaccessible to many players

The purpose of RiverRank is to create an alternative: a platform where players compete in free tournaments, gain or lose rating based on their performance, and progress through a clear ranking system without wagering money

Player ratings will correspond to visible ranks (and badges):
- Bronze
- Silver
- Gold
- Platinum 
- Diamond
- Master 
- Grandmaster
- Legend

The ranked ladder will offer a tangible measurement of progress and achievement beyond the virtual chips used in individual games


# Status

RiverRank v0.1 provides a local, terminal-playable no-limit Texas Hold'em game with one human player and five basic automated opponents. The deck, hand evaluator, and core engine have automated test coverage, and the game controller has basic integration tests.

Networking, user accounts, ranked matchmaking, persistence, and the web interface are in development.

# Supported Gameplay

- One human player against five automated opponents
- Tournament-style play with 2,000 starting chips per player
- Fixed small and big blinds of 10 and 20 chips
- Dealer, small-blind, and big-blind rotation, including heads-up positioning
- Preflop, flop, turn, river, and showdown progression
- Checking, calling, betting, raising, folding, and all-in calls
- Community-card dealing and seven-card hand evaluation
- Main pots, side pots, split pots, and deterministic odd-chip distribution
- Player elimination and game completion
- Concise & intuitive game output in terminal

# Python Version

RiverRank requires Python 3.12 or newer. The playable game uses only the Python standard library.

# Launching the Game

From the repository root, run:

```powershell
python -m game.game_controller
```

Enter a username when prompted. The game continues until the human player is eliminated or wins the tournament, or when Ctrl + C is input.

# Terminal Controls

Enter one of the actions displayed in the prompt:

| Input | Meaning |
| --- | --- |
| `check` | Pass action to next player; no chips committed |
| `call` | Match the current outstanding bet; go all-in if unable to match bet |
| `bet` | Make the first bet on a postflop street; enter desired chip amount separately |
| `raise` | Raise the outstanding bet, then enter the total amount to which you are raising (total amount committed on the current street) |
| `fold` | Surrender the hand. |

Input is case-insensitive. Press `Ctrl+C` to exit the game cleanly.

# Running Tests

Run the complete automated suite from the repository root:

```powershell
python -m pytest game/testing
```

# Known Limitations

- Short all-in raise action-reopening semantics are not supported in v0.1.
- Bots use a primitive randomized strategy
- Increasing blind amounts over time not implemented
- Games cannot be saved or resumed
- Play is local and single-player

# Architecture

- [`game/deck.py`](game/deck.py) owns deck creation, shuffling, dealing, burning.
- [`game/hand_evaluation.py`](game/hand_evaluation.py) evaluates 5 community cards with a player's 2 cards and returns lexicographically comparable tuples representing the best 5-card hand formed.
- [`game/game_engine.py`](game/game_engine.py) defines player abstractions, authoritative game state, turn order, betting state, street transitions, pots, showdown settlement, elimination, and game completion.
- [`game/game_controller.py`](game/game_controller.py) runs the terminal game loop, displays state, gathers human input, selects bot actions, and coordinates engine operations.