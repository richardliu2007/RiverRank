from game.deck import Deck

def valid_card(card):
    rank, suit = card
    if 2 <= rank <= 14 and suit in {"s", "c", "h", "d"}: return True
    return False

def test_deal_1():
    newDeck = Deck()
    cards = newDeck.deal()
    assert len(cards) == 2
    assert len(newDeck.deck) == 50

def test_deal_4():
    newDeck = Deck()
    p1 = newDeck.deal()
    p2 = newDeck.deal()
    p3 = newDeck.deal()
    p4 = newDeck.deal() 
    assert len(p1) == 2; assert len(p2) == 2; assert len(p3) == 2; assert len(p4) == 2
    assert len(newDeck.deck) == 44
    dealt = p1 + p2 + p3 + p4
    for card in dealt: assert valid_card(card)
    assert len(set(dealt)) == 8

def test_flop():
    newDeck = Deck()
    p1 = newDeck.deal()
    p2 = newDeck.deal()
    p3 = newDeck.deal()
    p4 = newDeck.deal() 
    flop = newDeck.flop()
    assert len(p1) == 2; assert len(p2) == 2; assert len(p3) == 2; assert len(p4) == 2
    for card in flop: assert valid_card(card)
    assert len(flop) == 3
    assert len(newDeck.deck) == 40

def test_turn():
    newDeck = Deck()
    p1 = newDeck.deal()
    p2 = newDeck.deal()
    p3 = newDeck.deal()
    p4 = newDeck.deal() 
    flop = newDeck.flop()
    turn = newDeck.turn()
    assert len(p1) == 2; assert len(p2) == 2; assert len(p3) == 2; assert len(p4) == 2
    for card in flop: assert valid_card(card)
    assert len(flop) == 3
    assert valid_card(turn)
    assert len(newDeck.deck) == 38

def test_river():
    newDeck = Deck()
    p1 = newDeck.deal()
    p2 = newDeck.deal()
    p3 = newDeck.deal()
    p4 = newDeck.deal() 
    flop = newDeck.flop()
    turn = newDeck.turn()
    river = newDeck.river()
    assert len(p1) == 2; assert len(p2) == 2; assert len(p3) == 2; assert len(p4) == 2
    for card in flop: assert valid_card(card)
    assert len(flop) == 3
    assert valid_card(turn)
    assert valid_card(river)
    assert len(newDeck.deck) == 36

def test_newround():
    newDeck = Deck()
    p1 = newDeck.deal()
    p2 = newDeck.deal()
    p3 = newDeck.deal()
    p4 = newDeck.deal() 
    flop = newDeck.flop()
    turn = newDeck.turn()
    river = newDeck.river()
    assert len(p1) == 2; assert len(p2) == 2; assert len(p3) == 2; assert len(p4) == 2
    for card in flop: assert valid_card(card)
    assert len(flop) == 3
    assert valid_card(turn)
    assert valid_card(river)
    assert len(newDeck.deck) == 36
    newDeck.newRound()
    assert len(set(newDeck.deck)) == 52

def test_init():
    newDeck = Deck()
    assert len(newDeck.deck) == 52

def test_valid_deck():
    newDeck = Deck()
    assert len(set(newDeck.deck)) == 52
    expected = {
        (rank, suit)
        for rank in range(2, 15)
        for suit in {"s", "c", "h", "d"}
    }
    assert set(newDeck.deck) == expected

def test_burn():
    newDeck = Deck()
    newDeck.burn()
    assert len(newDeck.deck) == 51

