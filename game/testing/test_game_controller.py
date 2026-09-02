from types import SimpleNamespace
from unittest.mock import Mock

from game.game_controller import (
    cardFormatter,
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
