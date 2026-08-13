from game.game_engine import Game, Player
import pytest

def test_next_seat_returns_next_player():
    players = [
        Player("A"),
        Player("B"),
        Player("C"),
    ]
    game = Game(1, 2, 0, players, 2000)
    assert game._nextSeat(0) == 1
    assert game._nextSeat(2) == 0

def test_next_action_seat_skips_ineligible_players():
    players = [
        Player("A"),
        Player("B", folded=True),
        Player("C", all_in=True),
        Player("D"),
    ]
    game = Game(1, 2, 0, players, 2000)
    game.action_idx = 0
    game._nextAct()
    assert game.action_idx == 3

def test_next_seat_skips_eliminated_player():
    players = [
        Player("A"),
        Player("B", eliminated=True),
        Player("C")
    ]
    game = Game(1, 2, 0, players, 2000)
    assert game._nextSeat(0) == 2

def test_next_seat_returns_none_when_no_seat_is_available():
    players = [
        Player("A"),
        Player("B", eliminated=True),
    ]
    game = Game(0, 1, 0, players, 2000)
    assert game._nextSeat(0) is None

def test_reopen_action():
    players = [
        Player("A"),
        Player("B", folded=True),
        Player("C", all_in=True),
        Player("D"),
    ]
    game = Game(1, 2, 0, players, 2000)
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
        Player("A"),
        Player("B"),
        Player("C"),
        Player("D"),
    ]
    game = Game(1, 2, 0, players, 2000)
    for player in game.players:
        player.to_act = False
    game.street = "flop"
    game._startStreet()
    assert all(player.to_act for player in players)
    assert all(player.street_bet == 0 for player in players)
    assert len(game.board) == 3
    assert all(len(card) == 2 for card in game.board)
    assert len(game.deck.deck) == 48

def test_start_street_one_player():
    players = [
        Player("A"),
        Player("B", folded=True),
        Player("C", folded=True),
        Player("D", folded=True),
    ]
    game = Game(1, 2, 3, players, 2000)
    game.street = "flop"
    game._startStreet()
    assert game.handEnded == True
    assert game.street == "flop"

def test_start_street_selects_first_player_who_can_act():
    players = [
        Player("Dealer"),
        Player("Folded", folded=True),
        Player("All-in", all_in=True),
        Player("Actor"),
    ]
    game = Game(1, 2, 0, players, 2000)
    game.street = "flop"
    game._startStreet()
    assert game.action_idx == 3

def total_chips(game):
    return sum(player.stack for player in game.players) + game.pot

def test_commit_updates_all_chip_locations():
    player = Player("A")
    game = Game(0, 1, 0, [player, Player("B")], 2000)
    initial_chips = total_chips(game)
    committed = game._commit(player, 30)
    assert total_chips(game) == initial_chips
    assert committed == 30
    assert player.stack == 1970
    assert player.street_bet == 30
    assert player.total_bet == 30
    assert game.pot == 30
    assert player.all_in is False

def test_commit_caps_at_remaining_stack():
    player = Player("A")
    game = Game(0, 1, 0, [player, Player("B")], 2000)
    initial_chips = total_chips(game)
    committed = game._commit(player, 2002)
    assert total_chips(game) == initial_chips
    assert committed == 2000
    assert player.stack == 0
    assert player.street_bet == 2000
    assert player.total_bet == 2000
    assert game.pot == 2000
    assert player.all_in is True

def test_commit_rejects_negative_amount():
    player = Player("A")
    game = Game(0, 1, 0, [player, Player("B")], 2000)
    initial_chips = total_chips(game)
    with pytest.raises(ValueError):
        game._commit(player, -10)
    assert total_chips(game) == initial_chips
    assert player.stack == 2000
    assert player.total_bet == 0
    assert player.street_bet == 0
    assert game.pot == 0

def test_start_hand_posts_blinds_as_contributions():
    players = [Player("A"), Player("B"), Player("C")]
    game = Game(1, 2, 0, players, 2000)
    initial_chips = total_chips(game)
    game._startHand()
    small_blind = players[game.sb_idx]
    big_blind = players[game.bb_idx]
    assert small_blind.street_bet == 10
    assert small_blind.total_bet == 10
    assert big_blind.street_bet == 20
    assert big_blind.total_bet == 20
    assert game.pot == 30
    assert game.outstanding_bet == 20
    assert total_chips(game) == initial_chips

