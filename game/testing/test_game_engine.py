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

# def test_start_street_one_player():
#     players = [
#         Player("A"),
#         Player("B", folded=True),
#         Player("C", folded=True),
#         Player("D", folded=True),
#     ]
#     game = Game(1, 2, 3, players, 2000)
#     game.street = "flop"
#     game._startStreet()
#     assert game.handEnded == True
#     assert game.street == "flop"

# def test_start_street_selects_first_player_who_can_act():
#     players = [
#         Player("Dealer"),
#         Player("Folded", folded=True),
#         Player("All-in", all_in=True),
#         Player("Actor"),
#     ]
#     game = Game(1, 2, 0, players, 2000)
#     game.street = "flop"
#     game._startStreet()
#     assert game.action_idx == 3

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

# def test_only_unfolded_player_wins_pot():
#     players = [
#         Player("Winner"),
#         Player("B", folded=True),
#         Player("C", folded=True),
#     ]
#     game = Game(1, 2, 0, players, 2000)
#     game.pot = 90

#     winner_stack_before = players[0].stack
#     total_before = total_chips(game)

#     game.street = "flop"
#     game._startStreet()

#     assert players[0].stack == winner_stack_before + 90
#     assert game.pot == 0
#     assert game.handEnded is True
#     assert total_chips(game) == total_before

# def test_all_in_players_run_out_board():
#     players = [
#         Player("A", all_in=True),
#         Player("B", all_in=True),
#         Player("Folded", folded=True),
#     ]
#     game = Game(1, 2, 0, players, 2000)
#     players[0].stack = 0
#     players[0].all_in = True
#     players[1].stack = 0
#     players[1].all_in = True
#     game.street = "flop"
#     game._startStreet()
#     assert len(game.board) == 5
#     assert game.street == "showdown"

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

# def test_all_in_runout_from_turn_adds_turn_and_river():
#     players = [Player("A"), Player("B")]
#     game = Game(0, 1, 0, players, 2000)
#     game.board = [(2, "s"), (7, "d"), (11, "c")]
#     game.street = "turn"
#     for player in players:
#         player.all_in = True
#         player.stack = 0
#     game._startStreet()
#     assert len(game.board) == 5
#     assert game.street == "showdown"

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

def test_build_pots_ignores_folded_only_contribution_levels():
    players = [
        Player("A"),
        Player("B"),
        Player("C"),
        Player("Folded D"),
        Player("Folded E"),
    ]
    game = Game(0, 1, 2, players, 2000)
    game.board = [(3, "s"), (3, "h"), (3, "d"), (2, "s"), (6, "c")]
    players[0].cards = [(3, "c"), (14, "c")]
    players[1].cards = [(14, "d"), (14, "s")]
    players[2].cards = [(13, "c"), (13, "d")]
    players[3].cards = [(12, "c"), (12, "d")]
    players[4].cards = [(11, "c"), (11, "d")]

    game._commit(players[0], 50)
    game._commit(players[1], 150)
    game._commit(players[2], 250)
    game._commit(players[3], 100)
    game._commit(players[4], 200)
    players[3].folded = True
    players[4].folded = True

    stacks_before = [player.stack for player in players]
    pots = game.buildPots()

    assert pots == [
        (250, [0], 0, (8, 3, 14)),
        (350, [1], 1, (7, 3, 14)),
        (150, [2], 2, (7, 3, 13)),
    ]
    assert sum(pot_amount for pot_amount, _, _, _ in pots) == game.pot == 750
    assert [player.stack for player in players] == stacks_before


def test_build_pots_counts_folded_contribution_below_first_active_level():
    players = [Player("A"), Player("B"), Player("Folded")]
    game = Game(0, 1, 2, players, 2000)
    game.board = [(3, "s"), (3, "h"), (3, "d"), (2, "s"), (6, "c")]
    players[0].cards = [(3, "c"), (14, "c")]
    players[1].cards = [(14, "d"), (14, "s")]
    players[2].cards = [(13, "c"), (13, "d")]

    game._commit(players[0], 100)
    game._commit(players[1], 200)
    game._commit(players[2], 40)
    players[2].folded = True

    assert game.buildPots() == [
        (240, [0], 0, (8, 3, 14)),
        (100, [1], 1, (7, 3, 14)),
    ]

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

