from game.game_engine import Game, Player
import pytest

def test_next_seat_returns_next_player():
    players = [
        Player("A"),
        Player("B"),
        Player("C"),
    ]
    game = Game(1, 2, 0, players)
    assert game._nextSeat(0) == 1
    assert game._nextSeat(2) == 0

def test_next_action_seat_skips_ineligible_players():
    players = [
        Player("A"),
        Player("B", folded=True),
        Player("C", all_in=True),
        Player("D"),
    ]
    game = Game(1, 2, 0, players)
    game.action_idx = 0
    game._nextAct()
    assert game.action_idx == 3

def test_next_seat_skips_eliminated_player():
    players = [
        Player("A"),
        Player("B", eliminated=True),
        Player("C")
    ]
    game = Game(1, 2, 0, players)
    assert game._nextSeat(0) == 2

def test_next_seat_returns_none_when_no_seat_is_available():
    players = [
        Player("A"),
        Player("B", eliminated=True),
    ]
    game = Game(0, 1, 0, players)
    assert game._nextSeat(0) is None

def test_reopen_action():
    players = [
        Player("A"),
        Player("B", folded=True),
        Player("C", all_in=True),
        Player("D"),
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
        Player("A"),
        Player("B"),
        Player("C"),
        Player("D"),
    ]
    game = Game(1, 2, 0, players)
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
    game = Game(1, 2, 3, players)
    game.street = "flop"
    game._startStreet()
    assert game.street == "preflop"

def test_start_street_selects_first_player_who_can_act():
    players = [
        Player("Dealer"),
        Player("Folded", folded=True),
        Player("All-in", all_in=True),
        Player("Actor"),
    ]
    game = Game(1, 2, 0, players)
    game.street = "flop"
    game._startStreet()
    assert game.action_idx == 3

def total_chips(game):
    return sum(player.stack for player in game.players) + game.pot

def test_commit_updates_all_chip_locations():
    player = Player("A")
    game = Game(0, 1, 0, [player, Player("B")])
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
    game = Game(0, 1, 0, [player, Player("B")])
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
    game = Game(0, 1, 0, [player, Player("B")])
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
    game = Game(1, 2, 0, players)
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
    game = Game(1, 2, 0, players)
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