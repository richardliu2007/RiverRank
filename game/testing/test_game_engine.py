from game.game_engine import Game, Player

def test_next_seat_returns_next_player():
    players = [
        Player("A", 100),
        Player("B", 100),
        Player("C", 100),
    ]
    game = Game(1, 2, 0, players)
    assert game._nextSeat(0) == 1
    assert game._nextSeat(2) == 0

def test_next_action_seat_skips_ineligible_players():
    players = [
        Player("A", 100),
        Player("B", 100, folded=True),
        Player("C", 0, all_in=True),
        Player("D", 100),
    ]
    game = Game(1, 2, 0, players)
    game.action_idx = 0
    game._nextAct()
    assert game.action_idx == 3