def test_legal_min_raise():
    players = [Player("A"), Player("B"), Player("C")]
    game = Game(0, 1, 2, players, 2000)
    game.players[0].stack = 300
    game.players[1].stack = 300
    game.players[2].stack = 300
    game.street = "flop"
    game.action_idx = 0
    game._bet(game.players[0], 30)
    game._nextAct()
    game._raise(game.players[1], 60)
    assert game.pot == 90

def test_undersize_raise():
    players = [Player("A"), Player("B"), Player("C")]
    game = Game(0, 1, 2, players, 2000)
    game.players[0].stack = 300
    game.players[1].stack = 300
    game.players[2].stack = 300
    game.street = "flop"
    game.action_idx = 0
    game._bet(game.players[0], 30)
    game._nextAct()
    with pytest.raises(ValueError):
        game._raise(game.players[1], 50)
    assert game.pot == 30

def test_full_raise_large():
    players = [Player("A"), Player("B"), Player("C")]
    game = Game(0, 1, 2, players, 2000)
    game.players[0].stack = 300
    game.players[1].stack = 300
    game.players[2].stack = 300
    game.street = "flop"
    game.action_idx = 0
    game._bet(game.players[0], 30)
    game._nextAct()
    game._raise(game.players[1], 150)
    assert game.pot == 180

def test_short_all_in_raise():
    players = [Player("A"), Player("B"), Player("C")]
    game = Game(0, 1, 2, players, 2000)
    game.players[0].stack = 300
    game.players[1].stack = 100
    game.players[2].stack = 300
    game.street = "flop"
    game.action_idx = 0
    game._bet(game.players[0], 60)
    game._nextAct()
    game._raise(game.players[1], 100)
    assert game.pot == 160
    assert game.outstanding_bet == 100
    assert game.toRaise == 60  # previous full raise increment remains
    assert players[1].all_in is True

def test_over_raise():
    players = [Player("A"), Player("B"), Player("C")]
    game = Game(0, 1, 2, players, 2000)
    game.players[0].stack = 300
    game.players[1].stack = 300
    game.players[2].stack = 300
    game.street = "flop"
    game.action_idx = 0
    game._bet(game.players[0], 60)
    game._nextAct()
    game._raise(game.players[1], 100000)
    assert game.pot == 360

def test_preflop_minimum_raise_is_big_blind():
    players = [Player("A"), Player("B"), Player("C")]
    game = Game(0, 1, 2, players, 2000)
    game._startHand()
    with pytest.raises(ValueError):
        game._raise(game.players[game.action_idx], 30)
    assert game.outstanding_bet == 20
    assert game.toRaise == 20

def test_BB_check_or_raise_when_preflop_limp_around():
    players = [Player("A"), Player("B"), Player("C")]
    game = Game(0, 1, 2, players, 2000)
    game.players[0].stack = 300
    game.players[1].stack = 100
    game.players[2].stack = 300
    game._startHand()
    game._call(game.players[0])
    game._nextAct()
    game._call(game.players[1])
    actionsC = game.legalActions(game.players[2], False)
    assert actionsC["call"] == False
    assert actionsC["bet"] == False
    assert actionsC["check"] == True
    assert actionsC["raise"] == True
    assert actionsC["fold"] is True

def test_preflop_runout_deals_five_cards():
    players = [Player("A"), Player("B"), Player("C")]
    game = Game(0, 1, 2, players, 2000)
    game.street = "preflop"
    game._runoutBoard()
    assert len(game.board) == 5
    assert game.street == "showdown"

def test_cannot_reraise_if_acted_and_facing_short_all_in_raise():
    players = [Player("A"), Player("B"), Player("C")]
    game = Game(0, 1, 2, players, 2000)
    game.players[0].stack = 300
    game.players[1].stack = 100
    game.players[2].stack = 300
    game.street = "flop"
    game.action_idx = 0
    game._bet(game.players[0], 60)
    game._nextAct()
    game._raise(game.players[1], 100)
    game._nextAct()
    game._call(game.players[2])
    game._nextAct()
    actionsA = game.legalActions(game.players[0], True, True)
    assert actionsA["raise"] == False

def test_first_player_to_act_on_street_actions():
    players = [Player("A"), Player("B"), Player("C")]
    game = Game(0, 1, 2, players, 2000)
    game.players[0].stack = 300
    game.players[1].stack = 100
    game.players[2].stack = 300
    game.street = "flop"
    game._startStreet()
    actionsA = game.legalActions(game.players[0], False)
    assert game.action_idx == 0
    assert actionsA["check"] == True
    assert actionsA["bet"] == True
    assert actionsA["call"] == False
    assert actionsA["raise"] == False

