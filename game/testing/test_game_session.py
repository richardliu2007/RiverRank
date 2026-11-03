from copy import deepcopy

import pytest

from game.backend.game_session import GameSession
from game.game_engine import Game, Player


@pytest.fixture
def session():
    players = [Player("Alice"), Player("Bob")]
    game = Game(0, 1, 1, players, 100)
    game._startHand()
    players[0].cards = [(13, "s"), (13, "h")]
    players[1].cards = [(14, "s"), (14, "h")]
    # Deck draws from the end: burn, flop, burn, turn, burn, river.
    game.deck.deck = list(reversed([
        (3, "s"), (2, "c"), (7, "d"), (9, "h"),
        (4, "s"), (11, "c"), (5, "s"), (12, "d"),
    ]))
    return GameSession(game)


def test_fold_awards_pot_to_last_opponent(session):
    game = session.game
    alice, bob = game.players

    assert session.submit_action(alice, {"action": "fold"}) is True

    assert alice.folded is True
    assert alice.stack == 90
    assert bob.stack == 110
    assert game.pot == 0
    assert game.handEnded is True
    assert game.action_idx is None
    assert game.board == []


def test_rejected_action_does_not_increment_version(session):
    alice, bob = session.game.players
    assert session.submit_action(alice, {"action": "call"}) is True
    version_before = session.version

    # Bob has matched the bet already, so calling is illegal.
    assert session.submit_action(bob, {"action": "call"}) is False

    assert session.version == version_before


def test_successful_action_increments_version_exactly_once(session):
    alice = session.game.players[0]
    version_before = session.version

    assert session.submit_action(alice, {"action": "call"}) is True

    assert session.version == version_before + 1
    assert session.game.street == "preflop"
    assert session.game.action_idx == 1


def test_action_with_automatic_street_transition_increments_version_once(session):
    alice, bob = session.game.players
    assert session.submit_action(alice, {"action": "call"}) is True
    version_before = session.version

    assert session.submit_action(bob, {"action": "check"}) is True

    assert session.game.street == "flop"
    assert len(session.game.board) == 3
    assert session.version == version_before + 1


def test_completed_preflop_betting_advances_to_flop(session):
    game = session.game
    alice, bob = game.players

    assert session.submit_action(alice, {"action": "call"}) is True
    assert game.street == "preflop"
    assert session.submit_action(bob, {"action": "check"}) is True

    assert game.street == "flop"
    assert game.board == [(2, "c"), (7, "d"), (9, "h")]
    assert game.handEnded is False
    assert game.action_idx == 1
    assert game.pot == 40
    assert game.outstanding_bet == 0
    assert all(p.stack == 80 and p.street_bet == 0 and p.to_act for p in game.players)
    assert sum(p.stack for p in game.players) + game.pot == 200


def test_all_in_with_outstanding_call_waits_for_opponent(session):
    game = session.game
    alice, bob = game.players

    assert session.submit_action(alice, {"action": "raise", "amount": 100}) is True

    assert alice.all_in is True
    assert alice.stack == 0
    assert bob.stack == 80
    assert bob.to_act is True
    assert game.outstanding_bet - bob.street_bet == 80
    assert game.action_idx == 1
    assert game.street == "preflop"
    assert game.board == []
    assert game.handEnded is False
    assert game.pot == 120
    assert len(game.deck.deck) == 8


def test_resolved_all_in_call_runs_out_board_and_settles_showdown(session):
    game = session.game
    alice, bob = game.players
    assert session.submit_action(alice, {"action": "raise", "amount": 100}) is True

    assert session.submit_action(bob, {"action": "call"}) is True

    assert game.board == [(2, "c"), (7, "d"), (9, "h"), (11, "c"), (12, "d")]
    assert game.street == "showdown"
    assert game.handEnded is True
    assert game.action_idx is None
    assert game.pot == 0
    assert alice.stack == 0
    assert bob.stack == 200
    assert sum(p.stack for p in game.players) == 200


@pytest.mark.parametrize("action", [
    {"action": "check"},
    {"action": "bet", "amount": 20},
    {"action": "raise", "amount": 30},
    {"action": "raise", "amount": "100"},
    {"action": "raise"},
    {"action": "unknown"},
    {},
    None,
])
def test_invalid_action_preserves_entire_game_state(session, action):
    game = session.game

    def snapshot():
        return deepcopy({
            **vars(game),
            "players": [vars(p) for p in game.players],
            "deck": vars(game.deck),
        })

    before = snapshot()

    assert session.submit_action(game.players[0], action) is False

    assert snapshot() == before


def test_unmatched_excess_is_returned_when_larger_bettor_loses(session):
    game = session.game
    alice, bob = game.players
    # Alice started with 200 chips; Bob started with 100.
    alice.stack = 190
    assert sum(p.stack for p in game.players) + game.pot == 300
    assert session.submit_action(alice, {"action": "raise", "amount": 200}) is True
    assert game.handEnded is False
    assert game.pot == 220

    assert session.submit_action(bob, {"action": "call"}) is True

    # Bob's aces win the 200-chip contested pot. Alice gets her excess 100 back.
    assert alice.total_bet == 200
    assert bob.total_bet == 100
    assert alice.stack == 100
    assert bob.stack == 200
    assert game.pot == 0
    assert game.street == "showdown"
    assert game.handEnded is True
    assert game.action_idx is None
    assert sum(p.stack for p in game.players) == 300
