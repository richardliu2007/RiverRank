from types import SimpleNamespace
from unittest.mock import Mock
import pytest

from game.game_controller import (
    cardFormatter,
    promptAction,
    getBotAction,
    displayPlayerInfo,
    displayShowdownInfo,
    displayTableInfo,
    promptForInteger,
)
from game.game_engine import Game, Player


def test_prompt_for_integer_retries_after_invalid_input(monkeypatch, capsys):
    responses = iter(["not a number", "40"])
    monkeypatch.setattr("builtins.input", lambda _: next(responses))
    result = promptForInteger("Enter amount: ")
    assert result == 40
    assert "Please enter an integer." in capsys.readouterr().out


def test_card_formatter_formats_face_card_and_suit():
    assert cardFormatter((14, "s")) == "A♠"
    assert cardFormatter((10, "d")) == "10♦"


def test_display_table_info_reports_game_state_and_hides_eliminated_players(capsys):
    players = [
        Player("Alice"),
        Player("Bob"),
        Player("Carol"),
        Player("Eliminated", eliminated=True),
    ]
    game = Game(0, 1, 2, players, 2_000)
    game.pot = 150
    game.street = "flop"
    game.board = [(14, "s"), (10, "d"), (2, "c")]
    game.action_idx = 2
    players[0].folded = True
    players[1].all_in = True

    displayTableInfo(game)

    output = capsys.readouterr().out
    lines = output.splitlines()
    assert "*** Pot: 150 | Street: flop ***" in output
    assert f"Board: {' '.join(cardFormatter(card) for card in game.board)}" in output
    assert any("Alice" in line and "SB" in line and "FOLDED" in line for line in lines)
    assert any("Bob" in line and "BB" in line and "ALL-IN" in line for line in lines)
    assert any("Carol" in line and "BTN" in line and "TO ACT" in line for line in lines)
    assert "Eliminated" not in output


def test_display_player_info_reports_private_cards_and_bets(capsys):
    player = Player(
        "Alice",
        stack=1_750,
        cards=[(14, "h"), (13, "h")],
        total_bet=250,
        street_bet=50,
    )

    displayPlayerInfo(player)

    output = capsys.readouterr().out
    assert "Your stack: 1750" in output
    assert f"Your cards: {cardFormatter((14, 'h'))} {cardFormatter((13, 'h'))}" in output
    assert "Your total bet this hand: 250" in output
    assert "Your total bet this street: 50" in output


def test_display_showdown_info_reveals_eligible_hands_and_formats_pots(capsys):
    players = [
        Player("Alice", cards=[(14, "s"), (13, "s")]),
        Player("Bob", cards=[(10, "h"), (10, "d")]),
        Player("Folded", cards=[(2, "s"), (3, "s")], folded=True),
        Player("Eliminated", cards=[(4, "c"), (5, "c")], eliminated=True),
    ]
    showdown = Mock(
        return_value=[
            (300, 0, "Alice", 300, (5, 14)),
            (100, 1, "Bob", 100, (2, 10)),
        ]
    )
    game = SimpleNamespace(players=players, _showdown=showdown)

    displayShowdownInfo(game, game._showdown())

    output = capsys.readouterr().out
    showdown.assert_called_once_with()
    assert "Alice hand:" in output
    assert "Bob hand:" in output
    assert "Folded hand:" not in output
    assert "Eliminated hand:" not in output
    assert "Alice wins 300 from main pot of size 300 with: straight" in output
    assert "Bob wins 100 from side pot 1 of size 100 with: pair" in output

def create_action_game():
    players = [Player("Alice"), Player("Bob")]
    game = Game(0, 1, 1, players, 2_000)
    game.action_idx = 0
    return game, players[0]

def test_prompt_action_returns_check_without_amount(monkeypatch):
    game, player = create_action_game()
    monkeypatch.setattr("builtins.input", lambda _: "check")
    result = promptAction(player, game)
    assert result == {
        "action": "check",
        "amount": None,
    }

def test_prompt_action_reports_call_amount(monkeypatch, capsys):
    game, player = create_action_game()
    game.outstanding_bet = 50
    player.street_bet = 20
    monkeypatch.setattr("builtins.input", lambda _: "call")
    result = promptAction(player, game)
    assert result == {
        "action": "call",
        "amount": None,
    }
    assert "Amount to call: 30" in capsys.readouterr().out


def test_prompt_action_retries_invalid_bet_amounts(monkeypatch, capsys):
    game, player = create_action_game()
    responses = iter([
        "bet",
        "not a number",
        "10",  # Below the 20-chip minimum.
        "40",
    ])
    monkeypatch.setattr("builtins.input", lambda _: next(responses))
    result = promptAction(player, game)
    assert result == {
        "action": "bet",
        "amount": 40,
    }
    output = capsys.readouterr().out
    assert "Please enter an integer." in output