def test_second_player_to_act_on_street_after_bet_actions():
    players = [Player("A"), Player("B"), Player("C")]
    game = Game(0, 1, 2, players, 2000)
    game.players[0].stack = 300
    game.players[1].stack = 100
    game.players[2].stack = 300
    game.street = "flop"
    game._startStreet()
    game.action_idx = 0
    game._bet(game.players[0], 50)
    actionsB = game.legalActions(game.players[1], False)
    assert actionsB["check"] == False
    assert actionsB["bet"] == False
    assert actionsB["call"] == True
    assert actionsB["raise"] == True 

def test_second_player_to_act_on_street_after_bet_actions_if_cannot_raise():
    players = [Player("A"), Player("B"), Player("C")]
    game = Game(0, 1, 2, players, 2000)
    game.players[0].stack = 300
    game.players[1].stack = 100
    game.players[2].stack = 300
    game.street = "flop"
    game._startStreet()
    game.action_idx = 0
    game._bet(game.players[0], 200)
    actionsB = game.legalActions(game.players[1], False)
    assert actionsB["check"] == False
    assert actionsB["bet"] == False
    assert actionsB["call"] == True
    assert actionsB["raise"] == False

def test_heads_up_button_is_small_blind():
    players = [Player("A"), Player("B"), Player("C")]
    game = Game(0, 1, 2, players, 2000)
    game.players[0].stack = 300
    game.players[1].stack = 100
    game.players[2].stack = 0
    game.players[2].eliminated = True
    game._startHand()
    assert game.btn_idx == game.sb_idx


def test_heads_up_other_player_is_big_blind():
    players = [Player("A"), Player("B"), Player("C")]
    game = Game(0, 1, 2, players, 2000)
    game.players[0].stack = 0
    game.players[1].stack = 100
    game.players[2].stack = 200
    game.players[0].eliminated = True
    game._startHand()
    assert game.btn_idx == 1
    assert game.bb_idx == 2
    assert game.sb_idx == 1

def test_heads_up_button_acts_first_preflop():
    players = [Player("A"), Player("B"), Player("C")]
    game = Game(0, 1, 2, players, 2000)
    game.players[0].stack = 0
    game.players[1].stack = 100
    game.players[2].stack = 200
    game.players[0].eliminated = True
    game._startHand()
    assert game.action_idx == game.btn_idx

def test_heads_up_big_blind_acts_first_postflop():
    players = [Player("A"), Player("B"), Player("C")]
    game = Game(0, 1, 2, players, 2000)
    game.players[0].stack = 0
    game.players[1].stack = 100
    game.players[2].stack = 200
    game.players[0].eliminated = True
    game._startHand()
    game._flop()
    assert game.action_idx == game.bb_idx

def test_heads_up_button_alternates_each_hand():
    players = [Player("A"), Player("B"), Player("C")]
    game = Game(0, 1, 2, players, 2000)
    game.players[0].stack = 0
    game.players[1].stack = 100
    game.players[2].stack = 200
    game.players[0].eliminated = True
    game._startHand()
    assert game.btn_idx == 1
    game._startHand()
    assert game.btn_idx == 2

def create_heads_up_game(sb_stack, bb_stack):
    players = [Player("SB"), Player("BB")]
    game = Game(0, 1, 1, players, 2_000)

    # _startHand() advances the button from seat 1 to seat 0,
    # making seat 0 the button/small blind.
    players[0].stack = sb_stack
    players[1].stack = bb_stack
    game._startHand()

    assert game.sb_idx == 0
    assert game.bb_idx == 1
    return game, players

def test_heads_up_short_small_blind_is_skipped_as_actor():
    game, players = create_heads_up_game(sb_stack=5, bb_stack=100)

    assert players[0].all_in is True
    assert players[0].street_bet == 5
    assert game.action_idx == game.bb_idx
    assert players[game.action_idx].all_in is False

def test_heads_up_short_big_blind_sets_actual_outstanding_bet():
    game, players = create_heads_up_game(sb_stack=100, bb_stack=15)

    small_blind = players[game.sb_idx]
    big_blind = players[game.bb_idx]

    assert small_blind.street_bet == 10
    assert big_blind.street_bet == 15
    assert big_blind.all_in is True
    assert game.outstanding_bet == 15
    assert game.action_idx == game.sb_idx

    actions = game.legalActions(small_blind, False)

    assert actions["call"] is True
    assert game.outstanding_bet - small_blind.street_bet == 5

