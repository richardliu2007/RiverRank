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

def test_reopen_action():
    players = [
        Player("A", 100),
        Player("B", 100, folded=True),
        Player("C", 0, all_in=True),
        Player("D", 100),
    ]
    game = Game(1, 2, 0, players)
    game.action_idx = 0
    for player in game.players:
        player.to_act = False
    game.reopenAction(game.players[0])
    assert game.players[0].to_act == False
    assert game.players[1].to_act == False
    assert game.players[2].to_act == False
    assert game.players[3].to_act == True

def test_start_street():
    players = [
        Player("A", 100),
        Player("B", 100),
        Player("C", 100),
        Player("D", 100),
    ]
    game = Game(1, 2, 0, players)
    for player in game.players:
        player.to_act = False
    game.street = "flop"
    game._startStreet()
    assert game.action_idx == 1
    assert game.street == "flop"
    assert len(game.board) == 3
    assert game.outstanding_bet == 0
    assert game.toRaise == 0

def test_start_street_one_player():
    players = [
        Player("A", 100),
        Player("B", 100, folded=True),
        Player("C", 0, folded=True),
        Player("D", 100, folded=True),
    ]
    game = Game(1, 2, 3, players)
    game.street = "flop"
    game._startStreet()
    assert game.street == "showdown"