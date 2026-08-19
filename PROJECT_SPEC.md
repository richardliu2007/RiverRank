# RiverRank Project Specification

## Project Overview
RiverRank is a free-to-play multiplayer no-limit Texas Hold'em tournament platform with skill-based matchmaking and a ranked ladder.

## Long-Term Goal
Players should be able to:
- create an account
- queue for ranked poker tournaments
- play multiplayer NLH
- gain or lose rating based on tournament results
- progress through visible ranks
- view rankings and statistics through a web interface

## Current Development Phase
Phase 1: Build a correct local poker engine.

Current goals:
- represent cards, decks, players, and game state
- implement NLH hand progression
- implement legal player actions
- implement betting
- implement hand evaluation
- implement pots and side pots
- support complete local games
- test the engine thoroughly

## Roadmap

### Phase 1 — Game Engine
Build and test a complete local poker engine.

### Phase 2 — Multiplayer
Allow multiple remote players to participate in the same game.

Exact networking architecture: TBD.

### Phase 3 — Web Application
Build a browser-based interface and connect it to the multiplayer game system.

Frontend framework: TBD.
Backend framework: TBD.

### Phase 4 — Ranked System
Add player ratings, matchmaking, ranks, and leaderboards.

Exact rating algorithm: TBD.

### Phase 5 — Deployment
Deploy RiverRank so external users can play it.

Hosting architecture: TBD.
Scaling strategy: TBD.

## Current Technical Decisions
Language: Python
Other technologies: TBD

## Open Questions
- How should the poker engine be structured?
- How should multiplayer networking work?
- What backend framework should be used?
- What frontend framework should be used?
- How should game state be synchronized?
- How should data be persisted?
- How should matchmaking work?
- How should ratings be calculated?
- How should the application be deployed?

These decisions should be made as the project reaches the relevant stage.