def test_big_blind_shorter_than_small_blind_requires_no_call():
    game, players = create_heads_up_game(sb_stack=100, bb_stack=5)

    small_blind = players[game.sb_idx]
    big_blind = players[game.bb_idx]

    assert small_blind.street_bet == 10
    assert big_blind.street_bet == 5
    assert big_blind.all_in is True
    assert game.outstanding_bet == 10

    actions = game.legalActions(small_blind, False)

    assert actions["call"] is False
    assert actions["check"] is True
    assert game._checkRunoutNeeded() is True

def test_runout_does_not_skip_remaining_call_decision():
    game, players = create_heads_up_game(sb_stack=100, bb_stack=15)

    actor = players[game.action_idx]
    actions = game.legalActions(actor, False)
    available_actions = [
        action
        for action, allowed in actions.items()
        if allowed
    ]
    assert game._checkRunoutNeeded() is True
    assert "call" in available_actions
    should_run_out = (
        "call" not in available_actions
        and game._checkRunoutNeeded()
    )
    assert should_run_out is False

@pytest.mark.parametrize("invalid_action", [
    None,
    "check",
    ["check"],
    42,
])
def test_apply_action_rejects_invalid_input_types(invalid_action):
    players = [Player("A"), Player("B"), Player("C")]
    game = Game(0, 1, 2, players, 100)
    game.street = "flop"
    game.action_idx = 0
    result = game.applyAction(players[0], invalid_action)
    assert result is False
    assert game.action_idx == 0
    assert game.pot == 0
    assert players[0].stack == 100
    assert players[0].to_act is True

def test_apply_action_rejects_nonexistent_player():
    players = [Player("A"), Player("B"), Player("C")]
    game = Game(0, 1, 2, players, 100)
    game.street = "flop"
    game.action_idx = 0
    nonexistent_player = Player("Not seated", stack=100)
    result = game.applyAction(
        nonexistent_player,
        {"action": "check", "amount": None},
    )
    assert result is False
    assert game.action_idx == 0
    assert game.pot == 0
    assert players[0].to_act is True

def test_apply_action_rejects_player_without_current_action():
    players = [Player("A"), Player("B"), Player("C")]
    game = Game(0, 1, 2, players, 100)
    game.street = "flop"
    game.action_idx = 0
    result = game.applyAction(
        players[1],
        {"action": "check", "amount": None},
    )
    assert result is False
    assert game.action_idx == 0
    assert game.pot == 0
    assert players[0].to_act is True
    assert players[1].to_act is True

@pytest.mark.parametrize("invalid_choice", [
    "dance",
    "call",  # A call is unavailable when there is no outstanding bet.
])
def test_apply_action_rejects_invalid_action_choices(invalid_choice):
    players = [Player("A"), Player("B"), Player("C")]
    game = Game(0, 1, 2, players, 100)
    game.street = "flop"
    game.action_idx = 0
    game.outstanding_bet = 0
    result = game.applyAction(
        players[0],
        {"action": invalid_choice, "amount": None},
    )
    assert result is False
    assert game.action_idx == 0
    assert game.pot == 0
    assert players[0].stack == 100
    assert players[0].to_act is True

@pytest.mark.parametrize("invalid_amount", [
    "20",
    20.0,
    True,
])
def test_apply_action_rejects_invalid_amount_typing(invalid_amount):
    players = [Player("A"), Player("B"), Player("C")]
    game = Game(0, 1, 2, players, 100)
    game.street = "flop"
    game.action_idx = 0
    game.outstanding_bet = 0
    result = game.applyAction(
        players[0],
        {"action": "bet", "amount": invalid_amount},
    )
    assert result is False
    assert game.action_idx == 0
    assert game.pot == 0
    assert players[0].stack == 100
    assert players[0].street_bet == 0
    assert players[0].total_bet == 0

def test_apply_action_check_preserves_chips_and_advances_action():
    players = [Player("A"), Player("B"), Player("C")]
    game = Game(0, 1, 2, players, 100)
    game.street = "flop"
    game.action_idx = 0
    game.outstanding_bet = 0
    actor = players[0]
    chips_before = sum(player.stack for player in players) + game.pot
    result = game.applyAction(
        actor,
        {"action": "check", "amount": None},
    )
    chips_after = sum(player.stack for player in players) + game.pot
    assert result is True
    assert chips_after == chips_before
    assert actor.stack == 100
    assert actor.street_bet == 0
    assert actor.total_bet == 0
    assert game.pot == 0
    assert actor.to_act is False
    assert game.action_idx == 1