def test_prompt_action_returns_none_when_all_in_runout_is_needed(monkeypatch):
    players = [Player("Alice"), Player("Bob")]
    game = Game(0, 1, 1, players, 2_000)
    actor, opponent = players
    game.action_idx = 0
    game.outstanding_bet = 0
    opponent.all_in = True
    # Input must not be requested when the board should run out.
    def fail_if_prompted(_):
        pytest.fail("promptAction should not request input during an all-in runout")
    monkeypatch.setattr("builtins.input", fail_if_prompted)
    result = promptAction(actor, game)
    assert game._checkRunoutNeeded() is True
    assert result is None

def test_prompt_action_displays_amount_to_call(monkeypatch, capsys):
    players = [Player("Alice"), Player("Bob")]
    game = Game(0, 1, 1, players, 2_000)
    player = players[0]
    game.action_idx = 0
    game.outstanding_bet = 50
    player.street_bet = 20
    monkeypatch.setattr("builtins.input", lambda _: "call")
    result = promptAction(player, game)
    output = capsys.readouterr().out
    assert "Amount to call: 30" in output
    assert result == {
        "action": "call",
        "amount": None,
    }

def test_prompt_action_does_not_display_amount_to_call_when_call_is_unavailable(
    monkeypatch,
    capsys,
):
    players = [Player("Alice"), Player("Bob")]
    game = Game(0, 1, 1, players, 2_000)
    player = players[0]
    game.action_idx = 0
    game.outstanding_bet = 0
    monkeypatch.setattr("builtins.input", lambda _: "check")
    result = promptAction(player, game)
    output = capsys.readouterr().out
    assert "Amount to call:" not in output
    assert result == {
        "action": "check",
        "amount": None,
    }

def test_prompt_action_reprompts_after_invalid_action(monkeypatch):
    game, player = create_action_game()
    responses = iter(["raise", "check"])
    prompts = []
    def fake_input(prompt):
        prompts.append(prompt)
        return next(responses)
    monkeypatch.setattr("builtins.input", fake_input)
    result = promptAction(player, game)
    assert result == {"action": "check", "amount": None}
    assert len(prompts) == 2
    assert prompts[1].startswith("Try another action:")

def test_prompt_action_accepts_minimum_raise(monkeypatch):
    game, player = create_action_game()
    game.outstanding_bet = 50
    game.toRaise = 20
    player.street_bet = 20
    responses = iter(["raise", "70"])
    monkeypatch.setattr("builtins.input", lambda _: next(responses))
    result = promptAction(player, game)
    assert result == {
        "action": "raise",
        "amount": 70,
    }

def test_prompt_action_reprompts_after_undersized_raise(monkeypatch):
    game, player = create_action_game()
    game.outstanding_bet = 50
    game.toRaise = 20
    player.street_bet = 20
    responses = iter(["raise", "60", "70"])
    prompts = []
    def fake_input(prompt):
        prompts.append(prompt)
        return next(responses)
    monkeypatch.setattr("builtins.input", fake_input)
    result = promptAction(player, game)
    assert result == {
        "action": "raise",
        "amount": 70,
    }
    assert len(prompts) == 3
    assert prompts[2] == "Raise amount too low: "

def test_prompt_action_accepts_short_all_in_raise(monkeypatch):
    game, player = create_action_game()
    game.outstanding_bet = 50
    game.toRaise = 20
    player.street_bet = 20
    player.stack = 40  # Maximum raise target is 60, below the normal minimum of 70.
    responses = iter(["raise", "60"])
    prompts = []
    def fake_input(prompt):
        prompts.append(prompt)
        return next(responses)
    monkeypatch.setattr("builtins.input", fake_input)
    result = promptAction(player, game)

    assert result == {
        "action": "raise",
        "amount": 60,
    }
    assert len(prompts) == 2

# def test_prompt_action_caps_raise_at_players_available_chips(monkeypatch):
#     game, player = create_action_game()
#     game.outstanding_bet = 50
#     game.toRaise = 20
#     player.street_bet = 20
#     player.stack = 80  # Maximum raise target is 100.
#     responses = iter(["raise", "1000"])
#     monkeypatch.setattr("builtins.input", lambda _: next(responses))
#     result = promptAction(player, game)
#     assert result == {
#         "action": "raise",
#         "amount": 100,
#     }

