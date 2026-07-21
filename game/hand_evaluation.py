#hand_evaluation.py
"""
Hand strength and corresponding value listed below:
1: high card
2: pair
3: two pair
4: trips
5: straight
6: flush
7: full house
8: four of a kind
9: straight flush
"""

#returns a tuple (value of straight (assume 5), max rank in straight)
def evalStraight(sevenCards):
    ranks = [card[0] for card in sevenCards]
    uniqueRanks = sorted(set(ranks), reverse=True)
    inARow = 1
    if len(uniqueRanks) < 5: return None
    for i in range(0, len(uniqueRanks) - 1):
        if uniqueRanks[i+1] == uniqueRanks[i] - 1:
            inARow += 1
            if inARow == 5:
                return (5, uniqueRanks[i-3])
        else:
            inARow = 1
    if 14 in uniqueRanks and 2 in uniqueRanks and 3 in uniqueRanks and 4 in uniqueRanks and 5 in uniqueRanks:
        return (5, 5)
    return None


def evalStraightFlush(sevenCards): #input the 2 player cards and 5 board cards
    suits = {'s': [], 'c': [], 'h': [], 'd': []}
    for rank, suit in sevenCards:
        suits[suit].append((rank, suit))
    for suited_cards in suits.values():
        if len(suited_cards) >= 5:
            straight = evalStraight(suited_cards)
            if straight is not None:
                return (9, straight[1])
    return None

def evalQuads(sevenCards):
    ranksCount = [0] * 15  # ranks 2..14, ace = 14
    for rank, suit in sevenCards:
        ranksCount[rank] += 1
    quad_rank = None
    for rank in range(14, 1, -1):
        if ranksCount[rank] == 4:
            quad_rank = rank
            break
    if quad_rank is None:
        return None
    kicker = max(rank for rank, suit in sevenCards if rank != quad_rank)
    return (8, quad_rank, kicker)

def evalTrips(sevenCards):
    ranksCount = [0] * 15  # ranks 2..14, ace = 14
    for rank, suit in sevenCards:
        ranksCount[rank] += 1
    trip_rank = None
    for rank in range(14, 1, -1):
        if ranksCount[rank] == 3:
            trip_rank = rank
            break
    if trip_rank is None:
        return None
    remaining = sorted(
        [rank for rank, suit in sevenCards if rank != trip_rank],
        reverse=True
    )
    kicker1, kicker2 = remaining[0], remaining[1]
    return (4, trip_rank, kicker1, kicker2)

def evalPair(sevenCards):
    ranksCount = [0] * 15  # ranks 2..14, ace = 14
    for rank, suit in sevenCards:
        ranksCount[rank] += 1
    pair_rank = None
    for rank in range(14, 1, -1):
        if ranksCount[rank] == 2:
            pair_rank = rank
            break
    if pair_rank is None:
        return None
    remaining = sorted(
        [rank for rank, suit in sevenCards if rank != pair_rank],
        reverse=True
    )
    kicker1, kicker2, kicker3 = remaining[0], remaining[1], remaining[2]
    return (2, pair_rank, kicker1, kicker2, kicker3)

def eval2Pair(sevenCards):
    ranksCount = [0] * 15
    for rank, suit in sevenCards:
        ranksCount[rank] += 1
    pair_ranks = []
    for rank in range(14, 1, -1):
        if ranksCount[rank] == 2:
            pair_ranks.append(rank)
    if len(pair_ranks) < 2:
        return None
    high_pair = pair_ranks[0]
    low_pair = pair_ranks[1]
    kicker = max(
        rank for rank, suit in sevenCards
        if rank != high_pair and rank != low_pair
    )
    return (3, high_pair, low_pair, kicker)

def evalFlush(sevenCards): #returns the strength of flush

    suits = {'s': [], 'c': [], 'h': [], 'd': []}
    for rank, suit in sevenCards:
        suits[suit].append(rank)
    for suit in suits:
        if len(suits[suit]) >= 5:
            top5 = tuple(sorted(suits[suit], reverse=True)[:5])
            return (6, top5[0], top5[1], top5[2], top5[3], top5[4])
    return None

def evalHigh(sevenCards):
    ranks = sorted([rank for rank, suit in sevenCards], reverse=True)
    top5 = ranks[:5]
    return (1, top5[0], top5[1], top5[2], top5[3], top5[4])

def evalBoat(sevenCards):
    ranksCount = [0] * 15
    for rank, suit in sevenCards:
        ranksCount[rank] += 1
    boatRanks = []
    for rank in range(14, 1, -1):
        if ranksCount[rank] == 3:
            boatRanks.append(rank)
            break
    if len(boatRanks) == 0:
        return None
    for rank in range(14, 1, -1):
        if ranksCount[rank] >= 2 and rank != boatRanks[0]:
            boatRanks.append(rank)
            break
    if len(boatRanks) < 2:
        return None
    main = boatRanks[0]
    full_of = boatRanks[1]
    return (7, main, full_of)


# input the 7 cards for a given player (rank, suit)
def evaluate_7(cards):
    """
    Refer to hand evaluation diagram based on max rank count and max suit count attached in references folder
    Determine the max repeat ranks and suits
    Use helper functions to evaluate hand strength
    """
    result = evalStraightFlush(cards)
    if result is not None:
        return result
    result = evalQuads(cards)
    if result is not None:
        return result
    result = evalBoat(cards)
    if result is not None:
        return result
    result = evalFlush(cards)
    if result is not None:
        return result
    result = evalStraight(cards)
    if result is not None:
        return result
    result = evalTrips(cards)
    if result is not None:
        return result
    result = eval2Pair(cards)
    if result is not None:
        return result
    result = evalPair(cards)
    if result is not None:
        return result
    return evalHigh(cards)