def test_apply_action_fold_preserves_chips_and_advances_action():
    players = [Player("A"), Player("B"), Player("C")]
    game = Game(0, 1, 2, players, 100)
    game.street = "flop"
    game.action_idx = 0
    actor = players[0]
    chips_before = sum(player.stack for player in players) + game.pot
    result = game.applyAction(
        actor,
        {"action": "fold", "amount": None},
    )
    chips_after = sum(player.stack for player in players) + game.pot
    assert result is True
    assert chips_after == chips_before
    assert actor.stack == 100
    assert actor.street_bet == 0
    assert actor.total_bet == 0
    assert game.pot == 0
    assert actor.folded is True
    assert actor.to_act is False
    assert game.action_idx == 1

def test_apply_action_call_matches_bet_conserves_chips_and_advances_action():
    players = [Player("A"), Player("B"), Player("C")]
    game = Game(0, 1, 2, players, 100)
    game.street = "flop"
    game.action_idx = 0
    actor = players[0]
    bettor = players[2]
    actor.stack = 80
    actor.street_bet = 20
    actor.total_bet = 20
    bettor.stack = 50
    bettor.street_bet = 50
    bettor.total_bet = 50
    bettor.to_act = False
    game.outstanding_bet = 50
    game.toRaise = 20
    game.pot = 70
    chips_before = sum(player.stack for player in players) + game.pot
    result = game.applyAction(
        actor,
        {"action": "call", "amount": None},
    )
    chips_after = sum(player.stack for player in players) + game.pot
    assert result is True
    assert chips_after == chips_before
    assert actor.stack == 50
    assert actor.street_bet == game.outstanding_bet == 50
    assert actor.total_bet == 50
    assert game.pot == 100
    assert actor.to_act is False
    assert game.action_idx == 1


def test_apply_action_bet_rejects_undersized_bet():
    players = [Player("A"), Player("B"), Player("C")]
    game = Game(0, 1, 2, players, 100)
    game.street = "flop"
    game.action_idx = 0
    game.outstanding_bet = 0
    actor = players[0]
    chips_before = sum(player.stack for player in players) + game.pot
    result = game.applyAction(
        actor,
        {"action": "bet", "amount": 10},
    )
    chips_after = sum(player.stack for player in players) + game.pot
    assert result is False
    assert chips_after == chips_before
    assert actor.stack == 100
    assert actor.street_bet == 0
    assert actor.total_bet == 0
    assert actor.to_act is True
    assert game.pot == 0
    assert game.outstanding_bet == 0
    assert game.action_idx == 0

def test_apply_action_bet_accepts_short_all_in_bet():
    players = [Player("A"), Player("B"), Player("C")]
    game = Game(0, 1, 2, players, 100)
    game.street = "flop"
    game.action_idx = 0
    game.outstanding_bet = 0
    actor = players[0]
    actor.stack = 10
    chips_before = sum(player.stack for player in players) + game.pot
    result = game.applyAction(
        actor,
        {"action": "bet", "amount": 10},
    )
    chips_after = sum(player.stack for player in players) + game.pot
    assert result is True
    assert chips_after == chips_before
    assert actor.stack == 0
    assert actor.street_bet == 10
    assert actor.total_bet == 10
    assert actor.all_in is True
    assert actor.to_act is False
    assert game.pot == 10
    assert game.outstanding_bet == 10
    assert game.toRaise == 10
    assert game.action_idx == 1

def test_apply_action_bet_conserves_chips_and_advances_action():
    players = [Player("A"), Player("B"), Player("C")]
    game = Game(0, 1, 2, players, 100)
    game.street = "flop"
    game.action_idx = 0
    game.outstanding_bet = 0
    actor = players[0]
    chips_before = sum(player.stack for player in players) + game.pot
    result = game.applyAction(
        actor,
        {"action": "bet", "amount": 40},
    )
    chips_after = sum(player.stack for player in players) + game.pot
    assert result is True
    assert chips_after == chips_before
    assert actor.stack == 60
    assert actor.street_bet == 40
    assert actor.total_bet == 40
    assert actor.to_act is False
    assert game.pot == 40
    assert game.outstanding_bet == 40
    assert game.toRaise == 40
    assert game.action_idx == 1