def test_start_hand_deals_two_unique_cards_to_each_active_player():
    players = [Player("A"), Player("B"), Player("C")]
    game = Game(1, 2, 0, players, 2000)
    game._startHand()
    dealt = [
        card
        for player in players
        for card in player.cards
    ]
    assert all(len(player.cards) == 2 for player in players)
    assert len(dealt) == 6
    assert len(set(dealt)) == 6
    assert len(game.deck.deck) == 46

def test_start_hand_preserves_total_chips():
    players = [Player("A"), Player("B"), Player("C")]
    game = Game(1, 2, 0, players, 2000)
    initial_chips = total_chips(game)
    game._startHand()
    assert total_chips(game) == initial_chips

def test_only_unfolded_player_wins_pot():
    players = [
        Player("Winner"),
        Player("B", folded=True),
        Player("C", folded=True),
    ]
    game = Game(1, 2, 0, players, 2000)
    game.pot = 90

    winner_stack_before = players[0].stack
    total_before = total_chips(game)

    game.street = "flop"
    game._startStreet()

    assert players[0].stack == winner_stack_before + 90
    assert game.pot == 0
    assert game.handEnded is True
    assert total_chips(game) == total_before

def test_all_in_players_run_out_board():
    players = [
        Player("A", all_in=True),
        Player("B", all_in=True),
        Player("Folded", folded=True),
    ]
    game = Game(1, 2, 0, players, 2000)
    players[0].stack = 0
    players[0].all_in = True
    players[1].stack = 0
    players[1].all_in = True
    game.street = "flop"
    game._startStreet()
    assert len(game.board) == 5
    assert game.street == "showdown"

def test_start_street_resets_street_state():
    players = [Player("A"), Player("B"), Player("C")]
    game = Game(1, 2, 0, players, 2000)
    for player in players:
        player.street_bet = 50
        player.to_act = False
    game.outstanding_bet = 50
    game.toRaise = 30
    game.street = "flop"
    game._startStreet()
    assert all(player.street_bet == 0 for player in players)
    assert all(player.to_act for player in players)
    assert game.outstanding_bet == 0
    assert game.toRaise == 0

def test_all_in_runout_from_turn_adds_turn_and_river():
    players = [Player("A"), Player("B")]
    game = Game(0, 1, 0, players, 2000)
    game.board = [(2, "s"), (7, "d"), (11, "c")]
    game.street = "turn"
    for player in players:
        player.all_in = True
        player.stack = 0
    game._startStreet()
    assert len(game.board) == 5
    assert game.street == "showdown"

def test_showdown_does_not_mutate_board():
    players = [Player("A"), Player("B"), Player("C")]
    game = Game(0, 1, 2, players, 2000)
    game._flop()
    game._turn()
    game._river()
    board_before = list(game.board)
    game._showdown()
    assert game.board == board_before
    assert game.handEnded is True
    assert game.action_idx is None

def test_short_stack_only_wins_main_pot():
    players = [Player("A"), Player("B"), Player("C")]
    game = Game(0, 1, 2, players, 2000)
    game.players[0].stack = 100
    game.players[1].stack = 300
    game.players[2].stack = 300
    game.board = [(3, 's'), (3, 'h'), (3, 'd'), (2, 's'), (6, 'c')]
    game.players[0].cards = [(3, 'c'), (14, 'c')]
    game.players[1].cards = [(13, 'c'), (13, 'd')]
    game.players[2].cards = [(14, 'd'), (14, 's')]
    game._commit(game.players[0], 100)
    game._commit(game.players[1], 200)
    game._commit(game.players[2], 200)
    game._showdown()
    assert game.players[0].stack == 300
    assert game.players[1].stack == 100
    assert game.players[2].stack == 300
    assert game.pot == 0

