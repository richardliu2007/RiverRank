from game.hand_evaluation import evaluate_7

#ace is 14
#(rank, suit)

def test_high():
    sevenCards = [(3, 's'), (5, 'd'), (4, 'c'), (6, 'h'), (14, 's'), (12, 's'), (11, 's')]
    assert evaluate_7(sevenCards) == (1, 14, 12, 11, 6, 5)

def test_pair():
    sevenCards = [(3, 's'), (5, 'd'), (3, 'c'), (6, 'h'), (14, 's'), (12, 's'), (11, 's')]
    assert evaluate_7(sevenCards) == (2, 3, 14, 12, 11)

def test_2_pair():
    sevenCards = [(3, 's'), (5, 'd'), (3, 'c'), (5, 'h'), (14, 's'), (12, 's'), (11, 's')]
    assert evaluate_7(sevenCards) == (3, 5, 3, 14)

def test_trips():
    sevenCards = [(3, 's'), (5, 'd'), (3, 'c'), (3, 'h'), (14, 's'), (12, 's'), (11, 's')]
    assert evaluate_7(sevenCards) == (4, 3, 14, 12)

def test_straight():
    sevenCards = [(3, 's'), (4, 'd'), (5, 'c'), (6, 'h'), (7, 's'), (2, 's'), (11, 's')]
    assert evaluate_7(sevenCards) == (5, 7)

def test_wheel():
    sevenCards = [(3, 's'), (4, 'd'), (5, 'c'), (2, 'h'), (14, 's'), (12, 's'), (11, 's')]
    assert evaluate_7(sevenCards) == (5, 5)

def test_flush():
    sevenCards = [(3, 'h'), (4, 'h'), (5, 'c'), (14, 'h'), (7, 'h'), (12, 'h'), (11, 'h')]
    assert evaluate_7(sevenCards) == (6, 14, 12, 11, 7, 4)

def test_boat():
    sevenCards = [(3, 's'), (5, 'd'), (3, 'c'), (3, 'h'), (5, 's'), (4, 's'), (4, 'd')]
    assert evaluate_7(sevenCards) == (7, 3, 5)

def test_quads():
    sevenCards = [(3, 's'), (3, 'd'), (3, 'c'), (3, 'h'), (5, 's'), (4, 's'), (4, 'd')]
    assert evaluate_7(sevenCards) == (8, 3, 5)  

def test_straight_flush():
    sevenCards = [(3, 's'), (4, 's'), (5, 's'), (6, 's'), (7, 's'), (2, 's'), (11, 's')]
    assert evaluate_7(sevenCards) == (9, 7) 

def test_wheel_straight_flush():
    sevenCards = [(3, 's'), (4, 's'), (5, 's'), (2, 's'), (14, 's'), (12, 's'), (11, 's')]
    assert evaluate_7(sevenCards) == (9, 5)