def test_apply_action_raise_rejects_undersized_raise():
    players = [Player("A"), Player("B"), Player("C")]
    game = Game(0, 1, 2, players, 100)
    game.street = "flop"
    game.action_idx = 0
    actor = players[0]
    bettor = players[2]
    actor.stack = 80
    actor.street_bet = 20
    actor.total_bet = 20
    bettor.stack = 50
    bettor.street_bet = 50
    bettor.total_bet = 50
    bettor.to_act = False
    game.pot = 70
    game.outstanding_bet = 50
    game.toRaise = 20
    chips_before = sum(player.stack for player in players) + game.pot
    result = game.applyAction(
        actor,
        {"action": "raise", "amount": 60},
    )
    chips_after = sum(player.stack for player in players) + game.pot
    assert result is False
    assert chips_after == chips_before
    assert actor.stack == 80
    assert actor.street_bet == 20
    assert actor.total_bet == 20
    assert actor.to_act is True
    assert game.pot == 70
    assert game.outstanding_bet == 50
    assert game.toRaise == 20
    assert game.action_idx == 0

def test_apply_action_raise_accepts_short_all_in_raise():
    players = [Player("A"), Player("B"), Player("C")]
    game = Game(0, 1, 2, players, 100)
    game.street = "flop"
    game.action_idx = 0
    actor = players[0]
    bettor = players[2]
    actor.stack = 40
    actor.street_bet = 20
    actor.total_bet = 20
    bettor.stack = 50
    bettor.street_bet = 50
    bettor.total_bet = 50
    bettor.to_act = False
    game.pot = 70
    game.outstanding_bet = 50
    game.toRaise = 20
    chips_before = sum(player.stack for player in players) + game.pot
    result = game.applyAction(
        actor,
        {"action": "raise", "amount": 60},
    )
    chips_after = sum(player.stack for player in players) + game.pot
    assert result is True
    assert chips_after == chips_before
    assert actor.stack == 0
    assert actor.street_bet == 60
    assert actor.total_bet == 60
    assert actor.all_in is True
    assert actor.to_act is False
    assert game.pot == 110
    assert game.outstanding_bet == 60
    # A short raise does not change the previous full-raise increment.
    assert game.toRaise == 20
    assert game.action_idx == 1

def test_apply_action_raise_conserves_chips_and_advances_action():
    players = [Player("A"), Player("B"), Player("C")]
    game = Game(0, 1, 2, players, 100)
    game.street = "flop"
    game.action_idx = 0
    actor = players[0]
    bettor = players[2]
    actor.stack = 80
    actor.street_bet = 20
    actor.total_bet = 20
    bettor.stack = 50
    bettor.street_bet = 50
    bettor.total_bet = 50
    bettor.to_act = False
    game.pot = 70
    game.outstanding_bet = 50
    game.toRaise = 20
    chips_before = sum(player.stack for player in players) + game.pot
    result = game.applyAction(
        actor,
        {"action": "raise", "amount": 70},
    )
    chips_after = sum(player.stack for player in players) + game.pot
    assert result is True
    assert chips_after == chips_before
    assert actor.stack == 30
    assert actor.street_bet == 70
    assert actor.total_bet == 70
    assert actor.to_act is False
    assert game.pot == 120
    assert game.outstanding_bet == 70
    assert game.toRaise == 20
    assert game.action_idx == 1

def test_apply_action_accepts_short_all_in_call():
    players = [Player("A"), Player("B"), Player("C")]
    game = Game(0, 1, 2, players, 100)
    game.street = "flop"
    game.action_idx = 0
    actor = players[0]
    bettor = players[2]
    actor.stack = 20
    actor.street_bet = 20
    actor.total_bet = 20
    bettor.stack = 50
    bettor.street_bet = 50
    bettor.total_bet = 50
    bettor.to_act = False
    game.pot = 70
    game.outstanding_bet = 50
    game.toRaise = 20
    chips_before = sum(player.stack for player in players) + game.pot
    result = game.applyAction(
        actor,
        {"action": "call", "amount": None},
    )
    chips_after = sum(player.stack for player in players) + game.pot
    assert result is True
    assert chips_after == chips_before
    assert actor.stack == 0
    assert actor.street_bet == 40
    assert actor.total_bet == 40
    assert actor.street_bet < game.outstanding_bet
    assert actor.all_in is True
    assert actor.to_act is False
    assert game.pot == 90
    assert game.outstanding_bet == 50
    assert game.action_idx == 1