def test_prompt_action_normalizes_case_and_whitespace(monkeypatch):
    game, player = create_action_game()
    monkeypatch.setattr("builtins.input", lambda _: "  ChEcK  ")
    result = promptAction(player, game)
    assert result == {
        "action": "check",
        "amount": None,
    }

def test_prompt_action_returns_fold_without_amount(monkeypatch):
    game, player = create_action_game()
    monkeypatch.setattr("builtins.input", lambda _: "fold")
    result = promptAction(player, game)
    assert result == {
        "action": "fold",
        "amount": None,
    }

def test_get_bot_action_returns_check_without_amount(monkeypatch):
    game, bot = create_action_game()
    monkeypatch.setattr(
        "game.game_controller.random.choice",
        lambda _: "check",
    )
    result = getBotAction(bot, game)
    assert result == {
        "action": "check",
        "amount": None,
    }


def test_get_bot_action_returns_call_without_amount(monkeypatch):
    game, bot = create_action_game()
    game.outstanding_bet = 50
    bot.street_bet = 20
    monkeypatch.setattr(
        "game.game_controller.random.choice",
        lambda _: "call",
    )
    result = getBotAction(bot, game)
    assert result == {
        "action": "call",
        "amount": None,
    }


def test_get_bot_action_returns_big_blind_bet(monkeypatch):
    game, bot = create_action_game()
    monkeypatch.setattr(
        "game.game_controller.random.choice",
        lambda _: "bet",
    )
    result = getBotAction(bot, game)
    assert result == {
        "action": "bet",
        "amount": game.blinds["big"],
    }


def test_get_bot_action_returns_none_when_all_in_runout_is_needed(
    monkeypatch,
):
    game, bot = create_action_game()
    opponent = game.players[1]
    opponent.all_in = True
    def fail_if_called(_):
        pytest.fail("random.choice should not run when a runout is needed")
    monkeypatch.setattr(
        "game.game_controller.random.choice",
        fail_if_called,
    )
    result = getBotAction(bot, game)
    assert game._checkRunoutNeeded() is True
    assert result is None


def test_get_bot_action_does_not_skip_remaining_call_decision(
    monkeypatch,
):
    game, bot = create_action_game()
    opponent = game.players[1]
    opponent.all_in = True
    game.outstanding_bet = 50
    bot.street_bet = 20
    monkeypatch.setattr(
        "game.game_controller.random.choice",
        lambda _: "call",
    )
    result = getBotAction(bot, game)
    assert game._checkRunoutNeeded() is True
    assert result == {
        "action": "call",
        "amount": None,
    }


def test_get_bot_action_returns_minimum_raise(monkeypatch):
    game, bot = create_action_game()
    game.outstanding_bet = 50
    game.toRaise = 20
    bot.street_bet = 20
    monkeypatch.setattr(
        "game.game_controller.random.choice",
        lambda _: "raise",
    )
    result = getBotAction(bot, game)
    assert result == {
        "action": "raise",
        "amount": 70,
    }


# def test_get_bot_action_caps_short_all_in_raise(monkeypatch):
#     game, bot = create_action_game()
#     game.outstanding_bet = 50
#     game.toRaise = 20
#     bot.street_bet = 20
#     bot.stack = 40  # can only raise to 60 vs. min raise of 70
#     monkeypatch.setattr(
#         "game.game_controller.random.choice",
#         lambda _: "raise",
#     )
#     result = getBotAction(bot, game)
#     assert result == {
#         "action": "raise",
#         "amount": 60,
#     }


# def test_get_bot_action_uses_remaining_stack_for_short_all_in_bet(
#     monkeypatch,
# ):
#     game, bot = create_action_game()
#     bot.stack = 10  #less than 20 min bet
#     monkeypatch.setattr(
#         "game.game_controller.random.choice",
#         lambda _: "bet",
#     )
#     result = getBotAction(bot, game)
#     assert result == {
#         "action": "bet",
#         "amount": 10,
#     }


def test_get_bot_action_returns_fold_without_amount(monkeypatch):
    game, bot = create_action_game()
    game.outstanding_bet = 50
    bot.street_bet = 20
    monkeypatch.setattr(
        "game.game_controller.random.choice",
        lambda _: "fold",
    )
    result = getBotAction(bot, game)
    assert result == {
        "action": "fold",
        "amount": None,
    }


def test_get_bot_action_reselects_fold_when_bot_can_check(monkeypatch):
    game, bot = create_action_game()
    selections = iter(["fold", "check"])
    monkeypatch.setattr(
        "game.game_controller.random.choice",
        lambda _: next(selections),
    )
    result = getBotAction(bot, game)
    assert result == {
        "action": "check",
        "amount": None,
    }