def test_folded_contributes_but_cannot_win_pot():
    players = [Player("A"), Player("B"), Player("C")]
    game = Game(0, 1, 2, players, 2000)
    game.players[0].stack = 300
    game.players[1].stack = 300
    game.players[2].stack = 300
    game.board = [(3, 's'), (3, 'h'), (3, 'd'), (2, 's'), (6, 'c')]
    game.players[0].cards = [(3, 'c'), (14, 'c')]
    game.players[1].cards = [(13, 'c'), (13, 'd')]
    game.players[2].cards = [(14, 'd'), (14, 's')]
    game._commit(game.players[0], 100)
    game.players[0].folded = True
    game._commit(game.players[1], 200)
    game._commit(game.players[2], 200)
    game._showdown()
    assert game.players[0].stack == 200
    assert game.players[1].stack == 100
    assert game.players[2].stack == 600
    assert game.pot == 0

def test_multiple_side_pots():
    players = [Player("A"), Player("B"), Player("C"), Player("D")]
    game = Game(0, 1, 2, players, 2000)
    game.players[0].stack = 100
    game.players[1].stack = 200
    game.players[2].stack = 300
    game.players[3].stack = 300
    game.board = [(3, 's'), (3, 'h'), (3, 'd'), (2, 's'), (6, 'c')]
    game.players[0].cards = [(3, 'c'), (14, 'c')]
    game.players[1].cards = [(13, 'c'), (13, 'd')]
    game.players[2].cards = [(14, 'd'), (14, 's')]
    game.players[3].cards = [(12, 'd'), (12, 's')]
    game._commit(game.players[0], 100)
    game._commit(game.players[1], 200)
    game._commit(game.players[2], 300)
    game._commit(game.players[3], 300)
    pots = game.buildPots()
    game._showdown()
    assert pots[0][0] == 400
    assert pots[1][0] == 300
    assert pots[2][0] == 200
    assert game.players[0].stack == 400
    assert game.players[1].stack == 0
    assert game.players[2].stack == 500
    assert game.pot == 0

def test_chop_pot():
    players = [Player("A"), Player("B"), Player("C")]
    game = Game(0, 1, 2, players, 2000)
    game.players[0].stack = 300
    game.players[1].stack = 300
    game.players[2].stack = 300
    game.board = [(3, 's'), (4, 's'), (5, 's'), (6, 's'), (7, 's')]
    game.players[0].cards = [(3, 'c'), (14, 'c')]
    game.players[1].cards = [(13, 'c'), (13, 'd')]
    game.players[2].cards = [(14, 'd'), (14, 's')]
    game._commit(game.players[0], 250)
    game._commit(game.players[1], 250)
    game._commit(game.players[2], 250)
    game._showdown()
    assert game.players[0].stack == 300
    assert game.players[1].stack == 300
    assert game.players[2].stack == 300
    assert game.pot == 0

def test_uncalled_excess_returns_to_only_contributor():
    players = [Player("A"), Player("B"), Player("C")]
    game = Game(0, 1, 2, players, 2000)
    game.players[0].stack = 300
    game.players[1].stack = 300
    game.players[2].stack = 600
    game.board = [(3, 's'), (4, 's'), (5, 's'), (6, 's'), (7, 's')]
    game.players[0].cards = [(3, 'c'), (14, 'c')]
    game.players[1].cards = [(13, 'c'), (13, 'd')]
    game.players[2].cards = [(14, 'd'), (14, 's')]
    game._commit(game.players[0], 300)
    game._commit(game.players[1], 300)
    game._commit(game.players[2], 600)
    game._showdown()
    assert game.players[0].stack == 300
    assert game.players[1].stack == 300
    assert game.players[2].stack == 600
    assert game.pot == 0

def test_chop_odd_pot_awarded_to_lowest_index():
    players = [Player("A"), Player("B"), Player("C")]
    game = Game(0, 1, 2, players, 2000)
    game.players[0].stack = 300
    game.players[1].stack = 300
    game.players[2].stack = 300
    game.board = [(3, 's'), (2, 'd'), (3, 'd'), (2, 's'), (7, 'c')]
    game.players[0].cards = [(2, 'c'), (14, 'c')]
    game.players[1].cards = [(3, 'h'), (13, 'd')]
    game.players[2].cards = [(3, 'c'), (14, 's')]
    game._commit(game.players[0], 11)
    game._commit(game.players[1], 200)
    game._commit(game.players[2], 200)
    game.players[0].folded = True
    game._showdown()
    assert game.players[0].stack == 289
    assert game.players[1].stack == 306
    assert game.players[2].stack == 305
    assert game.pot == 0