@pytest.mark.parametrize(
    "ineligible_state",
    [
        "folded",
        "eliminated",
        "all_in",
        "already_acted",
    ],
)
def test_apply_action_rejects_ineligible_current_player(ineligible_state):
    players = [Player("A"), Player("B"), Player("C")]
    game = Game(0, 1, 2, players, 100)
    game.street = "flop"
    game.action_idx = 0
    actor = players[0]
    if ineligible_state == "folded":
        actor.folded = True
    elif ineligible_state == "eliminated":
        actor.eliminated = True
        actor.stack = 0
    elif ineligible_state == "all_in":
        actor.all_in = True
        actor.stack = 0
    elif ineligible_state == "already_acted":
        actor.to_act = False
    state_before = (
        game.action_idx,
        game.pot,
        actor.stack,
        actor.street_bet,
        actor.total_bet,
        actor.folded,
        actor.eliminated,
        actor.all_in,
        actor.to_act,
    )
    result = game.applyAction(
        actor,
        {"action": "fold", "amount": None},
    )
    state_after = (
        game.action_idx,
        game.pot,
        actor.stack,
        actor.street_bet,
        actor.total_bet,
        actor.folded,
        actor.eliminated,
        actor.all_in,
        actor.to_act,
    )
    assert result is False
    assert state_after == state_before


@pytest.mark.parametrize(
    "action_request",
    [
        pytest.param(
            {"action": "bet"},
            id="bet-missing-amount",
        ),
        pytest.param(
            {"action": "bet", "amount": None},
            id="bet-none-amount",
        ),
        pytest.param(
            {"action": "bet", "amount": "20"},
            id="bet-string-amount",
        ),
        pytest.param(
            {"action": "bet", "amount": 20.0},
            id="bet-float-amount",
        ),
        pytest.param(
            {"action": "bet", "amount": True},
            id="bet-boolean-amount",
        ),
        pytest.param(
            {"action": "raise"},
            id="raise-missing-amount",
        ),
        pytest.param(
            {"action": "raise", "amount": None},
            id="raise-none-amount",
        ),
        pytest.param(
            {"action": "raise", "amount": "70"},
            id="raise-string-amount",
        ),
        pytest.param(
            {"action": "raise", "amount": 70.0},
            id="raise-float-amount",
        ),
        pytest.param(
            {"action": "raise", "amount": True},
            id="raise-boolean-amount",
        ),
    ],
)
def test_apply_action_rejects_missing_or_invalid_sized_action_amount(
    action_request,
):
    players = [Player("A"), Player("B"), Player("C")]
    game = Game(0, 1, 2, players, 100)
    game.street = "flop"
    game.action_idx = 0
    actor = players[0]
    if action_request["action"] == "raise":
        bettor = players[2]
        actor.stack = 80
        actor.street_bet = 20
        actor.total_bet = 20
        bettor.stack = 50
        bettor.street_bet = 50
        bettor.total_bet = 50
        bettor.to_act = False
        game.pot = 70
        game.outstanding_bet = 50
        game.toRaise = 20
    state_before = (
        game.action_idx,
        game.pot,
        game.outstanding_bet,
        game.toRaise,
        actor.stack,
        actor.street_bet,
        actor.total_bet,
        actor.to_act,
    )
    result = game.applyAction(actor, action_request)
    state_after = (
        game.action_idx,
        game.pot,
        game.outstanding_bet,
        game.toRaise,
        actor.stack,
        actor.street_bet,
        actor.total_bet,
        actor.to_act,
    )
    assert result is False
    assert state_after == state_before

