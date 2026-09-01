from game.game_controller import cardFormatter
from game.game_controller import promptForInteger


def test_prompt_for_integer_retries_after_invalid_input(monkeypatch, capsys):
    responses = iter(["not a number", "40"])
    monkeypatch.setattr("builtins.input", lambda _: next(responses))
    result = promptForInteger("Enter amount: ")
    assert result == 40
    assert "Please enter an integer." in capsys.readouterr().out

def test_card_formatter_formats_face_card_and_suit():
    assert cardFormatter((14, "s")) == "A♠"
    assert cardFormatter((10, "d")) == "10♦"