def test_apply_action_full_raise_reopens_action_for_other_eligible_players():
    players = [Player("A"), Player("B"), Player("C")]
    game = Game(0, 1, 2, players, 100)
    game.street = "flop"
    game.action_idx = 0
    actor = players[0]
    next_player = players[1]
    previous_bettor = players[2]
    actor.stack = 80
    actor.street_bet = 20
    actor.total_bet = 20
    next_player.to_act = False
    previous_bettor.stack = 50
    previous_bettor.street_bet = 50
    previous_bettor.total_bet = 50
    previous_bettor.to_act = False
    game.pot = 70
    game.outstanding_bet = 50
    game.toRaise = 20
    chips_before = sum(player.stack for player in players) + game.pot
    result = game.applyAction(
        actor,
        {"action": "raise", "amount": 70},
    )
    chips_after = sum(player.stack for player in players) + game.pot
    assert result is True
    assert chips_after == chips_before
    assert actor.stack == 30
    assert actor.street_bet == 70
    assert actor.total_bet == 70
    assert actor.to_act is False
    assert next_player.to_act is True
    assert previous_bettor.to_act is True
    assert game.pot == 120
    assert game.outstanding_bet == 70
    assert game.toRaise == 20
    assert game.action_idx == 1

from game.game_controller import cardFormatter

@pytest.mark.parametrize(
    ("street", "board"),
    [
        pytest.param(
            "preflop",
            [],
            id="preflop",
        ),
        pytest.param(
            "flop",
            [(2, "c"), (7, "d"), (11, "s")],
            id="flop",
        ),
        pytest.param(
            "turn",
            [(2, "c"), (7, "d"), (11, "s"), (14, "h")],
            id="turn",
        ),
        pytest.param(
            "river",
            [(2, "c"), (7, "d"), (11, "s"), (14, "h"), (10, "c")],
            id="river",
        ),
    ],
)
def test_get_visible_state_returns_expected_three_handed_state(
    street,
    board,
):
    players = [
        Player("Alice"),
        Player("Bob"),
        Player("Carol"),
    ]
    game = Game(0, 1, 2, players, 100)
    viewer = players[1]
    players[0].stack = 90
    players[0].street_bet = 10
    viewer.stack = 80
    viewer.street_bet = 20
    viewer.cards = [(14, "h"), (13, "h")]
    players[2].stack = 70
    players[2].street_bet = 30
    game.street = street
    game.board = board
    game.pot = 60
    game.action_idx = 0
    game.btn_idx = 2
    result = game.getVisibleState(viewer)
    assert result == {
        "yourID": 1,
        "actionID": 0,
        "buttonID": 2,
        "players": {
            0: {
                "name": "Alice",
                "stack": 90,
                "streetBet": 10,
                "folded": False,
                "allIn": False,
            },
            1: {
                "name": "Bob",
                "stack": 80,
                "streetBet": 20,
                "folded": False,
                "allIn": False,
            },
            2: {
                "name": "Carol",
                "stack": 70,
                "streetBet": 30,
                "folded": False,
                "allIn": False,
            },
        },
        "board": " ".join(cardFormatter(card) for card in board),
        "hand": " ".join(
            cardFormatter(card)
            for card in viewer.cards
        ),
        "pot": 60,
    }

def test_get_visible_state_returns_public_information_for_other_players():
    players = [
        Player("Alice"),
        Player("Bob"),
        Player("Carol"),
    ]
    game = Game(0, 1, 2, players, 500)
    viewer = players[0]
    opponent_one = players[1]
    opponent_two = players[2]
    viewer.cards = [(14, "s"), (14, "d")]
    viewer.stack = 450
    viewer.street_bet = 50
    opponent_one.cards = [(13, "s"), (13, "d")]
    opponent_one.stack = 375
    opponent_one.street_bet = 125
    opponent_one.folded = True
    opponent_two.cards = [(2, "c"), (7, "h")]
    opponent_two.stack = 0
    opponent_two.street_bet = 200
    opponent_two.all_in = True
    game.board = [(10, "h"), (9, "h"), (8, "c")]
    game.pot = 375
    game.action_idx = 2
    game.btn_idx = 1
    result = game.getVisibleState(viewer)
    assert result["yourID"] == 0
    assert result["actionID"] == 2
    assert result["buttonID"] == 1
    assert result["pot"] == 375
    assert result["players"][1] == {
        "name": "Bob",
        "stack": 375,
        "streetBet": 125,
        "folded": True,
        "allIn": False,
    }
    assert result["players"][2] == {
        "name": "Carol",
        "stack": 0,
        "streetBet": 200,
        "folded": False,
        "allIn": True,
    }
    expected_public_fields = {
        "name",
        "stack",
        "streetBet",
        "folded",
        "allIn",
    }
    assert set(result["players"][1]) == expected_public_fields
    assert set(result["players"][2]) == expected_public_fields
    # Only the requesting player's private cards are returned.
    assert result["hand"] == " ".join(
        cardFormatter(card)
        for card in viewer.cards
    )